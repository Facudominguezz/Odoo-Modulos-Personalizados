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
        Obtiene la lista de impresoras disponibles desde la API externa usando constantes.

        Returns:
            list: Lista de tuplas (valor, etiqueta) para el campo Selection
        """
        try:
            controller = self._get_controller()

            _logger.info("Obteniendo impresoras para Selection usando constantes de relex_api")
            # Usar el método que utiliza constantes
            return controller.get_impresoras_para_selection()

        except Exception as e:
            _logger.error(f"Error al obtener impresoras desde controlador: {e}")
            return [
                ('', 'Seleccione una impresora...'),
                ('error', 'Error al consultar impresoras - Use "Refrescar Lista API"'),
            ]

    def consultar_impresoras_api(self):
        """
        Método para refrescar manualmente la lista de impresoras desde la API usando constantes.
        Este método se llama desde el botón en la vista y usa el controlador.
        """
        try:
            # Limpiar selección actual
            self.impresora_seleccionada = False
            
            # Usar el controlador para consultar la API
            controller = self._get_controller()

            _logger.info("Refrescando lista de impresoras usando constantes de relex_api")

            # Consultar la API usando constantes
            impresoras_data = controller.consultar_impresoras_api_externa()

            if impresoras_data:
                # Forzar recarga del campo Selection
                self._fields['impresora_seleccionada'].selection = self._get_impresoras_disponibles()
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Éxito',
                        'message': f'Lista actualizada: {len(impresoras_data)} impresoras encontradas desde API configurada',
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Advertencia',
                        'message': 'No se pudo conectar con la API - Verificar configuración en relex_api',
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
        los datos usando el controlador con constantes.
        """
        if self.impresora_seleccionada and self.impresora_seleccionada not in ['sin_conexion', 'vacio', 'error']:
            try:
                # Obtener los datos directamente de la API usando el controlador
                controller = self._get_controller()

                # Usar constantes para consultar la API
                impresoras_data = controller.consultar_impresoras_api_externa()

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
                    # Si hay un puerto definido, usarlo, sino dejar vacío
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

            except Exception as e:
                _logger.error(f"Error al actualizar datos de impresora: {e}")
                # En caso de error, mantener el nombre seleccionado
                self.name = f"{self.impresora_seleccionada}"
                self.direccion_ip = False
                self.puerto = False

    # ==================== VALIDACIONES Y CONSTRAINS ====================

    @api.constrains('es_predeterminada')
    def _check_una_predeterminada(self):
        """
        Validación para asegurar que solo una impresora puede ser marcada como predeterminada.
        """
        predeterminadas = self.search([('es_predeterminada', '=', True)])
        if len(predeterminadas) > 1:
            raise models.ValidationError(
                "Solo puede haber una impresora marcada como predeterminada. "
                f"Actualmente hay {len(predeterminadas)} marcadas."
            )

    # ==================== MÉTODOS AUTOMÁTICOS ====================

    def _enviar_predeterminada_automatico(self):
        """
        Envía automáticamente la configuración cuando se marca una impresora como predeterminada.
        Este método se ejecuta automáticamente al guardar.
        """
        if self.es_predeterminada:
            try:
                controller = self._get_controller()

                impresora_data = {
                    'name': self.name,
                    'direccion_ip': self.direccion_ip,
                    'puerto': self.puerto,
                }

                exito = controller.enviar_predeterminada_api_externa(impresora_data)

                if exito:
                    _logger.info(f"Impresora predeterminada enviada automáticamente: {self.name}")
                else:
                    _logger.warning(f"No se pudo enviar impresora predeterminada automáticamente: {self.name}")

            except Exception as e:
                _logger.error(f"Error al enviar impresora predeterminada automáticamente: {e}")

    @api.model
    def write(self, vals):
        """
        Sobrescribir el método write para manejar automáticamente las impresoras predeterminadas.
        """
        # Si se está marcando como predeterminada, desmarcar las demás
        if vals.get('es_predeterminada'):
            # Buscar otras impresoras marcadas como predeterminadas
            otras_predeterminadas = self.search([
                ('es_predeterminada', '=', True),
                ('id', '!=', self.id)
            ])
            # Desmarcarlas
            if otras_predeterminadas:
                otras_predeterminadas.write({'es_predeterminada': False})

        # Ejecutar el write original
        result = super().write(vals)

        # Si se marcó como predeterminada, enviar a API automáticamente
        if vals.get('es_predeterminada'):
            self._enviar_predeterminada_automatico()

        return result

    @api.onchange('es_predeterminada')
    def _onchange_es_predeterminada(self):
        """
        Cuando se marca/desmarca como predeterminada, manejar la lógica automáticamente.
        """
        if self.es_predeterminada:
            # Advertir que se desmarcará automáticamente cualquier otra predeterminada
            otras_predeterminadas = self.search([
                ('es_predeterminada', '=', True),
                ('id', '!=', self.id)
            ])
            if otras_predeterminadas:
                nombres = ', '.join(otras_predeterminadas.mapped('name'))
                return {
                    'warning': {
                        'title': 'Cambio de impresora predeterminada',
                        'message': f'Al marcar esta impresora como predeterminada, se desmarcará automáticamente: {nombres}'
                    }
                }

    # ==================== MÉTODOS DE UTILIDAD ====================

    @api.model
    def obtener_impresora_predeterminada(self):
        """
        Obtiene la impresora marcada como predeterminada.

        Returns:
            recordset: La impresora predeterminada o recordset vacío si no hay ninguna
        """
        return self.search([('es_predeterminada', '=', True)], limit=1)

    def verificar_consistencia_predeterminada(self):
        """
        Verifica la consistencia de las impresoras predeterminadas y corrige problemas.

        Returns:
            dict: Resultado de la verificación con estadísticas
        """
        try:
            predeterminadas = self.search([('es_predeterminada', '=', True)])

            if len(predeterminadas) == 0:
                return {
                    'status': 'sin_predeterminada',
                    'message': 'No hay impresoras marcadas como predeterminadas',
                    'count': 0
                }
            elif len(predeterminadas) == 1:
                return {
                    'status': 'consistente',
                    'message': f'Una impresora predeterminada: {predeterminadas[0].name}',
                    'count': 1,
                    'predeterminada': predeterminadas[0].name
                }
            else:
                # Hay múltiples predeterminadas - corregir automáticamente
                # Mantener solo la más reciente
                predeterminada_a_mantener = predeterminadas.sorted('write_date', reverse=True)[0]
                otras_a_desmarcar = predeterminadas - predeterminada_a_mantener

                otras_a_desmarcar.write({'es_predeterminada': False})

                return {
                    'status': 'corregido',
                    'message': f'Se encontraron {len(predeterminadas)} predeterminadas. Se mantuvo: {predeterminada_a_mantener.name}',
                    'count': len(predeterminadas),
                    'predeterminada': predeterminada_a_mantener.name,
                    'corregidas': len(otras_a_desmarcar)
                }

        except Exception as e:
            _logger.error(f"Error al verificar consistencia predeterminada: {e}")
            return {
                'status': 'error',
                'message': f'Error al verificar: {str(e)}',
                'count': 0
            }

    def establecer_como_predeterminada(self):
        """
        Establece esta impresora como la predeterminada del sistema y envía
        la configuración a la API externa usando constantes.
        """
        try:
            # Quitar marca de predeterminada a todas las demás impresoras
            otras_impresoras = self.search([('id', '!=', self.id)])
            otras_impresoras.write({'es_predeterminada': False})

            # Marcar esta como predeterminada
            self.es_predeterminada = True

            # Enviar configuración a API externa usando constantes
            controller = self._get_controller()

            impresora_data = {
                'name': self.name,
                'direccion_ip': self.direccion_ip,
                'puerto': self.puerto,
            }

            exito = controller.enviar_predeterminada_api_externa(impresora_data)

            if exito:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Éxito',
                        'message': f'Impresora "{self.name}" establecida como predeterminada y enviada a API',
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Advertencia',
                        'message': f'Impresora marcada como predeterminada pero no se pudo enviar a API externa',
                        'type': 'warning',
                    }
                }

        except Exception as e:
            _logger.error(f"Error al establecer impresora predeterminada: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': f'Error al establecer impresora predeterminada: {str(e)}',
                    'type': 'danger',
                }
            }
