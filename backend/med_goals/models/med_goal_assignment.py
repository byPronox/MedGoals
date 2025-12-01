from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MedGoalAssignment(models.Model):
    _name = "med.goal.assignment"
    _description = "Goal Assignment to Employee"
    _order = "evaluation_cycle_id desc, employee_id, name"

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
        domain="[('state', 'in', ['draft', 'open'])]",
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

    # BACK-END VALIDATION: target_value > 0, actual_value >= 0
    @api.constrains("target_value", "actual_value")
    def _check_values(self):
        for rec in self:
            if rec.target_value is not None and rec.target_value <= 0:
                raise ValidationError(
                    _("Target value must be greater than zero.")
                )
            if rec.actual_value is not None and rec.actual_value < 0:
                raise ValidationError(
                    _("Actual value cannot be negative.")
                )

    @api.depends("target_value", "actual_value")
    def _compute_completion_rate(self):
        for rec in self:
            if rec.target_value:
                rec.completion_rate = (rec.actual_value or 0.0) / rec.target_value * 100.0
            else:
                rec.completion_rate = 0.0

    @api.model
    def create(self, vals):
        if not vals.get("name"):
            emp_name = ""
            goal_name = ""
            cycle_name = ""

            if vals.get("employee_id"):
                emp = self.env["hr.employee"].browse(vals["employee_id"])
                emp_name = emp.name or ""

            if vals.get("goal_id"):
                goal = self.env["med.goal.definition"].browse(vals["goal_id"])
                goal_name = goal.name or ""

            if vals.get("evaluation_cycle_id"):
                cycle = self.env["med.evaluation.cycle"].browse(vals["evaluation_cycle_id"])
                cycle_name = cycle.name or ""

            parts = [p for p in [emp_name, goal_name, cycle_name] if p]
            vals["name"] = " - ".join(parts) if parts else _("Goal Assignment")

        return super().create(vals)
