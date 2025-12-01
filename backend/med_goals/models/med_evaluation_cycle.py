import logging # <--- IMPORTANTE: AGREGAR ESTO ARRIBA
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__) # <--- IMPORTANTE

class MedEvaluationCycle(models.Model):
    _name = "med.evaluation.cycle"
    _description = "Evaluation Cycle (Period)"
    _order = "date_start desc, name"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )

    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("open", "Open"),
            ("closed", "Closed"),
        ],
        default="draft",
        required=True,
    )

    scoring_config_id = fields.Many2one(
        "med.scoring.config",
        string="Scoring Configuration",
        help="Weights to use when computing scores.",
    )

    assignment_ids = fields.One2many(
        "med.goal.assignment",
        "evaluation_cycle_id",
        string="Assignments in Cycle",
    )
    employee_score_ids = fields.One2many(
        "med.employee.score",
        "cycle_id",
        string="Employee Scores",
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique(name, company_id)",
            "The evaluation cycle name must be unique per company.",
        )
    ]

    # BACK-END VALIDATION: date_end must be >= date_start
    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(
                    _("End date must be greater than or equal to start date.")
                )

    def action_open(self):
        for rec in self:
            if rec.state != "draft":
                continue
            rec.state = "open"

    def action_close(self):
        for rec in self:
            if rec.state == "closed":
                continue
            rec._compute_scores()
            rec.state = "closed"

    def _compute_scores(self):
        self.ensure_one()
        Score = self.env["med.employee.score"]
        Score.search([("cycle_id", "=", self.id)]).unlink()

        config = self.scoring_config_id
        if not config:
            w_goals, w_prod, w_qual, w_eco = 1.0, 0.0, 0.0, 0.0
        else:
            w_goals = config.weight_goals
            w_prod = config.weight_productivity
            w_qual = config.weight_quality
            w_eco = config.weight_economic

        assignments = self.assignment_ids.filtered(lambda a: a.state != "cancelled")
        employees = assignments.mapped("employee_id")

        days_in_cycle = (self.date_end - self.date_start).days + 1
        if days_in_cycle <= 0: days_in_cycle = 1

        _logger.info(f"=== INICIANDO CÁLCULO CICLO: {self.name} (Días: {days_in_cycle}) ===")

        for employee in employees:
            emp_assignments = assignments.filtered(lambda a: a.employee_id == employee)
            
            goals_list = emp_assignments.filtered(lambda a: a.goal_id.category == 'goal')
            score_goals = self._calculate_weighted_average(goals_list)

            prod_list = emp_assignments.filtered(lambda a: a.goal_id.category == 'productivity')
            if prod_list:
                score_prod = self._calculate_weighted_average(prod_list)
            else:
                logs = self.env['med.performance.log'].search([
                    ('employee_id', '=', employee.id),
                    ('date', '>=', self.date_start),
                    ('date', '<=', self.date_end)
                ])
                total_val = sum(logs.mapped('metric_value'))
                score_prod = min(total_val, 10.0)

            qual_list = emp_assignments.filtered(lambda a: a.goal_id.category == 'quality')
            score_qual = self._calculate_weighted_average(qual_list) if qual_list else 10.0

            contract = self.env['hr.contract'].search([
                ('employee_id', '=', employee.id),
                ('state', 'in', ['open', 'draft']),
            ], limit=1, order='date_start desc')

            wage = contract.wage if contract else 0.0
            cycle_cost = (wage / 30.0) * days_in_cycle

            monetary_goals = emp_assignments.filtered(lambda a: a.goal_id.target_type == 'monetary')
            value_generated = sum(monetary_goals.mapped('actual_value'))

            score_eco = 0.0
            if cycle_cost > 0:
                roi = (value_generated - cycle_cost) / cycle_cost
                if roi < 0:
                    score_eco = max(0.0, 5.0 + (roi * 5.0))
                else:
                    score_eco = min(10.0, 5.0 + (roi * 2.5))
            elif value_generated > 0:
                score_eco = 10.0
            
            _logger.info(f"EMP: {employee.name} | Wage: {wage} | CostoCiclo: {cycle_cost}")
            _logger.info(f"   -> Metas Monetarias Encontradas: {len(monetary_goals)}")
            _logger.info(f"   -> Valor Generado (Suma Actual Value): {value_generated}")
            _logger.info(f"   -> ROI Calculado: {((value_generated - cycle_cost) / cycle_cost) if cycle_cost else 0}")
            _logger.info(f"   -> SCORE ECONOMICO FINAL: {score_eco}")

            total_score = (
                (score_goals * w_goals) +
                (score_prod * w_prod) +
                (score_qual * w_qual) +
                (score_eco * w_eco)
            )
            total_weight = w_goals + w_prod + w_qual + w_eco
            final_score = total_score / total_weight if total_weight > 0 else 0.0

            Score.create({
                "employee_id": employee.id,
                "cycle_id": self.id,
                "score_goals": score_goals,
                "score_productivity": score_prod,
                "score_quality": score_qual,
                "score_economic": score_eco,
                "score_total": final_score,
            })
        
        self._compute_rankings()

    def _calculate_weighted_average(self, assignments):
        """Helper para calcular promedio ponderado 0-10 de un set de asignaciones"""
        if not assignments:
            return 0.0
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for a in assignments:
            weight = a.goal_id.weight or 0.0
            # Completion rate es 0-100, lo pasamos a 0-10
            score_10 = (a.completion_rate or 0.0) / 10.0
            # Cap en 10 (por si completaron 120%)
            score_10 = min(score_10, 10.0)
            
            weighted_score += (score_10 * weight)
            total_weight += weight
            
        if total_weight == 0:
            return 0.0
            
        return weighted_score / total_weight

    # Global rank / AREA / ESPECIALTY
    def _compute_rankings(self):
        scores = self.employee_score_ids.sorted(lambda s: -s.score_total)

        # Global rank
        rank = 0
        last_score = None
        for s in scores:
            if last_score is None or s.score_total < last_score:
                rank += 1
                last_score = s.score_total
            s.rank_global = rank

        # Rank by area
        scores_by_area = {}
        for s in scores:
            area = s.employee_id.med_area_id
            scores_by_area.setdefault(area, self.env["med.employee.score"])
            scores_by_area[area] |= s

        for area, area_scores in scores_by_area.items():
            rank = 0
            last_score = None
            for s in area_scores.sorted(lambda r: -r.score_total):
                if last_score is None or s.score_total < last_score:
                    rank += 1
                    last_score = s.score_total
                s.rank_area = rank

        # Rank by specialty
        scores_by_spec = {}
        for s in scores:
            spec = s.employee_id.med_specialty_id
            scores_by_spec.setdefault(spec, self.env["med.employee.score"])
            scores_by_spec[spec] |= s

        for spec, spec_scores in scores_by_spec.items():
            rank = 0
            last_score = None
            for s in spec_scores.sorted(lambda r: -r.score_total):
                if last_score is None or s.score_total < last_score:
                    rank += 1
                    last_score = s.score_total
                s.rank_specialty = rank

        top_global = scores.sorted(lambda s: s.rank_global)[:3]
        for s in scores:
            s.is_top_performer = s in top_global
