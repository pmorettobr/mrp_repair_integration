from odoo import models, fields, api
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    # ✅ Operador: vínculo COM hr.employee (módulo RH)
    operator_id = fields.Many2one(
        'hr.employee',
        string="Operador",
        domain="[('active', '=', True)]",
        copy=False,
        help="Funcionário responsável por esta operação"
    )

    # ✅ Controle de tempo
    operator_start_date = fields.Datetime(string="Início Operação", copy=False)
    operator_end_date = fields.Datetime(string="Fim Operação", copy=False)

    # ✅ Campos de QC
    quality_approval_state = fields.Selection(
        [('pending', 'Pendente'), ('approved', 'Aprovado'), ('rejected', 'Rejeitado')],
        default='pending',
        string="Status QC",
        copy=False,
        tracking=True
    )
    quality_notes = fields.Text(string="Observações QC", copy=False)

    # ✅ Exigir operador antes de iniciar
    def button_start(self):
        for rec in self:
            if not rec.operator_id:
                raise UserError("Selecione o operador antes de iniciar a operação.")
            rec.operator_start_date = fields.Datetime.now()
        return super().button_start()

    # ✅ Registrar fim automaticamente
    def button_finish(self):
        for rec in self:
            rec.operator_end_date = fields.Datetime.now()
        return super().button_finish()
