# Show list of all instruments owned by that customer

import frappe

from frappe import _

from frappe.exceptions import ValidationError

from bnovate.bnovate.utils.iot_apis import rms_get_access_configs, _rms_start_session, _rms_get_status
from .helpers import get_session_customers, get_session_primary_customer, auth, build_sidebar

no_cache = 1

auth()

def get_context(context):
    context.instruments = get_instruments()
    build_sidebar(context)
    context.title = _("My Instruments")
    return context

def get_instruments():
    primary_customer = get_session_primary_customer()

    assets = frappe.get_all("Serial No", filters={
            "owned_by": ["=", primary_customer.docname],
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

def auth_remote_session(config_id):
    # Open Remote session if the gateway is owned by a linked customer
    # Device ID here is the RMS device ID.

    access_configs = [ c for c in rms_get_access_configs(auth=False) if str(c['id']) == config_id ]
    if not access_configs:
        frappe.throw("Remote access configuration does not exist")
    
    config = access_configs[0]
    device_id = config['device_id']

    cp_owner = frappe.get_value("Connectivity Package", filters={
                "rms_id": ["=", device_id],
            }, fieldname="customer")

    if cp_owner is None or all(c.docname != cp_owner for c in get_session_customers()):
        # None of the linked customers match this connectivity package owner
        frappe.throw("{} does not have access to this device".format(frappe.session.user))

    return True



@frappe.whitelist()
def portal_start_session(config_id):

    # Raises error if user is not allowed.
    auth_remote_session(config_id)
    channel = _rms_start_session(config_id, auth=False)
    frappe.cache().set_value("channel-owner-{}".format(channel), frappe.session.sid, expires_in_sec=60*60)
    return channel

@frappe.whitelist()
def portal_get_status(channel):
    if not frappe.cache().get_value("channel-owner-{}".format(channel)) == frappe.session.sid:
        frappe.throw("{} is not authorized to read this channel".format(frappe.session.user))
    return _rms_get_status(channel, auth=False)