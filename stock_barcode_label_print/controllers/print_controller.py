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

        printer_config = {
            # nombre obtenido del registro predeterminado
            "printer_name": pred.name or "",
            # dimensiones en milímetros
            "label_width_mm": int(pred.ancho_mm or 0),
            "label_height_mm": int(pred.alto_mm or 0),
        }

        payload = dict(payload or {})
        payload["printer_config"] = printer_config
    # Si existe el cliente de 'impresoras', lo usamos (centraliza timeouts/reintentos/headers)
        if Cliente:
            try:
                client = Cliente(env)
                resp = client.consultar_api(
                    endpoint_key="print_pdf", metodo="POST", datos=payload
                )
                if resp is None:
                    return {"ok": False, "message": "Fallo al enviar a middleware (consultar_api)"}
                return {"ok": True, "result": resp}
            except Exception as e:  # pragma: no cover
                _logger.exception("Error usando cliente impresoras: %s", e)
                return {"ok": False, "message": str(e)}

        # Fallback liviano: llamada directa usando relex_api
        if not build_url:
            return {"ok": False, "message": "No se puede construir URL (relex_api no presente)"}
        try:
            url = build_url(env, "print_pdf")
            r = requests.post(url, json=payload, timeout=15)
            r.raise_for_status()
            return {"ok": True, "result": r.json()}
        except Exception as e:  # pragma: no cover
            _logger.exception("Error enviando a middleware (fallback): %s", e)
            return {"ok": False, "message": str(e)}
