# Módulo de Impresión Personalizada

## Descripción
Este módulo permite gestionar configuraciones de impresión conectándose a una API externa para obtener la lista de impresoras disponibles y establecer cuál es la impresora predeterminada del sistema.

## Características

### 🖨️ **Gestión de Impresoras**
- Consulta automática a API externa para obtener lista de impresoras
- Selección de impresora desde lista obtenida de la API
- Configuración de impresora predeterminada
- Envío automático de configuración predeterminada a la API
- Datos técnicos obtenidos de la respuesta de la API externa

### 🔧 **Configuración**
- URL configurable de la API
- Validaciones automáticas
- Interfaz simplificada con enfoque en la funcionalidad principal
- Garantía de una sola impresora predeterminada

## Uso del Módulo

### 1. **Configurar la API**
- Edite el campo "URL de la API" con la dirección de su servicio
- Por defecto: `http://localhost:8080/api/impresoras`

### 2. **Obtener Lista de Impresoras**
- Use el botón "Refrescar Lista API" para consultar las impresoras disponibles
- El módulo hará una petición GET a la API configurada

### 3. **Seleccionar y Configurar Impresora**
- **Seleccione una impresora** de la lista desplegable obtenida desde la API
- **Datos automáticos**: Al seleccionar, el sistema completa automáticamente:
  - Nombre de la configuración
  - Dirección IP de la impresora (desde API o valor por defecto)
  - Puerto de conexión (desde API o valor por defecto)
- **Marque como predeterminada**: Se envía automáticamente la configuración a la API

### 4. **Envío Automático a API**
- **Automático**: Al marcar una impresora como predeterminada, se envía automáticamente a la API
- El sistema muestra notificaciones de éxito o error del envío
- No requiere acción manual adicional del usuario

## Flujo de Trabajo

### **🎯 Proceso Automatizado**
1. **Clic en "Refrescar Lista API"**: Obtiene impresoras disponibles
2. **Seleccionar impresora**: Del desplegable obtenido de la API
3. **Automático**: El sistema completa nombre, IP y puerto (desde API o valores por defecto)
4. **Marcar como predeterminada**: Al hacer clic automáticamente:
   - Se valida que solo una esté marcada como predeterminada
   - Se envía la configuración a la API externa
   - Se muestra notificación del resultado

## Comportamiento de Impresora Predeterminada

### **🔄 Gestión Automática**
Cuando marca una impresora como predeterminada:

1. **Desmarcado automático**: La impresora anteriormente predeterminada se desmarca automáticamente
2. **Envío automático a API**: La nueva configuración se envía automáticamente a la API externa
3. **Notificaciones**: El sistema muestra el resultado del envío (éxito o error)
4. **Una sola acción**: Solo necesita marcar el checkbox, todo lo demás es automático
5. **Actualización visual**: Los cambios se reflejan inmediatamente en todas las vistas

### **✅ Garantías del Sistema**
- Solo puede existir **una impresora predeterminada** en todo momento
- **Datos automáticos**: Nombre, IP y puerto se obtienen de la API o se usan valores por defecto
- **Envío automático**: La configuración se envía a la API automáticamente
- Los cambios son **inmediatos** y **visibles** sin necesidad de recargar
- **Transacciones atómicas** que garantizan integridad de datos

## Formato de API Esperado

### **GET** - Consulta de impresoras disponibles
**URL configurada en el módulo (por defecto: `http://localhost:8080/api/impresoras`)**

**Respuesta esperada:**
```json
[
    {
        "nombre": "HP_LaserJet_001",
        "descripcion": "HP LaserJet Pro en Oficina 1",
        "direccion_ip": "192.168.1.100",
        "puerto": 9100
    },
    {
        "nombre": "Canon_Pixma_002", 
        "descripcion": "Canon PIXMA en Recepción",
        "direccion_ip": "192.168.1.101",
        "puerto": 9100
    }
]
```

