# -*- coding: utf-8 -*-

# Importaciones necesarias de Odoo
from odoo import models, fields, api
import logging

# Logger para debug y errores
_logger = logging.getLogger(__name__)


class Impresoras(models.Model):
    """
    Modelo para gestionar configuraciones de impresoras.

    Este modelo almacena configuraciones de impresoras de forma independiente.
    """
    
    # ==================== CONFIGURACIÓN DEL MODELO ====================
    
    # Nombre técnico del modelo (usado internamente por Odoo)
    _name = "impresoras"

    # Descripción humana del modelo (aparece en logs y referencias)
    _description = "Impresoras"


    # ==================== DEFINICIÓN DE CAMPOS ====================
    
    # Campo de texto para identificar la configuración
    name = fields.Char(
        string='Nombre',
        required=False,
        help="Nombre descriptivo de la impresora"
    )
    
    # Campo para almacenar la dirección IP de la impresora
    direccion_ip = fields.Char(
        string='Dirección IP',
        required=False,
        help="Dirección IP de la impresora"
    )
    
    # Campo numérico para el puerto de conexión
    puerto = fields.Char(
        string='Puerto',
        default='9100',
        help="Puerto de conexión de la impresora"
    )
    
    # Campo para la URL de la API
    # Campo para las URLs de la API (múltiples endpoints)
    api_url = fields.Text(
        string='URLs de API',
        default='http://10.218.3.162:5000/\nhttp://10.218.3.163:5000/\nhttp://localhost:5000/',
        help="URLs de las APIs donde se consultan las impresoras disponibles (una por línea)"
    )

    # Campo de selección para las impresoras disponibles desde la API
    impresora_seleccionada = fields.Selection(
        selection='_get_impresoras_disponibles',
        string='Impresora Disponible',
        help="Selecciona una impresora de la lista obtenida desde la API"
    )
    
    # Campo booleano para marcar la impresora predeterminada
    es_predeterminada = fields.Boolean(
        string='Impresora Predeterminada',
        default=False,
        help="Marca esta impresora como la predeterminada del sistema"
    )
    

    # ==================== MÉTODOS DE INTEGRACIÓN CON CONTROLADOR ====================
    
    def _get_controller(self):
        """
        Obtiene una instancia del controlador para realizar consultas a APIs externas.
        
        Returns:
            ImpresionPersonalizadaController: Instancia del controlador
        """
        try:
            from ..controllers.controllers import ImpresionPersonalizadaController
            return ImpresionPersonalizadaController()
        except ImportError:
            _logger.error("No se pudo importar el controlador de impresión personalizada")
            raise
    
    def _get_impresoras_disponibles(self):
        """
        Obtiene la lista de impresoras disponibles desde la API externa usando el controlador.
        
        Returns:
            list: Lista de tuplas (valor, etiqueta) para el campo Selection
        """
        try:
            controller = self._get_controller()

            # Usar la URL del registro actual o una URL por defecto
            url_a_usar = 'http://10.218.3.162:5000/printers'

            _logger.info(f"Obteniendo impresoras para Selection usando URL: {url_a_usar}")
            return controller.get_impresoras_para_selection_con_url(url_a_usar)

        except Exception as e:
            _logger.error(f"Error al obtener impresoras desde controlador: {e}")
            return [
                ('', 'Seleccione una impresora...'),
                ('error', 'Error al consultar impresoras - Use "Refrescar Lista API"'),
            ]

    def consultar_impresoras_api(self):
        """
        Método para refrescar manualmente la lista de impresoras desde la API.
        Este método se llama desde el botón en la vista y usa el controlador.
        """
        try:
            # Limpiar selección actual
            self.impresora_seleccionada = False
            
            # Usar el controlador para consultar la API
            controller = self._get_controller()

            # Log para debug - mostrar qué URL se está usando
            _logger.info(f"Usando URL: {self.api_url}")

            # Consultar la API
            impresoras_data = controller.consultar_impresoras_api_externa_con_url(self.api_url)

            if impresoras_data:
                # Forzar recarga del campo Selection
                self._fields['impresora_seleccionada'].selection = self._get_impresoras_disponibles()
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Éxito',
                        'message': f'Lista actualizada: {len(impresoras_data)} impresoras encontradas usando {self.api_url}',
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Advertencia',
                        'message': f'No se pudo conectar con la API en {self.api_url} - Verificar URL y conectividad',
                        'type': 'warning',
                    }
                }
                
        except Exception as e:
            _logger.error(f"Error al refrescar impresoras: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Error al actualizar impresoras: {str(e)}',
                    'type': 'danger',
                }
            }
    
    @api.onchange('impresora_seleccionada')
    def _onchange_impresora_seleccionada(self):
        """
        Cuando se selecciona una impresora desde la API, obtener automáticamente
        los datos del middleware usando el controlador.
        """
        if self.impresora_seleccionada and self.impresora_seleccionada not in ['sin_conexion', 'vacio', 'error']:
            try:
                # Obtener los datos directamente de la API usando el controlador
                controller = self._get_controller()

                # Usar la URL del registro actual
                impresoras_data = controller.consultar_impresoras_api_externa_con_url(self.api_url)

                # Buscar la impresora seleccionada en los datos de la API
                impresora_encontrada = None
                for impresora in impresoras_data:
                    if impresora.get('name') == self.impresora_seleccionada:
                        impresora_encontrada = impresora
                        break

                if impresora_encontrada:
                    # Usar los datos reales de la API sin generar datos sintéticos
                    self.name = f"{impresora_encontrada.get('name', 'Sin nombre')}"

                    # Usar el puerto real de la API tal como viene
                    puerto_api = impresora_encontrada.get('port', '')
                    # Si hay un puerto definido, intentar extraer número, sino dejar vacío
                    if puerto_api:
                        self.puerto = puerto_api  # Mantener el puerto tal como viene de la API
                    else:
                        self.puerto = False  # Dejar vacío si no hay puerto

                    # No generar IP sintética, dejar vacío
                    self.direccion_ip = False  # Dejar vacío - no generar IPs

                    _logger.info(f"Datos actualizados para {self.impresora_seleccionada}: Nombre={self.name}, Puerto={self.puerto}, IP={self.direccion_ip}")
                else:
                    # Si no se encuentra la impresora en la API, usar valores por defecto
                    self.name = f"{self.impresora_seleccionada}"
                    self.direccion_ip = False  # Dejar vacío
                    self.puerto = False  # Dejar vacío
                    _logger.warning(f"No se encontró {self.impresora_seleccionada} en los datos de la API, usando valores por defecto")

            except Exception as e:
                _logger.error(f"Error al obtener datos de la API para {self.impresora_seleccionada}: {e}")
                # En caso de error, limpiar campos
                self.name = f"Configuración {self.impresora_seleccionada}"
                self.direccion_ip = False  # Dejar vacío
                self.puerto = False  # Dejar vacío
        else:
            # Si no hay impresora seleccionada o es un valor especial, limpiar campos
            self.name = False
            self.direccion_ip = False
            self.puerto = False
    
    
    # ==================== VALIDACIONES Y CONSTRAINS ====================
    
    @api.constrains('es_predeterminada')
    def _check_una_predeterminada(self):
        """
        Validación para asegurar que solo haya una impresora predeterminada.
        Si se marca una nueva impresora como predeterminada, desmarca automáticamente las demás
        y envía la configuración a la API automáticamente.
        """
        for record in self:
            if record.es_predeterminada:
                # Buscar otras impresoras marcadas como predeterminadas (excluyendo la actual)
                otras_predeterminadas = self.search([
                    ('es_predeterminada', '=', True),
                    ('id', '!=', record.id)
                ])
                
                if otras_predeterminadas:
                    # Desmarcar las otras como predeterminadas sin triggar constraints adicionales
                    self.env.cr.execute(
                        "UPDATE impresoras SET es_predeterminada = false WHERE id = ANY(%s)",
                        (otras_predeterminadas.ids,)
                    )
                    
                    # Invalidar el cache para que se reflejen los cambios
                    otras_predeterminadas.invalidate_recordset(['es_predeterminada'])
                    
                    _logger.info(f"Se desmarcaron {len(otras_predeterminadas)} impresoras como predeterminadas. Nueva predeterminada: {record.name}")
                
                # Enviar automáticamente a la API cuando se marca como predeterminada
                record._enviar_predeterminada_automatico()
    
    def _enviar_predeterminada_automatico(self):
        """
        Envía automáticamente la configuración de impresora predeterminada a la API usando el controlador.
        Este método se ejecuta automáticamente cuando se marca una impresora como predeterminada.
        """
        try:
            # Verificar que hay datos completos para enviar
            if not self.name:
                _logger.warning(f"No se puede enviar a API: datos incompletos para {self.id}")
                return
            
            # Preparar datos para envío
            datos_impresora = {
                'name': self.name,
                'direccion_ip': self.direccion_ip or '',
                'puerto': self.puerto or 0
            }
            
            # Usar el controlador para enviar a la API
            controller = self._get_controller()
            exito = controller.enviar_predeterminada_api_externa(datos_impresora)
            
            if exito:
                _logger.info(f"Impresora predeterminada enviada automáticamente: {datos_impresora}")
            else:
                _logger.error(f"Error al enviar automáticamente impresora predeterminada: {datos_impresora}")

        except Exception as e:
            _logger.error(f"Error inesperado al enviar automáticamente impresora predeterminada: {e}")
            # No lanzar excepción para no interrumpir el proceso de marcado como predeterminada
    
    def write(self, vals):
        """
        Método write normal - la lógica de unicidad se maneja en el constraint.
        """
        _logger.info(f"WRITE llamado con vals: {vals}")
        _logger.info(f"Estado actual antes de write - ID: {self.id}, Nombre: {self.name}, Puerto: {self.puerto}, IP: {self.direccion_ip}")

        result = super(Impresoras, self).write(vals)

        # Log después del write para verificar si se guardó
        self.invalidate_recordset()  # Invalida el cache para refrescar datos
        _logger.info(f"Estado después de write - ID: {self.id}, Nombre: {self.name}, Puerto: {self.puerto}, IP: {self.direccion_ip}")

        return result

    @api.onchange('es_predeterminada')
    def _onchange_es_predeterminada(self):
        """
        Método que se ejecuta cuando cambia el campo es_predeterminada en la interfaz.
        Proporciona feedback inmediato al usuario sobre el cambio.
        """
        if self.es_predeterminada:
            # Buscar si ya hay otra impresora predeterminada
            otras_predeterminadas = self.search([
                ('es_predeterminada', '=', True),
                ('id', '!=', self.id if self.id else 0)
            ])
            
            if otras_predeterminadas:
                # Mostrar mensaje informativo sobre el cambio que se realizará
                return {
                    'warning': {
                        'title': 'Cambio de impresora predeterminada',
                        'message': f'Al marcar "{self.name}" como predeterminada, se desmarcará automáticamente: {", ".join(otras_predeterminadas.mapped("name"))}'
                    }
                }
    
    @api.model
    def obtener_impresora_predeterminada(self):
        """
        Método para obtener la impresora predeterminada actual.
        
        Returns:
            dict: Información de la impresora predeterminada o None si no hay ninguna
        """
        impresora = self.search([('es_predeterminada', '=', True)], limit=1)
        if impresora:
            return {
                'nombre': impresora.name,
                'impresora': impresora.impresora_seleccionada,
                'ip': impresora.direccion_ip,
                'puerto': impresora.puerto,
                'id': impresora.id
            }
        return None
    
    @api.model
    def verificar_consistencia_predeterminada(self):
        """
        Método para verificar y corregir inconsistencias en impresoras predeterminadas.
        Útil para mantenimiento y limpieza de datos.
        
        Returns:
            dict: Estadísticas sobre la verificación
        """
        predeterminadas = self.search([('es_predeterminada', '=', True)])
        total_predeterminadas = len(predeterminadas)
        
        if total_predeterminadas == 0:
            _logger.info("No hay impresoras predeterminadas configuradas")
            return {
                'status': 'ok',
                'message': 'No hay impresoras predeterminadas configuradas',
                'total_predeterminadas': 0,
                'accion_tomada': 'ninguna'
            }
        elif total_predeterminadas == 1:
            _logger.info(f"Configuración correcta: una impresora predeterminada ({predeterminadas[0].name})")
            return {
                'status': 'ok',
                'message': f'Configuración correcta: {predeterminadas[0].name} es la impresora predeterminada',
                'total_predeterminadas': 1,
                'impresora_predeterminada': predeterminadas[0].name,
                'accion_tomada': 'ninguna'
            }
        else:
            # Hay múltiples predeterminadas, mantener solo la primera
            impresora_mantener = predeterminadas[0]
            impresoras_desmarcar = predeterminadas[1:]
            
            impresoras_desmarcar.write({'es_predeterminada': False})
            
            _logger.warning(f"Se encontraron {total_predeterminadas} impresoras predeterminadas. Se mantuvo '{impresora_mantener.name}' y se desmarcaron {len(impresoras_desmarcar)}")
            
            return {
                'status': 'corregido',
                'message': f'Se corrigió la configuración. {impresora_mantener.name} es ahora la única impresora predeterminada',
                'total_predeterminadas': total_predeterminadas,
                'impresora_predeterminada': impresora_mantener.name,
                'impresoras_desmarcadas': [imp.name for imp in impresoras_desmarcar],
                'accion_tomada': 'correccion_automatica'
            }
