from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class RepairOrder(models.Model):
    _inherit = "repair.order"

    # === Campos de Integração MRP ===
    production_ids = fields.Many2many(
        'mrp.production',
        'repair_mrp_production_rel',
        'repair_id',
        'production_id',
        string="Ordens de Produção Vinculadas",
        copy=False,
        help="🔗 Ordens de produção geradas a partir deste reparo. "
             "Clique para navegar diretamente à MO."
    )
    production_count = fields.Integer(
        compute='_compute_production_count',
        string="Qtd. Produções",
        copy=False
    )

    # === Campos de Operador (herdados para work orders) ===
    operator_id = fields.Many2one(
        'hr.employee',
        string="Técnico Responsável",
        help="👤 Funcionário responsável pela execução deste reparo. "
             "Será replicado para as work orders vinculadas."
    )

    # =========================================================================
    # COMPUTE METHODS
    # =========================================================================

    @api.depends('production_ids')
    def _compute_production_count(self):
        for repair in self:
            repair.production_count = len(repair.production_ids)

    # =========================================================================
    # ACTION METHODS - UX OTIMIZADA
    # =========================================================================

    def action_view_productions(self):
        """Abre as ordens de produção vinculadas em lista ou formulário"""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        
        if len(self.production_ids) > 1:
            # Vista em lista com filtro
            action['domain'] = [('id', 'in', self.production_ids.ids)]
            action['context'] = {
                'search_default_id': self.production_ids.ids[0] if self.production_ids else False,
                'default_repair_order_id': self.id,
            }
        elif self.production_ids:
            # Abre diretamente o formulário da única MO
            action.update({
                'view_mode': 'form',
                'res_id': self.production_ids.id,
                'context': {'default_repair_order_id': self.id},
            })
        else:
            # Nenhuma MO vinculada - sugere criação via wizard
            action = self.action_open_create_production_wizard()
        
        return action

    def action_open_create_production_wizard(self):
        """Abre o wizard para criar nova Ordem de Produção"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Criar Ordem de Produção'),
            'res_model': 'repair.create.production.wizard',
            'view_mode': 'form',
            'target': 'new',  # Modal
            'context': {
                'default_repair_id': self.id,
                'default_product_id': self.product_id.id,
                'default_product_qty': self.product_qty,
                'default_origin': self.name,
            },
        }

    def action_create_production_quick(self):
        """Cria MO rapidamente com dados padrão (atalho para usuários avançados)"""
        self.ensure_one()
        
        if not self.product_id:
            raise ValidationError(_("É necessário informar um produto no reparo."))
        
        # Tenta encontrar BOM padrão
        bom = self.env['mrp.bom'].search([
            ('product_id', '=', self.product_id.id),
            ('type', '=', 'normal'),
            ('active', '=', True)
        ], limit=1)
        
        production = self.env['mrp.production'].create({
            'product_id': self.product_id.id,
            'product_qty': self.product_qty or 1.0,
            'product_uom_id': self.product_uom.id or self.product_id.uom_id.id,
            'bom_id': bom.id,
            'origin': self.name,
            'repair_order_id': self.id,  # ✅ Vínculo automático
            'date_deadline': self.schedule_date or fields.Date.today(),
        })
        
        # Notificação automática
        self._post_integration_message(production, "criada")
        
        # Feedback visual ao usuário
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Produção Criada! 🎉'),
                'message': _('Ordem de Produção <a href="#" data-oe-model="mrp.production" data-oe-id="%d">%s</a> vinculada com sucesso.') % (production.id, production.name),
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_repair_done(self):
        """Override para validar work orders antes de finalizar"""
        for repair in self:
            # Verifica se há work orders em andamento vinculadas
            related_workorders = self.env['mrp.workorder'].search([
                ('production_id.repair_order_id', '=', repair.id),
                ('state', 'in', ['confirmed', 'progress', 'waiting'])
            ])
            
            if related_workorders:
                pending = related_workorders.filtered(lambda w: w.state != 'done')
                if pending:
                    raise UserError(
                        _("⚠️ Não é possível finalizar o reparo.\n\n"
                          "Existem operações de produção ainda pendentes:\n%s\n\n"
                          "Finalize as operações ou cancele-as antes de concluir o reparo.") 
                        % "\n• ".join(pending.mapped('name'))
                    )
        
        return super().action_repair_done()

    # =========================================================================
    # UTILITÁRIOS
    # =========================================================================

    def _post_integration_message(self, record, action_type):
        """Posta mensagem de integração no chatter de ambos os documentos"""
        labels = {
            'created': 'criada',
            'linked': 'vinculada',
            'unlinked': 'desvinculada',
        }
        label = labels.get(action_type, action_type)
        
        message = f"🔗 Ordem de Produção <a href='#id={record.id}' class='o_mail_redirect'>{record.name}</a> {label}."
        
        # Posta no repair
        self.message_post(body=message, subtype_xmlid='mail.mt_comment')
        
        # Posta na production (se tiver chatter)
        if hasattr(record, 'message_post'):
            record.message_post(
                body=f"🔗 Vinculada ao Reparo <a href='#id={self.id}' class='o_mail_redirect'>{self.name}</a>.",
                subtype_xmlid='mail.mt_comment'
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-atribui operador se não informado e usuário tiver employee"""
        for vals in vals_list:
            if not vals.get('operator_id'):
                employee = self.env['hr.employee'].search([
                    ('user_id', '=', self.env.user.id)
                ], limit=1)
                if employee:
                    vals['operator_id'] = employee.id
        return super().create(vals_list)
