from odoo import models, fields

class MedPerformanceLog(models.Model):
    _name = "med.performance.log"
    _description = "Performance Log Entry"

    name = fields.Char(string="Description", required=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
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
    )

    metric_value = fields.Float(
        string="Measured Value",
        help="Quantity measured in this log.",
    )
    notes = fields.Text()
