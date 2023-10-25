import frappe

def get_homepage(user):
    """ Called through hooks.py after login"""
    user_type = frappe.db.get_value("User", {"name": user}, "user_type")
    if user_type == "Website User":
        return "index"
    return "desk"