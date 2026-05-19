{
    'name': 'Maintenance Bulk Request',
    'version': '19.0.1.0.0',
    'summary': 'Create maintenance requests in bulk for multiple equipment records',
    'description': """
        Adds a wizard under the Maintenance menu to create maintenance requests in bulk.

        Features:
        - Filter equipment by: Name, Location, Building, Zone, Floor, Room, Model, Category
        - Preview matching equipment and deselect individual records before confirming
        - Set common values for all requests: Name, Team, Scheduled Date, Priority
        - Navigates to the created requests after confirmation

        Depends on equipment_asset_extension for:
        location_id (stock.location), building_id (building.master),
        zone_id (zone.master), floor (Char), room (Char), model_name (Char)
    """,
    'category': 'Maintenance',
    'author': 'Custom Development',
    'depends': ['maintenance', 'equipment_asset_extension'],
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_bulk_request_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
