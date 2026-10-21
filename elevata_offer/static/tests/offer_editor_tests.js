/** @odoo-module **/

import { registry } from "@web/core/registry";
import { click, editInput, getFixture, mount, nextTick, makeDeferred, patchWithCleanup } from "@web/../tests/helpers/utils";
import { HtmlField } from "@web_editor/js/backend/html_field";
import { setSelection } from "@web_editor/js/editor/odoo-editor/src/utils/utils";
import { insertText } from "@web_editor/js/editor/odoo-editor/test/utils";
import { makeView, setupViewRegistries } from "@web/../tests/views/helpers";
import { OfferPreviewWidget } from "@elevata_offer/js/offer_preview_widget";

QUnit.module("Elevata V6 editor", (hooks) => {
    let target;
    let serverData;
    hooks.beforeEach(() => {
        setupViewRegistries();
        target = getFixture();
        const fields = Object.fromEntries(registry.category("fields").get("offer_design_preview").fieldDependencies.map((field) => [field.name, { ...field, string: field.name }]));
        fields.state = { type: "selection", selection: [["draft", "Draft"], ["won", "Won"]] };
        serverData = { models: { "elevata.offer": { fields, records: [{ id: 1, offer_title: "Original", content: "<p>Introduktion</p>", state: "draft" }] } } };
    });

    QUnit.test("PDF widget mounts independently", async (assert) => {
        await mount(OfferPreviewWidget, target, {
            props: { name: 'offer_title', record: { resModel: 'elevata.offer', resId: 1 } },
            env: { services: { orm: { call: async () => ({}) } } },
        });
        assert.containsOnce(target, '.o_offer_pdf_preview button');
    });

    QUnit.test("text fields save before PDF; download uses the same blob", async (assert) => {
        const calls = [];
        const view = await makeView({
            type: "form", resModel: "elevata.offer", resId: 1, serverData,
            arch: '<form><field name="state" invisible="1"/><field name="offer_title" widget="offer_design_preview"/></form>',
            mockRPC(route, args) {
                if (args.method === "web_save") calls.push("save");
                if (args.method === "get_report_pdf_preview") {
                    calls.push("pdf");
                    assert.strictEqual(view.model.root.data.offer_title, "Ny rubrik");
                    return { data: btoa("%PDF-1.4\n%%EOF"), filename: "Test.pdf" };
                }
            },
        });
        assert.containsOnce(target, '.o_offer_editor .o_field_char input');
        await editInput(target, '.o_offer_editor .o_field_char input', 'Ny rubrik');
        await click(target, '.o_offer_pdf_preview button');
        await nextTick();
        assert.deepEqual(calls, ["save", "pdf"]);
        const frame = target.querySelector('.o_offer_pdf_preview iframe');
        assert.ok(frame.dataset.src.startsWith('blob:'));
        assert.strictEqual(target.querySelector('a[download]').href, frame.dataset.src);
    });

    QUnit.test("HTML editor changes the shared field and exposes code view", async (assert) => {
        let htmlField;
        const ready = makeDeferred();
        patchWithCleanup(HtmlField.prototype, {
            async startWysiwyg() {
                await super.startWysiwyg(...arguments);
                htmlField = this;
                ready.resolve();
            },
        });
        const view = await makeView({
            type: "form", resModel: "elevata.offer", resId: 1, serverData,
            arch: '<form><field name="state" invisible="1"/><field name="offer_title" widget="offer_design_preview" options="{\'html_only\': True}"/></form>',
        });
        await ready;
        assert.containsOnce(target, '.odoo-editor-editable');
        const editor = htmlField.wysiwyg.odooEditor;
        editor.testMode = true;
        setSelection(editor.editable.querySelector('p'), 0);
        await insertText(editor, 'Redigerad ');
        await view.model.root.save();
        assert.ok(view.model.root.data.content.includes('Redigerad Introduktion'), 'Rich text saved: ' + view.model.root.data.content);
        await click(document, '.o_codeview_btn');
        assert.containsOnce(target, 'textarea.o_codeview');
        await editInput(target, 'textarea.o_codeview', '<p>Text via kodläge</p>');
        await view.model.root.save();
        assert.ok(view.model.root.data.content.includes('Text via kodläge'), 'HTML source saved: ' + view.model.root.data.content);
        assert.containsNone(target, '.o_offer_pdf_preview');
    });
});
