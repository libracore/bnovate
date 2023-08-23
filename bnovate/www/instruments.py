# Show list of all instruments owned by that customer

import frappe

from frappe import _

from bnovate.bnovate.utils.iot_apis import rms_get_access_configs

from .helpers import get_session_primary_customer, auth, build_sidebar

no_cache = 1

auth()

def get_context(context):
    context.instruments = get_instruments()
    build_sidebar(context)
    context.title = _("Instruments")
    return context

def get_instruments():
    primary_customer = get_session_primary_customer()

    assets = frappe.get_all("Serial No", filters={
            "owned_by": ["=", primary_customer.customer_name],
            "item_group": ["=", "Instruments"],
        },
        fields="*"
    )

    for asset in assets:
        # Find service agreements
        sa = frappe.get_all("Subscription Contract", filters={
                "serial_no": ["=", asset.serial_no],
                "status": ["=", "Active"]
            },
            fields="*"
        )
        if sa:
            asset.sa = sa[0]

        # Find connectivity packages
        cp = frappe.get_all("Connectivity Package", filters={
                "instrument_serial_no": ["=", asset.serial_no],
                "customer": ["=", asset.owned_by]
            },
            fields="*"
        )

        if cp:
            asset.cp = cp[0]
            if asset.cp.rms_id:
                access_configs = rms_get_access_configs(asset.cp.rms_id, auth=False)
                web = [ c for c in access_configs if 'protocol' in c and c['protocol'] == 'https' ]
                vnc = [ c for c in access_configs if 'protocol' in c and c['protocol'] == 'vnc' ]

                if web:
                    asset.cp.web = web[0]
                if vnc:
                    asset.cp.vnc = vnc[0]


    return assets

