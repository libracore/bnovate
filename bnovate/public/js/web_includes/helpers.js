// (C) 2023, bnovate
// Helpers & general lib for portal

frappe.provide("bnovate.web");

frappe.require("/assets/js/control.min.js");
frappe.require("/assets/js/dialog.min.js");
frappe.require("/assets/bnovate/js/bnovate_common.js");

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

bnovate.web.get_instrument_status_modal = async function (cp_docname, cp_device_name) {
    const status = await bnovate.iot.portal_get_instrument_status(cp_docname);

    function format_date(unix_ts) {
        const date = moment.unix(unix_ts);
        if (date.isBefore()) {
            return `<div class="alert alert-warning" style="margin: 0px">${date.format("DD-MM-YYYY")}</div>`;
        } else {
            return date.format("DD-MM-YYYY");
        }
    }

    if (status) {
        console.log(status)
        bnovate.utils.html_dialog(
            cp_device_name || __('Status'),
            `<table class="table table-condensed no-margin" style="border-bottom: 1px solid #d1d8dd">
                <tbody>
                    <tr>
                        <th>Serial No</th>
                        <td>${status.serialNumber}</td>
                    </tr>
                    <tr>
                        <th>Status</th>
                        <td>${status.status}</td>
                    </tr>
                    <tr>
                        <th>Fill Serial No</th>
                        <td>${status.fillSerial}</td>
                    </tr>
                    <tr>
                        <th>Cartridge Level</th>
                        <td>${Math.round(status.cartridgeLevel / (status.cartridgeCapacity || 1000) * 100)} %</td>
                    </tr>
                    <tr>
                        <th>Cartridge Expiry</th>
                        <td>${format_date(status.cartridgeExpiry)}</div></td>
                    </tr>
                    <tr>
                        <th>Cartridge Serial No</th>
                        <td>${status.cartridgeSerial}</td>
                    </tr>
                    <tr>
                        <th>Service: Due Date</th>
                        <td>${format_date(status.nextServiceDue)}</td>
                    </tr>
                    <tr>
                        <th>Service: Wear Parts Lifetime Remaining</th>
                        <td>${Math.round(100 - Math.max(status.valveMotions / (status.valveLifetime || 60000), status.plungerMotions / (status.plungerLifetime || 10000)) * 100)} %</td>
                    </tr>
                </tbody>
            </table>`
        );
    }
}