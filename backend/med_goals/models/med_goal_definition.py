from odoo import models, fields

class MedGoalDefinition(models.Model):
    _name = "med.goal.definition"
    _description = "Goal Definition"

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
