""" Added to login by hooks.py """

import urllib
import frappe
import frappe.utils


def get_context(context):
    # Fix Redirect URI
    # Social login redirect URI contains hostname from site_config. Replace by current session hostname

    import pprint
    pprint.pprint(context)

    if context.provider_logins:
        config_hostname = frappe.utils.get_url()
        session_hostname = frappe.utils.get_host_name_from_request()

        for provider in context.provider_logins:
            print(provider)
            print(urllib.parse.quote(config_hostname, ""))
            print(urllib.parse.quote(session_hostname, ""))

            # TODO: replace config hostname by session hostname in provider.auth_url


        pprint.pprint(context.provider_logins)

    return context