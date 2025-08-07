# -*- coding: utf-8 -*-

# Importaciones necesarias de Odoo y Python
from odoo import http
from odoo.http import request
import requests
import logging

# Logger para debug y errores
_logger = logging.getLogger(__name__)


class ImpresionPersonalizadaController(http.Controller):
    """
    Controlador para manejar todas las comunicaciones externas relacionadas
    con la gestión de impresoras personalizadas.
    
    Este controlador centraliza todas las consultas a APIs externas para:
    - Consultar APIs externas para obtener listas de impresoras
    - Enviar configuraciones a APIs externas  
    - Consultar middleware para obtener datos completos de impresoras
    """
    
    # ==================== MÉTODOS PARA CONSULTAR API EXTERNA ====================

    def _get_api_url(self, record_id=None):
        """
        Obtiene la URL de la API configurada en el sistema.

        Args:
            record_id (int): ID del registro específico para obtener su URL

        Returns:
            str: URL de la API o URL por defecto
        """
        try:
            # Si se proporciona un record_id específico, usarlo
            if record_id:
                config = request.env['impresoras'].browse(record_id)
                if config.exists() and config.api_url:
                    return config.api_url

            # Buscar configuración con URL de API (prioritizar la predeterminada)
            config = request.env['impresoras'].search([
                ('api_url', '!=', False),
                ('es_predeterminada', '=', True)
            ], limit=1)

            if config and config.api_url:
                return config.api_url

            # Si no hay predeterminada, buscar cualquier configuración con URL
            config = request.env['impresoras'].search([('api_url', '!=', False)], limit=1)
            if config and config.api_url:
                return config.api_url

        except Exception as e:
            _logger.error(f"Error al obtener URL de API: {e}")

        # URL por defecto si no hay configuración
        return 'http://10.218.3.162:5000/printers'

    def _consultar_api_externa_con_url(self, url_base, endpoint='', metodo='GET', datos=None):
        """
        Método auxiliar para realizar peticiones a APIs externas con URL específica.

        Args:
            url_base (str): URL base específica a usar
            endpoint (str): Endpoint específico a consultar
            metodo (str): Método HTTP (GET, POST, etc.)
            datos (dict): Datos a enviar en caso de POST

        Returns:
            dict: Respuesta de la API o None en caso de error
        """
        try:
            # Validar que url_base sea una cadena válida
            if not url_base or not isinstance(url_base, str):
                _logger.error(f"URL base inválida: {url_base}")
                return None

            url = url_base + endpoint

            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Odoo-ImpresionPersonalizada/1.0'
            }

            if metodo.upper() == 'GET':
                response = requests.get(url, timeout=10, headers=headers)
            elif metodo.upper() == 'POST':
                response = requests.post(url, json=datos, timeout=10, headers=headers)
            else:
                raise ValueError(f"Método HTTP no soportado: {metodo}")

            response.raise_for_status()
            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            _logger.error(f"Error en petición a API externa: {e}")
            return None
        except Exception as e:
            _logger.error(f"Error inesperado en API externa: {e}")
            return None

    def consultar_impresoras_api_externa_con_url(self, url_especifica):
        """
        Consulta la API externa para obtener la lista de impresoras disponibles usando una URL específica.

        Args:
            url_especifica (str): URL específica para consultar

        Returns:
            list: Lista de diccionarios con información de impresoras o lista vacía en caso de error
        """
        try:
            _logger.info(f"Consultando API de impresoras en URL específica: {url_especifica}")

            # Usar el método centralizado para consultar la API con URL específica
            impresoras_data = self._consultar_api_externa_con_url(url_especifica)

            if impresoras_data:
                _logger.info(f"Se obtuvieron {len(impresoras_data)} impresoras de la API externa")
                return impresoras_data
            else:
                _logger.warning("No se obtuvieron datos de la API externa")
                return []

        except Exception as e:
            _logger.error(f"Error inesperado al obtener impresoras: {e}")
            return []

    def get_impresoras_para_selection_con_url(self, url_especifica):
        """
        Obtiene la lista de impresoras formateada para campos Selection de Odoo usando una URL específica.

        Args:
            url_especifica (str): URL específica para consultar

        Returns:
            list: Lista de tuplas (valor, etiqueta) para el campo Selection
        """
        try:
            # Consultar API externa con URL específica
            impresoras_data = self.consultar_impresoras_api_externa_con_url(url_especifica)

            if not impresoras_data:
                return [('sin_conexion', f'Sin conexión a API - Verificar {url_especifica}')]

            # Convertir a formato Selection de Odoo
            impresoras_list = []
            for impresora in impresoras_data:
                # Adaptar a la estructura de respuesta de tu API
                nombre = impresora.get('name', 'Sin nombre')  # Tu API usa 'name'
                puerto = impresora.get('port', '')  # Tu API usa 'port'
                # Crear descripción combinando nombre y puerto
                descripcion = f"{nombre} ({puerto})" if puerto else nombre
                impresoras_list.append((nombre, descripcion))

            _logger.info(f"Se formatearon {len(impresoras_list)} impresoras para Selection desde {url_especifica}")
            return impresoras_list if impresoras_list else [('vacio', 'No hay impresoras disponibles')]

        except Exception as e:
            _logger.error(f"Error al formatear impresoras para Selection con URL {url_especifica}: {e}")
            return [('error', f'Error al consultar {url_especifica}')]

    def enviar_predeterminada_api_externa(self, impresora_data):
        """
        Envía la configuración de impresora predeterminada a la API externa.
        
        Args:
            impresora_data (dict): Datos de la impresora a enviar
            
        Returns:
            bool: True si el envío fue exitoso, False en caso contrario
        """
        try:
            _logger.info(f"Enviando impresora predeterminada a API externa")
            
            # Obtener URL de configuración
            api_url = self._get_api_url()

            # Preparar datos para envío
            datos_envio = {
                'nombre': impresora_data.get('name'),
                'ip': impresora_data.get('direccion_ip'),
                'puerto': impresora_data.get('puerto'),
                'timestamp': request.env.cr.now().isoformat()
            }
            
            # Enviar usando el método centralizado
            respuesta = self._consultar_api_externa_con_url(api_url, '/impresora/predeterminada', 'POST', datos_envio)

            if respuesta is not None:
                _logger.info(f"Impresora predeterminada enviada exitosamente: {datos_envio}")
                return True
            else:
                _logger.error(f"Error al enviar impresora predeterminada: {datos_envio}")
                return False
            
        except Exception as e:
            _logger.error(f"Error inesperado al enviar impresora predeterminada: {e}")
            return False
