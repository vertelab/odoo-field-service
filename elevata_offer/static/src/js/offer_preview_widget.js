/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useRef, onWillUnmount } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

const REPORT_NAME = "elevata_offer.report_offer_document";

/* ───────────────────────────────────────────────────────────
   PDF-flik — genererar riktig PDF och visar i iframe
   ─────────────────────────────────────────────────────────── */
export class OfferPreviewWidget extends Component {
    static props = { ...standardFieldProps };
    static template = "elevata_offer.OfferPreviewWidget";

    setup() {
        this.state = useState({ url: false, loading: false, error: false, filename: "Offert.pdf" });
        this.orm = useService("orm");
        this.disposed = false;
        onWillUnmount(() => {
            this.disposed = true;
            if (this.state.url) URL.revokeObjectURL(this.state.url);
        });
    }

    get recordId() {
        const record = this.props.record;
        if (record.resModel === "elevata.offer") return record.resId;
        const value = record.data[this.props.name] || "";
        const match = value.match(new RegExp(`/report/(?:html|pdf)/${REPORT_NAME}/(\\d+)$`));
        return match ? Number(match[1]) : false;
    }

    async loadPreview() {
        if (this.state.loading) return;
        this.state.loading = true;
        this.state.error = false;
        if (this.state.url) URL.revokeObjectURL(this.state.url);
        this.state.url = false;
        try {
            const record = this.props.record;
            if (record.resModel === "elevata.offer" && record.isInEdition) {
                if (!(await record.save())) return;
            }
            if (!this.recordId) return;
            const result = await this.orm.call("elevata.offer", "get_report_pdf_preview", [[this.recordId]]);
            if (this.disposed) return;
            const bytes = Uint8Array.from(atob(result.data), (c) => c.charCodeAt(0));
            this.state.url = URL.createObjectURL(new Blob([bytes], { type: "application/pdf" }));
            this.state.filename = result.filename;
        } catch (error) {
            this.state.error = error.data?.message || error.message || "PDF kunde inte skapas.";
        } finally {
            if (!this.disposed) this.state.loading = false;
        }
    }
}

/* ───────────────────────────────────────────────────────────
   HTML-redigering — renderar offertens HTML i iframe,
   gör [data-field]-element contenteditable.
   ─────────────────────────────────────────────────────────── */

const EDITABLE_FIELDS = [
    "offer_title", "content", "background", "scope_of_work",
    "modernization_proposal", "service_sections",
    "closing_title", "closing_text",
    "warranty_terms", "payment_terms_text", "delivery_time",
    "delivery_terms", "terms_conditions", "not_included",
    "modernization_inspection_note", "modernization_quality_env",
    "modernization_reservations", "ce_compliance_note",
    "tech_general", "tech_doors", "tech_machine_room", "tech_shaft",
    "tech_car", "tech_control_panel", "tech_signalization", "tech_options",
    "delivery_time_info", "downtime_info",
];

// Char fields — save textContent, not innerHTML
const CHAR_FIELDS = ["offer_title", "closing_title", "delivery_time_info", "downtime_info", "ce_compliance_note"];

export class OfferHtmlEditorWidget extends Component {
    static props = { ...standardFieldProps };
    static template = "elevata_offer.OfferHtmlEditorWidget";

    setup() {
        this.state = useState({
            loading: false,
            error: false,
            codeMode: false,
            codeField: "",
            codeValue: "",
            dirty: false,
            savedMsg: "",
            editableCount: 0,
        });
        this.iframeRef = useRef("editFrame");
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.disposed = false;
        onWillUnmount(() => { this.disposed = true; });
    }

    get recordId() {
        const record = this.props.record;
        if (record.resModel === "elevata.offer" && record.resId) return record.resId;
        // Fallback: extract ID from the field value
        const value = record.data[this.props.name] || "";
        if (value) {
            const match = String(value).match(/\/(\d+)$/);
            if (match) return Number(match[1]);
        }
        return false;
    }

