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

bnovate.web.delete_address = async function delete_address(name) {
    const resp = await frappe.call("bnovate.www.helpers.delete_address", {
        name
    })
    return resp.message;
}

bnovate.web.get_countries = async function get_countries() {
    const resp = await frappe.call("bnovate.www.helpers.get_countries")
    return resp.message;
}

// Return FA icon corresponding to signal strength
bnovate.web.signal_icon = function (strength) {
    if (strength > -65) {
        return '/assets/bnovate/img/icons/signal-strength-4.svg';
    } else if (strength > -75) {
        return '/assets/bnovate/img/icons/signal-strength-3.svg';
    } else if (strength > -85) {
        return '/assets/bnovate/img/icons/signal-strength-2.svg';
    } else if (strength > -95) {
        return '/assets/bnovate/img/icons/signal-strength-1.svg';
    }
    return '/assets/bnovate/img/icons/signal-strength-0.svg';
}