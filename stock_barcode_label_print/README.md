# Stock Barcode Label Print (Odoo 18)

Botón “Imprimir” en la UI de Código de Barras (recepciones/pickings) que arma un JSON con los datos de la línea y lo reenvía a un middleware de impresión. No requiere vistas adicionales: se integra en los botones superiores de cada línea.

## Compatibilidad y dependencias
- Odoo 18 (Enterprise) – integra con `stock_barcode` (OWL/JS).
- Depende de:
  - `relex_api` (URL base y utilidades `build_url`).
  - `impresoras` (opcional: cliente HTTP genérico para llamadas al middleware; no gestiona impresoras predeterminadas ni tamaños de etiqueta).
- Python: `requests` (ya declarado por los módulos).

## Qué hace
- Inyecta un botón con ícono de impresora sobre cada línea del escáner de códigos de barras.
- Al hacer clic, construye un payload con:
  - Datos del producto y del lote/serie (incluye `expiration_date`).
  - Cantidad a imprimir (respeta tracking: serial imprime 1).
- En el backend:
  - Reenvía el JSON al middleware usando el cliente HTTP de `impresoras` o, en su defecto, `requests` con `build_url`.
  - La selección de impresora y las dimensiones de etiqueta NO las gestiona este módulo; deben definirse en tu backend o resolverse en el middleware.

## Instalación
1) Instalar/configurar dependencias:
- `relex_api` (Ajustes → Integrations → “Impresoras - API Base URL”).
- Opcional: `impresoras` (solo si deseas reutilizar su cliente HTTP genérico).

2) Instalar este módulo `stock_barcode_label_print`.

3) Actualizar (para recompilar assets) y recargar el navegador:
```powershell
. .venv\Scripts\Activate.ps1
python odoo-bin -c odoo.conf -d <db> -u stock_barcode_label_print
# En el navegador: abrir /web?debug=assets y hacer Hard Reload (Ctrl+F5)
```

## Uso
- Ir a Inventario → Código de barras → abrir una operación.
- En cada línea verás un botón con ícono de impresora en la franja superior.
- Clic en “Imprimir” para enviar el trabajo al middleware.

## Flujo técnico
### Frontend (OWL/JS)
- Hereda la plantilla `stock_barcode.LineUpperButtons` para insertar el botón.
- Parchea el componente `LineComponent` agregando `onPrintLabel()`.
- Construcción del payload (resumen):
  - `product_data`:
    - `name`, `barcode`, `internal_reference`, `price` (si está disponible).
    - `lot_serial_number` (si tracking ≠ none).
  - `expiration_date`: prioridad `line.expiration_date`, si no existe toma `lot_id.expiration_date` o `lot_id.use_date`.
  - `quantity`: si tracking = serial → 1; si no, utiliza cantidad hecha o remanente.
  - `printer_config`: el frontend puede enviarlo si ya lo conoce; este módulo no lo completa automáticamente.
- Llamada al servidor vía `rpc("/barcode_label_print/print", payload)` o la ruta que implementes.

### Backend (Controlador HTTP JSON)
- Ruta sugerida: `/barcode_label_print/print` (`auth="user"`).
- Recibe el payload del frontend y, si aplica, lo complementa (por ejemplo `printer_config`) según tu lógica.
- Envía al middleware usando:
  - Preferido: cliente HTTP del módulo `impresoras` (`ImpresionPersonalizadaController.consultar_api(...)`).
  - Alternativa: `requests.post(build_url(env, "print_pdf"), json=payload)`.

## Contrato de datos (referencia)
Solicitud (el backend puede añadir `printer_config` si tu integración lo requiere):
```json
{
  "product_data": {
    "name": "Producto X",
    "barcode": "0123456789012",
    "internal_reference": "INT-001",
    "price": 0,
    "lot_serial_number": "L-0001",
    "expiration_date": "2025-08-24 14:43:28"
  },
  "printer_config": {},  // opcional, definido por tu backend/middleware
  "quantity": 1
}
```
Respuesta esperada del middleware (ejemplo):
```json
{ "status": "ok" }
```
El controlador reenvía el cuerpo recibido; si falla la llamada devuelve `{ ok: false, message: "..." }` al frontend.

## Configuración necesaria
- Ajustes → Integrations → “Impresoras - API Base URL” (módulo `relex_api`).
- `impresoras` NO es obligatorio; si lo instalas, úsalo sólo como cliente HTTP. La lógica de impresora predeterminada/dimensiones depende de tu implementación o del middleware.

## Extensiones sugeridas
- Enviar `copies` cuando tracking = serial y la cantidad escaneada > 1.
- Registrar bitácora de impresiones (modelo simple) y añadir traducciones.
- Exponer endpoint para consultar y/o seleccionar impresora si tu caso lo requiere.

## Licencia y autoría
- Licencia: LGPL-3
- Autor: Reswoy
- Enviar `copies` cuando tracking = serial y la cantidad escaneada > 1.
- Registrar bitácora de impresiones (modelo simple) y añadir traducciones.
- Exponer endpoint para consultar la impresora predeterminada actual.

## Licencia y autoría
- Licencia: LGPL-3
- Autor: Reswoy
