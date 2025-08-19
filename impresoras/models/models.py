# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class Impresoras(models.Model):
    _name = "impresoras"
    _description = "Impresoras"

    # === Parámetros de etiqueta (lenguaje fijo y dimensiones editables) ===
    lenguaje = fields.Selection(
        selection=[('zpl', 'ZPL')],
        string='Lenguaje',
        default='zpl',
        required=True,
        readonly=True
    )
    ancho_mm = fields.Float(string='Ancho (mm)', default=50.0, required=True)
    alto_mm = fields.Float(string='Alto (mm)', default=30.0, required=True)

    # Estos valores se envían pero NO se muestran en la vista
    mensaje = fields.Char(string='Mensaje', default='Impresora Configurada Correctamente', readonly=True)
    codigo_estatico = fields.Char(string='Código Estático', default='ABC-001-XYZ', readonly=True)

    # Datos de la impresora (se completan al elegir en selection)
    name = fields.Char(string='Nombre', required=False, help="Nombre descriptivo de la impresora")
    direccion_ip = fields.Char(string='Dirección IP', required=False, help="Dirección IP de la impresora")
    puerto = fields.Char(string='Puerto', default='9100', help="Puerto de conexión de la impresora")

    # Lista dinámica de impresoras desde la API
    impresora_seleccionada = fields.Selection(
        selection='_get_impresoras_disponibles',
        string='Impresora Disponible',
        help="Selecciona una impresora de la lista obtenida desde la API"
    )

    es_predeterminada = fields.Boolean(
        string='Impresora Predeterminada',
        default=False,
        help="Marca esta impresora como la predeterminada del sistema"
    )

    # ==================== INTEGRACIÓN CON CONTROLADOR ====================

    def _get_controller(self):
        """Devuelve una instancia del controlador que expone consultar_api()."""
        try:
            from ..controllers.controllers import ImpresionPersonalizadaController
            return ImpresionPersonalizadaController(self.env)
        except ImportError:
            _logger.error("No se pudo importar el controlador de impresión personalizada")
            raise

    def armar_datos_configuracion(self):
        """Construye el payload de prueba para el middleware (/imprimir) con el nuevo formato.

        Estructura:
        {
          "datos_producto": {
            "nombre": str,
            "codigo_barras": str,
            "referencia_interna": str,
            "precio": number,
            "numero_lote_serial": str | None,
            "fecha_vencimiento": str | None
          },
          "cantidad": int,
          "printer_config": {"label_width_mm": int, "label_height_mm": int}
        }
        """
        self.ensure_one()
        if self.ancho_mm <= 0 or self.alto_mm <= 0:
            raise UserError("El ancho y alto deben ser mayores a 0.")

        return {
            "datos_producto": {
                "nombre": "Página de prueba",
                "codigo_barras": "TEST-0000000000",
                "referencia_interna": "TEST-PAGE",
                "precio": 0,
                # Campos opcionales pueden ser null (se serializan como null en JSON)
                "numero_lote_serial": "LOT2024-08A",
                "fecha_vencimiento": "2025-12-3",
            },
            # Para prueba imprimimos 1 etiqueta
            "cantidad": 1,
            "printer_config": {
                "label_width_mm": int(self.ancho_mm),
                "label_height_mm": int(self.alto_mm),
            },
        }

    # ==================== FUENTES DE DATOS DINÁMICAS ====================

    def _get_impresoras_disponibles(self):
        """
        Devuelve [(valor, etiqueta), ...] para el Selection, consultando /printers.
        valor = name de la impresora; etiqueta = name mostrado.
        """
        try:
            controller = self._get_controller()
            data = controller.consultar_api(endpoint_key='printers', metodo='GET', datos=None) or []
            if not isinstance(data, list):
                _logger.warning("Respuesta de /printers no es lista: %s", data)
                return [('','Seleccione una impresora...')]
            opciones = [(imp.get('name') or '', imp.get('name') or '') for imp in data if imp.get('name')]
            return opciones or [('','Seleccione una impresora...')]
        except Exception as e:
            _logger.error("Error al consultar /printers: %s", e)
            return [
                ('', 'Seleccione una impresora...'),
                ('error', 'Error al consultar impresoras - Use "Refrescar Lista API"'),
            ]

    # ==================== ACCIONES UI ====================

    def consultar_impresoras_api(self):
        """
        Refresca la lista: recarga la vista para que el Selection llame nuevamente a _get_impresoras_disponibles().
        """
        _logger.info("Refrescando lista de impresoras (reload de vista)")
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.onchange('impresora_seleccionada')
    def _onchange_impresora_seleccionada(self):
        """
        Al elegir una impresora del Selection, completa nombre y puerto con datos reales de /printers.
        """
        if self.impresora_seleccionada and self.impresora_seleccionada not in ['sin_conexion', 'vacio', 'error']:
            try:
                controller = self._get_controller()
                data = controller.consultar_api(endpoint_key='printers', metodo='GET', datos=None) or []
                if isinstance(data, list):
                    imp = next((i for i in data if i.get('name') == self.impresora_seleccionada), None)
                    if imp:
                        self.name = imp.get('name') or self.impresora_seleccionada
                        self.puerto = imp.get('port') or False
                        self.direccion_ip = False  # no forzamos IP
                        _logger.info("Actualizada impresora: name=%s port=%s ip=%s", self.name, self.puerto, self.direccion_ip)
                    else:
                        self.name = self.impresora_seleccionada
                        self.puerto = False
                        self.direccion_ip = False
                else:
                    _logger.warning("Respuesta /printers no lista en onchange: %s", data)
            except Exception as e:
                _logger.error("Error en onchange de impresora: %s", e)
                self.name = self.impresora_seleccionada
                self.puerto = False
                self.direccion_ip = False

    def imprimir_pagina_prueba(self):
        """
        Permite imprimir SOLO desde la impresora marcada como predeterminada.
        Envía el JSON de configuración al endpoint /imprimir (POST).
        """
        # Debe existir una única predeterminada
        pred = self.search([('es_predeterminada', '=', True)], limit=1)
        if not pred:
            raise UserError("Debes marcar una impresora como predeterminada antes de imprimir.")

        # La acción debe ejecutarse sobre ese registro (no sobre otro)
        if len(self) != 1 or self.id != pred.id:
            raise UserError(f"Solo la impresora predeterminada puede imprimir: {pred.name or pred.impresora_seleccionada}.")

        # Enviar al middleware
        controller = pred._get_controller()
        payload = pred.armar_datos_configuracion()
        _logger.info("POST /imprimir (predeterminada=%s) payload=%s", pred.name, payload)

        resp = controller.consultar_api(endpoint_key='imprimir', metodo='POST', datos=payload)
        _logger.info("Respuesta /imprimir: %s", resp)

        if resp is None:
            raise UserError("No se pudo enviar la configuración de prueba al middleware.")

        return True

    # ==================== LÓGICA PREDETERMINADA ====================

    def _enviar_predeterminada_automatico(self):
        """
        Enviar a /impresoras/predeterminada cuando queda marcada como predeterminada.
        """
        if self.es_predeterminada:
            try:
                controller = self._get_controller()
                # La API espera claves en español: nombre, ip, puerto (+ timestamp opcional)
                # No enviar valores False; omitir claves vacías
                impresora_data = {
                    'nombre': self.name or self.impresora_seleccionada or '',
                    'puerto': self.puerto or '',
                    'timestamp': fields.Datetime.now().isoformat(),
                }
                if self.direccion_ip:
                    impresora_data['ip'] = self.direccion_ip
                resp = controller.consultar_api(endpoint_key='default_printer', metodo='POST', datos=impresora_data)
                if resp is not None:
                    _logger.info("Predeterminada enviada a API: %s payload=%s", self.name, impresora_data)
                else:
                    _logger.warning("No se pudo enviar predeterminada a API: %s", self.name)
            except Exception as e:
                _logger.error("Error enviando predeterminada a API: %s", e)

    @api.model
    def write(self, vals):
        """
        Si se marca como predeterminada, desmarca otras y envía a la API.
        """
        res = super().write(vals)
        if vals.get('es_predeterminada'):
            # Desmarcar otras (multi-record safe)
            otras = self.search([('es_predeterminada', '=', True), ('id', 'not in', self.ids)])
            if otras:
                otras.write({'es_predeterminada': False})
            # Enviar esta como predeterminada
            self._enviar_predeterminada_automatico()
        return res

    @api.onchange('es_predeterminada')
    def _onchange_es_predeterminada(self):
        if self.es_predeterminada:
            otras = self.search([('es_predeterminada', '=', True), ('id', '!=', self.id)])
            if otras:
                nombres = ', '.join(otras.mapped('name'))
                return {
                    'warning': {
                        'title': 'Cambio de impresora predeterminada',
                        'message': f'Al marcar esta impresora como predeterminada, se desmarcará automáticamente: {nombres}'
                    }
                }

    # ==================== UTILIDADES ====================

    @api.model
    def obtener_impresora_predeterminada(self):
        return self.search([('es_predeterminada', '=', True)], limit=1)

    def verificar_consistencia_predeterminada(self):
        try:
            pred = self.search([('es_predeterminada', '=', True)])
            if len(pred) == 0:
                return {'status': 'sin_predeterminada', 'message': 'No hay impresoras predeterminadas', 'count': 0}
            if len(pred) == 1:
                return {'status': 'consistente', 'message': f'Predeterminada: {pred[0].name}', 'count': 1, 'predeterminada': pred[0].name}
            pred_keep = pred.sorted('write_date', reverse=True)[0]
            (pred - pred_keep).write({'es_predeterminada': False})
            return {
                'status': 'corregido',
                'message': f'Se mantuvo: {pred_keep.name}',
                'count': len(pred),
                'predeterminada': pred_keep.name,
                'corregidas': len(pred) - 1
            }
        except Exception as e:
            _logger.error("Error al verificar consistencia predeterminada: %s", e)
            return {'status': 'error', 'message': str(e), 'count': 0}
