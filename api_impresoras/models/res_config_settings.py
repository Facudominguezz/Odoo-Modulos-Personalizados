# -*- coding: utf-8 -*-
"""
Configuraciones del módulo Reswoy API.

Este módulo extiende res.config.settings para agregar configuraciones
específicas de la API de impresoras Reswoy.
"""

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    """
    Configuraciones del sistema para la API de Reswoy.

    Extiende el modelo res.config.settings para agregar parámetros
    de configuración específicos del módulo api_impresoras.
    """
    _inherit = 'res.config.settings'

    # Campo de configuración para la URL base de la API
    api_base_url = fields.Char(
        string="API Base URL",
        config_parameter='api_impresoras.api_base_url',
        help="URL base para la API de impresoras Reswoy. "
             "Ejemplo: https://api.reswoy.com/v1"
    )
    
    api_key = fields.Char(
        string="API Key",
        config_parameter='api_impresoras.api_key',
        help="Clave de API proporcionada por Reswoy para autenticarse con el middleware"
    )
