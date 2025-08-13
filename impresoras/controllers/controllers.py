"""Cliente de API para el módulo Impresoras.

Centraliza las llamadas HTTP hacia el middleware/servicio externo usando
la URL base configurada en el módulo ``relex_api``.
"""

import logging
import time
from typing import Any, Optional

import requests

from odoo.addons.relex_api.constants import build_url

_logger = logging.getLogger(__name__)


class ImpresionPersonalizadaController:
    """Cliente simple para llamadas a la API externa.

    No define rutas HTTP de Odoo; solo provee utilidades de cliente.
    """

    def __init__(self, env):
        # Guardamos el env para leer parámetros de sistema al construir URLs
        self.env = env

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _get_api_url(self, endpoint_key: str) -> str:
        """Obtiene la URL completa del endpoint a partir de la clave.

        Usa ``relex_api.constants.build_url`` que combina la base con el endpoint.
        """
        if not self.env:
            raise ValueError("Falta env para construir la URL de API")
        return build_url(self.env, endpoint_key)

    # ---------------------------------------------------------
    # HTTP client
    # ---------------------------------------------------------
    def consultar_api(
        self,
        endpoint_key: str,
        metodo: str,
        datos: Optional[dict] = None,
        timeout: float = 10.0,
        reintentos: int = 2,
        backoff: float = 0.5,
    ) -> Optional[Any]:
        """Realiza una llamada HTTP a la API externa.

        - Envía/recibe JSON.
        - Reintenta ante errores transitorios de red/timeout.
        - Devuelve el JSON parseado o None si falla.
        """
        try:
            url = self._get_api_url(endpoint_key)
        except Exception as e:
            _logger.error("No se pudo construir la URL para '%s': %s", endpoint_key, e)
            return None

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Odoo-Impresoras/1.0",
        }

        metodo = (metodo or "GET").upper()
        payload = datos or {}

        for intento in range(reintentos + 1):
            try:
                if metodo == "GET":
                    _logger.info("HTTP GET %s", url)
                    resp = requests.get(url, timeout=timeout, headers=headers)
                elif metodo == "POST":
                    _logger.info("HTTP POST %s payload=%s", url, payload)
                    resp = requests.post(url, json=payload, timeout=timeout, headers=headers)
                elif metodo == "PUT":
                    _logger.info("HTTP PUT %s payload=%s", url, payload)
                    resp = requests.put(url, json=payload, timeout=timeout, headers=headers)
                elif metodo == "PATCH":
                    _logger.info("HTTP PATCH %s payload=%s", url, payload)
                    resp = requests.patch(url, json=payload, timeout=timeout, headers=headers)
                elif metodo == "DELETE":
                    _logger.info("HTTP DELETE %s payload=%s", url, payload)
                    resp = requests.delete(url, json=payload, timeout=timeout, headers=headers)
                else:
                    _logger.error("Método HTTP no soportado: %s", metodo)
                    return None

                resp.raise_for_status()

                try:
                    return resp.json()
                except ValueError:
                    _logger.error("La respuesta no es JSON válido. body=%s", resp.text[:500])
                    return None

            except (requests.ConnectionError, requests.Timeout) as e:
                _logger.warning(
                    "Fallo de red/timeout (intento %s/%s): %s",
                    intento + 1,
                    reintentos + 1,
                    e,
                )
                if intento < reintentos:
                    time.sleep(backoff * (intento + 1))
                    continue
                return None
            except requests.RequestException as e:
                status = getattr(e.response, "status_code", "sin_status")
                cuerpo = getattr(e.response, "text", "") if getattr(e, "response", None) else ""
                _logger.error(
                    "HTTP %s %s falló (status=%s): %s | body=%s",
                    metodo,
                    url,
                    status,
                    e,
                    (cuerpo or "")[:500],
                )
                return None
            except Exception as e:
                _logger.error("Error inesperado consultando API: %s", e)
                return None

        return None
