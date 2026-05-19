{
    'name': 'Maintenance Request Type',
    'version': '19.0.1.0.0',
    'summary': 'Add Request Type field to Maintenance Requests',
    'category': 'Maintenance',
    'author': 'Wesam',
    'license': 'LGPL-3',
    'depends': ['maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_request_views.xml',
    ],
    'installable': True,
    'application': False,
}
