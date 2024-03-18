
const modal_template = `
<div class="modal" tabindex="-1" role="dialog" id="myModal" style="display:none">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">{{ __("Request Refill") }}</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">
                
                <ol class="wizard-ribbon">
                    <li class="wizard-step current" data-step="1">{{ __("Cartridges") }}</li>
                    <li class="wizard-step" data-step="2">{{ __("Shipping") }}</li>
                    <li class="wizard-step" data-step="3">{{ __("Billing") }}</li>
                    <li class="wizard-step" data-step="4">{{ __("Summary") }}</li>
                </ol>
                
                <div class="wizard-page" id="page1"> 
                    <i class="fa fa-cog fa-spin" style="font-size: 20px"></i>
                </div>
                <div class="wizard-page" id="page2" style="display: none;"></div>
                <div class="wizard-page" id="page3" style="display: none;"></div>
                <div class="wizard-page wizard-summary" id="page4" style="display: none;"></div>

                <div class="modal-footer">
                    <div class="wizard-buttons">
                        <!-- <button type="button" class="btn btn-danger" id="cancelButton">{{ __("Cancel") }}</button> -->
                        <button type="button" class="btn btn-secondary" id="prev-button">{{ __("Previous") }}</button>
                        <button type="button" class="btn btn-primary" id="next-button" disabled>{{ __("Next") }}</button>
                        <button type="button" class="btn btn-primary" id="done-button">{{ __("Confirm Order") }}</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
`;

const template_page1 = `
<table class="table">
    <thead>
        <th>{{ __("Serial No") }}</th>
        <th>{{ __("Variant") }}</th>
    </thead>
    <tbody>
        <tr>
            <td>[{{ __("All") }}]</td>
            <td>
                <select id="variant-default">
                    <option value=""></option>
                    <option>TCC</option>
                    <option>ICC</option>
                    <option>ICC+</option>
                </select>
            </td>
        </tr>
        {% for sn in serial_nos %}
        <tr>
            <td>{{ sn.serial_no }}</td>
            <td>
                <select class="variant-select" name="variant-{{sn.serial_no}}" data-sn="{{sn.serial_no}}" data-last_shipped="{{sn.address_short}}">
                    <option value=""></option>
                    <option>TCC</option>
                    <option>ICC</option>
                    <option>ICC+</option>
                </select>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
`;

const template_page2 = `
<div class="card-group">
    {% for addr in addresses %}
    <div class="card">
        <div class="card-body">
            <input type="radio" name="shipping_address" id="ship-{{addr.name}}" value="{{addr.name}}" {% if addresses.length == 1 %}checked{% endif %}/>
            <label for="ship-{{addr.name}}">{{addr.display}}</label>
        </div>
    </div>
    {% endfor %}
</div>
`

const template_page3 = `
<div class="card-group">
    {% for addr in addresses %}
    <div class="card">
        <div class="card-body">
            <input type="radio" name="billing_address" id="bill-{{addr.name}}" value="{{addr.name}}" {% if addresses.length == 1 %}checked{% endif %}/>
            <label for="bill-{{addr.name}}">{{addr.display}}</label>
        </div>
    </div>
    {% endfor %}
</div>
`

const template_page4 = `
<div class="row">
    <div class="col-sm">
        <h5>{{ __("Shipping Address") }}</h5>
        {{doc.shipping_address_display}}
    </div>
    <div class="col-sm">
        <h5>{{ __("Billing Address") }}</h5>
        {{doc.billing_address_display}}
    </div>
</div>

<div class="row">
    <div class="col-sm">
        <h5>{{ __("Cartridges") }}</h5>
        <table class="table">
            <thead>
                <th>{{ __("Serial No") }}</th>
                <th>{{ __("Variant") }}</th>
                <th>{{ __("Last Shipped To") }}</th>
            </thead>
            <tbody>
                {% for it in doc.items %}
                <tr>
                    <td>{{ it.serial_no }}</td>
                    <td>{{ it.type }}</td>
                    <td>{{ it.last_shipped }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>


<div class="row">
    <div class="col-sm">
        <h5>{{ __("Remarks") }}</h5>
        <label for="remarks" style="display: none">Remarks</label>
        <textarea type="text" name="remarks"></textarea>
    </div>
</div>

<div class="row">
    <div class="col-sm">
    <p>{{ __("After confirming this order, the cartridges will be filled, shipped, and charged to your account.") }}</p>
    </div>
</div>
`

