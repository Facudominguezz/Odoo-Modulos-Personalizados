# modules/etiquetas_zpl/__manifest__.py
{
    "name": "Etiquetas - Plantillas por Categoría",
    "summary": "Gestiona plantillas de etiquetas ZPL por categoría de producto",
    "version": "18.0.1.0.0",
    "author": "Relex",
    "website": "https://example.com",
    "license": "OPL-1",
    "depends": [
        "product",          # categorías y productos del inventario
        "stock",
    ],
    "data": [
        "security/etiquetas_security.xml",
        "security/ir.model.access.csv",
        "views/etiqueta_plantilla_categoria_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
