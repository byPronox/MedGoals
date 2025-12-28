"""
Score engine with pluggable strategies.

Applies SOLID (SRP/OCP/DIP) by isolating score calculation rules
from the Odoo model and allowing new strategies/weights without
editing the model.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass
class ScoreWeights:
    goals: float
    productivity: float
    quality: float
    economic: float

    @property
    def total(self) -> float:
        return (self.goals or 0.0) + (self.productivity or 0.0) + (self.quality or 0.0) + (self.economic or 0.0)


class ScoreStrategy(ABC):
    """Base Strategy for each score component."""

    key: str

    @abstractmethod
    def compute(self, engine: "ScoreEngine", employee, assignments) -> float:
        raise NotImplementedError


class GoalsStrategy(ScoreStrategy):
    key = "goals"

    def compute(self, engine: "ScoreEngine", employee, assignments) -> float:
        goals = assignments.filtered(lambda a: a.goal_id.category == "goal")
        return engine.weighted_average(goals)


class ProductivityStrategy(ScoreStrategy):
    key = "productivity"

    def compute(self, engine: "ScoreEngine", employee, assignments) -> float:
        prod_list = assignments.filtered(lambda a: a.goal_id.category == "productivity")
        if prod_list:
            return engine.weighted_average(prod_list)

        # Fallback: logs in the cycle
        logs = engine.env["med.performance.log"].search(
            [
                ("employee_id", "=", employee.id),
                ("date", ">=", engine.cycle.date_start),
                ("date", "<=", engine.cycle.date_end),
            ]
        )
        total_val = sum(logs.mapped("metric_value"))
        return min(total_val, 10.0)


class QualityStrategy(ScoreStrategy):
    key = "quality"

    def compute(self, engine: "ScoreEngine", employee, assignments) -> float:
        quality = assignments.filtered(lambda a: a.goal_id.category == "quality")
        return engine.weighted_average(quality) if quality else 10.0


class EconomicStrategy(ScoreStrategy):
    key = "economic"

    def compute(self, engine: "ScoreEngine", employee, assignments) -> float:
        contract = engine.env["hr.contract"].search(
            [
                ("employee_id", "=", employee.id),
                ("state", "in", ["open", "draft"]),
            ],
            limit=1,
            order="date_start desc",
        )
        wage = contract.wage if contract else 0.0
        cycle_cost = (wage / 30.0) * engine.cycle_days

        monetary_goals = assignments.filtered(lambda a: a.goal_id.target_type == "monetary")
        value_generated = sum(monetary_goals.mapped("actual_value"))

        score_eco = 0.0
        if cycle_cost > 0:
            roi = (value_generated - cycle_cost) / cycle_cost
            if roi < 0:
                score_eco = max(0.0, 5.0 + (roi * 5.0))
            else:
                score_eco = min(10.0, 5.0 + (roi * 2.5))
        elif value_generated > 0:
            score_eco = 10.0

        engine.log_economic_debug(employee, wage, cycle_cost, monetary_goals, value_generated, score_eco)
        return score_eco


class ScoreEngine:
    """Aggregates strategies and weights to compute final scores."""

    def __init__(
        self,
        env,
        cycle,
        weights: ScoreWeights,
        strategies: Iterable[ScoreStrategy],
        logger: Optional[logging.Logger] = None,
    ):
        self.env = env
        self.cycle = cycle
        self.weights = weights
        self.logger = logger or logging.getLogger(__name__)
        self.cycle_days = max((cycle.date_end - cycle.date_start).days + 1, 1)
        self.strategies: Dict[str, ScoreStrategy] = {s.key: s for s in strategies}

    # Adapter/utility that keeps weighted average reusable and testable
    def weighted_average(self, assignments) -> float:
        if not assignments:
            return 0.0

        total_weight = 0.0
        weighted_score = 0.0

        for assignment in assignments:
            weight = assignment.goal_id.weight or 0.0
            score_10 = min((assignment.completion_rate or 0.0) / 10.0, 10.0)
            weighted_score += score_10 * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_score / total_weight

    def compute_components(self, employee, assignments) -> Dict[str, float]:
        results: Dict[str, float] = {}
        for key, strategy in self.strategies.items():
            results[key] = strategy.compute(self, employee, assignments)
        results["total"] = self._compute_total(results)
        return results

    def _compute_total(self, results: Dict[str, float]) -> float:
        if not self.weights.total:
            return 0.0

        total_score = (
            (results.get("goals", 0.0) * self.weights.goals)
            + (results.get("productivity", 0.0) * self.weights.productivity)
            + (results.get("quality", 0.0) * self.weights.quality)
            + (results.get("economic", 0.0) * self.weights.economic)
        )
        return total_score / self.weights.total

    # Keep debug logging encapsulated
    def log_economic_debug(self, employee, wage, cycle_cost, monetary_goals, value_generated, score_eco):
        self.logger.info(
            "EMP: %s | Wage: %s | CycleCost: %s",
            employee.name,
            wage,
            cycle_cost,
        )
        self.logger.info(
            "   -> Monetary goals: %s | Generated value: %s | Score: %s",
            len(monetary_goals),
            value_generated,
            score_eco,
        )


class ScoreEngineFactory:
    """Factory pattern to assemble a ScoreEngine from a cycle."""

    @staticmethod
    def from_cycle(env, cycle, logger: Optional[logging.Logger] = None) -> ScoreEngine:
        config = cycle.scoring_config_id
        weights = ScoreWeights(
            goals=config.weight_goals if config else 1.0,
            productivity=config.weight_productivity if config else 0.0,
            quality=config.weight_quality if config else 0.0,
            economic=config.weight_economic if config else 0.0,
        )
        if weights.total <= 0:
            # fallback to avoid division by zero
            weights = ScoreWeights(1.0, 0.0, 0.0, 0.0)

        strategies: List[ScoreStrategy] = [
            GoalsStrategy(),
            ProductivityStrategy(),
            QualityStrategy(),
            EconomicStrategy(),
        ]
        return ScoreEngine(env, cycle, weights, strategies, logger=logger)
