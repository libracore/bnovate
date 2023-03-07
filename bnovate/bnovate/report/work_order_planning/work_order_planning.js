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
    onload(report) {
        this.report = report;
        this.colours = ["dark", "light"];
    },
    after_datatable_render(datatable) {
        this.report.$chart.html(`
                <div class="chart-container">
                    <div id="timeline" class="report-chart">Timeline</div>
                </div>
        `);

        draw_google_chart('timeline', this.report);
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

function draw_google_chart(container_id, report) {
    google.charts.load('current', { 'packages': ['timeline'] });
    google.charts.setOnLoadCallback(drawChart);
    function drawChart() {
        var container = document.getElementById(container_id);
        var chart = new google.visualization.Timeline(container);
        // google.visualization.events.addListener(chart, 'select', (event) => { console.log("selected", event, chart.getSelection()) });

        chart.draw(build_google_dt(report), {
            height: 300,
            tooltip: {
                isHtml: true,
                // trigger: 'selection',
            },
        });
        report.chart = chart;
    }
}

function build_google_dt(report) {
    var dataTable = new google.visualization.DataTable();

    dataTable.addColumn({ type: 'string', id: 'Workstation' });
    dataTable.addColumn({ type: 'string', id: 'Work Order' });
    dataTable.addColumn({ type: 'string', role: 'tooltip' });
    dataTable.addColumn({ type: 'string', id: 'style', role: 'style' });
    dataTable.addColumn({ type: 'date', id: 'Start' });
    dataTable.addColumn({ type: 'date', id: 'End' });

    rows = report.data
        .filter(row => row.indent == 0)
        .map(row => [
            row.workstation || "Unknown",
            row.work_order,
            frappe.render_template(`
            <div class="popover-container" style="display:table">
                <div class="popover link-preview-popover in" style="display: block; position: relative;">
                    <div class="popover-content">
                        <div class="preview-popover-header">
                            <div class="preview-header">
                            </div>

                            <div class="preview-header">
                                <div class="preview-main">
                                    <a class="preview-name bold" href="#Form/Work Order/{{ work_order }}">{{ work_order }}: {{ item_name }}</a>
                                    <span class="text-muted small">Item <a class="text-muted" href="#Form/Item/{{ item }}">{{ item }}</a></span>
                                </div>
                            </div>
                        </div>
                        <hr>
                        <div class="popover-body">
                            <div class="preview-table" style="max-width: none;">
                                <div class="preview-field">
                                    <div class="small preview-label text-muted bold">Qty remaining to produce</div>
                                    <div class="small preview-value">{{ required_qty }}</div>
                                </div>
                                <div class="preview-field">
                                    <div class="small preview-value">
                                        <table class="table table-condensed no-margin" style="border-bottom: 1px solid #d1d8dd; width:100%">
                                        <thead>
                                            <th></th>
                                            <th class="text-left">Item</th>
                                            <th class="text-left">Name</th>
                                            <th class="text-right">Required</th>
                                            <th class="text-right">Stock</th>
                                        </thead>
                                        <tbody>
                                            {% for item in items %}
                                            <tr>
                                                <td><span class="indicator {{ item.sufficient_stock ? "green" : "red" }}"></span></td>
                                                <td class="text-left">{{ item.item_code }}</td>
                                                <td class="text-left">{{ frappe.ellipsis(item.item_name, 30) }}</td>
                                                <td class="text-right">{{ item.required_qty }}</td>
                                                <td class="text-right">{{ item.available_stock }}</td>
                                            </tr>
                                            {% endfor %}
                                        </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            `, row),
            row.sufficient_stock ? "color: #98d85b;" : "color: #ff5858;",
            frappe.datetime.str_to_obj(row.planned_start_date),
            frappe.datetime.str_to_obj(
                row.planned_end_date ||
                row.planned_start_date + " 12:00:00"
            ),
        ])
    dataTable.addRows(rows);
    console.log(dataTable);
    return dataTable;
}