from odoo import models, fields

class MedArea(models.Model):
    _name = "med.area"
    _description = "Area (Business Unit / Department)"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    description = fields.Text()
    employee_ids = fields.One2many(
        "hr.employee",
        "med_area_id",
        string="Employees",
    )
