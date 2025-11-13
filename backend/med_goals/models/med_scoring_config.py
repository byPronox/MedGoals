from odoo import models, fields, api

class MedScoringConfig(models.Model):
    _name = "med.scoring.config"
    _description = "Scoring Configuration"
    _rec_name = "name"

    name = fields.Char(required=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    active = fields.Boolean(default=True)

    # Pesos relativos (deben sumar 1.0 idealmente)
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

    @api.depends(
        "weight_goals",
        "weight_productivity",
        "weight_quality",
        "weight_economic",
    )
    def _compute_normalized(self):
        for rec in self:
            total = (
                rec.weight_goals
                + rec.weight_productivity
                + rec.weight_quality
                + rec.weight_economic
            )
            rec.total_weight = total
            rec.normalized = abs(total - 1.0) < 0.0001
