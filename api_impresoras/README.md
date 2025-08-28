# Módulo `api_impresoras`

Configuración y utilidades centrales para consumir servicios externos (middleware) relacionados con impresoras u otros servicios Relex. Proporciona:

- Parámetro global de URL base de la API (por compañía) configurable en Ajustes.
- Construcción segura de endpoints mediante funciones auxiliares (`build_url`, `get_api_base_url`).
- Catálogo único de endpoints estándar usados por otros módulos (p.ej. módulo `impresoras`).
- Aislamiento: los módulos consumidores no codifican URLs estáticas, sólo claves lógicas.

## Objetivo
Estandarizar cómo los módulos Odoo internos acceden a la API externa, evitando duplicación de lógica y facilitando cambios futuros (p.ej. versionado de API, cambio de dominio, nuevos endpoints).

## Funcionalidad Actual
1. Campo de configuración en `Ajustes > General Settings > Integrations`: API Base URL.
2. Parámetro del sistema: `api_impresoras.api_base_url` (almacenado en `ir.config_parameter`).
3. Función `get_api_base_url(env)` devuelve la URL base configurada (string o None).
4. Función `build_url(env, key)` combina la base con el endpoint asociado a `key`.
5. Diccionario interno de endpoints (centralizado en `constants.py`).

## Endpoints Definidos
Clave → Ruta relativa final:
- `root` → `/`
- `printers` → `/printers` (lista de impresoras disponibles)
- `default_printer` → `/impresora/predeterminada` (recepción de impresora predeterminada)
- `print_pdf` → `/print-pdf` (recepción de PDF para impresión)

Ejemplo (si `API Base URL` = `http://localhost:8080/api`):
- build_url(env, 'printers') → `http://localhost:8080/api/printers`
- build_url(env, 'default_printer') → `http://localhost:8080/api/impresora/predeterminada`
- build_url(env, 'print_pdf') → `http://localhost:8080/api/print-pdf`

## Instalación
Dependencias declaradas:
- Odoo: `base`, `base_setup`
- Python: `requests` (por coherencia con módulos consumidores)

Instalar:
```powershell
pip install requests
python odoo-bin -c odoo.conf -d <db> -i api_impresoras
```

Actualizar tras cambios:
```powershell
python odoo-bin -c odoo.conf -d <db> -u api_impresoras
```

## Configuración
1. Ir a Ajustes (Settings) con permisos de administrador.
2. Localizar bloque Integrations.
3. Campo: “Impresoras - API Base URL”. Ejemplo: `http://localhost:8080/api` (sin slash final opcional; la función lo normaliza).
4. Guardar. El parámetro se almacena como `api_impresoras.api_base_url`.

## Uso en Otros Módulos
Importar utilidades:
```python
from odoo.addons.api_impresoras.constants import build_url, get_api_base_url

api_base = get_api_base_url(env)               # -> 'http://localhost:8080/api'
printers_url = build_url(env, 'printers')      # -> 'http://localhost:8080/api/printers'
```

Manejo de errores (clave inexistente):
`build_url` lanza `KeyError` si la clave no está definida. En módulos consumidores se recomienda capturarla y registrar log.

## Buenas Prácticas para Módulos Consumidores
- NO concatenar manualmente rutas; siempre usar `build_url`.
- Validar que `get_api_base_url` retorne un valor antes de hacer llamadas HTTP.
- Centralizar cualquier lógica adicional (tokens, headers comunes) en este módulo para mantener consistencia.
- Añadir nuevas claves de endpoint ampliando el diccionario interno y actualizando este README.

## Ejemplo Integrado (Fragmento real del módulo `impresoras`)
```python
endpoint_url = build_url(request.env, 'print_pdf')
resp = requests.post(endpoint_url, files={'file': (filename, pdf_bytes, 'application/pdf')}, timeout=30)
```

## Extensiones Futuras Sugeridas
- Gestión de autenticación (token / OAuth) con almacenamiento en parámetros seguros.
- Versionado de endpoints (e.g. `/v2/`) controlado por campo adicional.
- Health check programado que valide conectividad y registre métricas.
- Cache ligero con TTL para metadata general.

## Troubleshooting Rápido
- Valor None / vacío: configurar `API Base URL` en Ajustes.
- URL duplicada (doble slash): `urljoin` ya normaliza; revisar sólo que no haya espacios.
- KeyError en `build_url`: revisar nombre de la clave y que exista en `constants.py`.

## Referencia de Código
- Archivo: `constants.py` (funciones y endpoints)
- Vista: `views/res_config_settings_views.xml` (inserta campo en bloque Integrations)
- Modelo extendido: `models/res_config_settings.py`

## Seguridad
Actualmente no maneja tokens ni credenciales; cualquier autenticación futura deberá:
- Evitar almacenar secretos en texto plano en código.
- Usar parámetros del sistema (`ir.config_parameter` encriptados si es necesario).
- Limitar acceso al ajuste sólo a usuarios con permisos de configuración.

## Notas
- El módulo por sí solo no realiza llamadas HTTP; delega esa responsabilidad a consumidores (ej: `impresoras`).
- Mantener este README sincronizado al agregar o cambiar endpoints.

---
Estado de documentación al 11/08/2025.
