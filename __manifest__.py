{
    'name': 'Integração Reparo - MRP com Qualidade e Operador',
    'version': '16.0.1.0.0',
    'category': 'Manufacturing/Repair',
    'summary': 'Vincula Ordens de Reparo a Ordens de Produção, com aprovação QC e operador do módulo HR',
    'description': """
        Módulo de integração entre Repair e MRP para Odoo 16 Community.
        
        Funcionalidades:
        - Vínculo bidirecional entre Ordem de Reparo e Ordem de Produção
        - Navegação via smart buttons entre documentos vinculados
        - Controle de Qualidade (aprovação/rejeição) em Repair, Production e Work Order
        - Atribuição de operador (res.users + hr.employee) nas Work Orders
        - Cálculo automático de duração da operação
    """,
    'depends': [
        'repair',  # Módulo base de reparos
        'mrp',     # Módulo de produção
        'hr',      # Módulo de RH para operadores
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/repair_order_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workorder_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
