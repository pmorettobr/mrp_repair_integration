from odoo import models, fields, api
from odoo.exceptions import UserError


class RepairOrder(models.Model):
    _inherit = "repair.order"

    production_ids = fields.One2many(
        'mrp.production', 'repair_order_id', string="Ordens de Produção", copy=False
    )
    production_count = fields.Integer(string="Total de Produções", compute="_compute_production_count")

    # Campos QC
    quality_approval_state = fields.Selection(
        [('pending', 'Pendente'), ('approved', 'Aprovado'), ('rejected', 'Rejeitado')],
        default='pending', string="Status QC", copy=False, tracking=True
    )
    quality_approved_by = fields.Many2one('res.users', string="Aprovado por", copy=False)
    quality_approval_date = fields.Datetime(string="Data Aprovação", copy=False)
    quality_notes = fields.Text(string="Observações QC", copy=False)

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

    # ✅ Método: Aprovar QC
    def action_approve_quality(self):
        for rec in self:
            rec.write({
                'quality_approval_state': 'approved',
                'quality_approved_by': self.env.user.id,
                'quality_approval_date': fields.Datetime.now()
            })
        return True

    # ✅ Método: Rejeitar QC
    def action_reject_quality(self):
        for rec in self:
            rec.write({
                'quality_approval_state': 'rejected',
                'quality_approved_by': self.env.user.id,
                'quality_approval_date': fields.Datetime.now()
            })
        return True

    # ✅ Bloquear finalização sem QC aprovado
    def action_repair_end(self):
        for repair in self:
            if repair.quality_approval_state != 'approved':
                raise UserError(
                    "Não é possível finalizar o reparo.\n\n"
                    "O Controle de Qualidade precisa estar APROVADO."
                )
        return super().action_repair_end()
