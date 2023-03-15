// Copyright (c) 2023, bNovate, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("/assets/bnovate/js/lib/gcharts/loader.js")
// frappe.require("/assets/bnovate/js/modals.js")  // provides bnovate.modals

frappe.query_reports["Subscription Timeline"] = {
    filters: [
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },

    ],
    onload(report) {
        this.report = report;
    },
    after_datatable_render(datatable) {
        draw_google_chart(this.report);
    },
};



function draw_google_chart(report) {
    report.$chart.html(`
            <div class="chart-container">
                <div id="timeline" class="report-chart">Timeline</div>
            </div>
    `);

    // Track mouse position in chart to draw popover at correct location
    report.mousePos = { x: 0, y: 0 };
    let container = document.getElementById("timeline");
    document.addEventListener("mousemove", (e) => {
        console.log(e)
        report.mousePos.x = e.pageX;
        report.mousePos.y = e.pageY;
    });

    // Popover is the popup shown when clicking a bar on the timeline chart.
    // #sacrificial is a little 0x0 px square created at the location clicked.
    function dismiss_popover() {
        $('#sacrificial').popover('hide');
        $('#sacrificial').remove();
    }

    google.charts.load('current', { 'packages': ['timeline'] });
    google.charts.setOnLoadCallback(drawChart);
    function drawChart() {
        let chart = new google.visualization.Timeline(container);
        report.chart = chart;

        report.chart_dt = build_google_dt(report);

        // Show a popover when a timeline element is clicked. Popovers in bootstrap 3 don't
        // delete nicely, so I made a workaround where I create a sacrificial div centered on the
        // click and bind the popover to this div.
        google.visualization.events.addListener(chart, 'select', () => {

            dismiss_popover();


            $(document.body).append(
                `<div id="sacrificial" style="left: ${report.mousePos.x}px; top: ${report.mousePos.y}px"></div>`
            )
            console.log("reached here")

            let row = chart.getSelection()[0].row;
            let contents = report.chart_dt.getValue(row, 2);

            $("#sacrificial").popover({
                container: "body",
                title: "My fancy popover",
                html: true,
                content: contents,
                placement: "bottom",
            }).popover('show');

        });

        // Any click outside the popover dismisses it. May interfere with other popovers...
        document.addEventListener("click", (event) => {
            const popover = $(".popover");
            if (popover.is(event.target) || popover.has(event.target).length) {
                // Ignore if click target is inside a popover
                return;
            }
            dismiss_popover();
        });
        frappe.route.on('change', () => { dismiss_popover() });

        chart.draw(report.chart_dt, {
            height: 250,
            fontName: "Open Sans",
            tooltip: {
                // isHtml: true,
                trigger: 'both', // disable it

            },
        });
    }


}

function build_google_dt(report) {
    var dataTable = new google.visualization.DataTable();

    dataTable.addColumn({ type: 'string', id: 'Customer Name' });
    dataTable.addColumn({ type: 'string', id: 'Subscription' });
    dataTable.addColumn({ type: 'string', id: 'tooltip', role: 'tooltip' });
    // dataTable.addColumn({ type: 'string', id: 'style', role: 'style' });
    dataTable.addColumn({ type: 'date', id: 'Start' });
    dataTable.addColumn({ type: 'date', id: 'End' });

    let rows = report.data.map(row => [
        row.customer_name,
        `${row.subscription}: ${row.title}`,
        frappe.render_template(popover_template, row),
        frappe.datetime.str_to_obj(row.start_date),
        frappe.datetime.str_to_obj(row.computed_end_date),
    ]);

    dataTable.addRows(rows);

    return dataTable;
}

const popover_template = `
    <div class="preview-popover-header">
        <div class="preview-header">
        </div>

        <div class="preview-header">
            <div class="preview-main">
                {{ subscription }}: {{ title }}
                <span class="small preview-value">
                </span>
                <br>
                <span class="small text-muted">{{ start_date }} {% if end_date %} - {{ end_date }}{% endif %}</span>
            </div>
        </div>
    </div>
    <hr>
    <div class="popover-body">
        <div class="preview-table" style="max-width: none">
            <div class="preview-field">
                <div class="small preview-label text-muted bold">Planned End Date</div>
                <div class="small preview-value">{{ planned_end_date || "TBD" }}</div>
            </div>
            <div class="preview-field">
                <div class="small preview-label text-muted bold">Actual End Date</div>
                <div class="small preview-value">{{ end_date || "TBD" }}</div>
            </div>

        </div>
    </div>
`