# Módulo Impresoras

Gestión centralizada de impresoras obtenidas desde un servicio externo (middleware / API) y envío de la impresora predeterminada. Incluye prueba de impresión (PDF sencillo) al endpoint remoto.

## Resumen Funcional Actual
1. Obtiene lista de impresoras (campos name / port) vía GET al endpoint configurado por constantes del módulo `relex_api`.
2. Permite seleccionar una impresora y almacenar su nombre y puerto. La IP no se genera: queda vacía (se reserva para futuras extensiones si la API la provee).
3. Garantiza que sólo haya una impresora marcada como predeterminada; al marcar una nueva, desmarca las demás.
4. Envía (POST) la impresora predeterminada al endpoint correspondiente (`default_printer`).
5. Botón adicional: envía una página PDF de prueba al endpoint (`print_pdf`).
6. Todas las llamadas HTTP se encapsulan en el controlador; el modelo no usa directamente `requests`.

## Diferencias vs README anterior
- Ya no se generan IP y puerto “por defecto”; se usa exactamente lo que devuelve la API (sólo name y port actualmente). IP permanece vacía salvo que el servicio futuro la provea.
- Nuevo botón: Imprimir Página Prueba (envía PDF mínimo embebido).
- Uso de constantes centralizadas (`build_url`, `get_api_base_url`) provistas por `relex_api` para formar URLs.
- Estructura esperada de respuesta de impresoras: lista de objetos con claves `name` y (opcional) `port`.
- Datos enviados al establecer predeterminada: nombre, ip (puede ir vacío), puerto y timestamp.

## Flujo de Uso
1. Configurar en Ajustes (relex_api) la URL base de la API (`relex_api.api_base_url`).
2. Abrir menú: Impresoras > Configuraciones.
3. Crear un registro (puede estar vacío al inicio) y pulsar “Refrescar Lista API”.
4. Elegir una impresora del desplegable (se rellena name y port; IP queda en blanco si no viene).
5. Marcar “Impresora Predeterminada” y Guardar: se envía automáticamente al endpoint remoto.
6. (Opcional) Pulsar “Imprimir Página Prueba” sólo desde la impresora marcada como predeterminada.

## Botones en Formulario
- Refrescar Lista API: vuelve a consultar lista de impresoras (`GET printers`).
- Imprimir Página Prueba: genera PDF mínimo y lo envía (`POST print_pdf`). Sólo permitido para la impresora predeterminada vigente.

## Endpoints Consumidos (vía controlador)
- GET printers → Lista de impresoras. Respuesta ejemplo:
```json
[
    {"name": "HP01", "port": "9100"},
    {"name": "ZebraZQ", "port": "9101"}
]
```
- POST default_printer → Recibe impresora predeterminada:
```json
{
    "nombre": "HP01",
    "ip": null,
    "puerto": "9100",
    "timestamp": "2025-08-11T10:25:30.123456"
}
```
- POST print_pdf (multipart form-data) → Archivo `file` (PDF test_page.pdf).

## Modelo (fields principales)
- name (Char, readonly en vista): nombre proveniente de la API.
- direccion_ip (Char, readonly): sin valor actualmente (placeholder).
- puerto (Char, readonly): puerto recibido de la API.
- impresora_seleccionada (Selection dinámico): opciones construidas desde respuesta GET.
- es_predeterminada (Boolean): unicidad garantizada vía constraint y lógica en write().

## Lógica Clave
- Selección: `onchange` busca la impresora en la respuesta fresca y rellena name / port, limpia IP.
- Unicidad predeterminada: antes de escribir, desmarca otras; luego envía a API (`default_printer`).
- Verificación y corrección: método `verificar_consistencia_predeterminada()` puede corregir múltiples marcadas.
- PDF prueba: genera bytes PDF embebidos (sin librerías externas) y los envía al endpoint centralizado.

## Controlador
Centraliza todas las peticiones externas usando `requests` y funciones `build_url` / `get_api_base_url` (proporcionadas por módulo `relex_api`). Métodos relevantes:
- `_consultar_api_externa(endpoint_key, metodo, datos)`
- `consultar_impresoras_api_externa()`
- `get_impresoras_para_selection()`
- `enviar_predeterminada_api_externa(impresora_data)`
- `enviar_pdf_prueba(pdf_bytes, filename)`

## Dependencias
- Odoo base
- Módulo interno: `relex_api` (constantes y parámetros de configuración)
- Librería Python: `requests`

## Instalación / Actualización
```powershell
pip install requests
python odoo-bin -c odoo.conf -d <db> -i impresoras
# Actualizar después de cambios
python odoo-bin -c odoo.conf -d <db> -u impresoras
```

## Restricciones y Validaciones
- Sólo una impresora predeterminada (constraint + lógica write()).
- Botón de impresión de prueba exige que el registro sea la impresora predeterminada vigente.
- Manejo de errores con notificaciones y logging (`_logger`).

## Manejo de Errores (Mensajes Comunes)
- Sin conexión a API: opción 'sin_conexion' en Selection con mensaje instructivo.
- Error al consultar impresoras: opción 'error'.
- Intento de imprimir prueba en una no predeterminada: UserError claro.

## Extensión Futuras (Sugerido)
- Añadir soporte para campo IP real cuando la API lo exponga.
- Endpoint propio para exponer impresora predeterminada hacia terceros.
- Cache local / cron para refrescar lista periódica.
- Log de auditoría de cambios de impresora predeterminada.

## Ejemplo de Uso Rápido
1. Configurar parámetro `relex_api.api_base_url` (ej: http://localhost:8080/api ).
2. Instalar módulo `relex_api` y luego `impresoras`.
3. Abrir Impresoras > Configuraciones, crear registro, refrescar lista.
4. Seleccionar impresora, marcar predeterminada, guardar.
5. Pulsar “Imprimir Página Prueba”.

## Notas
- El campo IP está previsto para ampliaciones: hoy se deja intencionalmente vacío.
- No se generan datos sintéticos: se refleja exactamente lo retornado por la API.
- El PDF de prueba es minimalista (bytes embebidos) para evitar dependencias adicionales.

---
Documento actualizado para reflejar el estado funcional al 11/08/2025.
