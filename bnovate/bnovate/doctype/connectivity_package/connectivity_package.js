// Copyright (c) 2023, libracore and contributors
// For license information, please see license.txt

frappe.require("/assets/bnovate/js/iot.js")  // provides bnovate.iot

frappe.ui.form.on('Connectivity Package', {
	onload(frm) {
		frm.set_query("subscription", function () {
			return {
				filters: {
					customer: frm.doc.customer,
				}
			}
		});
	},

	async refresh(frm) {
		frm.rms_modal = rms_modal;
		frm.start_session = (config_id, device_id) => start_session(frm, config_id, device_id);

		clear_info(frm);

		// Wait for first Save before fetching any data from API...
		if (!frm.doc.creation) {
			return;
		}

		let device_id = await get_device_id(frm, true);
		if (!device_id) {
			return;
		}

		frm.add_custom_button(__("Auto-configure"), () => configure_device(frm))

		get_device_info(frm)
		get_connections(frm);

	},

	async refresh_connections(frm) {
		get_device_info(frm);
		get_connections(frm);
	},

	async validate(frm) {
		// Ensure uniqueness of Serial No. Redundant with "Unique" param of the field, but this message is more helpful.
		const results = await frappe.db.get_list("Connectivity Package", {
			filters: { teltonika_serial: frm.doc.teltonika_serial }
		});
		console.log(results)

		const duplicates = results.filter(doc => doc.name != frm.doc.name);
		console.log(duplicates)
		if (duplicates.length) {
			frappe.validated = false;
			const link = frappe.utils.get_form_link("Connectivity Package", results[0].name, true, results[0].name)
			frappe.msgprint({
				indicator: 'red',
				message: __(`Another package already exists with this serial number: ${link}`)
			});
		}
	}

});

// General info
///////////////

// Cache device ID
async function get_device_id(frm, refresh = false) {
	if (!locals.rms_device_id) {
		locals.rms_device_id = {};
	}

	if (!refresh && locals.rms_device_id[frm.doc.teltonika_serial]) {
		return locals.rms_device_id[frm.doc.teltonika_serial];
	}

	locals.rms_device_id[frm.doc.teltonika_serial] = await rms_get_id(frm.doc.teltonika_serial);
	return locals.rms_device_id[frm.doc.teltonika_serial];
}

function clear_info(frm) {
	$(frm.fields_dict.info.wrapper).html(``);
	set_message(frm)
}

async function get_device_info(frm) {
	const device = await rms_get_device(await get_device_id(frm));
	$(frm.fields_dict.info.wrapper).html(`
		<span class="indicator whitespace-nowrap ${device.status ? 'green' : 'red'}"></span><b>${device.name}</b><br />
		${device.operator}, ${device.connection_type} [${device.signal} dBm] <br />
		<a href="https://rms.teltonika-networks.com/devices/${device.id}" target="_blank">Manage on RMS<i class="fa fa-external-link"></i></a>
	`)
}

// Remote connections
///////////////////

function set_message(frm, message = "Loading...") {
	$(frm.fields_dict.connection_table.wrapper).html(message)
}


async function get_connections(frm) {
	if (!frm.has_perm(WRITE)) {
		return
	}
	set_message(frm, "Loading...");
	const device_id = await get_device_id(frm)
	if (device_id) {
		const access_configs = await rms_get_sessions(device_id);
		if (access_configs.length) {
			draw_table(frm, access_configs);
		} else {
			set_message(frm, "No remote access configurations for this device.")
		}
	} else {
		set_message(frm, "Device not found on RMS.")
	}
}

async function start_session(frm, config_id, device_id) {
	const link = await rms_start_session(config_id, device_id);
	if (link) {
		window.open("https://" + link, "_blank");
	}
	get_connections(frm);
}

function draw_table(frm, access_configs) {
	$(frm.fields_dict.connection_table.wrapper).html(
		frappe.render_template(`
			<table class="table table-condensed no-margin" style="border-bottom: 1px solid #d1d8dd">
			<thead>
				<th>Name</th>
				<th>Protocol</th>
				<th>Link</th>
				<th>Valid Until</th>
			</thead>
			<tbody>
				{% for access in access_configs %}
				<tr>
					<td><b>{{ access.name }}</b></td>
					<td>{{ access.protocol.toUpperCase() }}</td>
					<td><button class="btn btn-xs btn-primary" onclick="cur_frm.start_session({{ access.id }}, {{ access.device_id }})">New</button></td>
					<td></td>
				</tr>
					{% for session in access.sessions %}
					<tr>
						<td></td>
						<td></td>
						<td>
							<a><i onclick="cur_frm.rms_modal('https://{{ session.url }}')" class="fa fa-desktop"></i></a>
							<a href="https://{{ session.url }}" target="_blank"><i class="fa fa-external-link"></i></a>
						</td>
						<td>{{ frappe.datetime.get_time(session.end_time * 1000) }}</td>
					</tr>
					{% endfor %}
				{% endfor %}
			</tbody>
			</table>
		`, {
			access_configs
		}));
}

// Show modal with embedded RMS remote, for example VNC
function rms_modal(url) {
	let d = new frappe.ui.Dialog({
		title: 'RMS Connection to xyz',
		fields: [{
			label: 'iFrame',
			fieldname: 'iframe',
			fieldtype: 'HTML',
			options: `<iframe src="${url}" sandbox="allow-scripts" width="800" height="480"></iframe>`,
		}]
	})
	d.show();
}


///////////////////////////////////////
// Device Info
//////////////////////////////////////

// Rename device and add HTTP and VNC remotes for first available ports.
async function configure_device(frm) {
	const device_id = await get_device_id(frm)
	let values = await prompt(
		"Enter device details",
		[{
			label: "Device Name",
			fieldname: "device_name",
			fieldtype: "Data",
			reqd: 1,
		}],
		"Configure",
		"Cancel"
	);

	if (!values) {
		return;
	}

	set_message(frm, "Loading...");
	await rms_initialize_device(device_id, values.device_name);
	await get_device_info(frm);
	return get_connections(frm);
}

// Promise-ified frappe prompt:
function prompt(title, fields, primary_action_label, secondary_action_label) {
	return new Promise((resolve, reject) => {
		const d = new frappe.ui.Dialog({
			title,
			fields,
			primary_action_label,
			secondary_action_label,
			primary_action(values) {
				resolve(values);
				this.hide();
			},
			secondary_action() { resolve(null); },
		})
		d.show();
	})
}