    get htmlUrl() {
        if (!this.recordId) return false;
        return `/report/html/${REPORT_NAME}/${this.recordId}`;
    }

    async refreshPreview() {
        if (this.state.loading) return;
        this.state.loading = true;
        this.state.error = false;
        this.state.editableCount = 0;
        try {
            const record = this.props.record;
            if (record.isInEdition) {
                if (!(await record.save())) {
                    this.state.loading = false;
                    return;
                }
            }
            const iframe = this.iframeRef.el;
            if (iframe && this.htmlUrl) {
                iframe.src = this.htmlUrl + "?t=" + Date.now();
            }
        } catch (error) {
            this.state.error = error.message || "Kunde inte ladda förhandsgranskning.";
            this.state.loading = false;
        }
    }

    onIframeLoad() {
        // Small delay to ensure DOM is fully available
        setTimeout(() => {
            this._makeEditable();
            if (!this.disposed) this.state.loading = false;
        }, 300);
    }

    _makeEditable() {
        const iframe = this.iframeRef.el;
        if (!iframe) {
            console.warn("[OfferEditor] No iframe element");
            return;
        }
        let doc;
        try {
            doc = iframe.contentDocument || iframe.contentWindow?.document;
        } catch (e) {
            console.warn("[OfferEditor] Cannot access iframe contentDocument (cross-origin?):", e.message);
            this.state.error = "Kan inte komma åt iframe-innehållet. Kontrollera att du är inloggad.";
            return;
        }
        if (!doc || !doc.body) {
            console.warn("[OfferEditor] iframe document or body is null");
            return;
        }
        const editables = doc.querySelectorAll("[data-field]");
        console.log("[OfferEditor] Found", editables.length, "editable elements");
        this.state.editableCount = editables.length;

        if (!editables.length) {
            this.state.error = "Inga redigerbara fält hittades i renderingen. Kontrollera att offerten har V6-layout.";
            return;
        }

        editables.forEach((el) => {
            el.contentEditable = "true";
            el.style.cursor = "text";
            el.style.minHeight = "1em";
            el.style.transition = "outline 0.15s";
            // Hover
            el.addEventListener("mouseenter", () => {
                if (doc.activeElement !== el) {
                    el.style.outline = "2px dashed rgba(47,69,96,0.4)";
                    el.style.outlineOffset = "2px";
                }
            });
            el.addEventListener("mouseleave", () => {
                if (doc.activeElement !== el) {
                    el.style.outline = "none";
                    el.style.outlineOffset = "";
                }
            });
            el.addEventListener("focus", () => {
                el.style.outline = "2px solid #2F4560";
                el.style.outlineOffset = "2px";
                this.state.dirty = true;
            });
            el.addEventListener("blur", () => {
                el.style.outline = "none";
                el.style.outlineOffset = "";
            });
            el.addEventListener("input", () => {
                this.state.dirty = true;
            });
        });

        // Add visual cue styles
        try {
            const style = doc.createElement("style");
            style.textContent = `
                [data-field] {
                    position: relative;
                    border-radius: 3px;
                }
                [data-field]::before {
                    content: attr(data-field);
                    position: absolute;
                    top: -16px;
                    left: 0;
                    font-size: 9px;
                    background: #2F4560;
                    color: #fff;
                    padding: 0 4px;
                    border-radius: 2px;
                    opacity: 0;
                    pointer-events: none;
                    transition: opacity 0.15s;
                    z-index: 999;
                    font-family: monospace;
                }
                [data-field]:hover::before,
                [data-field]:focus::before {
                    opacity: 1;
                }
            `;
            doc.head.appendChild(style);
        } catch (e) { /* ignore */ }
    }

