// (C) 2023, bnovate
// Helpers & general lib for portal

async function get_addresses() {
    const resp = await frappe.call("bnovate.www.helpers.get_addresses")
    return resp.message;
}