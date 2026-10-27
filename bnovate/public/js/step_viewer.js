/* step_viewer.js. (c) 2026, bNovate.
 *
 * View STEP (CAD) files in a modal, coloured by subassembly.
 *
 * Libraries, loaded from a CDN the first time the viewer is opened:
 *  - three.js renders the model,
 *  - occt-import-js (OpenCascade compiled to WebAssembly) reads the STEP file and meshes it.
 *
 * Usage: bnovate.step.show({ title, files }), where files are File rows: [{ file_name, file_url }, ...]
 *
 ****************************************************/

frappe.provide('bnovate.step');

bnovate.step.THREE_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/+esm';
bnovate.step.ORBIT_CONTROLS_URL = 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js/+esm';
bnovate.step.OCCT_BASE_URL = 'https://cdn.jsdelivr.net/npm/occt-import-js@0.0.23/dist/';

// Above this number of triangles, edges are off by default (they are slow to compute and to draw)
bnovate.step.MAX_TRIANGLES_FOR_EDGES = 400000;

bnovate.step.is_step_file = (file) => /\.(step|stp)$/i.test(file.file_name || '');

// Item code at the start of the name of a component, e.g. "100655" in "100655_MASM_Housing". Without revision.
bnovate.step.item_code_of = (name) => ((name || '').match(/^(\d{5,7})_/) || [])[1];

// Versions of items (100655.01, 100655.02...) for item codes without revision. Return { code: [{ name, item_name, disabled }] }
bnovate.step.get_item_versions = async function (codes) {
    if (!codes.length) return {};
    const r = await frappe.call({
        method: 'bnovate.bnovate.utils.items.get_item_versions',
        args: { codes },
    });
    return r.message || {};
}

bnovate.step.load_script = function (src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = () => reject(new Error(`Could not load ${src}`));
        document.head.appendChild(script);
    });
}

// Load the libraries once, return { THREE, OrbitControls, occt }
bnovate.step.load_libraries = function () {
    if (!bnovate.step._libraries) {
        bnovate.step._libraries = (async () => {
            const [THREE, controls] = await Promise.all([
                import(bnovate.step.THREE_URL),
                import(bnovate.step.ORBIT_CONTROLS_URL),
            ]);
            await bnovate.step.load_script(bnovate.step.OCCT_BASE_URL + 'occt-import-js.js');
            const occt = await window.occtimportjs({ locateFile: (name) => bnovate.step.OCCT_BASE_URL + name });
            return { THREE, OrbitControls: controls.OrbitControls, occt };
        })();
        // Try again next time if it failed (e.g. no internet access)
        bnovate.step._libraries.catch(() => { bnovate.step._libraries = null; });
    }
    return bnovate.step._libraries;
}

// Group the meshes of a STEP file by subassembly, from the tree of the assembly in the file.
// The subassemblies are the children of the first node of the tree that has several children.
// Instances of the same subassembly (same name, e.g. the screws) are merged.
// Return [{ name, mesh_indices, instances }, ...]
bnovate.step.group_meshes = function (result) {
    const collect = (node) => [...(node.meshes || []), ...(node.children || []).flatMap(collect)];

    let node = result.root;
    while ((node.children || []).length === 1 && !(node.meshes || []).length) {
        node = node.children[0];
    }

    const groups = (node.children || []).map(child => ({ name: child.name, mesh_indices: collect(child) }));
    if ((node.meshes || []).length) {
        groups.push({ name: groups.length ? __('Other parts') : node.name, mesh_indices: [...node.meshes] });
    }
    const merged = [];
    groups.filter(group => group.mesh_indices.length).forEach((group, i) => {
        // CAD systems append the name of the configuration, which is not interesting here
        const name = ((group.name || '').trim() || result.meshes[group.mesh_indices[0]].name || `${__('Subassembly')} ${i + 1}`)
            .replace(/_(D\u00e9faut|Default|Par d\u00e9faut)$/i, '');
        const same = merged.find(other => other.name.toLowerCase() === name.toLowerCase());
        if (same) {
            same.mesh_indices.push(...group.mesh_indices);
            same.instances += 1;
        } else {
            merged.push({ name, mesh_indices: [...group.mesh_indices], instances: 1 });
        }
    });
    return merged;
}

