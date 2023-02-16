// Copyright (c) 2023, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('Connectivity Package', {
	refresh(frm) {
		frm.rms_modal = rms_modal;
		get_connections(frm);
	},

	async refresh_connections(frm) {
		get_connections(frm);
	},
});

async function get_connections(frm) {
	set_loading(frm);
	const device_id = await rms_get_id(frm.doc.teltonika_serial);
	const access_configs = await rms_get_sessions(device_id);
	draw_table(frm, access_configs);
}

function set_loading(frm) {
	$(frm.fields_dict.connection_table.wrapper).html(`Loading...`)
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
					<td></td>
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
			options: `<iframe src="${url}" width="800" height="480"></iframe>`,
		}]
	})
	d.show();
}