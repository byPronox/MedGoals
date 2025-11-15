from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HREmployee(models.Model):
    _inherit = "hr.employee"

    med_area_id = fields.Many2one("med.area", string="MED Area")
    med_specialty_id = fields.Many2one("med.specialty", string="MED Specialty")

    goal_assignment_ids = fields.One2many(
        "med.goal.assignment",
        "employee_id",
        string="Assigned Goals",
    )
    performance_log_ids = fields.One2many(
        "med.performance.log",
        "employee_id",
        string="Performance Logs",
    )
    employee_score_ids = fields.One2many(
        "med.employee.score",
        "employee_id",
        string="Score History",
    )

    last_score = fields.Float(
        string="Last Total Score",
        digits=(3, 2),
        compute="_compute_last_score_info",
        store=True,
    )
    last_evaluation_date = fields.Datetime(
        string="Last Evaluation Date",
        compute="_compute_last_score_info",
        store=True,
    )
    is_top_performer = fields.Boolean(
        string="Top Performer",
        compute="_compute_last_score_info",
        store=True,
    )
    rank_area = fields.Integer(
        string="Rank in Area",
        compute="_compute_last_score_info",
        store=True,
    )
    rank_specialty = fields.Integer(
        string="Rank in Specialty",
        compute="_compute_last_score_info",
        store=True,
    )

    @api.depends("employee_score_ids.score_total", "employee_score_ids.create_date")
    def _compute_last_score_info(self):
        for employee in self:
            last = employee.employee_score_ids.sorted(
                key=lambda s: s.create_date or s.id, reverse=True
            )[:1]
            if last:
                last = last[0]
                employee.last_score = last.score_total
                employee.last_evaluation_date = last.create_date
                employee.is_top_performer = last.is_top_performer
                employee.rank_area = last.rank_area
                employee.rank_specialty = last.rank_specialty
            else:
                employee.last_score = 0.0
                employee.last_evaluation_date = False
                employee.is_top_performer = False
                employee.rank_area = 0
                employee.rank_specialty = 0

    # -----------------------------
    # BACK-END VALIDATIONS (SENSITIVE DATA)
    # -----------------------------

    @api.constrains("private_email")
    def _check_private_email(self):
        """Private email must be a valid basic email format."""
        for employee in self:
            email = (employee.private_email or "").strip()
            if not email:
                # allow empty, only validate if user set a value
                continue

            # Validación muy simple para el proyecto (no RFC completo)
            if "@" not in email or "." not in email.split("@")[-1]:
                raise ValidationError(
                    _("Private email must be a valid email address.")
                )

    @api.constrains("private_phone")
    def _check_private_phone(self):
        """Private phone must contain only digits and have a reasonable length."""
        for employee in self:
            phone = (employee.private_phone or "").strip()
            if not phone:
                continue

            if not phone.isdigit():
                raise ValidationError(
                    _("Private phone must contain only digits.")
                )

            if len(phone) < 7 or len(phone) > 15:
                raise ValidationError(
                    _("Private phone length must be between 7 and 15 digits.")
                )

    @api.constrains("identification_id")
    def _check_identification_id(self):
        """
        Identification ID is considered a sensitive personal document.
        For Ecuador, we enforce 10 numeric characters as a basic rule.
        """
        for employee in self:
            ident = (employee.identification_id or "").strip()
            if not ident:
                continue

            if not ident.isdigit():
                raise ValidationError(
                    _("Identification ID must contain only digits.")
                )

            if len(ident) != 10:
                raise ValidationError(
                    _("Identification ID must have exactly 10 digits (Ecuadorian ID format).")
                )
