from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
            # Optional: evita cerrar ciclos sin assignments
            # if not rec.assignment_ids:
            #     raise ValidationError(_("You cannot close a cycle without assignments."))
            rec._compute_scores()
            rec.state = "closed"

    def _compute_scores(self):
        """Compute scores per employee for this cycle and create med.employee.score records."""
        self.ensure_one()
        Score = self.env["med.employee.score"]

        # Delete existing scores for this cycle (recompute)
        old_scores = Score.search([("cycle_id", "=", self.id)])
        old_scores.unlink()

        # Group assignments by employee
        assignments = self.assignment_ids.filtered(lambda a: a.state != "cancelled")
        by_employee = {}
        for a in assignments:
            by_employee.setdefault(a.employee_id, self.env["med.goal.assignment"])
            by_employee[a.employee_id] |= a

        for employee, emp_assignments in by_employee.items():
            total_weight = 0.0
            weighted_score = 0.0
            for a in emp_assignments:
                weight = a.goal_id.weight or 0.0
                total_weight += weight
                # completion_rate 0-100 → score 0-10
                score_10 = (a.completion_rate or 0.0) / 10.0
                weighted_score += weight * score_10

            final_score = 0.0
            if total_weight:
                final_score = weighted_score / total_weight

            Score.create(
                {
                    "employee_id": employee.id,
                    "cycle_id": self.id,
                    "score_total": final_score,
                    "score_goals": final_score,
                }
            )

        # Assign rankings
        self._compute_rankings()

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

        # Mark top global performers (e.g., top 3)
        top_global = scores.sorted(lambda s: s.rank_global)[:3]
        for s in scores:
            s.is_top_performer = s in top_global
