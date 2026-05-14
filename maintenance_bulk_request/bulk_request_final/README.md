# Maintenance Bulk Request (`maintenance_bulk_request`)

Odoo 19 Community module — create maintenance requests in bulk for multiple equipment records in one go.

---

## Features

| Feature | Detail |
|---|---|
| Equipment filter | Name, Location, Building, Zone, Floor, Room, Model, Category |
| Result preview | Interactive list — uncheck rows to exclude individual equipment |
| Bulk fields | Request Name, Maintenance Team, Scheduled Date, Priority |
| After confirm | Redirects to the list of newly created maintenance requests |

---

## Installation

1. Copy the `maintenance_bulk_request` folder into your Odoo **addons path**.
2. Restart the Odoo server.
3. Go to **Settings → Apps**, search for *Maintenance Bulk Request*, and click **Install**.

**Dependency:** the standard `maintenance` module must be installed first.

---

## New fields on `maintenance.equipment`

The module adds four optional location-detail fields to the Equipment model:

| Field | Type | Description |
|---|---|---|
| `building` | Char | Building / block (e.g. Block A) |
| `zone` | Char | Zone within the building (e.g. North Wing) |
| `floor` | Char | Floor number or name (e.g. Floor 2) |
| `room` | Char | Room number or name (e.g. Room 204) |

These fields appear on the Equipment form view, just below the existing **Location** field.

> **Note:** The `model` filter in the wizard uses the standard `model` field already present on `maintenance.equipment` — no new field is created for it.

---

## How to use

1. Open the **Maintenance** app.
2. Click **Maintenance → Bulk Request** in the menu.
3. **Step 1 — Set filters** (any combination of the 8 fields) and click **Search Equipment**.
4. **Step 2 — Review results.** Remove any equipment you want to exclude by clicking the delete icon on its row.
5. **Step 3 — Fill in the bulk data:** Request Name (required), Team, Scheduled Date, Priority.
6. Click **Create Requests**. One `maintenance.request` is created per selected equipment, and Odoo navigates to the resulting list.

---

## Menu parent — how to verify / change

The menu item is placed under `maintenance.menu_m_maintenance`.  
If this ID does not match your Odoo instance, run the following in a shell or the Odoo REPL:

```python
self.env.ref('maintenance.menu_m_maintenance')
```

Then update the `parent` attribute in `views/maintenance_bulk_request_wizard_views.xml` accordingly.

---

## Access rights

| Group | Read | Write | Create | Delete |
|---|---|---|---|---|
| Maintenance Manager | ✓ | ✓ | ✓ | ✓ |
| Maintenance User | ✓ | ✓ | ✓ | — |

---

## License

LGPL-3
