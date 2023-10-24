# (C) 2023 bNovate
#
# Push notifications to browser. This module exists to work around the difficulty of setting up frappe.realtime.

import frappe

STATUS_RUNNING = -1
STATUS_DONE = 0


@frappe.whitelist()
def get_new_id():
    """ Return a new id for a long-running task"""

    current = frappe.cache().get_value('bn_task_id')
    if type(current) not in (float, int):
        new_id = 1
    else:
        new_id = int((current + 1) % 1e4)

    frappe.cache().set_value('bn_task_id', int(new_id))
    frappe.cache().set_value('bn_sid_{:d}'.format(new_id), frappe.session.sid)
    return new_id

def set_status(data, task_id, status=STATUS_RUNNING):
    """ Set realtime data for task_id. If task_id is None, ignore. """

    print("------------ Post status --------------------", task_id, data)

    if task_id is None:
        return

    task_id = int(task_id)

    if frappe.cache().get_value('bn_sid_{:d}'.format(task_id)) != frappe.session.sid:
        frappe.throw("Forbidden: logged in user does not own this task")

    frappe.cache().set_value('bn_data_{:d}'.format(task_id), {'code': status, 'data': data})

@frappe.whitelist()
def get_status(task_id):
    """ Return status, only if the logged in user is associated with the request. """
    task_id = int(task_id)

    if frappe.cache().get_value('bn_sid_{:d}'.format(task_id)) != frappe.session.sid:
        frappe.throw("Forbidden: logged in user cannot query status for this task")
    return frappe.cache().get_value('bn_data_{:d}'.format(task_id))
