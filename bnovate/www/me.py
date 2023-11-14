# (c) 2023, bNovate
#
# Hacky middleware to control what happens post-login.
#
# After successful oauth login, user is redirected to /me. I can't 
# change this through hooks. Instead, I redirect in JS from me.html

import frappe

from frappe.www import me

from .helpers import is_guest

def get_context(context):
    me.get_context(context)

    context.is_guest = is_guest()

