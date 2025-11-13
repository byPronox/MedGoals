from odoo import models, fields, api

class MedGoalAssignment(models.Model):
    _name = "med.goal.assignment"
    _description = "Goal Assignment to Employee"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
    )
    area_id = fields.Many2one(
        related="employee_id.med_area_id",
        store=True,
        readonly=True,
    )
    specialty_id = fields.Many2one(
        related="employee_id.med_specialty_id",
        store=True,
        readonly=True,
    )

    goal_id = fields.Many2one(
        "med.goal.definition",
        string="Goal",
        required=True,
    )
    evaluation_cycle_id = fields.Many2one(
        "med.evaluation.cycle",
        string="Evaluation Cycle",
        required=True,
    )

    target_value = fields.Float(string="Target", required=True)
    unit = fields.Char(string="Unit", help="e.g., units, %, $, hours.")
    actual_value = fields.Float(string="Actual Value")
    completion_rate = fields.Float(
        string="% Completion",
        compute="_compute_completion_rate",
        store=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
    )

    performance_log_ids = fields.One2many(
        "med.performance.log",
        "assignment_id",
        string="Performance Logs",
    )

    @api.depends("target_value", "actual_value")
    def _compute_completion_rate(self):
        for rec in self:
            if rec.target_value:
                rec.completion_rate = (rec.actual_value / rec.target_value) * 100.0
            else:
                rec.completion_rate = 0.0
