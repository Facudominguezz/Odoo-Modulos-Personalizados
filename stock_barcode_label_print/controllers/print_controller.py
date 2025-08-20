# -*- coding: utf-8 -*-
import logging
from typing import Any, Optional

import requests
from odoo import http
from odoo.http import request

# Reuso del cliente HTTP del módulo impresoras (si está instalado)
Cliente: Optional[Any] = None
try:
    from odoo.addons.impresoras.controllers.controllers import (
        ImpresionPersonalizadaController as Cliente,  # type: ignore
    )
except Exception:  # pragma: no cover
    Cliente = None

# Reuso de utilidades relex_api para URLs
try:
    from odoo.addons.relex_api.constants import build_url  # type: ignore
except Exception:  # pragma: no cover
    build_url = None  # type: ignore

_logger = logging.getLogger(__name__)


class BarcodeLabelPrintController(http.Controller):
    """Endpoint JSON que recibe el payload desde la UI de Barcode y lo reenvía al middleware."""

    @http.route("/barcode_label_print/print", type="json", auth="user")
    def barcode_label_print(self, **payload):
        """
        Espera un JSON como:
        {
          "product_data": {...},
          "printer_config": {...},
          "quantity": 1
        }
        """
        env = request.env

        # Completar la configuración de impresora desde el módulo 'impresoras'.
        # No confiamos en lo que venga del frontend.
        try:
            pred = env["impresoras"].sudo().search([("es_predeterminada", "=", True)], limit=1)
        except Exception:  # si el modelo no existe por algún motivo
            pred = env["impresoras"]

        if not pred:
            return {
                "ok": False,
                "message": "No hay una impresora predeterminada configurada. Configure una en el módulo Impresoras.",
            }

        # Configuración de etiqueta solicitada por el middleware (solo dimensiones)
        printer_config = {
            # dimensiones en milímetros
            "ancho_mm": int(pred.ancho_mm or 0),
            "alto_mm": int(pred.alto_mm or 0),
        }

        # Normalizar payload y evitar llaves duplicadas entre ES/EN
        payload = dict(payload or {})

        # Mapear datos de producto y normalizarlos a claves ES requeridas por el middleware
        raw_pd = payload.get("datos_producto") or payload.get("product_data") or {}
        # Aceptamos claves ES y, si vienen en EN, las convertimos
        datos_producto = {
            "nombre": raw_pd.get("nombre") or raw_pd.get("name"),
            "codigo_barras": raw_pd.get("codigo_barras") or raw_pd.get("barcode"),
            "referencia_interna": raw_pd.get("referencia_interna") or raw_pd.get("default_code") or raw_pd.get("internal_reference"),
            "precio": raw_pd.get("precio") if raw_pd.get("precio") is not None else raw_pd.get("price"),
            # Estos campos pueden ser null; no los forzamos a string
            "numero_lote_serial": raw_pd.get("numero_lote_serial") or raw_pd.get("lot_serial_number") or raw_pd.get("lot") or raw_pd.get("serial"),
            "fecha_vencimiento": raw_pd.get("fecha_vencimiento") or raw_pd.get("expiration_date") or raw_pd.get("use_date"),
        }

        # Mapear cantidad: preferir EN, fallback ES
        quantity = payload.get("cantidad")
        if quantity is None:
            quantity = payload.get("quantity")
        try:
            if quantity is not None:
                quantity = int(quantity)
        except Exception:
            quantity = None

        # Construir payload final EXACTO requerido por el middleware
        out_payload = {
            "datos_producto": datos_producto,
            "config_impresora": printer_config,
        }
        if quantity is not None:
            out_payload["cantidad"] = quantity
        
        # Si existe el cliente de 'impresoras', lo usamos (centraliza timeouts/reintentos/headers)
        if Cliente:
            try:
                client = Cliente(env)
                resp = client.consultar_api(
                    endpoint_key="imprimir", metodo="POST", datos=out_payload
                )
                if resp is None:
                    return {"ok": False, "message": "Fallo al enviar a middleware (consultar_api)"}
                return {"ok": True, "result": resp}
            except Exception as e:  # pragma: no cover
                # Mensaje claro cuando falta API Key / URL base u otros errores
                msg = str(e) or "Error al enviar al middleware. Verifique configuración Relex API."
                _logger.exception("Error usando cliente impresoras: %s", msg)
                return {"ok": False, "message": msg}