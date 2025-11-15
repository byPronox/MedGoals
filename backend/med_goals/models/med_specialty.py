from odoo import models, fields


class MedSpecialty(models.Model):
    _name = "med.specialty"
    _description = "Employee Specialty"
    _order = "area_id, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    area_id = fields.Many2one(
        "med.area",
        string="Area",
        required=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    description = fields.Text()
    employee_ids = fields.One2many(
        "hr.employee",
        "med_specialty_id",
        string="Employees",
    )

    _sql_constraints = [
        (
            "code_company_uniq",
            "unique(code, company_id)",
            "The specialty code must be unique per company.",
        ),
    ]
