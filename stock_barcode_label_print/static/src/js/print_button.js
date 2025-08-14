/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import LineComponent from "@stock_barcode/components/line";

/*
  Parcheamos LineComponent para manejar el click del botón de impresión que
  añadimos en el XML (onPrintLabel) y armar el payload para el endpoint.
*/
// New patch API: second argument is the object with methods to add/override.
patch(LineComponent.prototype, {
    onSetLabelQty(ev) {
        ev.stopPropagation();
        const line = this.line;
        if (!line) return;
        const current = line._label_print_qty || "";
        const raw = window.prompt(_t("Cantidad de etiquetas a imprimir"), String(current));
        if (raw === null) return; // cancelado
        const n = parseInt(String(raw).trim(), 10);
        if (isNaN(n) || n <= 0) {
            this.env.model.notification(_t("Ingrese un número válido mayor a 0."), { type: "warning" });
            return;
        }
        line._label_print_qty = n;
        if (this.render) {
            try { this.render(true); } catch (_) {}
        }
    },
    async onPrintLabel(ev) {
        ev.stopPropagation();
        const line = this.line;
        if (!line) {
            this.env.model.notification(_t("Seleccione una línea antes de imprimir."), { type: "warning" });
            return;
        }

        const product = line.product_id || {};
        const qty = this.env.model.getQtyDone(line) || this.env.model.getLineRemainingQuantity(line) || 1;

        // tracking: 'none' | 'lot' | 'serial'
        const tracking = (product.tracking || "none").toLowerCase();
        const lot_name = (line.lot_id && line.lot_id.name) || line.lot_name || null;
        // Prefer the move line's own expiration_date when available (stock.move.line),
        // then fall back to lot/serial dates. Normalize Luxon DateTime via toISO() if present.
        const normalizeDate = (d) => (d && typeof d === "object" && typeof d.toISO === "function") ? d.toISO() : d;
        const expiration_date = normalizeDate(
            line.expiration_date
            || (line.lot_id && (line.lot_id.expiration_date || line.lot_id.use_date))
            || null
        );

        const baseQty = tracking === "serial" ? 1 : (qty || 1);
        const userQty = Number.isFinite(+line._label_print_qty) && +line._label_print_qty > 0
            ? Math.floor(+line._label_print_qty)
            : null;
        const quantity = userQty || baseQty;

        const payload = {
            product_data: {
                name: product.display_name || product.name || "",
                barcode: product.barcode || "",
                internal_reference: product.default_code || "",
                price: product.lst_price || product.list_price || 0,
                lot_serial_number: tracking !== "none" ? lot_name : null,
                expiration_date: expiration_date,
            },
            // Leave printer config responsibility to the backend (reads from 'impresoras').
            printer_config: {},
            quantity: quantity,
        };

        try {
            const res = await rpc("/barcode_label_print/print", payload);
            if (res && res.ok) {
                this.env.model.notification(_t("Etiqueta enviada a impresión."), { type: "success" });
            } else {
                throw new Error(res && res.message ? res.message : "Error desconocido");
            }
        } catch (e) {
            console.error(e);
            this.env.model.notification(_t("No se pudo imprimir: ") + (e.message || ""), { type: "danger" });
        }
    },
});
