# -*- coding: utf-8 -*-
{
    # --- Metadatos básicos ----------------------------------------------------
    "name": "API Impresoras – Configuración",
    "summary": "Configuración centralizada para APIs de Reswoy",
    "description": """
Módulo para gestionar configuraciones centralizadas de APIs.

Características:
* Configuración de URL base de API desde interfaz de usuario
* Gestión centralizada de endpoints
* Configuraciones por empresa
""",
    "author": "Reswoy",
    "website": "https://www.reswoy.com/es",
    "maintainer": "Reswoy",

    # --- Información Odoo ----------------------------------------------------
    "version": "18.0.1.0.0",          # <major>.<odoo_ver>.<patch>
    "license": "LGPL-3",
    "category": "Technical",

    # --- Dependencias --------------------------------------------------------
    # 'base' es suficiente; los demás módulos lo heredarán.
    'depends': ['base', 'base_setup'],

    # Si en los mixins usas 'requests', decláralo aquí para que Odoo lo avise
    "external_dependencies": {
        "python": ["requests"],
    },

    # --- Archivos de datos XML/CSV -------------------------------------------
    "data": [
        "views/res_config_settings_views.xml",
    ],

    # --- Configuración -------------------------------------------------------
    "installable": True,
    "application": False,
    "auto_install": False,
}
