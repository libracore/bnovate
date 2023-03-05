frappe.require(["/assets/frappe/css/frappe-datatable.css",
	"/assets/frappe/js/lib/clusterize.min.js",
	"/assets/frappe/js/lib/Sortable.min.js",
	"/assets/frappe/js/lib/frappe-datatable.js"])

frappe.provide("frappe.bnovate.device_map");

frappe.pages['device-map'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Connected Device Map',
		single_column: true
	});

	// for easier debugging
	frappe.bnovate.device_map.page = page;
	window.page = page;

	const state = {
		devices: [], 	// List of connected devices
		map: null,   	// will contain leaflet map
		report_data: {} // will contain columns and result for DataTable as provided by a report.
	}
	frappe.bnovate.device_map.state = state;
	window.state = state;

	let form = new frappe.ui.FieldGroup({
		fields: [{
			label: 'Map',
			fieldname: 'map',
			fieldtype: 'HTML',
			options: '<div id="map" style="height: 800px; width: 100%"></div>',
		}, {
			label: 'Table',
			fieldname: 'table',
			fieldtype: 'HTML',
			options: '<div id="table"></div>',

		}],
		body: page.body
	});
	form.make();
	page.form = form;

	function draw() {
		page.set_secondary_action('Reload', () => load());
		draw_map();
		draw_table();
	}

	function draw_map() {
		let [bn_lat, bn_long] = [46.35357481001013, 6.7310494232727764]
		state.map?.off();
		state.map?.remove();

		let map = L.map('map').setView([bn_lat, bn_long], 5);
		state.map = map;

		L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
		}).addTo(map);
		let markers = L.markerClusterGroup();
		map.addLayer(markers);

		for (let device of state.devices) {
			// if (device.accuracy || device.cell_tower_accuracy) {
			// 	markers.addLayer(
			// 		L.circle([
			// 			device.latitude || device.cell_tower_latitude,
			// 			device.longitude || device.cell_tower_longitude,

			// 		], device.accuracy || device.cell_tower_accuracy, {

			// 		})
			// 	)
			// }
			markers.addLayer(
				L.marker([
					device.latitude || device.cell_tower_latitude || device.user_set_latitude || bn_lat,
					device.longitude || device.cell_tower_longitude || device.user_set_longitude || bn_long
				])
					.bindPopup(`
					<span class="indicator whitespace-nowrap ${device.status ? 'green' : 'red'}"></span><b>${device.name}</b><br />
					${device.operator}, ${device.connection_type} [${device.signal} dBm] <br />
					${frappe.utils.get_form_link("Connectivity Package", device.docname, true, "Manage")}
					`)
					.openPopup()
			);
		}
		map.fitBounds(markers.getBounds().pad(0.5));
	}

	async function draw_table() {
		// Use Frappe's QueryReport class to transform data for DataTable:
		let report = new frappe.views.QueryReport({
			report_name: "Connected Devices",
			parent: page.form.fields_dict.table.wrapper,
		});
		await report.get_report_doc();
		await report.get_report_settings();
		report.$report = [form.fields_dict.table.wrapper];
		report.prepare_report_data(state.report_data);
		report.render_datatable();
	}
	window.draw_table = draw_table

	/********************************
	 * DATA MODEL
	 ********************************/

	async function load() {
		await load_report();

		draw();
	}

	async function load_report() {
		state.report_data = await get_report();
		state.devices = state.report_data.result.filter(row => row.indent == 1) // Devices are indented 1, customers 0.
	}

	load();

	/*******************************
	 * SERVER CALLS
	 *******************************/

	// Return array of all connected devices with current cycle data usage.
	async function get_devices_and_data() {
		let resp = await frappe.call({
			method: "bnovate.bnovate.utils.iot_apis.get_devices_and_data",
			args: {}
		});
		return resp.message;
	}
	window.get_devices_and_data = get_devices_and_data;

	// Fetch report data
	async function get_report() {
		let resp = await frappe.call({
			method: "frappe.desk.query_report.run",
			args: {
				report_name: "Connected Devices",
				filters: {
					// only_stock_items: 1,
				}
			}
		})
		return resp.message;
	}
}