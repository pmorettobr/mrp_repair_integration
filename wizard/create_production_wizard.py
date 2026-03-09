from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RepairCreateProductionWizard(models.TransientModel):
    _name = 'repair.create.production.wizard'
    _description = 'Wizard para Criar Ordem de Produção a partir do Reparo'

    # === Dados do Reparo Origem (readonly) ===
    repair_id = fields.Many2one(
        'repair.order',
        string="Ordem de Reparo",
        required=True,
        readonly=True,
        ondelete='cascade',
        help="🔗 Reparo que originará a nova ordem de produção."
    )

    # === Dados da Produção (editáveis) ===
    product_id = fields.Many2one(
        'product.product',
        string="Produto",
        required=True,
        domain="[('type', 'in', ['product', 'consu'])]",
        help="📦 Produto a ser manufaturado."
    )
    product_qty = fields.Float(
        string="Quantidade",
        default=1.0,
        required=True,
        help="🔢 Quantidade a produzir."
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string="Unidade",
        required=True,
        help="📏 Unidade de medida da produção."
    )
    
    bom_id = fields.Many2one(
        'mrp.bom',
        string="Lista de Materiais",
        domain="[('product_id', '=', product_id), ('type', '=', 'normal'), ('active', '=', True)]",
        help="📋 BOM a ser utilizada. Deixe em branco para usar a padrão do produto."
    )
    
    location_src_id = fields.Many2one(
        'stock.location',
        string="Local de Origem",
        domain="[('usage', '=', 'internal')]",
        help="📍 Almoxarifado de origem dos componentes."
    )
    location_dest_id = fields.Many2one(
        'stock.location',
        string="Local de Destino",
        domain="[('usage', '=', 'internal')]",
        help="📍 Almoxarifado de destino do produto acabado."
    )
    
    date_deadline = fields.Date(
        string="Data de Entrega",
        default=fields.Date.context_today,
        required=True,
        help="📅 Prazo esperado para conclusão."
    )
    
    note = fields.Text(
        string="Observações",
        help="📝 Informações adicionais para a equipe de produção."
    )

    # =========================================================================
    # ONCHANGE METHODS - UX DINÂMICA
    # =========================================================================

    @api.onchange('repair_id')
    def _onchange_repair_set_defaults(self):
        """Preenche dados padrão a partir do reparo"""
        if self.repair_id:
            self.product_id = self.repair_id.product_id
            self.product_qty = self.repair_id.product_qty
            self.product_uom_id = self.repair_id.product_uom or self.repair_id.product_id.uom_id
            self.note = self.repair_id.note

    @api.onchange('product_id')
    def _onchange_product_set_bom_uom(self):
        """Atualiza BOM e UOM ao mudar produto"""
        if self.product_id:
            # Define UOM padrão do produto
            self.product_uom_id = self.product_id.uom_id
            
            # Busca BOM padrão ativa
            bom = self.env['mrp.bom'].search([
                ('product_id', '=', self.product_id.id),
                ('type', '=', 'normal'),
                ('active', '=', True)
            ], limit=1, order='sequence, id')
            self.bom_id = bom.id

    # =========================================================================
    # ACTION METHODS
    # =========================================================================

    def action_create_production(self):
        """Cria a Ordem de Produção e vincula ao reparo"""
        self.ensure_one()
        
        # Validações básicas
        if self.product_qty <= 0:
            raise ValidationError(_("A quantidade deve ser maior que zero."))
        
        if not self.product_uom_id:
            raise ValidationError(_("Informe a unidade de medida do produto."))
        
        # Prepara valores para criação
        production_vals = {
            'product_id': self.product_id.id,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'bom_id': self.bom_id.id,
            'origin': self.repair_id.name,
            'repair_order_id': self.repair_id.id,  # ✅ Vínculo automático
            'date_deadline': self.date_deadline,
            'note': self.note,
        }
        
        # Locais (se informados)
        if self.location_src_id:
            production_vals['location_src_id'] = self.location_src_id.id
        if self.location_dest_id:
            production_vals['location_dest_id'] = self.location_dest_id.id
        
        # Cria a produção
        production = self.env['mrp.production'].create(production_vals)
        
        # ✅ Vínculo bidirecional
        self.repair_id.write({
            'production_ids': [(4, production.id)]
        })
        
        # Notificação automática
        self.repair_id._post_integration_message(production, "created")
        
        # Feedback visual e redirecionamento
        return {
            'type': 'ir.actions.act_window',
            'name': _('Ordem de Produção Criada! 🎉'),
            'res_model': 'mrp.production',
            'res_id': production.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'notification': {
                    'type': 'success',
                    'title': _('Sucesso!'),
                    'message': _('Produção <a href="#" data-oe-model="mrp.production" data-oe-id="%d">%s</a> criada e vinculada ao reparo.') % (production.id, production.name),
                }
            },
        }

    def action_cancel(self):
        """Fecha o wizard sem criar nada"""
        return {'type': 'ir.actions.act_window_close'}
