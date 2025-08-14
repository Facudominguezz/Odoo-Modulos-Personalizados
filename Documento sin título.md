# **Módulo `stock_barcode_label_print`**

**Objetivo**: Añadir un botón **Imprimir** en la UI del módulo **Código de Barras** (Recepciones/Operaciones) para enviar un **JSON** con los datos del producto/lote/cantidad al middleware de impresión, reutilizando la infraestructura existente de `relex_api` e **importando** el cliente `consultar_api` del módulo `impresoras`.

---

## **Decisión de arquitectura**

* **Nuevo módulo** (recomendado): `stock_barcode_label_print` que **depende** de `stock_barcode`, `relex_api` e `impresoras`.

* Se **reusa** el cliente HTTP `consultar_api` definido en el controller del módulo `impresoras`. El nuevo módulo expone una ruta JSON (`/barcode_label_print/print`) que recibe el payload de la UI y lo reenvía al middleware a través de ese cliente.

* **Fallback**: si `impresoras` no está presente, se usa `relex_api.build_url(...)` \+ `requests` para llamar al endpoint `print_pdf`.

---

## **Estructura del módulo**

stock\_barcode\_label\_print/  
├─ \_\_init\_\_.py  
├─ \_\_manifest\_\_.py  
├─ controllers/  
│  ├─ \_\_init\_\_.py  
│  └─ print\_controller.py  
├─ static/  
│  └─ src/  
│     ├─ js/  
│     │  └─ print\_button.js  
│     └─ xml/  
│        └─ print\_button.xml  
└─ security/  
   └─ ir.model.access.csv

---

## **Archivos completos**

### **`__manifest__.py`**

\# \-\*- coding: utf-8 \-\*-  
{  
    "name": "Stock Barcode Label Print",  
    "summary": "Botón 'Imprimir' en la UI de Código de Barras (Recepciones/Picking) que envía el JSON al middleware",  
    "version": "18.0.1.0.0",  
    "author": "Reswoy",  
    "license": "LGPL-3",  
    "website": "https://github.com/reswoy/Odoo-Modulos-Personalizados",  
    "category": "Inventory/Barcode",  
    "depends": \[  
        "stock",  
        "stock\_barcode",  
        "web",  
        "relex\_api",     \# endpoints y configuración  
        "impresoras",    \# cliente consultar\_api (reuso)  
    \],  
    "assets": {  
        "web.assets\_backend": \[  
            "stock\_barcode\_label\_print/static/src/xml/print\_button.xml",  
            "stock\_barcode\_label\_print/static/src/js/print\_button.js",  
        \],  
    },  
    "data": \[  
        "security/ir.model.access.csv",  
    \],  
    "installable": True,  
    "application": False,  
}

### **`__init__.py`**

\# \-\*- coding: utf-8 \-\*-  
from . import controllers

### **`controllers/__init__.py`**

\# \-\*- coding: utf-8 \-\*-  
from . import print\_controller

### **`controllers/print_controller.py`**

\# \-\*- coding: utf-8 \-\*-  
import logging

import requests  
from odoo import http  
from odoo.http import request

\# Reuso del cliente HTTP del módulo impresoras (si está instalado)  
Cliente \= None  
try:  
    from odoo.addons.impresoras.controllers import ImpresionPersonalizadaController as Cliente  \# noqa: E402  
except Exception:  \# pragma: no cover  
    Cliente \= None

\# Reuso de utilidades relex\_api para URLs  
try:  
    from odoo.addons.relex\_api.constants import build\_url  \# noqa: E402  
except Exception:  \# pragma: no cover  
    build\_url \= None

\_logger \= logging.getLogger(\_\_name\_\_)

