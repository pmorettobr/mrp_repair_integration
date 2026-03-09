from odoo import models, fields, api
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # ✅ Vínculo com Repair Order
    repair_order_id = fields.Many2one(
        'repair.order',
        string="Ordem de Reparo",
        ondelete='set null',
        copy=False,
        index=True,
        help="Ordem de reparo que originou esta produção"
    )
