from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class MedScoringConfig(models.Model):
    _name = "med.scoring.config"
    _description = "Scoring Configuration"
    _rec_name = "name"
    _order = "company_id, name"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    active = fields.Boolean(default=True)

    # Relative weights
    weight_goals = fields.Float(string="Goals Weight", default=1.0)
    weight_productivity = fields.Float(string="Productivity Weight", default=0.0)
    weight_quality = fields.Float(string="Quality Weight", default=0.0)
    weight_economic = fields.Float(string="Economic Contribution Weight", default=0.0)

    normalized = fields.Boolean(
        string="Weights Sum to 1",
        compute="_compute_normalized",
        store=True,
    )
    total_weight = fields.Float(
        string="Total Weight",
        compute="_compute_normalized",
        store=True,
    )

    _sql_constraints = [
        (
            "name_company_uniq",
            "unique(name, company_id)",
            "The scoring configuration name must be unique per company.",
        ),
    ]

    @api.depends(
        "weight_goals",
        "weight_productivity",
        "weight_quality",
        "weight_economic",
    )
    def _compute_normalized(self):
        for rec in self:
            total = (
                (rec.weight_goals or 0.0)
                + (rec.weight_productivity or 0.0)
                + (rec.weight_quality or 0.0)
                + (rec.weight_economic or 0.0)
            )
            rec.total_weight = total
            rec.normalized = abs(total - 1.0) < 0.0001

    # BACK-END VALIDATION: pesos no negativos y suma > 0
    @api.constrains(
        "weight_goals",
        "weight_productivity",
        "weight_quality",
        "weight_economic",
    )
    def _check_weights(self):
        for rec in self:
            weights = [
                rec.weight_goals,
                rec.weight_productivity,
                rec.weight_quality,
                rec.weight_economic,
            ]
            if any(w is not None and w < 0 for w in weights):
                raise ValidationError(_("Weights cannot be negative."))
            if rec.total_weight <= 0:
                raise ValidationError(_("Total weight must be greater than zero."))
