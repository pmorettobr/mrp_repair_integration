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

    # ✅ Campos de Controle de Qualidade
    quality_approval_state = fields.Selection(
        [
            ('pending', 'Pendente'),
            ('approved', 'Aprovado'),
            ('rejected', 'Rejeitado')
        ],
        default='pending',
        string="Status QC",
        copy=False,
        tracking=True  # ✅ Registra alterações no chatter
    )

    quality_approved_by = fields.Many2one(
        'res.users',
        string="Aprovado por",
        copy=False
    )

    quality_approval_date = fields.Datetime(
        string="Data Aprovação",
        copy=False
    )

    quality_notes = fields.Text(
        string="Observações QC",
        copy=False
    )

    # ✅ Método: Aprovar QC
    def action_approve_quality(self):
        """Aprova o Controle de Qualidade da Ordem de Produção"""
        for rec in self:
            rec.write({
                'quality_approval_state': 'approved',
                'quality_approved_by': self.env.user.id,
                'quality_approval_date': fields.Datetime.now()
            })
        return True

    # ✅ Método: Rejeitar QC
    def action_reject_quality(self):
        """Rejeita o Controle de Qualidade da Ordem de Produção"""
        for rec in self:
            rec.write({
                'quality_approval_state': 'rejected',
                'quality_approved_by': self.env.user.id,
                'quality_approval_date': fields.Datetime.now()
            })
        return True
