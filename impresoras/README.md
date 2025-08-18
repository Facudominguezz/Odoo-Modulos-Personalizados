# Impresoras

Centraliza llamadas HTTP a un servicio/middleware externo usando la URL base y utilidades provistas por el módulo `relex_api`.

## Descripción
Este módulo expone un cliente simple (no define rutas HTTP de Odoo) para consumir la API externa:
- Construye URLs con `relex_api.constants.build_url(env, endpoint_key)`.
- Soporta métodos: GET, POST, PUT, PATCH, DELETE.
- Envía/recibe JSON.
- Maneja reintentos ante fallos transitorios de red/timeout (con backoff incremental).
- Registra eventos y errores con `_logger`.

## Requisitos
- Python: biblioteca `requests`.
- Módulo interno: `relex_api` (provee `build_url` y configuración de base URL).

## Configuración
- Configura la URL base de la API y el mapeo de endpoints en el módulo `relex_api` (parámetros/constantes que usa `build_url`).
- Este cliente no añade autenticación por defecto. Si la API requiere tokens/cabeceras personalizadas, ajusta el cliente antes de enviar la petición.

## Uso
Ejemplo de invocación desde código Odoo:

```python
from odoo import models
from odoo.addons.impresoras.controllers.controllers import ImpresionPersonalizadaController

class MiModelo(models.Model):
    _name = "mi.modelo"

    def _llamar_api_externa(self):
        ctrl = ImpresionPersonalizadaController(self.env)
        resp = ctrl.consultar_api(
            endpoint_key="MI_ENDPOINT",   # clave que reconoce relex_api.build_url
            metodo="POST",
            datos={"foo": "bar"},
            timeout=10.0,
            reintentos=2,
            backoff=0.5,
        )
        if resp is None:
            # Manejo de error
            return
        return resp
```

Notas:
- GET: actualmente no envía parámetros ni `datos` en querystring; si necesitas params, añádelos en la URL del endpoint o extiende el cliente.
- La respuesta debe ser JSON válido; en caso contrario, se retorna `None`.

## Comportamiento y errores
- Intentos totales: 1 intento inicial + `reintentos` ante `ConnectionError`/`Timeout` (espera `backoff * (intento + 1)` entre reintentos).
- Errores HTTP no exitosos (`raise_for_status`) generan log y retornan `None`.
- Si la respuesta no es JSON válido, se loguea y retorna `None`.
- Si `env` no está disponible para construir la URL, se loguea y retorna `None`.

## Registro (logging)
- Se registran método, URL y (en su caso) payload. Evita incluir datos sensibles en `datos` o ajusta el logging si es necesario.
- En errores, se loguea el cuerpo truncado (hasta 500 caracteres).

---
Última actualización: 18/08/2025.