class BarcodeLabelPrintController(http.Controller):  
    """Endpoint JSON que recibe el payload desde la UI de Barcode y lo reenvía al middleware."""

    @http.route("/barcode\_label\_print/print", type="json", auth="user")  
    def barcode\_label\_print(self, \*\*payload):  
        """  
        Espera un JSON como:  
        {  
          "product\_data": {...},  
          "printer\_config": {...},  
          "quantity": 1  
        }  
        """  
        env \= request.env  
        \# Si existe el cliente de 'impresoras', lo usamos (centraliza timeouts/reintentos/headers)  
        if Cliente:  
            client \= Cliente(env)  
            resp \= client.consultar\_api(endpoint\_key="print\_pdf", metodo="POST", datos=payload)  
            if resp is None:  
                return {"ok": False, "message": "Fallo al enviar a middleware (consultar\_api)"}  
            return {"ok": True, "result": resp}

        \# Fallback liviano: llamada directa usando relex\_api  
        if not build\_url:  
            return {"ok": False, "message": "No se puede construir URL (relex\_api no presente)"}  
        try:  
            url \= build\_url(env, "print\_pdf")  
            r \= requests.post(url, json=payload, timeout=15)  
            r.raise\_for\_status()  
            return {"ok": True, "result": r.json()}  
        except Exception as e:  \# pragma: no cover  
            \_logger.exception("Error enviando a middleware (fallback): %s", e)  
            return {"ok": False, "message": str(e)}

### **`static/src/xml/print_button.xml`**

\<?xml version="1.0" encoding="UTF-8"?\>  
\<templates xml:space="preserve"\>  
  \<\!--  
    Extendemos la línea de picking en la UI de Barcode para insertar el botón  
    a la izquierda de la miniatura.  
    Nota: el id del template puede variar por versión; en Odoo 18 el client  
    action de stock\_barcode renderiza cada línea en 'stock\_barcode.PickingLine'.  
  \--\>  
  \<t t-name="stock\_barcode\_label\_print.PickingLinePrint"  
     t-inherit="stock\_barcode.PickingLine"  
     t-inherit-mode="extension"\>  
    \<xpath expr=".//div\[contains(@class,'o\_line\_picture')\]" position="before"\>  
      \<button type="button"  
              class="btn btn-secondary o\_print\_label\_btn"  
              t-att-title="'Imprimir etiqueta'"\>  
        \<i class="fa fa-print"/\>  
      \</button\>  
    \</xpath\>  
  \</t\>  
\</templates\>

### **`static/src/js/print_button.js`**

/\*\* @odoo-module \*\*/

import { registry } from "@web/core/registry";  
import { patch } from "@web/core/utils/patch";  
import { \_t } from "@web/core/l10n/translation";

const actionRegistry \= registry.category("actions");

/\*  
  Parcheamos el ClientAction del Barcode para:  
  \- Capturar click en nuestro botón.  
  \- Armar el payload con datos del producto/lote/qty.  
  \- Llamar al endpoint JSON del nuevo módulo.  
