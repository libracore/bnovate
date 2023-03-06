// Copyright (c) 2016, libracore and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("/assets/bnovate/js/lib/gcharts/loader.js")

frappe.query_reports["Work Order Planning"] = {
    filters: [
        {
            "fieldname": "workstation",
            "label": __("Workstation"),
            "fieldtype": "Link",
            "options": "Workstation"
        },
    ],
    async onload(report) {
        this.report = report;
        this.colours = ["dark", "light"];

        if (this.loaded === undefined) {
            await report.refresh();
            // report.$tree_footer.after(`
            report.$report.before(`
                <div class="chart-wrapper" style="display:block; min-height:300px; overflow: auto">
                    <div class="chart-container">
                        <div id="timeline" class="report-chart">Timeline</div>
                    </div>
                </div>
            `);
            this.loaded = true;

            google.charts.load('current', { 'packages': ['timeline'] });
            google.charts.setOnLoadCallback(drawChart);
            function drawChart() {
                var container = document.getElementById('timeline');
                var chart = new google.visualization.Timeline(container);
                let dt = build_google_dt(report);
                chart.draw(dt);
                report.chart = chart;
            }
        }
    },
    after_datatable_render(datatable) {
        console.log(datatable);

        if (frappe.query_report.chart) {
            let dt = build_google_dt(frappe.query_report);
            frappe.query_report.chart.draw(dt);
        }
    },
    formatter(value, row, col, data, default_formatter) {
        if (col.fieldname === "sufficient_stock") {
            let color = value ? 'green' : 'red';
            return `<span class="indicator ${color}"></span>`;
        }
        if (data.indent === 1) {
            if (['planned_start_date', 'comment', 'status'].indexOf(col.fieldname) >= 0) {
                return '';
            }
        } else {
            if (col.fieldname === 'comment' && value) {
                value = `<span title="${value}">${value}</span>`
            } else if (col.fieldname === 'status') {
                let [legend, colour] = work_order_indicator(data);
                return `<span class="coloured ${this.colours[data.idx % this.colours.length]}">
                        <span class="indicator ${colour}">${legend}</span>
                    </span>
                    `;
            }
            return `<span class="coloured ${this.colours[data.idx % this.colours.length]}">${default_formatter(value, row, col, data)}</span>`;
        }
        return default_formatter(value, row, col, data)
    },
    initial_depth: 0,
};

// Stolen from work_order_list.js on ERPNext 
function work_order_indicator(doc) {
    if (doc.status === "Submitted") {
        return [__("Not Started"), "orange"];
    } else {
        return [__(doc.status), {
            "Draft": "red",
            "Stopped": "red",
            "Not Started": "red",
            "In Process": "orange",
            "Completed": "green",
            "Cancelled": "darkgrey"
        }[doc.status]];
    }
}

function refresh_google_chart(chart, report) {
}

function build_google_dt(report) {
    var dataTable = new google.visualization.DataTable();

    dataTable.addColumn({ type: 'string', id: 'Workstation' });
    dataTable.addColumn({ type: 'string', id: 'Work Order' });
    dataTable.addColumn({ type: 'string', id: 'style', role: 'style' });
    dataTable.addColumn({ type: 'date', id: 'Start' });
    dataTable.addColumn({ type: 'date', id: 'End' });

    rows = report.data
        .filter(row => row.indent == 0)
        .map(row => [
            row.workstation || "Unknown",
            row.work_order,
            row.sufficient_stock ? "color: #98d85b;" : "color: #ff5858;",
            frappe.datetime.str_to_obj(row.planned_start_date),
            frappe.datetime.str_to_obj(
                row.planned_end_date ||
                row.planned_start_date + " 12:00:00"
            ),
        ])
    console.log(rows)
    dataTable.addRows(rows);
    return dataTable;
}