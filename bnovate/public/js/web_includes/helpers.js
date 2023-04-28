// (C) 2023, bnovate
// Helpers & general lib for portal

frappe.provide("bnovate.web");

bnovate.web.get_addresses = async function get_addresses() {
    const resp = await frappe.call("bnovate.www.helpers.get_addresses")
    return resp.message;
}

bnovate.web.create_address = async function create_address(doc) {
    const resp = await frappe.call("bnovate.www.helpers.create_address", {
        ...doc
    })
    return resp.message;
}

bnovate.web.get_countries = async function get_countries() {
    const resp = await frappe.call("bnovate.www.helpers.get_countries")
    return resp.message;
}