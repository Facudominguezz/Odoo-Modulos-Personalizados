# -*- coding: utf-8 -*-
{
    # Información básica del módulo
    'name': "Impresoras",  # Nombre descriptivo del módulo

    'summary': "Gestión de configuraciones para impresión personalizada",  # Resumen corto

    'description': """
        Módulo para gestionar configuraciones de impresión personalizada.
        
        Características principales:
        * Configuración de impresoras por IP y puerto
        * Gestión centralizada de configuraciones
        * Interfaz simple para administrar impresoras
        * Configuración de URL de API desde ajustes del sistema
    """,

    # Información del desarrollador
    'author': "Mi Empresa",
    'website': "https://www.miempresa.com",
    'license': 'LGPL-3',  # Agregando la licencia que faltaba

    # Clasificación del módulo
    # Categorías disponibles en: https://github.com/odoo/odoo/blob/18.0/odoo/addons/base/data/ir_module_category_data.xml
    'category': 'Productivity',  # Categoría más apropiada para herramientas de productividad
    'version': '18.0.1.0.0',  # Formato: [versión_odoo].[major].[minor].[patch]

    # Dependencias del módulo
    'depends': [
        'base', # Módulo base de Odoo (siempre requerido)
        'relex_api',
    ],

    # Dependencias externas de Python (paquetes que se deben instalar)
    'external_dependencies': {
        'python': ['requests'],  # Librería para hacer peticiones HTTP a APIs
    },

    # Archivos de datos que se cargarán siempre
    'data': [
        # Archivos de seguridad (permisos)
        'security/ir.model.access.csv',

        # Archivos de vistas (interfaz de usuario)
        'views/templates.xml',  # Vistas principales del módulo
        'views/impresoras_menus.xml',  # Vistas Menu de navegación
    ],

    # Configuraciones adicionales
    'installable': True,  # El módulo se puede instalar
    'auto_install': False,  # No se instala automáticamente
    'application': False,  # No es una aplicación independiente, es un módulo
}
