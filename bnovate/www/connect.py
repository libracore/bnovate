# Show list of all instruments owned by that customer

import frappe

from frappe import _

from frappe.exceptions import ValidationError

from bnovate.bnovate.utils.iot_apis import rms_get_access_configs, _rms_start_session, _rms_get_status, rms_initialize_device, _rms_get_device
from bnovate.bnovate.doctype.connectivity_package.connectivity_package import set_info_from_rms
from .helpers import get_session_customers, get_session_primary_customer, auth, build_sidebar

no_cache = 1

auth()

def get_context(context):
    context.customers = sorted(get_session_customers(), key=lambda c: c.customer_name)
    context.instruments = get_instruments(context.customers)
    # build_sidebar(context)
    context.title = _("Connect BactoLink")

    # Gateway serial no
    # if frappe.form_dict.serial_no:
    context.serial_no = frappe.form_dict.serial_no
    return context

def get_instruments(customers):
    return {c.docname: get_instruments_one_customer(c) for c in customers}

def get_instruments_one_customer(customer):
    assets = frappe.get_all("Serial No", filters={
            "owned_by": ["=", customer.docname],
            "item_group": ["=", "Instruments"],
        },
        fields="*"
    )

    for asset in assets:
        # Name stored in DB can be outdated:
        asset.owned_by_name = customer.customer_name

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

def auth_remote_session(config_id, device_id):
    """ Return True if access config relates to a gateway owned by a linked customer.

    frappe.throw if config doesn't exist or doesn't belong to a customer linked to current user.
     
       """
    # Open Remote session associated with config if the gateway is owned by a linked customer

    access_configs = [ c for c in rms_get_access_configs(device_id=device_id, auth=False) if str(c['id']) == config_id ]
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
def portal_initialize_device(teltonika_serial, device_name):
    """ Scan ports and create remote access configs """

    # - Find associated Connectivity Package (CP)
    # - Authenticate: must belong to a linked Customer
    # - Get Device ID from CP
    # - Initialize using device ID.
    # - Fetch and associate instrument SN

    cp = frappe.get_value("Connectivity Package", filters={
        "teltonika_serial": ["=", teltonika_serial],
    }, fieldname=['name', 'customer', 'rms_id'], as_dict=True)

    if cp is None:
        frappe.throw("Unknown serial number {}".format(teltonika_serial))

    if cp.customer is None or all(customer.docname != cp.customer for customer in get_session_customers()):
        # None of the linked customers match this connectivity package owner
        frappe.throw("{} does not have access to device {}".format(frappe.session.user, teltonika_serial))
 
    # If this point is reached, user is authorized.
    rms_initialize_device(cp.rms_id, device_name, auth=False)
    frappe.db.set_value('Connectivity Package', cp.name, 'device_name', device_name)


@frappe.whitelist()
def portal_start_session(config_id, device_id):
    # Raises error if user is not allowed.
    auth_remote_session(config_id, device_id)
    channel = _rms_start_session(config_id, auth=False)
    frappe.cache().set_value("channel-owner-{}".format(channel), frappe.session.sid, expires_in_sec=60*60)
    return channel

@frappe.whitelist()
def portal_get_status(channel):
    if not frappe.cache().get_value("channel-owner-{}".format(channel)) == frappe.session.sid:
        frappe.throw("{} is not authorized to read this channel".format(frappe.session.user))
    return _rms_get_status(channel, auth=False)

@frappe.whitelist()
def portal_get_device(device_id):
    """ Return connection info only if device_id belongs to a connected Customer """

    cp_owner = frappe.get_value("Connectivity Package", 
                                filters={"rms_id": ["=", device_id]}, 
                                fieldname="customer")

    if cp_owner is None or all(c.docname != cp_owner for c in get_session_customers()):
        # None of the linked customers match this connectivity package owner
        frappe.throw("{} does not have access to this device".format(frappe.session.user)) 

    return _rms_get_device(device_id, auth=False)