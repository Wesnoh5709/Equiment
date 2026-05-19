# -*- coding: utf-8 -*-
{
    'name': "Maintenance Dashboard",
    'version': '19.0.1.0.0',
    'category': 'Maintenance',
    'summary': "Visual Maintenance Dashboard with advanced search filters and KPI tiles",
    'description': """
        Maintenance Dashboard — comprehensive visual dashboard for the Maintenance module.
        - Advanced search: Team, Equipment, Request Type, Date Range, Status,
          Location, Zone, Building, Floor, Room, Tag
        - KPI tiles: Total Equipment, Total Maintenance, Maintenance Today, Overdue Requests
        - Charts: Requests by Stage, Requests by Equipment
        - MTTR Charts: by Team, by Equipment, 12-month trend
        - Export: Excel (multi-sheet incl. PPM Schedule matrix) and PDF
    """,
    'author': 'Custom Development',
    'depends': ['maintenance', 'equipment_asset_extension', 'maintenance_request_type'],
    'data': [
        'views/maintenance_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js',
            'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js',
            'test_dashboard/static/src/css/style.css',
            'test_dashboard/static/src/js/maintenance_dashboard.js',
            'test_dashboard/static/src/xml/dashboard_templates.xml',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
