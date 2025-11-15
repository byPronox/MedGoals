from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MedEmployeeScore(models.Model):
    _name = "med.employee.score"
    _description = "Employee Score per Evaluation Cycle"

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
    )
    company_id = fields.Many2one(
        related="employee_id.company_id",
        store=True,
        readonly=True,
    )
    cycle_id = fields.Many2one(
        "med.evaluation.cycle",
        string="Evaluation Cycle",
        required=True,
    )

    score_total = fields.Float(
        string="Total Score (0-10)",
        required=True,
    )
    score_goals = fields.Float(
        string="Goals Score (0-10)",
        required=True,
    )
    score_productivity = fields.Float(
        string="Productivity (0-10)",
        required=True,
    )
    score_quality = fields.Float(
        string="Quality (0-10)",
        required=True,
    )
    score_economic = fields.Float(
        string="Economic Contribution (0-10)",
        required=True,
    )

    rank_global = fields.Integer(string="Global Rank")
    rank_area = fields.Integer(string="Area Rank")
    rank_specialty = fields.Integer(string="Specialty Rank")

    is_top_performer = fields.Boolean(string="Top Performer")

    _sql_constraints = [
        (
            "med_employee_score_unique_cycle",
            "unique(employee_id, cycle_id)",
            "An employee can only have one score per evaluation cycle.",
        ),
    ]

    @api.constrains(
        "score_total",
        "score_goals",
        "score_productivity",
        "score_quality",
        "score_economic",
    )
    def _check_scores_range(self):
        """Validate that all scores are between 0 and 10."""
        for record in self:
            for field_name in [
                "score_total",
                "score_goals",
                "score_productivity",
                "score_quality",
                "score_economic",
            ]:
                value = record[field_name]
                # None is not expected because fields are required, but we keep check defensive
                if value is not None and (value < 0 or value > 10):
                    raise ValidationError(
                        "All scores must be between 0 and 10. "
                        f"Field '{field_name}' has an invalid value: {value}."
                    )
