// (C) 2023, bnovate
// Simulate realtime update from the server.

frappe.provide('bnovate.shipping');

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

// Return last possible time for same-day pickup
bnovate.shipping.get_same_day_cutoff = async function (pallets) {
    const resp = await frappe.call({
        method: 'bnovate.bnovate.utils.shipping.get_same_day_cutoff',
        args: {
            pallets
        }
    })
    return resp.message
}

bnovate.shipping.validate_address = async function (name, throw_error = true) {
    try {
        const resp = await frappe.call({
            method: 'bnovate.bnovate.utils.shipping.validate_address',
            args: {
                name,
                throw_error
            }
        });

        if (!throw_error) {
            return !!resp.message;
        }

    } catch (e) {
        // Error message is displayed anyway.
        return;
    }

    // If no error raised, Address is shippable
    frappe.msgprint(__("Address is deliverable"))
}