    _collectChanges() {
        const iframe = this.iframeRef.el;
        if (!iframe) return {};
        const changes = {};
        let doc;
        try {
            doc = iframe.contentDocument || iframe.contentWindow?.document;
        } catch (e) {
            console.warn("[OfferEditor] Cannot access iframe for collecting changes:", e.message);
            return {};
        }
        if (!doc) return {};
        const editables = doc.querySelectorAll("[data-field]");
        editables.forEach((el) => {
            const field = el.dataset.field;
            if (field && EDITABLE_FIELDS.includes(field)) {
                if (CHAR_FIELDS.includes(field)) {
                    changes[field] = el.textContent.trim();
                } else {
                    changes[field] = el.innerHTML;
                }
            }
        });
        return changes;
    }

    async saveChanges() {
        if (!this.recordId) {
            this.notification.add("Offerten har inget ID — spara den först.", { type: "warning" });
            return;
        }
        const changes = this._collectChanges();
        // Apply code mode changes
        if (this.state.codeMode && this.state.codeField) {
            changes[this.state.codeField] = this.state.codeValue;
        }
        const keys = Object.keys(changes);
        if (!keys.length) {
            this.notification.add("Inga ändringar hittades. Klicka i texten först.", { type: "info" });
            return;
        }
        try {
            await this.orm.write("elevata.offer", [this.recordId], changes);
            this.state.dirty = false;
            this.state.savedMsg = `${keys.length} fält sparade.`;
            this.notification.add(`Sparade: ${keys.join(", ")}`, { type: "success" });
            setTimeout(() => { if (!this.disposed) this.state.savedMsg = ""; }, 4000);
            // Reload record in form
            await this.props.record.load();
            // Refresh preview
            await this.refreshPreview();
        } catch (error) {
            const msg = error.data?.message || error.message || "Kunde inte spara.";
            this.notification.add(msg, { type: "danger" });
            console.error("[OfferEditor] Save failed:", error);
        }
    }

    toggleCodeMode() {
        if (this.state.codeMode) {
            // Leaving code mode: apply to iframe
            if (this.state.codeField) {
                try {
                    const iframe = this.iframeRef.el;
                    const doc = iframe?.contentDocument || iframe?.contentWindow?.document;
                    const el = doc?.querySelector(`[data-field="${this.state.codeField}"]`);
                    if (el) {
                        el.innerHTML = this.state.codeValue;
                        this.state.dirty = true;
                    }
                } catch (e) { /* ignore */ }
            }
            this.state.codeMode = false;
            this.state.codeField = "";
            this.state.codeValue = "";
        } else {
            // Entering code mode
            let field = "", html = "";
            try {
                const iframe = this.iframeRef.el;
                const doc = iframe?.contentDocument || iframe?.contentWindow?.document;
                if (doc) {
                    const active = doc.activeElement;
                    if (active?.dataset?.field) {
                        field = active.dataset.field;
                        html = active.innerHTML;
                    } else {
                        const first = doc.querySelector("[data-field]");
                        if (first) { field = first.dataset.field; html = first.innerHTML; }
                    }
                }
            } catch (e) { /* ignore */ }
            this.state.codeField = field;
            this.state.codeValue = html;
            this.state.codeMode = true;
        }
    }

    onCodeFieldChange(ev) {
        const field = ev.target.value;
        this.state.codeField = field;
        try {
            const iframe = this.iframeRef.el;
            const doc = iframe?.contentDocument || iframe?.contentWindow?.document;
            const el = doc?.querySelector(`[data-field="${field}"]`);
            this.state.codeValue = el ? el.innerHTML : "";
        } catch (e) { this.state.codeValue = ""; }
    }

    onCodeInput(ev) {
        this.state.codeValue = ev.target.value;
        this.state.dirty = true;
    }

    get editableFields() {
        const fields = [];
        try {
            const iframe = this.iframeRef.el;
            const doc = iframe?.contentDocument || iframe?.contentWindow?.document;
            if (doc) {
                doc.querySelectorAll("[data-field]").forEach((el) => {
                    if (!fields.includes(el.dataset.field)) fields.push(el.dataset.field);
                });
            }
        } catch (e) { /* ignore */ }
        return fields.length ? fields : EDITABLE_FIELDS;
    }
}

