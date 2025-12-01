from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MedPerformanceLog(models.Model):
    _name = "med.performance.log"
    _description = "Performance Log Entry"
    _order = "date desc, id desc"

    name = fields.Char(string="Description", required=True)
    date = fields.Datetime(
        default=lambda self: fields.Datetime.now(),
        required=True,
    )
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
    assignment_id = fields.Many2one(
        "med.goal.assignment",
        string="Goal Assignment",
        domain="[('employee_id', '=', employee_id)]",
    )

    metric_value = fields.Float(
        string="Measured Value",
        help="Quantity measured in this log.",
    )
    notes = fields.Text()

    # BACK-END VALIDATION: SENSITIVE performance data PER LOG ENTRY
    @api.constrains("metric_value")
    def _check_metric_value(self):
        for rec in self:
            if rec.metric_value is not None and rec.metric_value < 0:
                raise ValidationError(_("Measured value cannot be negative."))

    @api.onchange("assignment_id")
    def _onchange_assignment_id(self):
        """Sync employee & company from assignment to avoid inconsistencies."""
        if self.assignment_id:
            self.employee_id = self.assignment_id.employee_id
            self.company_id = self.assignment_id.company_id
