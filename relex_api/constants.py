# -*- coding: utf-8 -*-
"""
Constantes globales para la API de impresoras.
Cualquier módulo puede:  from odoo.addons.company_api_core.constants import *
"""
from urllib.parse import urljoin

API_BASE_URL = 'http://10.218.3.162:5000'

ENDPOINTS = {
    'root': '/',
    'printers': '/printers',
    'default_printer': '/impresora/predeterminada',
}

def build_url(key):
    """
    Devuelve la URL completa de un endpoint por su clave.
    >>> build_url('printers')
    'http://10.218.3.162:5000/printers'
    """

    return urljoin(API_BASE_URL.rstrip('/') + '/', ENDPOINTS[key].lstrip('/'))