/* ───────────────────────────────────────────────────────────
   Textavsnitt-editor för mallar (utan live preview)
   ─────────────────────────────────────────────────────────── */
import { Field } from "@web/views/fields/field";

const TEXT_FIELDS = [
    ["offer_title", "Rubrik", "char"],
    ["content", "Introduktion / offerttext", "html"],
    ["background", "Bakgrund och behov", "html"],
    ["scope_of_work", "Arbetets omfattning", "html"],
    ["modernization_proposal", "Föreslagen lösning", "html"],
    ["service_sections", "Serviceinnehåll", "html"],
    ["tech_general", "Teknik — allmänt", "html"],
    ["tech_doors", "Teknik — dörrar", "html"],
    ["tech_machine_room", "Teknik — maskinrum", "html"],
    ["tech_shaft", "Teknik — schakt", "html"],
    ["tech_car", "Teknik — hisskorg", "html"],
    ["tech_control_panel", "Teknik — styrning", "html"],
    ["tech_signalization", "Teknik — tablåer", "html"],
    ["tech_options", "Teknik — optioner", "html"],
    ["delivery_time_info", "Leveranstid i korthet", "char"],
    ["modernization_construction_time", "Ombyggnadstid", "char"],
    ["downtime_info", "Driftstopp", "text"],
    ["warranty_terms", "Garantivillkor", "html"],
    ["payment_terms_text", "Betalningsvillkor", "html"],
    ["delivery_time", "Leveranstid", "html"],
    ["delivery_terms", "Leveransvillkor", "html"],
    ["terms_conditions", "Allmänna villkor", "html"],
    ["not_included", "Ingår ej", "html"],
    ["modernization_inspection_note", "Besiktning", "html"],
    ["modernization_quality_env", "Kvalitet och miljö", "html"],
    ["modernization_reservations", "Reservationer", "html"],
    ["ce_compliance_note", "CE / myndighetskrav", "text"],
    ["cover_feature_1", "Omslagspunkt 1 (Rubrik|Beskrivning)", "char"],
    ["cover_feature_2", "Omslagspunkt 2 (Rubrik|Beskrivning)", "char"],
    ["cover_feature_3", "Omslagspunkt 3 (Rubrik|Beskrivning)", "char"],
    ["footer_text", "Sidfot", "text"],
    ["closing_title", "Avslutningsrubrik", "char"],
    ["closing_text", "Avslutningstext", "html"],
];

export class OfferTextEditorWidget extends Component {
    static props = { ...standardFieldProps };
    static template = "elevata_offer.OfferTextEditorWidget";
    static components = { Field };

    setup() {
        this.state = useState({ selected: "content" });
    }

    get sections() { return TEXT_FIELDS; }

    get selected() {
        return TEXT_FIELDS.find(([name]) => name === this.state.selected) || TEXT_FIELDS[0];
    }

    get readonly() { return false; }

    get fieldInfo() {
        const record = this.props.record;
        const node = document.createElement("field");
        node.setAttribute("name", this.state.selected);
        return Field.parseFieldNode(node, { [record.resModel]: record.fields }, record.resModel, "form");
    }

    async selectSection(event) {
        const next = event.target.value;
        const proms = [];
        this.props.record.model.bus.trigger("NEED_LOCAL_CHANGES", { proms });
        await Promise.all(proms);
        this.state.selected = next;
    }
}

/* ── Registreringar ── */

registry.category("fields").add("offer_preview", {
    component: OfferPreviewWidget,
    supportedTypes: ["char"],
});

registry.category("fields").add("offer_html_editor", {
    component: OfferHtmlEditorWidget,
    supportedTypes: ["char"],
});

registry.category("fields").add("offer_text_editor", {
    component: OfferTextEditorWidget,
    supportedTypes: ["char"],
    fieldDependencies: TEXT_FIELDS.map(([name, , type]) => ({ name, type, readonly: false })),
});
