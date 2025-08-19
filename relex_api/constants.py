"""
Constantes y utilidades para la API de Relex.

Este módulo contiene funciones auxiliares para la construcción de URLs
y manejo de endpoints de la API de impresoras Relex.
"""

from urllib.parse import urljoin
from odoo import api, SUPERUSER_ID


def get_api_base_url(env):
    """
    Obtiene la URL base de la API desde los parámetros de configuración.

    Args:
        env: Entorno de Odoo para acceder a los parámetros del sistema

    Returns:
        str: URL base de la API configurada en el sistema
    """
    return env['ir.config_parameter'].sudo().get_param('relex_api.api_base_url')


def build_url(env, key):
    """
    Construye una URL completa combinando la URL base con un endpoint específico.

    Args:
        env: Entorno de Odoo para acceder a la configuración
        key (str): Clave del endpoint a construir ('root', 'printers', 'default_printer')

    Returns:
        str: URL completa formada por la URL base + endpoint específico

    Raises:
        KeyError: Si la clave proporcionada no existe en ENDPOINTS
    """
    # Obtener la URL base desde la configuración del sistema
    API_BASE_URL = get_api_base_url(env) or ''

    # Diccionario de endpoints disponibles en la API
    ENDPOINTS = {
        'root': '/',                                # Endpoint raíz de la API
        'printers': '/printers',                    # Listado de impresoras
        'default_printer': '/impresora/predeterminada',  # Impresora por defecto
        'imprimir': '/print/label',                      # Enviar impresión/prueba (alias)
    }

    # Construir y retornar la URL completa usando urljoin para manejo seguro de rutas
    if not API_BASE_URL:
        raise ValueError("La URL base de la API no está configurada (relex_api.api_base_url)")
    return urljoin(API_BASE_URL.rstrip('/') + '/', ENDPOINTS[key].lstrip('/'))
