{
    'name': 'Integração Reparo - MRP',
    'version': '16.0.1.2.0',
    'category': 'Manufacturing/Repair',
    'summary': 'Vincula Ordens de Reparo e Produção com navegação fluida e UX otimizada',
    'description': """
        Integração entre módulos Repair e MRP para Odoo 16 Community.
        
        Funcionalidades:
        • Vínculo bidirecional entre Ordem de Reparo e Ordem de Produção
        • Smart buttons para navegação rápida entre documentos relacionados
        • Wizard intuitivo para criar MO a partir de um Reparo
        • Atribuição inteligente de operador (res.users + hr.employee)
        • Cálculo automático de duração da operação
        • Notificações automáticas ao vincular documentos
        • Filtros personalizados "Meus Reparos/Operações"
        
        Melhorias de UX:
        • Campos organizados em grupos lógicos com ícones
        • Badges coloridos por status para leitura rápida
        • Help text contextual em todos os campos customizados
        • Validações amigáveis com sugestões de correção
        • Auto-preenchimento de operador baseado no usuário logado
    """,
    'author': 'Paulo Moretto',
    'website': 'https://github.com/pmorettobr',
    'license': 'LGPL-3',
    'depends': [
        'repair',
        'mrp',
        'hr',
        'mail',  # Para notificações automáticas
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/create_production_wizard_views.xml',
        'views/repair_order_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workorder_views.xml',
    ],
    'demo': [
        'demo/repair_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
