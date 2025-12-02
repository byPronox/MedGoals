from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MedGoalDefinition(models.Model):
    _name = "med.goal.definition"
    _description = "Goal Definition"
    _order = "name asc, id asc"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    area_id = fields.Many2one("med.area", string="Area")
    specialty_id = fields.Many2one("med.specialty", string="Specialty")
    description = fields.Text()

    target_type = fields.Selection(
        [
            ("numeric", "Numeric"),
            ("percentage", "Percentage"),
            ("monetary", "Monetary"),
        ],
        default="numeric",
        required=True,
    )
    default_target_value = fields.Float(string="Default Target")
    weight = fields.Float(
        string="Goal Weight",
        help="Relative importance of this goal in scoring (0-1 or 0-100 depending on configuration).",
        default=1.0,
    )
    active = fields.Boolean(default=True)

    assignment_ids = fields.One2many(
        "med.goal.assignment",
        "goal_id",
        string="Assignments",
    )
    category = fields.Selection(
        [
            ("goal", "Strategic Goal"),
            ("productivity", "Productivity Metric"),
            ("quality", "Quality Standard"),
        ],
        string="Scoring Category",
        default="goal",
        required=True,
        help="Category for the automatic calculation in the Evaluation Cycle."
    )

    _sql_constraints = [
        (
            "med_goal_definition_code_company_uniq",
            "unique (company_id, code)",
            "The goal code must be unique per company.",
        ),
    ]

    # BACK-END VALIDATION: GOAL DEFINITION DATA
    @api.constrains("weight", "default_target_value")
    def _check_weight_and_target(self):
        for rec in self:
            if rec.weight <= 0:
                raise ValidationError(
                    "Goal weight must be greater than zero."
                )
            if rec.default_target_value and rec.default_target_value < 0:
                raise ValidationError(
                    "Default target value cannot be negative."
                )
