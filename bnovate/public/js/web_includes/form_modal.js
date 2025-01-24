customElements.define('form-modal', class extends HTMLElement {
    constructor() {
        super();

        window.theModal = this;
    }

    draw(contents) {
        // Attach template. Only draw when modal is summoned, makes it more likely that translations are loaded.
        this.attachShadow({ mode: "open" });
        // this.shadowRoot.innerHTML = frappe.render_template(modal_template, {});
        this.shadowRoot.appendChild(contents)

        this.modal = this.shadowRoot.getElementById("myModal");
        this.cancel = this.shadowRoot.getElementById("cancel-button");
        this.save = this.shadowRoot.getElementById("save-button");


        $(this.modal).on('show.bs.modal', (e) => {
            // this.bind_listeners(e.target);
        })

        $(this.modal).on('hide.bs.modal', (e) => {
            // e.target.querySelector('.modal-body #page1').innerHTML = '';
        })

        $(this.cancel).click(() => {
            // Close the modal or redirect to another page
            $(this.modal).modal("hide");
        });

        $(this.save).click(() => {
            this.confirm();
        });
    }

    async show(contents, validate, confirm_callback, data = {}) {
        if (!this.shadowRoot) {
            this.draw(contents);
        }

        // Populate modal. Keys in data are named the same as the input element IDs.
        Object.keys(data).forEach(key => {
            const input = this.modal.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = data[key];
            }
        });

        this.confirm_callback = confirm_callback;
        this.validate = validate;
        $(this.modal).modal({ backdrop: 'static', keyboard: false });
        this.bind_listeners();
    }

    hide() {
        $(this.modal).modal('hide');
    }


    // Enable or disable buttons based on form completion
    enable_buttons(valid) {
        if (valid) {
            this.save.disabled = false;
        } else {
            this.save.disabled = true;
        }
    }

    // Set all blank variant selects when the first one is modified
    bind_listeners() {
        console.log("bind listeners");
        [
            ...document.querySelectorAll("input"),
            ...document.querySelectorAll("select"),
        ].map(el => el.addEventListener("change", () => {
            this.enable_buttons(this.validate());
        }))
    }

    async confirm() {
        await this.confirm_callback();
        this.hide();
    }
})