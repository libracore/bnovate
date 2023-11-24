# Show list of all instruments owned by that customer

import json
import frappe

from frappe import _

from frappe.exceptions import ValidationError

from bnovate.bnovate.utils.iot_apis import rms_get_access_configs, _rms_get_device
from bnovate.bnovate.doctype.connectivity_package.connectivity_package import _start_session, _get_instrument_status, _sweep_instrument_status
from .helpers import get_session_customers, auth, build_sidebar

no_cache = 1


def get_context(context):
    auth(context)
    context.customers = sorted(get_session_customers(), key=lambda c: c.customer_name)
    context.instruments = get_instruments(context.customers)
    build_sidebar(context)
    context.title = _("My Instruments")
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

def auth_connectivity_package(cp_docname):
    """ Return True if access config relates to a gateway owned by a linked customer.

    frappe.throw if config doesn't exist or doesn't belong to a customer linked to current user.
    """
    res = frappe.get_value("Connectivity Package", cp_docname, fieldname=["customer", "rms_id"])
    if res is None:
        frappe.throw("{} Unregistered Connectivity Package {}".format(frappe.session.user))


    cp_owner, device_id = res
    if cp_owner is None or all(c.docname != cp_owner for c in get_session_customers()):
        # None of the linked customers match this connectivity package owner
        frappe.throw("{} does not have access to this device".format(frappe.session.user))

    return cp_owner, device_id

def auth_remote_session(config_id, cp_docname):
    """ Return True if access config relates to a gateway owned by a linked customer.

    frappe.throw if config doesn't exist or doesn't belong to a customer linked to current user.
     
    """

    cp_owner, device_id = auth_connectivity_package(cp_docname)
    # frappe.get_value("Connectivity Package", cp_docname, fieldname=["customer", "rms_id"])

    # if cp_owner is None or all(c.docname != cp_owner for c in get_session_customers()):
    #     # None of the linked customers match this connectivity package owner
    #     frappe.throw("{} does not have access to this device".format(frappe.session.user))

    access_configs = [ c for c in rms_get_access_configs(device_id=device_id, auth=False) if str(c['id']) == config_id ]
    if not access_configs:
        frappe.throw("Remote access configuration does not exist")
    

    return True

@frappe.whitelist()
def portal_start_session(config_id, cp_docname, task_id=None):
    # Raises error if user is not allowed.
    auth_remote_session(config_id, cp_docname)
    return _start_session(cp_docname, config_id, auth=False, task_id=task_id)

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


@frappe.whitelist()
def portal_get_instrument_status(cp_docname, task_id=None):
    """ Return instrument status from embedded /api/status """

    cp_owner = frappe.get_value("Connectivity Package", cp_docname, fieldname="customer")

    if cp_owner is None or all(c.docname != cp_owner for c in get_session_customers()):
        # None of the linked customers match this connectivity package owner
        frappe.throw("{} does not have access to this device".format(frappe.session.user)) 

    return _get_instrument_status(cp_docname, auth=False, task_id=task_id)


@frappe.whitelist()
def portal_sweep_instrument_status(cp_docnames, task_id=None):
    """ Return status of all devices in same order as cp_docnames. 

    Updates are also broadcast as they arrive on realtime.
    """
    if type(cp_docnames) != list:
        cp_docnames = json.loads(cp_docnames)

    for docname in cp_docnames:
        auth_connectivity_package(docname)

    return _sweep_instrument_status(cp_docnames, auth=False, task_id=task_id)