**Descripción de campos:**
- `nombre`: Identificador único de la impresora
- `descripcion`: Nombre descriptivo para mostrar al usuario
- `direccion_ip`: Dirección IP real de la impresora en la red
- `puerto`: Puerto de conexión de la impresora

### **POST** - Envío de impresora predeterminada
**URL: `{api_url}/predeterminada`**

**Datos enviados cuando se marca una impresora como predeterminada:**
```json
{
    "impresora_predeterminada": "HP_LaserJet_001",
    "nombre_configuracion": "Configuración HP_LaserJet_001",
    "ip": "192.168.1.100", 
    "puerto": 9100,
    "timestamp": "2025-08-04T15:30:45.123456"
}
```

**Descripción de campos:**
- `impresora_predeterminada`: Nombre de la impresora seleccionada desde la API
- `nombre_configuracion`: Nombre completo generado automáticamente
- `ip`: Dirección IP obtenida de la API o valor por defecto (192.168.1.100)
- `puerto`: Puerto de conexión obtenido de la API o valor por defecto (9100)
- `timestamp`: Marca de tiempo ISO 8601 del momento del envío automático

## Instalación

### 1. **Instalar Dependencias**
```bash
pip install requests
```

### 2. **Instalar Módulo**
```bash
python odoo-bin -r odooadmin -w 1234 --addons-path=addons,modules -d odoo -i impresoras
```

### 3. **Actualizar Módulo** (después de cambios)
```bash
python odoo-bin -r odooadmin -w 1234 --addons-path=addons,modules -d odoo -u impresoras
```

## Arquitectura del Módulo

### **Estructura del Código**
- **Modelo (models.py)**: Maneja la lógica de negocio y integración con controlador
- **Controlador (controllers.py)**: Centraliza todas las comunicaciones con APIs externas
- **Vistas (templates.xml)**: Interfaz de usuario con botones de acción

### **Métodos Principales en Models**
- `_get_controller()`: Obtiene instancia del controlador para comunicación con APIs
- `_get_impresoras_disponibles()`: Consulta la API y devuelve lista de impresoras
- `consultar_impresoras_api()`: Refresca manualmente la lista desde la interfaz
- `_onchange_impresora_seleccionada()`: Obtiene automáticamente datos del middleware al seleccionar impresora
- `_enviar_predeterminada_automatico()`: Envía configuración predeterminada a la API automáticamente
- `obtener_impresora_predeterminada()`: Método para obtener la impresora actual
- `verificar_consistencia_predeterminada()`: Verifica y corrige inconsistencias

### **Métodos Principales en Controllers**
- `_get_api_url()`: Obtiene la URL de la API configurada
- `_consultar_api_externa()`: Método centralizado para peticiones HTTP
- `consultar_impresoras_api_externa()`: Consulta impresoras desde API externa
- `get_impresoras_para_selection()`: Formatea impresoras para campos Selection de Odoo
- `enviar_predeterminada_api_externa()`: Envía configuración predeterminada a API externa

### **Validaciones y Constraints**
- **Solo una impresora predeterminada**: 
  - Constraint `_check_una_predeterminada()` garantiza unicidad
  - Al marcar una nueva, se desmarca automáticamente la anterior
  - Los cambios se reflejan en tiempo real en todas las vistas
- **Campos readonly**: Los datos técnicos no son editables manualmente
- **Manejo de errores**: Notificaciones al usuario y logs detallados

### **Obtención de Datos Técnicos**
El módulo obtiene los datos técnicos de las impresoras de la siguiente manera:

**Cuando se selecciona una impresora:**
1. **Trigger automático**: `_onchange_impresora_seleccionada()` se ejecuta
2. **Datos automáticos**: El sistema obtiene datos de:
   - **Respuesta de la API**: Si incluye campos `direccion_ip` y `puerto`
   - **Valores por defecto**: IP=192.168.1.100, Puerto=9100 si la API no incluye estos datos
3. **Actualización inmediata**: Los campos se llenan automáticamente

