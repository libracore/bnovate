import urllib
import frappe
import frappe.utils


def get_context(context):
    """ Added to login context by hooks.py """

    # Fix Redirect URI
    # Social login redirect URI contains hostname from site_config. This prevents serving the 
    # same site from several domains.
    # Replace by it by current session hostname instead.

    if context.provider_logins:
        config_hostname = frappe.utils.get_url()
        session_hostname = frappe.utils.get_host_name_from_request()

        for provider in context.provider_logins:
            provider['auth_url'] = provider['auth_url'].replace(
                urllib.parse.quote(config_hostname, safe=''), 
                urllib.parse.quote(session_hostname, safe=''),
            )

    return context