customElements.define('wizard-modal', class extends HTMLElement {
    constructor() {
        super();

        window.theModal = this;

        // Data used to build the refill request doc:
        this.serial_nos = [];
        this.addresses = [];
        this.doc = {};

        // Initialize the wizard
        this.currentPage = 1;
        this.numPages = 4; // $(".wizard-page").length;
    }

    draw() {
        // Attach template. Only draw when modal is summoned, makes it more likely that translations are loaded.
        this.attachShadow({ mode: "open" });
        this.shadowRoot.innerHTML = frappe.render_template(modal_template, {});


        this.modal = this.shadowRoot.getElementById("myModal");
        this.next = this.shadowRoot.getElementById("next-button");
        this.prev = this.shadowRoot.getElementById("prev-button");
        this.done = this.shadowRoot.getElementById("done-button");

        $(this.modal).on('show.bs.modal', (e) => {
            this.currentPage = 1;
            this.show_page(this.currentPage);

            e.target.querySelector('.modal-body #page1').innerHTML = frappe.render_template(template_page1, {
                serial_nos: this.serial_nos,
            });
            e.target.querySelector('.modal-body #page2').innerHTML = frappe.render_template(template_page2, {
                addresses: this.addresses,
            });
            e.target.querySelector('.modal-body #page3').innerHTML = frappe.render_template(template_page3, {
                addresses: this.addresses,
            });

            this.bind_listeners(e.target);
        })

        $(this.modal).on('hide.bs.modal', (e) => {
            // e.target.querySelector('.modal-body #page1').innerHTML = '';
        })

        // Add event listeners to the navigation buttons
        $(this.prev).click(() => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.show_page(this.currentPage);
            }
        });

        $(this.next).click(() => {
            if (this.currentPage < this.numPages) {
                this.currentPage++;
                this.show_page(this.currentPage);
            }
        });

        $(this.cancel).click(() => {
            // Close the modal or redirect to another page
            $(this.modal).modal("hide");
        });

        $(this.done).click(() => {
            this.confirm();
        });
    }

    show(serial_nos, addresses, callback) {
        if (!this.shadowRoot) {
            this.draw();
        }
        this.serial_nos = serial_nos;
        this.addresses = addresses;
        this.callback = callback;
        $(this.modal).modal({ backdrop: 'static', keyboard: false });
    }

    hide() {
        $(this.modal).modal('hide');
    }

    // Show or hide the navigation buttons based on the current page
    update_buttons() {
        if (this.currentPage == 1) {
            this.prev.disabled = true;
        } else {
            this.prev.disabled = false;
        }

        if (this.currentPage == this.numPages) {
            this.next.hidden = true;
            this.done.hidden = false;
        } else {
            this.next.hidden = false;
            this.done.hidden = true;
        }

        $(".wizard-step").removeClass("current");
        $(`.wizard-step[data-step='${this.currentPage}']`).addClass("current");
    }

    // Enable or disable buttons based on form completion
    enable_buttons() {
        const doc = this.build_doc()

        if (this.currentPage == 1) {
            if (doc.items.length && doc.items.findIndex(el => el.type == '') < 0) {
                this.next.disabled = false;
            } else {
                this.next.disabled = true;
            }
        } else if (this.currentPage == 2) {
            if (doc.shipping_address) {
                this.next.disabled = false;
            } else {
                this.next.disabled = true;
            }
        } else if (this.currentPage == 3) {
            if (doc.billing_address) {
                this.next.disabled = false;
            } else {
                this.next.disabled = true;
            }
        }
    }

    // Show the specified page and update the navigation buttons
    show_page(page) {
        if (page == this.numPages) {
            this.modal.querySelector('#page' + page).innerHTML = frappe.render_template(
                template_page4,
                { doc: this.build_doc() }
            );
        }

        $(".wizard-page").hide();
        $("#page" + page).show();

        this.update_buttons();
        this.enable_buttons();
    }

    // Set all blank variant selects when the first one is modified
    bind_listeners(el) {
        const selects = [...el.querySelectorAll(".variant-select")];
        el.querySelector("#variant-default").addEventListener("change", (e) => {
            selects.map(s => { s.value = e.target.value });
            this.enable_buttons();
        })

        selects.map(s => s.addEventListener('change', () => this.enable_buttons()));
        [...el.querySelectorAll("input")].map(i => i.addEventListener("change", () => this.enable_buttons()));
    }

    build_doc() {
        const items = [...this.modal.querySelectorAll(".variant-select")].map(el => ({
            serial_no: el.dataset.sn,
            last_shipped: el.dataset.last_shipped,
            type: el.value,
        }));
        const shipping_address = this.modal.querySelector("input[name='shipping_address']:checked")?.value;
        const billing_address = this.modal.querySelector("input[name='billing_address']:checked")?.value;
        const remarks = this.modal.querySelector("textarea[name='remarks']")?.value;

        const shipping_address_display = this.addresses.find(addr => addr.name == shipping_address)?.display;
        const billing_address_display = this.addresses.find(addr => addr.name == billing_address)?.display;

        const doc = {
            items,
            shipping_address,
            shipping_address_display,
            billing_address,
            billing_address_display,
            remarks,
        };
        return doc;
    }

    confirm() {
        this.callback(this.build_doc());
        this.hide();
    }
})