// (C) 2023, bnovate
// Helpers & general lib for portal

frappe.provide("bnovate.web");

bnovate.web.get_addresses = async function get_addresses() {
    const resp = await frappe.call("bnovate.www.helpers.get_addresses")
    return resp.message;
}