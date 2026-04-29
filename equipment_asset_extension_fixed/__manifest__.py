{
    'name': 'Equipment Asset Extension',
    'version': '1.1',
    'summary': 'Extend Equipment with Asset Details (Fixed for Odoo 19)',
    'depends': ['maintenance', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/building_views.xml',
        'views/zone_views.xml',
        'views/equipment_views.xml',
    ],
    'installable': True,
    'application': False,
}