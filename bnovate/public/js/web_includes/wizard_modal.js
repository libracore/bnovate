const modal_style = `
/* Style needs to be defined outside of shadow DOM. */
:root {
    --number-of-steps: 4;
    --line-width: 2px;
    --bullet-size: 2em;
    
    --line-color: #ffa632;
    --label-color: #575757;
    --completed-background-color: #ffecd4;
    --uncompleted-background-color: #ffffffff;
    
}

.wizard-ribbon {
    display: flex;
    /* justify-content: space-between; */
    align-items: center;
    margin-bottom: 1rem;
}

ol.wizard-ribbon {
    position: relative;
    overflow: hidden;
    counter-reset: wizard 0;
    list-style-type: none;
}

.wizard-ribbon li {
    position: relative;
    float: left;
    width: calc(100% / var(--number-of-steps));
    text-align: center;
    /* color: var(--active-background-color); */
}

.wizard-ribbon .current {
    font-weight: bold;
}
.wizard-ribbon .current ~ li {
    color: var(--label-color);
}

.wizard-ribbon li:before {
    counter-increment: wizard;
    content: ""; /* counter(wizard); */
    display: block;
    color: var(--line-color);
    background-color: var(--completed-background-color);
    border: var(--line-width) solid var(--line-color);
    text-align: center;
    width: var(--bullet-size);
    height: var(--bullet-size);
    line-height: var(--bullet-size);
    border-radius: var(--bullet-size);
    position: relative;
    left: 50%;
    margin-bottom: calc(var(--bullet-size) / 2);
    margin-left: calc(var(--bullet-size) * -0.5);
    z-index: 1;
}

.wizard-ribbon .current ~ li:before {
    background-color: var(--uncompleted-background-color);
    color: var(--line-color);
    border-color: var(--line-color);
}

.wizard-ribbon li + li:after {
    content: "";
    display: block;
    width: 100%;
    background-color: var(--line-color);
    height: var(--line-width);
    position: absolute;
    left: -50%;
    top: calc(var(--bullet-size) / 2);
    z-index: 0;
}

.wizard-ribbon .current ~ li:after {
    background-color: var(--line-color);
}

.modal-header {
    background-color: var(--completed-background-color);
}

.wizard-page textarea {
    width: 100%;
}

.wizard-page label:hover,
.wizard-page label:focus-within {
  background-color: #e9ecef;
}

.wizard-page .card-group > .card {
    flex: 0 0 33%;
}

.wizard-page .card-body {
  position: relative;
  padding: 0px;
}

.wizard-page .card-body label {
    margin: 0;
    padding: 10px 20px;
    height: 100%;
    width: 100%;
}

.wizard-page input[type="radio"] {
  position: absolute;
  appearance: none;
}

.wizard-page input[type="radio"]:checked ~ label {
  background-color: var(--completed-background-color);
}

.wizard-summary .row {
    padding: 20px;
}

.wizard-summary h5 {
    margin-bottom: 15px;
}

.wizard-summary .card-body {
    padding: 10px 20px;
}

</style >
`

const modal_template = `
<div class="modal" tabindex="-1" role="dialog" id="myModal" style="display:none">
    <div class="modal-dialog modal-lg" role="document">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Request Refill</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="modal-body">
                
                <ol class="wizard-ribbon">
                    <li class="wizard-step current" data-step="1">Cartridges</li>
                    <li class="wizard-step" data-step="2">Shipping</li>
                    <li class="wizard-step" data-step="3">Billing</li>
                    <li class="wizard-step" data-step="4">Summary</li>
                </ol>
                
                <div class="wizard-page" id="page1"> 
                    <i class="fa fa-cog fa-spin" style="font-size: 20px"></i>
                </div>
                <div class="wizard-page" id="page2" style="display: none;"></div>
                <div class="wizard-page" id="page3" style="display: none;"></div>
                <div class="wizard-page wizard-summary" id="page4" style="display: none;"></div>

                <div class="modal-footer">
                    <div class="wizard-buttons">
                        <!-- <button type="button" class="btn btn-danger" id="cancelButton">Cancel</button> -->
                        <button type="button" class="btn btn-secondary" id="prev-button">Previous</button>
                        <button type="button" class="btn btn-primary" id="next-button" disabled>Next</button>
                        <button type="button" class="btn btn-primary" id="done-button">Done</button>
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
        <th>Serial No</th>
        <th>Variant</th>
    </thead>
    <tbody>
        <tr>
            <td>{{ [__("All")] }}</td>
            <td>
                <select id="variant-default">
                    <option value=""></option>
                    <option>TCC</option>
                    <option>ICC</option>
                </select>
            </td>
        </tr>
        {% for sn in serial_nos %}
        <tr>
            <td>{{ sn.serial_no }}</td>
            <td>
                <select class="variant-select" name="variant-{{sn.serial_no}}" data-sn="{{sn.serial_no}}">
                    <option value=""></option>
                    <option>TCC</option>
                    <option>ICC</option>
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
            <input type="radio" name="shipping_address" id="ship-{{addr.name}}" value="{{addr.name}}"></option>
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
            <input type="radio" name="billing_address" id="bill-{{addr.name}}" value="{{addr.name}}"></option>
            <label for="bill-{{addr.name}}">{{addr.display}}</label>
        </div>
    </div>
    {% endfor %}
</div>
`

const template_page4 = `
<div class="row">
    <div class="col-sm">
        <h5>Shipping Address</h5>
        {{doc.shipping_address_display}}
    </div>
    <div class="col-sm">
        <h5>Billing Address</h5>
        {{doc.billing_address_display}}
    </div>
</div>

<div class="row">
    <div class="col-sm">
        <h5>Cartridges</h5>
        <table class="table">
            <thead>
                <th>Serial No</th>
                <th>Variant</th>
            </thead>
            <tbody>
                {% for it in doc.items %}
                <tr>
                    <td>{{ it.serial_no }}</td>
                    <td>{{ it.type }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>


<div class="row">
    <div class="col-sm">
        <h5>Remarks</h5>
        <label for="remarks" style="display: none">Remarks</label>
        <textarea type="text" name="remarks"></textarea>
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

        // Attach template.
        // const template = document.getElementById("wizard-modal-template").content;
        // this.shadowRoot.appendChild(template.cloneNode(true));
        this.attachShadow({ mode: "open" });
        this.shadowRoot.innerHTML = modal_template;

        const style = document.createElement("style");
        style.textContent = modal_style;
        document.head.appendChild(style);

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