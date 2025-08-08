# -*- coding: utf-8 -*-
"""
Configuraciones del módulo Relex API.

Este módulo extiende res.config.settings para agregar configuraciones
específicas de la API de impresoras Relex.
"""

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    """
    Configuraciones del sistema para la API de Relex.

    Extiende el modelo res.config.settings para agregar parámetros
    de configuración específicos del módulo relex_api.
    """
    _inherit = 'res.config.settings'

    # Campo de configuración para la URL base de la API
    api_base_url = fields.Char(
        string="API Base URL",
        config_parameter='relex_api.api_base_url',
        help="URL base para la API de impresoras Relex. "
             "Ejemplo: https://api.relex.com/v1"
    )
