// Copyright (c) 2023, libracore and contributors
// For license information, please see license.txt

frappe.require("/assets/bnovate/js/iot.js")  // provides bnovate.iot
frappe.require("/assets/bnovate/js/realtime.js")  // provides bnovate.iot
frappe.require("/assets/bnovate/js/web_includes/helpers.js")  // provides signal icons

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

		clear_connection_status(frm);
		clear_instrument_status(frm);

		// Wait for first Save before fetching any data from API...
		if (!frm.doc.creation) {
			return;
		}

		if (frm.doc.teltonika_serial) {
			frm.add_custom_button(__("Get RMS Info"), () => get_rms_info(frm), "Get Info");
		}
		if (frm.doc.rms_id) {
			frm.add_custom_button(__("Auto-configure"), () => configure_device(frm));
			frm.add_custom_button(__("Get Instrument SN"), () => get_instrument_sn(frm), "Get Info");

			get_connection_status(frm);
			get_connections(frm);
		}
	},

	async refresh_connections(frm) {
		get_connection_status(frm);
		get_connections(frm);
	},

	async get_status(frm) {
		get_service_info(frm);
	},

	async validate(frm) {
		// Ensure uniqueness of Serial No. Redundant with "Unique" param of the field, but this message is more helpful.
		const results = await frappe.db.get_list("Connectivity Package", {
			filters: { teltonika_serial: frm.doc.teltonika_serial }
		});

		const duplicates = results.filter(doc => doc.name != frm.doc.name);
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

/////////////////
// General info
/////////////////

// Cache device ID
function get_device_id(frm) {
	if (!frm.doc.rms_id) {
		frappe.msgprint("Missing RMS ID. Please get RMS info first.")
		throw ("Missing RMS ID");
	}
	return frm.doc.rms_id;
}

async function get_rms_info(frm) {
	const resp = await frappe.call({
		method: "bnovate.bnovate.doctype.connectivity_package.connectivity_package.set_info_from_rms",
		args: {
			docname: frm.doc.name,
		}
	});
	frm.reload_doc();
	return resp.message;
};

function clear_connection_status(frm) {
	$(frm.fields_dict.connection_status.wrapper).html(``);
	let message = null;
	if (!frm.doc.rms_id) {
		message = "Please get RMS info."
	}
	set_connections_message(frm, message);
}


async function get_connection_status(frm) {
	const device = await bnovate.iot.rms_get_device(get_device_id(frm));
	$(frm.fields_dict.connection_status.wrapper).html(`
		<span class="indicator whitespace-nowrap ${device.status ? 'green' : 'red'}"></span><b>${device.name}</b> <img src="${bnovate.web.signal_icon(device.signal)}" style="max-height: 2em"> <br />
		${device.operator}, ${device.connection_type} [${device.signal} dBm] <br />
		<a href="https://rms.teltonika-networks.com/devices/${device.id}" target="_blank">Manage on RMS<i class="fa fa-external-link"></i></a>
	`)
}

async function get_instrument_status(frm) {
	const resp = await bnovate.realtime.call({
		method: 'bnovate.bnovate.doctype.connectivity_package.connectivity_package.get_instrument_status',
		args: {
			docname: frm.doc.name,
		},
		callback(status) {
			console.log(status);
		}
	})
	return resp.message
}

async function get_instrument_sn(frm) {
	frappe.show_progress("Fetching Serial No...", 30, 100);
	setTimeout(() => frappe.show_progress("Fetching Serial No...", 60, 100), 300);
	const resp = await frappe.call({
		method: 'bnovate.bnovate.doctype.connectivity_package.connectivity_package.get_instrument_sn',
		args: {
			docname: frm.doc.name,
		}
	});

	frappe.hide_progress();
	frm.reload_doc();
}


///////////////////////
// Remote connections
///////////////////////

function set_connections_message(frm, message = "Loading...") {
	$(frm.fields_dict.connection_table.wrapper).html(message)
}


async function get_connections(frm) {
	if (!frm.has_perm(WRITE)) {
		return
	}
	set_connections_message(frm, "Loading...");
	const device_id = get_device_id(frm)
	if (device_id) {
		const access_configs = await bnovate.iot.rms_get_sessions(device_id);
		if (access_configs.length) {
			draw_table(frm, access_configs);
		} else {
			set_connections_message(frm, "No remote access configurations for this device.")
		}
	} else {
		set_connections_message(frm, "Device not found on RMS.")
	}
}

async function start_session(frm, config_id, device_id) {
	const startBtns = [...document.querySelectorAll('.rms-start')];
	startBtns.map(btn => btn.disabled = true);
	console.log("disable")
	try {
		// const link = await bnovate.iot.rms_start_session(config_id, device_id);
		const resp = await bnovate.realtime.call({
			method: "bnovate.bnovate.doctype.connectivity_package.connectivity_package.start_session",
			args: {
				docname: frm.doc.name,
				config_id: config_id,
			},
			callback(status) {
				console.log(status);
				if (status.data.progress < 100) {
					frappe.show_progress(__("Starting session...."), status.data.progress, 100, __(status.data.message));
				}
			}
		})
		const link = resp.message;
		if (link) {
			frappe.hide_progress();
			window.open("https://" + link, "_blank");
		}
	} finally {
		startBtns.map(btn => btn.disabled = false);
		console.log("enable")
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
					<td><button class="btn btn-xs btn-primary rms-start" onclick="cur_frm.start_session({{ access.id }}, {{ access.device_id }})">New</button></td>
					<td></td>
				</tr>
					{% for session in access.sessions %}
					<tr>
						<td></td>
						<td></td>
						<td>
							<!-- <a><i onclick="cur_frm.rms_modal('https://{{ session.url }}')" class="fa fa-desktop"></i></a> -->
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
// Device Configuration
//////////////////////////////////////

// Rename device and add HTTP and VNC remotes for first available ports.
async function configure_device(frm) {
	const device_id = get_device_id(frm)
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

	set_connections_message(frm, "Loading...");
	await frappe.call({
		method: "bnovate.bnovate.doctype.connectivity_package.connectivity_package.auto_configure_device",
		args: {
			device_id,
			new_device_name: values.device_name,
			docname: frm.doc.name,
		}
	});
	frm.reload_doc();
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



///////////////////////////////////////
// Instrument Status
//////////////////////////////////////


function clear_instrument_status(frm) {
	$(frm.fields_dict.instrument_status.wrapper).html(``);
}

async function get_service_info(frm) {

	function format_date(unix_ts) {
		const date = moment.unix(unix_ts);
		if (date.isBefore()) {
			return `<div class="alert alert-warning" style="margin: 0px">${frappe.datetime.obj_to_user(date)}</div>`;
		} else {
			return frappe.datetime.obj_to_user(date);
		}
	}

	$(frm.fields_dict.instrument_status.wrapper).html(`<i class="fa fa-cog fa-spin" style="font-size: 20px"></i>`);
	const status = await get_instrument_status(frm);
	$(frm.fields_dict.instrument_status.wrapper).html(frappe.render_template(
		`
		<table class="table table-condensed no-margin" style="border-bottom: 1px solid #d1d8dd">
		<tbody>
			<tr>
				<th>Serial No</th>
				<td>{{ status.serialNumber }}</td>
			</tr>
			<tr>
				<th>Status</th>
				<td>{{ status.status }}</td>
			</tr>
			<tr>
				<th>Error</th>
				<td>{{ status.lastError || "-" }}</td>
			</tr>
			<tr>
				<th>Software Version</th>
				<td>{{ status.version }}</td>
			</tr>
			<tr>
				<th>Fill Type</th>
				<td>{{ status.cartridgeType }}</td>
			</tr>
			<tr>
				<th>Fill Serial No</th>
				<td>{{ status.fillSerial }}</td>
			</tr>
			<tr>
				<th>Cartridge Level</th>
				<td>{{ Math.round(status.cartridgeLevel / ( status.cartridgeCapacity || 1000 ) * 100) }} %</td>
			</tr>
			<tr>
				<th>Cartridge Expiry</th>
				<td>{{ format_date(status.cartridgeExpiry) }}</div></td>
			</tr>
			<tr>
				<th>Cartridge Serial No</th>
				<td>{{ status.cartridgeSerial }}</td>
			</tr>
			<tr>
				<th>Temperature, Humidity</th>
				<td>{{ Math.round(status.temperature) }}° C, {{ Math.round(status.humidity) }} %RH</td>
			</tr>
			<tr>
				<th>Service: Due Date</th>
				<td>{{ format_date(status.nextServiceDue) }}</td>
			</tr>
			<tr>
				<th>Service: Valve Lifetime Remaining</th>
				<td>{{ Math.round(100 - status.valveMotions / ( status.valveLifetime || 1000 ) * 100) }} %</td>
			</tr>
			<tr>
				<th>Service: Plunger Lifetime Remaining </th>
				<td>{{ Math.round(100 - status.plungerMotions / ( status.plungerLifetime || 1000 ) * 100) }} %</td>
			</tr>
		</tbody>
		</table>
		`,
		{
			status,
			format_date,
		}));
}
