from odoo import models, fields, api, _
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

    score_total = fields.Float(string="Total Score (0-10)")
    score_goals = fields.Float(string="Goals Score (0-10)")
    score_productivity = fields.Float(string="Productivity (0-10)")
    score_quality = fields.Float(string="Quality (0-10)")
    score_economic = fields.Float(string="Economic Contribution (0-10)")

    rank_global = fields.Integer(string="Global Rank")
    rank_area = fields.Integer(string="Area Rank")
    rank_specialty = fields.Integer(string="Specialty Rank")

    is_top_performer = fields.Boolean(string="Top Performer")

    # BACK-END VALIDATION: HR PERFORMANCE DATA
    @api.constrains("score_total","score_goals","score_productivity","score_quality","score_economic")
    def _check_scores_range(self):
        for record in self:
            fields_to_check = [
                ("score_total", _("Total Score")),
                ("score_goals", _("Goals Score")),
                ("score_productivity", _("Productivity Score")),
                ("score_quality", _("Quality Score")),
                ("score_economic", _("Economic Contribution Score")),
            ]
            for field_name, label in fields_to_check:
                value = record[field_name]
                if value is not False and not (0.0 <= value <= 10.0):
                    raise ValidationError(
                        _("%s must be between 0 and 10.") % label
                    )
