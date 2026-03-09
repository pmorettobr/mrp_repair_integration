from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    # === Campos de Operador e Tempo ===
    operator_id = fields.Many2one(
        'hr.employee',
        string="Operador",
        help="👤 Funcionário responsável por esta operação. "
             "Preenchido automaticamente a partir do reparo ou usuário logado."
    )
    operator_start_date = fields.Datetime(string="Início Real", copy=False)
    operator_end_date = fields.Datetime(string="Fim Real", copy=False)
    
    # Campo computado para duração
    operator_duration = fields.Float(
        compute='_compute_operator_duration',
        string="Duração Real (horas)",
        store=True,
        help="⏱️ Tempo real gasto pelo operador nesta operação."
    )

    # =========================================================================
    # COMPUTE METHODS
    # =========================================================================

    @api.depends('operator_start_date', 'operator_end_date')
    def _compute_operator_duration(self):
        for work in self:
            if work.operator_start_date and work.operator_end_date:
                delta = work.operator_end_date - work.operator_start_date
                work.operator_duration = delta.total_seconds() / 3600
            else:
                work.operator_duration = 0.0

    # =========================================================================
    # OVERRIDE DE MÉTODOS NATIVOS - UX AMIGÁVEL
    # =========================================================================

    def button_start(self):
        """Inicia a work order com validação amigável de operador"""
        for work in self:
            if not work.operator_id:
                # Tenta auto-preencher com employee do usuário logado
                employee = self.env['hr.employee'].search([
                    ('user_id', '=', self.env.user.id)
                ], limit=1)
                
                if employee:
                    work.operator_id = employee.id
                    work.message_post(
                        body=f"✅ Operador definido automaticamente: <b>{employee.name}</b>",
                        subtype_xmlid='mail.mt_note'
                    )
                else:
                    # Mensagem educativa com links de ajuda
                    raise UserError(
                        _("⚠️ Operador não definido para esta operação.\n\n"
                          "Para continuar, você pode:\n\n"
                          "1️⃣ <b>Vincular seu usuário a um funcionário:</b>\n"
                          "   • Acesse: RH > Funcionários\n"
                          "   • Edite seu cadastro e preencha o campo 'Usuário'\n\n"
                          "2️⃣ <b>Selecionar manualmente:</b>\n"
                          "   • Escolha um funcionário no campo 'Operador' acima\n\n"
                          "💡 Dica: Esta informação é essencial para relatórios de produtividade!")
                    )
            
            # Registra horário de início
            if not work.operator_start_date:
                work.operator_start_date = fields.Datetime.now()
        
        return super().button_start()

    def button_finish(self):
        """Finaliza a work order registrando horário e validando produção"""
        for work in self:
            if work.operator_start_date and not work.operator_end_date:
                work.operator_end_date = fields.Datetime.now()
            
            # Validação suave: alerta se produção < planejada
            if work.production_id and float_compare(
                work.production_id.qty_producing, 
                work.production_id.product_qty, 
                precision_rounding=work.production_id.product_uom_id.rounding
            ) < 0:
                work.message_post(
                    body="⚠️ <b>Atenção:</b> Quantidade produzida menor que a planejada. "
                         "Verifique se há retrabalho necessário.",
                    subtype_xmlid='mail.mt_note'
                )
        
        return super().button_finish()

    def button_pending(self):
        """Pausa a work order"""
        for work in self:
            if work.operator_start_date and not work.operator_end_date:
                # Registra tempo parcial se estiver pausando
                work.message_post(
                    body=f"⏸️ Operação pausada. Tempo parcial: <b>{work.operator_duration:.2f}h</b>",
                    subtype_xmlid='mail.mt_note'
                )
        return super().button_pending()

    # =========================================================================
    # HERANÇA DE OPERADOR DO REPAIR/MRP
    # =========================================================================

    @api.onchange('production_id')
    def _onchange_production_set_operator(self):
        """Propaga operador da MO ou Repair para a work order"""
        if self.production_id:
            # Prioridade 1: Operador da própria MO
            if self.production_id.user_id:
                employee = self.env['hr.employee'].search([
                    ('user_id', '=', self.production_id.user_id.id)
                ], limit=1)
                if employee:
                    self.operator_id = employee.id
            
            # Prioridade 2: Operador do Repair vinculado
            elif self.production_id.repair_order_id and self.production_id.repair_order_id.operator_id:
                self.operator_id = self.production_id.repair_order_id.operator_id
