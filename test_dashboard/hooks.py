# -*- coding: utf-8 -*-
"""
Post-install hook: attach the Dashboard menu item under the Maintenance
app root menu, regardless of what Odoo version renamed it to.
"""


def post_init_hook(env):
    # Try every known XML ID for the Maintenance root menu across versions
    candidate_xmlids = [
        'maintenance.menu_maintenance_main',   # Odoo 19
        'maintenance.hr_equipment_menu_root',  # Odoo 16/17/18
        'maintenance.menu_maintenance',
    ]

    parent_menu = None
    for xmlid in candidate_xmlids:
        try:
            parent_menu = env.ref(xmlid, raise_if_not_found=False)
            if parent_menu:
                break
        except Exception:
            continue

    # Fall back: search by menu name
    if not parent_menu:
        parent_menu = env['ir.ui.menu'].search(
            [('name', '=', 'Maintenance'), ('parent_id', '=', False)],
            limit=1)

    if not parent_menu:
        # Last resort: attach at root level (shows as its own app tile)
        return

    # Fetch the menu record we created via XML and set its parent
    dashboard_menu = env.ref(
        'test_dashboard.test_dashboard_menu', raise_if_not_found=False)
    if dashboard_menu and parent_menu:
        dashboard_menu.write({'parent_id': parent_menu.id})
