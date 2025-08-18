/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import LineaComponente from "@stock_barcode/components/line";

/*
  Parcheamos LineaComponente para:
  - Siempre usar la cantidad definida manualmente por el usuario.
  - Pedir la cantidad en el momento si no está definida.
*/

/**
 * Función auxiliar para pedir al usuario la cantidad de etiquetas
 * mediante un prompt. Valida que el número ingresado sea mayor a 0.
 *
 * @param {string|number} valorActual - Valor previo para mostrar en el prompt.
 * @returns {number|null|NaN} Número válido, null si cancelado, NaN si inválido.
 */
function pedirCantidadInicial(valorActual = "") {
    const entrada = window.prompt(_t("Cantidad de etiquetas a imprimir"), String(valorActual));
    if (entrada === null) return null; // usuario canceló
    const numero = parseInt(String(entrada).trim(), 10);
    if (isNaN(numero) || numero <= 0) return NaN; // inválido
    return numero;
}

patch(LineaComponente.prototype, {
    

    /**
     * Evento de botón "Imprimir etiqueta".
     * Siempre solicita al usuario la cantidad mediante un prompt (usando el último valor como predeterminado).
     * Construye un payload con los datos del producto/lote/serie
     * y envía la solicitud de impresión al backend vía RPC.
     * Notifica en la UI el resultado (éxito o error).
     *
     * @param {Event} ev - Evento de click.
     */
    async alImprimirEtiqueta(ev) {
        ev.stopPropagation();
        const linea = this.line;
        if (!linea) {
            this.env.model.notification(_t("Seleccione una línea antes de imprimir."), { type: "warning" });
            return;
        }

        // Siempre pedir cantidad (usar la última como valor por defecto si existe)
        const numero = pedirCantidadInicial(linea._cantidad_impresion_etiquetas || "");
        if (numero === null) return; // cancelado
        if (Number.isNaN(numero)) {
            this.env.model.notification(_t("Ingrese un número válido mayor a 0."), { type: "warning" });
            return;
        }
        linea._cantidad_impresion_etiquetas = numero;
        // Re-render opcional (por si hay badges u otros indicadores)
        if (this.render) {
            try { this.render(true); } catch (_) {}
        }

        // Datos del producto y trazabilidad
        const producto = linea.product_id || {};
        const seguimiento = (producto.tracking || "none").toLowerCase(); // 'none' | 'lot' | 'serial'
        const numero_lote = (linea.lot_id && linea.lot_id.name) || linea.lot_name || null;

        // Normalizar fecha de vencimiento
        const normalizarFecha = (f) =>
            (f && typeof f === "object" && typeof f.toISO === "function") ? f.toISO() : f;

        const fecha_vencimiento = normalizarFecha(
            linea.expiration_date
            || (linea.lot_id && (linea.lot_id.expiration_date || linea.lot_id.use_date))
            || null
        );

        // Siempre usar la cantidad definida por el usuario
        const cantidad_final = Math.floor(+linea._cantidad_impresion_etiquetas);

        // Construcción del payload a enviar al backend
        const datos = {
            datos_producto: {
                nombre: producto.display_name || producto.name || "",
                codigo_barras: producto.barcode || "",
                referencia_interna: producto.default_code || "",
                precio: producto.lst_price || producto.list_price || 0,
                numero_lote_serial: seguimiento !== "none" ? numero_lote : null,
                fecha_vencimiento: fecha_vencimiento,
            },
            configuracion_impresora: {}, // se resuelve en backend ('impresoras')
            cantidad: cantidad_final,
        };

        // Enviar solicitud de impresión al backend
        try {
            const respuesta = await rpc("/barcode_label_print/print", datos);
            if (respuesta && respuesta.ok) {
                this.env.model.notification(_t("Etiqueta enviada a impresión."), { type: "success" });
            } else {
                throw new Error(respuesta && respuesta.message ? respuesta.message : "Error desconocido");
            }
        } catch (error) {
            console.error(error);
            this.env.model.notification(_t("No se pudo imprimir: ") + (error.message || ""), { type: "danger" });
        }
    },
});