bnovate.step.Viewer = class {
    constructor(container, libraries) {
        const { THREE, OrbitControls } = libraries;
        this.libraries = libraries;
        this.container = container;

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf3f4f6);

        this.camera = new THREE.PerspectiveCamera(40, 1, 0.1, 1000);
        // Lights follow the camera, so the part is always lit from the viewer's side
        this.scene.add(this.camera);
        this.camera.add(new THREE.HemisphereLight(0xffffff, 0x8a8f99, 1.0));
        const light = new THREE.DirectionalLight(0xffffff, 1.6);
        light.position.set(1, 1.5, 2);
        this.camera.add(light);

        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(this.renderer.domElement);
        this.renderer.domElement.style.display = 'block';

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;

        this.model = null;
        this.parts = [];            // [{ solid, edges, group, original_color }]
        this.groups = [];           // [{ name, color (hex string), part_count, visible }]
        this.edges_visible = true;
        this.colour_by_group = true;
        this.opacity = 1;

        this.resize_observer = new ResizeObserver(() => this.resize());
        this.resize_observer.observe(container);
        this.resize();

        this.disposed = false;
        const animate = () => {
            if (this.disposed) return;
            requestAnimationFrame(animate);
            this.controls.update();
            this.renderer.render(this.scene, this.camera);
        };
        animate();
    }

    resize() {
        const { clientWidth: width, clientHeight: height } = this.container;
        if (!width || !height) return;
        this.renderer.setSize(width, height);
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
    }

    clear() {
        if (!this.model) return;
        this.scene.remove(this.model);
        this.model.traverse(obj => {
            obj.geometry?.dispose();
            obj.material?.dispose();
        });
        this.model = null;
        this.parts = [];
        this.groups = [];
    }

    // Load a STEP file from a url.
    // Returns { size: [x, y, z], groups, triangles }, groups being the subassemblies, see group_meshes()
    async load(url) {
        const { THREE, occt } = this.libraries;

        const response = await fetch(url, { credentials: 'same-origin' });
        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`);
        }
        const content = new Uint8Array(await response.arrayBuffer());
        const result = occt.ReadStepFile(content, null);
        if (!result.success || !result.meshes.length) {
            throw new Error(__('This STEP file could not be read, or contains no solids.'));
        }

        // Colours: golden angle between hues keeps neighbouring subassemblies apart, whatever their number
        const groups = bnovate.step.group_meshes(result).map((group, i) => ({
            name: group.name,
            mesh_indices: group.mesh_indices,
            color: '#' + new THREE.Color().setHSL((i * 0.618034) % 1, 0.6, 0.55).getHexString(),
            part_count: group.mesh_indices.length,
            instances: group.instances,
            visible: true,
        }));
        const group_of_mesh = [];
        groups.forEach((group, i) => group.mesh_indices.forEach(m => { group_of_mesh[m] = i; }));

        const model = new THREE.Group();
        const parts = [];
        let triangles = 0;
        result.meshes.forEach((mesh, m) => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.Float32BufferAttribute(mesh.attributes.position.array, 3));
            if (mesh.attributes.normal) {
                geometry.setAttribute('normal', new THREE.Float32BufferAttribute(mesh.attributes.normal.array, 3));
            }
            geometry.setIndex(new THREE.BufferAttribute(Uint32Array.from(mesh.index.array), 1));
            if (!mesh.attributes.normal) {
                geometry.computeVertexNormals();
            }
            triangles += mesh.index.array.length / 3;

            const original_color = mesh.color ? new THREE.Color(mesh.color[0], mesh.color[1], mesh.color[2]) : new THREE.Color(0xb7c3d0);
            const solid = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({
                color: original_color, metalness: 0.15, roughness: 0.65, side: THREE.DoubleSide,
                polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,  // keep edges from fighting with faces
            }));
            model.add(solid);
            parts.push({ solid, edges: null, group: group_of_mesh[m] ?? 0, original_color });
        });
        // CAD is Z up, three.js is Y up
        model.rotation.x = -Math.PI / 2;

        this.clear();
        this.model = model;
        this.parts = parts;
        this.groups = groups;
        this.scene.add(model);

        this.edges_visible = triangles <= bnovate.step.MAX_TRIANGLES_FOR_EDGES;
        this.update_appearance();
        this.fit();

        const size = new THREE.Box3().setFromObject(model).getSize(new THREE.Vector3());
        // Size along the CAD axes (z and y swapped by the rotation)
        return { size: [size.x, size.z, size.y], groups, triangles };
    }

    // Apply colours, opacity and visibility to the parts
    update_appearance() {
        const { THREE } = this.libraries;
        for (const part of this.parts) {
            const group = this.groups[part.group];
            const material = part.solid.material;
            material.color.set(this.colour_by_group ? group.color : part.original_color);
            material.opacity = this.opacity;
            material.transparent = this.opacity < 1;
            material.depthWrite = this.opacity >= 1;  // see-through parts must not hide what is behind them
            material.needsUpdate = true;

            part.solid.visible = group.visible;
            if (this.edges_visible && group.visible && !part.edges) {
                // Edges are computed when first needed, it is slow for big models
                part.edges = new THREE.LineSegments(
                    new THREE.EdgesGeometry(part.solid.geometry, 30),
                    new THREE.LineBasicMaterial({ color: 0x2b2f36, transparent: true }));
                part.solid.add(part.edges);
            }
            if (part.edges) {
                part.edges.visible = this.edges_visible && group.visible;
                part.edges.material.opacity = Math.max(this.opacity, 0.35);
            }
        }
    }

    set_edges_visible(visible) {
        this.edges_visible = visible;
        this.update_appearance();
    }

    set_colour_by_group(value) {
        this.colour_by_group = value;
        this.update_appearance();
    }

    set_opacity(value) {
        this.opacity = value;
        this.update_appearance();
    }

    set_group_visible(index, visible) {
        this.groups[index].visible = visible;
        this.update_appearance();
    }

    // Frame the whole model, seen from the front right above
    fit() {
        if (!this.model) return;
        const { THREE } = this.libraries;
        this.model.updateMatrixWorld(true);
        const box = new THREE.Box3().setFromObject(this.model);
        const center = box.getCenter(new THREE.Vector3());
        const radius = box.getSize(new THREE.Vector3()).length() / 2 || 1;

        const distance = radius / Math.sin(THREE.MathUtils.degToRad(this.camera.fov / 2)) * 1.1;
        this.camera.near = distance / 100;
        this.camera.far = distance * 100;
        this.camera.updateProjectionMatrix();
        this.camera.position.copy(center).add(new THREE.Vector3(1, 0.7, 1).normalize().multiplyScalar(distance));
        this.controls.target.copy(center);
        this.controls.update();
    }

    dispose() {
        this.disposed = true;
        this.resize_observer.disconnect();
        this.clear();
        this.controls.dispose();
        this.renderer.dispose();
        this.renderer.domElement.remove();
    }
}

// Show STEP files in a large modal. files: [{ file_name, file_url }, ...]
bnovate.step.show = function ({ title, files }) {
    const dialog = new frappe.ui.Dialog({
        title,
        fields: [
            {
                fieldtype: 'Select', fieldname: 'file', label: __('File'),
                options: files.map(file => file.file_name), default: files[0].file_name,
                hidden: files.length < 2,
                change: () => load(dialog.get_value('file')),
            },
            { fieldtype: 'HTML', fieldname: 'viewer' },
        ],
    });

    dialog.$wrapper.find('.modal-dialog').css({ 'max-width': '96vw', 'width': '96vw' });
    dialog.fields_dict.viewer.$wrapper.html(`
        <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 8px; flex-wrap: wrap;">
            <button class="btn btn-default btn-xs step-reset">${__('Reset view')}</button>
            <label class="checkbox" style="margin: 0;"><input type="checkbox" class="step-edges" checked> ${__('Edges')}</label>
            <label class="checkbox" style="margin: 0;"><input type="checkbox" class="step-colour" checked> ${__('Colour by subassembly')}</label>
            <label style="margin: 0; display: flex; align-items: center; gap: 6px; font-weight: normal;">
                ${__('Opacity')}
                <input type="range" class="step-opacity" min="5" max="100" value="100" style="width: 140px;">
                <span class="step-opacity-value text-muted small" style="min-width: 32px;">100%</span>
            </label>
            <span class="text-muted small step-info" style="margin-left: auto;"></span>
        </div>
        <div style="display: flex; gap: 10px;">
            <div class="step-container" style="position: relative; flex: 1 1 auto; min-width: 0; height: 75vh; border: 1px solid var(--border-color, #d1d8dd); background: #f3f4f6;">
                <div class="step-message text-muted" style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; text-align: center; padding: 20px; pointer-events: none;"></div>
            </div>
            <div class="step-legend" style="flex: 0 0 280px; height: 75vh; overflow-y: auto; border: 1px solid var(--border-color, #d1d8dd); padding: 8px 10px; display: none;"></div>
        </div>
        <p class="text-muted small" style="margin: 6px 0 0 0;">${__('Drag to rotate, scroll to zoom, right-drag to move.')}</p>`);

    const $viewer = dialog.fields_dict.viewer.$wrapper;
    const container = $viewer.find('.step-container')[0];
    const set_message = (text) => $viewer.find('.step-message').text(text || '').toggle(!!text);
    let viewer = null;
    let request = 0;  // to ignore results of loads that were superseded

    const esc = frappe.utils.escape_html;

    // Versions of the items of the subassemblies: { code: [{ name, item_name, disabled }] }. Undefined until looked up.
    let versions;

    function load_versions(groups) {
        versions = undefined;
        const codes = [...new Set(groups.map(group => bnovate.step.item_code_of(group.name)).filter(Boolean))];
        bnovate.step.get_item_versions(codes)
            .then(result => { versions = result; })
            .catch(() => { versions = {}; });
    }

    // The item code of a subassembly is a link, see below
    function name_html(name) {
        const code = bnovate.step.item_code_of(name);
        if (!code) return esc(name);
        return `<a href="#" class="step-item-link" data-code="${code}">${code}</a>${esc(name.slice(code.length))}`;
    }

    function versions_html(code) {
        if (versions === undefined) {
            return `<span class="text-muted">${__('Looking up items...')}</span>`;
        }
        const items = versions[code] || [];
        if (!items.length) {
            return `<span class="text-muted">${__('No item found for {0}', [code])}</span>`;
        }
        const rows = items.map(item => `
            <div style="margin-bottom: 2px;">
                <a href="#Form/Item/${encodeURIComponent(item.name)}" class="step-item-open" data-name="${esc(item.name)}"><b>${esc(item.name)}</b></a>
                <span class="text-muted">${esc(item.item_name && item.item_name !== item.name ? item.item_name : '')}${item.disabled ? ` (${__('disabled')})` : ''}</span>
            </div>`).join('');
        return rows + `<div style="margin-top: 6px;"><a href="#" class="step-item-list" data-code="${code}">${__('Show all versions in the item list')}</a></div>`;
    }

    // Go to an item or to the list of its versions, leaving the viewer
    function open_item(name) {
        dialog.hide();
        frappe.set_route('Form', 'Item', name);
    }

    function open_item_list(code) {
        dialog.hide();
        frappe.route_options = { name: ['like', code + '%'] };
        frappe.set_route('List', 'Item');
    }

    function show_legend(groups) {
        const rows = groups.map((group, i) => `
            <label class="checkbox" style="display: flex; align-items: flex-start; gap: 6px; margin: 0 0 6px 0; font-weight: normal;">
                <input type="checkbox" class="step-group" data-index="${i}" checked style="margin-top: 3px;">
                <span class="step-swatch" style="flex: 0 0 12px; height: 12px; margin-top: 3px; border-radius: 2px; background: ${group.color};"></span>
                <span style="min-width: 0; overflow-wrap: anywhere;">${name_html(group.name)}
                    <span class="text-muted small">(${group.instances > 1 ? __('{0} instances', [group.instances]) + ', ' : ''}${__('{0} parts', [group.part_count])})</span></span>
            </label>`).join('');
        $viewer.find('.step-legend').html(`
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <b>${__('Subassemblies')} (${groups.length})</b>
                <a href="#" class="step-show-all small">${__('Show all')}</a>
            </div>${rows}`).show();
        viewer.resize();
    }

    function update_swatches() {
        // Swatches show the colour of the group, or grey when colouring by subassembly is off
        $viewer.find('.step-swatch').each(function (i) {
            $(this).css('opacity', viewer.colour_by_group ? 1 : 0.25);
        });
    }

    async function load(file_name) {
        const file = files.find(f => f.file_name === file_name);
        const this_request = ++request;
        $viewer.find('.step-info').text('');
        $viewer.find('.step-legend').hide();
        set_message(__('Loading...'));
        try {
            const libraries = await bnovate.step.load_libraries().catch(() => {
                throw new Error(__('The 3D viewer could not be loaded. It needs internet access.'));
            });
            if (dialog.is_closed) return;
            viewer = viewer || new bnovate.step.Viewer(container, libraries);
            viewer.colour_by_group = $viewer.find('.step-colour').is(':checked');
            viewer.opacity = $viewer.find('.step-opacity').val() / 100;
            const { size, groups, triangles } = await viewer.load(encodeURI(file.file_url).replace(/#/g, '%23'));
            if (this_request !== request) return;
            set_message('');
            $viewer.find('.step-edges').prop('checked', viewer.edges_visible);
            $viewer.find('.step-info').text(`${size.map(n => n.toFixed(1)).join(' × ')} ${__('(units of the file)')}`
                + ` • ${__('{0} triangles', [triangles.toLocaleString()])}`);
            show_legend(groups);
            update_swatches();
            load_versions(groups);
        } catch (e) {
            if (this_request !== request) return;
            console.error(e);
            set_message(`${__('Could not show this file.')} ${e.message}`);
        }
    }

    $viewer.find('.step-reset').on('click', () => viewer?.fit());
    $viewer.find('.step-edges').on('change', (e) => viewer?.set_edges_visible(e.target.checked));
    $viewer.find('.step-colour').on('change', (e) => {
        viewer?.set_colour_by_group(e.target.checked);
        update_swatches();
    });
    $viewer.find('.step-opacity').on('input', (e) => {
        $viewer.find('.step-opacity-value').text(`${e.target.value}%`);
        viewer?.set_opacity(e.target.value / 100);
    });
    $viewer.on('change', '.step-group', (e) => viewer?.set_group_visible(Number(e.target.dataset.index), e.target.checked));
    $viewer.on('click', '.step-show-all', (e) => {
        e.preventDefault();
        viewer?.groups.forEach((group, i) => viewer.set_group_visible(i, true));
        $viewer.find('.step-group').prop('checked', true);
    });
    // Hover card with the versions of an item
    const $card = $('<div class="step-versions"></div>').css({
        position: 'fixed', zIndex: 2000, display: 'none', maxWidth: '380px', fontSize: '12px', padding: '8px 10px',
        background: 'var(--card-bg, #fff)', border: '1px solid var(--border-color, #d1d8dd)', borderRadius: '6px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.18)',
    }).appendTo(dialog.$wrapper);
    let hide_timer = null;
    const hide_card_soon = () => { hide_timer = setTimeout(() => $card.hide(), 250); };
    const show_card = (anchor) => {
        clearTimeout(hide_timer);
        $card.html(versions_html(anchor.dataset.code)).show();
        const rect = anchor.getBoundingClientRect();
        $card.css({
            left: Math.max(8, Math.min(rect.left, window.innerWidth - $card.outerWidth() - 8)),
            top: Math.min(rect.bottom + 4, window.innerHeight - $card.outerHeight() - 8),
        });
    };
    $viewer.on('mouseenter', '.step-item-link', (e) => show_card(e.currentTarget));
    $viewer.on('mouseleave', '.step-item-link', hide_card_soon);
    $card.on('mouseenter', () => clearTimeout(hide_timer)).on('mouseleave', hide_card_soon);

    // Clicking the code opens the item if there is only one version, otherwise the list of its versions
    $viewer.on('click', '.step-item-link', (e) => {
        e.preventDefault();
        const code = e.currentTarget.dataset.code;
        const items = (versions || {})[code] || [];
        if (items.length === 1) {
            open_item(items[0].name);
        } else {
            open_item_list(code);
        }
    });
    $card.on('click', '.step-item-open', (e) => {
        e.preventDefault();
        open_item(e.currentTarget.dataset.name);
    });
    $card.on('click', '.step-item-list', (e) => {
        e.preventDefault();
        open_item_list(e.currentTarget.dataset.code);
    });

    dialog.onhide = () => {
        $card.remove();
        dialog.is_closed = true;
        viewer?.dispose();
        viewer = null;
    };

    dialog.show();
    load(files[0].file_name);
    return dialog;
}
