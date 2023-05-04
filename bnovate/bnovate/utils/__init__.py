import random
import string

import frappe

@frappe.whitelist()
def get_random_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))