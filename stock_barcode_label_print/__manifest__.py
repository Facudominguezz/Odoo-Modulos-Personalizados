# -*- coding: utf-8 -*-
{
    "name": "Stock Barcode Label Print",
    "summary": "Botón 'Imprimir' en la UI de Código de Barras (Recepciones/Picking) que envía un JSON al middleware",
    "version": "18.0.1.0.0",
    "author": "Reswoy",
    "license": "LGPL-3",
    "website": "https://github.com/reswoy/Odoo-Modulos-Personalizados",
    "category": "Inventory/Barcode",
    "depends": [
        "stock",
        "stock_barcode",
        "web",
        "relex_api",
        "impresoras",
    ],
    "assets": {
        "web.assets_backend": [
            "stock_barcode_label_print/static/src/xml/print_button.xml",
            "stock_barcode_label_print/static/src/js/print_button.js",
        ],
    },
    "data": [
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "application": False,
}
