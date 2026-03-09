from odoo import models, fields, api
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    production_ids = fields.One2many(
        'mrp.production', 'repair_order_id', string="Ordens de Produção", copy=False
    )
    production_count = fields.Integer(string="Total de Produções", compute="_compute_production_count")

    @api.depends('production_ids')
    def _compute_production_count(self):
        for rec in self:
            rec.production_count = len(rec.production_ids)

    def action_view_productions(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        productions = self.production_ids
        if len(productions) > 1:
            action['domain'] = [('id', 'in', productions.ids)]
        elif len(productions) == 1:
            action['views'] = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
            action['res_id'] = productions.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
