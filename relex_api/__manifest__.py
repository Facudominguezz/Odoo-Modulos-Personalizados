# relex_api/__manifest__.py
{
    # --- Metadatos básicos ----------------------------------------------------
    "name": "Relex API Core",
    "summary": "Constantes y mixins reutilizables para la API de impresoras",
    "description": """
Relex API Core
==============
Módulo técnico que centraliza:

* `API_BASE_URL`
* `ENDPOINTS`
* `build_url()`
* Mixins/ayudas relacionadas

No añade modelos funcionales ni vistas. Los demás addons de Relex deben
declararlo en `depends` para reutilizar estas utilidades.
""",
    "author": "Relex · Facundo Diaz Dominguez",
    "website": "https://www.relex.com",
    "maintainer": "Relex",

    # --- Información Odoo ----------------------------------------------------
    "version": "18.0.1.0.0",          # <major>.<odoo_ver>.<patch>
    "license": "LGPL-3",
    "category": "Technical/Tools",

    # --- Dependencias --------------------------------------------------------
    # 'base' es suficiente; los demás módulos lo heredarán.
    "depends": ["base"],

    # Si en los mixins usas 'requests', decláralo aquí para que Odoo lo avise
    "external_dependencies": {
        "python": ["requests"],
    },

    # --- Archivos de datos XML/CSV (no hay) ----------------------------------
    "data": [],

    # --- Configuración -------------------------------------------------------
    "installable": True,
    "application": False,
    "auto_install": False,
}
