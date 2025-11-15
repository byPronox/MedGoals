from odoo import models, fields, api, _

class HREmployee(models.Model):
    _inherit = "hr.employee"

    med_area_id = fields.Many2one(
        "med.area",
        string="MED Area",
        check_company=True,
        help="Business unit / department where the employee belongs for MED-GOALS."
    )
    med_specialty_id = fields.Many2one(
        "med.specialty",
        string="MED Specialty",
        check_company=True,
        help="Employee specialty used for performance evaluation in MED-GOALS."
    )

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
