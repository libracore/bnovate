frappe.provide("frappe.bnovate.device_map")

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
		devices: [], // List of connected devices
		map: null,   // will contain leaflet map
	}
	frappe.bnovate.device_map.state = state;
	window.state = state;

	let form = new frappe.ui.FieldGroup({
		fields: [{
			label: 'Map',
			fieldname: 'map',
			fieldtype: 'HTML',
			options: '<div id="map" style="height: 800px; width: 100%"></div>',
		}],
		body: page.body
	});
	form.make();
	page.form = form;

	function draw() {
		page.set_secondary_action('Reload', () => load_devices());
		draw_map();
	}

	function draw_map() {
		state.map?.off();
		state.map?.remove();

		let map = L.map('map').setView([46.35357481001013, 6.7310494232727764], 5);
		state.map = map;

		L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
		}).addTo(map);
		let markers = L.markerClusterGroup();
		map.addLayer(markers);

		for (let device of state.devices) {
			markers.addLayer(
				L.marker([device.latitude || device.user_set_latitude, device.longitude || device.user_set_longitude])
					.bindPopup(device.name)
					.openPopup()
			);
		}
		map.fitBounds(markers.getBounds().pad(0.5));
	}

	/********************************
	 * DATA MODEL
	 ********************************/

	async function load_devices() {
		state.devices = await get_devices();
		draw();
	}
	load_devices();


	/*******************************
	 * SERVER CALLS
	 *******************************/

	async function get_devices() {
		let resp = await frappe.call({
			method: "bnovate.bnovate.utils.iot_apis.rms_get_devices",
			args: {}
		});
		console.log(resp);

		return resp.message.data;
	}
}