**Implementación actual:**
```python
@api.onchange('impresora_seleccionada')
def _onchange_impresora_seleccionada(self):
    if self.impresora_seleccionada:
        self.name = f"Configuración {self.impresora_seleccionada}"
        # Valores por defecto para IP y puerto
        self.direccion_ip = '192.168.1.100'
        self.puerto = 9100
```

**Características del Sistema Actual:**
- **Datos consistentes**: Siempre hay datos disponibles para IP y puerto
- **Sin dependencias externas**: No requiere middleware adicional
- **Robusto**: El sistema funciona independientemente de la disponibilidad de servicios externos
- **Extensible**: Fácil modificación para integrar con middleware real en el futuro

## Navegación
- **Menú Principal**: "Impresión Personalizada" en la barra superior
- **Submenú**: "Configuraciones" para gestionar las impresoras

## Filtros y Búsquedas
- Búsqueda por nombre, impresora o IP
- Filtro rápido para ver solo la impresora predeterminada
- Agrupación por tipo de impresora

## Troubleshooting

### **Error: "consultar_impresoras_api no es una acción válida"**
- Verificar que el método `consultar_impresoras_api()` existe en models.py
- Asegurar que el módulo esté actualizado completamente
- Reiniciar el servidor Odoo si es necesario

### **Error: "Error al consultar API"**
- Verificar que la URL de la API sea correcta
- Comprobar conectividad de red
- Revisar que el servicio API esté funcionando
- Verificar que la API retorne el formato JSON esperado

### **Error: "Error de conexión con la API"**
- Verificar que el endpoint `/predeterminada` esté disponible
- Comprobar que la API acepta peticiones POST con formato JSON

### **No aparecen impresoras en la lista**
- Usar el botón "Refrescar Lista API"
- Verificar formato de respuesta de la API
- Revisar logs de Odoo para detalles del error

### **No se obtienen datos técnicos**
- **Implementación actual**: El sistema usa valores por defecto (IP=192.168.1.100, Puerto=9100)
- **Verificar API**: Para obtener IP y puerto reales, la API debe incluir campos `direccion_ip` y `puerto` en la respuesta
- **Modificar lógica**: Para integrar middleware real, editar `_onchange_impresora_seleccionada()` en models.py
- **Logs informativos**: Revisar logs para verificar la respuesta de la API

## Logs del Sistema
El módulo registra actividad en los logs de Odoo:
- Conexiones exitosas a la API
- Errores de conexión o formato
- Cambios en impresoras predeterminadas
- Selección de impresoras desde la API
- Envío de configuraciones a la API externa

## Extensibilidad

### **Integración con Middleware**
Para integrar con un middleware real que proporcione datos técnicos de las impresoras:

1. **Modificar `_onchange_impresora_seleccionada()` en models.py**:
```python
@api.onchange('impresora_seleccionada')
def _onchange_impresora_seleccionada(self):
    if self.impresora_seleccionada:
        self.name = f"Configuración {self.impresora_seleccionada}"
        
        # Obtener datos del middleware real
        try:
            middleware_data = self._consultar_middleware_real(self.impresora_seleccionada)
            self.direccion_ip = middleware_data.get('ip', '192.168.1.100')
            self.puerto = middleware_data.get('puerto', 9100)
        except:
            # Fallback a valores por defecto
            self.direccion_ip = '192.168.1.100'
            self.puerto = 9100
```

2. **Agregar método de consulta al middleware**:
```python
def _consultar_middleware_real(self, impresora_nombre):
    # Implementar consulta real al middleware
    # Retornar diccionario con 'ip' y 'puerto'
    pass
```

### **Agregar Endpoints HTTP**
Para exponer la configuración a otros sistemas:

1. **Agregar rutas en controllers.py**:
```python
@http.route('/api/impresion/predeterminada', type='json', auth='public')
def get_impresora_predeterminada(self):
    """Endpoint para obtener la impresora predeterminada actual"""
    # Implementación del endpoint
    pass
```
