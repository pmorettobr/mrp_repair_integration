from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    # === Campos de Integração Repair ===
    repair_order_id = fields.Many2one(
        'repair.order',
        string="Ordem de Reparo Origem",
        copy=False,
        ondelete='set null',
        help="🔗 Reparo que originou esta ordem de produção. "
             "Clique para navegar ao documento original."
    )
    repair_count = fields.Integer(
        compute='_compute_repair_count',
        string="Qtd. Reparos",
        copy=False
    )

    # =========================================================================
    # COMPUTE METHODS
    # =========================================================================

    @api.depends('repair_order_id')
    def _compute_repair_count(self):
        for prod in self:
            prod.repair_count = 1 if prod.repair_order_id else 0

    # =========================================================================
    # ACTION METHODS
    # =========================================================================

    def action_view_repair(self):
        """Abre a ordem de reparo vinculada"""
        self.ensure_one()
        if not self.repair_order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Criar Ordem de Reparo'),
                'res_model': 'repair.order',
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'default_product_id': self.product_id.id,
                    'default_product_qty': self.product_qty,
                    'default_mrp_production_id': self.id,
                },
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ordem de Reparo'),
            'res_model': 'repair.order',
            'res_id': self.repair_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_confirm(self):
        """Ao confirmar MO, propaga status para work orders"""
        res = super().action_confirm()
        for prod in self:
            if prod.repair_order_id:
                prod.repair_order_id._post_integration_message(prod, "linked")
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-vincula operador se vier do repair"""
        for vals in vals_list:
            repair_id = vals.get('repair_order_id')
            if repair_id:
                repair = self.env['repair.order'].browse(repair_id)
                if repair.operator_id and not vals.get('user_id'):
                    # Propaga operador para a MO
                    vals['user_id'] = repair.operator_id.user_id.id if repair.operator_id.user_id else False
        return super().create(vals_list)