\*/  
patch(actionRegistry, "stock\_barcode\_label\_print\_patch", {  
    get(name) {  
        const action \= this.\_super(...arguments);  
        if (name \=== "stock\_barcode.stock\_barcode\_picking\_client\_action") {  
            const Base \= action.Component;  
            class Patched extends Base {  
                setup() {  
                    super.setup();  
                    this.\_onGlobalClick \= this.\_onGlobalClick.bind(this);  
                }  
                mounted() {  
                    super.mounted && super.mounted();  
                    this.el.addEventListener("click", this.\_onGlobalClick);  
                }  
                willUnmount() {  
                    this.el.removeEventListener("click", this.\_onGlobalClick);  
                    super.willUnmount && super.willUnmount();  
                }  
                async \_onGlobalClick(ev) {  
                    const btn \= ev.target.closest(".o\_print\_label\_btn");  
                    if (\!btn) return;

                    // Obtenemos la línea seleccionada (o la línea del contexto)  
                    const line \= this.model.getSelectedLine ? this.model.getSelectedLine() : null;  
                    if (\!line) {  
                        this.notification.add(\_t("Seleccione una línea antes de imprimir."), { type: "warning" });  
                        return;  
                    }  
                    const product \= line.product || {};  
                    const qty \= line.qty\_done || line.quantity || 1;

                    // tracking: 'none' | 'lot' | 'serial'  
                    const tracking \= (product.tracking || "none").toLowerCase();  
                    const lot\_name \= line.lot\_name || (line.lot && line.lot.name) || null;  
                    const expiration\_date \=  
                        (line.lot && (line.lot.expiration\_date || line.lot.use\_date)) || null;

                    // Si es serializado, imprimir de a 1 por etiqueta (opcional: iteraciones)  
                    const quantity \= tracking \=== "serial" ? 1 : (qty || 1);

                    const payload \= {  
                        product\_data: {  
                            name: product.display\_name || product.name || "",  
                            barcode: product.barcode || "",  
                            internal\_reference: product.default\_code || "",  
                            price: product.list\_price || 0,  
                            lot\_serial\_number: tracking \!== "none" ? lot\_name : null,  
                            expiration\_date: expiration\_date,  
                        },  
                        // Nota: si querés, podés rellenar printer\_name desde  
                        // un modelo (RPC) y dimensiones desde parámetros.  
                        printer\_config: {  
                            printer\_name: null,  
                            label\_width\_mm: 50,  
                            label\_height\_mm: 25,  
                            dpi: 203,  
                        },  
                        quantity: quantity,  
                    };

                    try {  
                        const res \= await this.env.services.rpc("/barcode\_label\_print/print", payload);  
                        if (res && res.ok) {  
                            this.notification.add(\_t("Etiqueta enviada a impresión."), { type: "success" });  
                        } else {  
                            throw new Error(res && res.message ? res.message : "Error desconocido");  
                        }  
                    } catch (e) {  
                        console.error(e);  
                        this.notification.add(\_t("No se pudo imprimir: ") \+ (e.message || ""), { type: "danger" });  
                    }  
                }  
            }  
            return { ...action, Component: Patched };  
        }  
        return action;  
    },  
});

### **`security/ir.model.access.csv`**

id,name,model\_id:id,group\_id:id,perm\_read,perm\_write,perm\_create,perm\_unlink

---

## **JSON esperado por el middleware (ejemplo)**

{  
  "product\_data": {  
    "name": "Tape Cassette",  
    "barcode": "8993458880451",  
    "internal\_reference": "VC-TAPE-CASSETTE",  
    "price": 15.5,  
    "lot\_serial\_number": "LOT-00123",  
    "expiration\_date": "2025-12-31"  
  },  
  "printer\_config": {  
    "printer\_name": "Zebra ZD410",  
    "label\_width\_mm": 50,  
    "label\_height\_mm": 25,  
    "dpi": 203  
  },  
  "quantity": 5  
}

---

## **Instalación y prueba**

1. Copiar `stock_barcode_label_print/` en tu carpeta `modules/` del repo.

Actualizar e instalar:

 python odoo-bin \-c odoo.conf \-d \<db\> \-u stock\_barcode\_label\_print

2.   
3. Abrir **Código de Barras** → Recepción/Transferencia → en la línea del producto aparece el botón **Imprimir** a la izquierda de la imagen.

4. Al clickear, se arma el payload y se envía a `/barcode_label_print/print` → cliente `consultar_api` → endpoint `print_pdf` del middleware.

---

## **Notas y próximos pasos**

* Completar `printer_config.printer_name` leyendo la impresora **predeterminada** de tu modelo (`relex.printer`) o desde `ir.config_parameter`.

* Manejar iteraciones cuando `tracking == 'serial'` si querés imprimir una etiqueta por cada unidad.

* Registrar logs de impresión (modelo simple) para auditoría y troubleshooting.

* Si cambia el template QWeb del Barcode en futuras versiones, ajustar el `xpath` del `print_button.xml`.

