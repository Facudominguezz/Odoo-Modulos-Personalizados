# Flujo de Desarrollo en Odoo

## 1. Estructura del Proyecto

```
odoo/
├── addons/                 # Módulos oficiales de Odoo
├── modules/                # Módulos personalizados
│   └── mi_modulo_personalizado/
│       ├── __manifest__.py    # Archivo de configuración del módulo
│       ├── __init__.py        # Inicialización del módulo
│       ├── controllers/       # Controladores web y API
│       │   └── controllers.py
│       ├── data/             # Datos iniciales del módulo
│       │   └── data.xml
│       ├── i18n/             # Archivos de traducción
│       │   ├── es.po
│       │   └── en.po
│       ├── models/           # Modelos y lógica de negocio
│       │   └── models.py
│       ├── security/         # Permisos y grupos de seguridad
│       │   ├── ir.model.access.csv
│       │   └── security_groups.xml
│       ├── static/           # Contenido estático (CSS, JS, imágenes)
│       │   ├── src/
│       │   │   ├── css/
│       │   │   ├── js/
│       │   │   └── img/
│       │   └── description/
│       │       └── icon.png
│       ├── views/            # Vistas de la interfaz de usuario
│       │   ├── templates.xml
│       │   └── views.xml
│       └── wizard/           # Ventanas emergentes (pop-ups)
│           ├── __init__.py
│           ├── wizard_model.py
│           └── wizard_views.xml
├── odoo-bin               # Script principal de Odoo
└── odoo.conf              # Archivo de configuración
```

## 2. Descripción Detallada de Carpetas

### 📁 **__manifest__.py**
**El archivo más importante del módulo**
- Define todas las características y componentes del módulo
- Especifica nombre, versión, descripción y dependencias
- Lista todos los archivos que se cargarán (vistas, datos, seguridad, etc.)
- Es el archivo que identifica una carpeta como un módulo válido de Odoo

```python
{
    'name': 'Mi Módulo Personalizado',
    'version': '17.0.1.0.0',
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'wizard/wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mi_modulo/static/src/css/style.css',
            'mi_modulo/static/src/js/custom.js',
        ],
    },
    'installable': True,
    'application': True,
}
```

### 📁 **controllers/**
**Controladores de aplicación para interacciones frontend-backend**
- Maneja peticiones HTTP desde páginas web hacia el backend
- Procesa formularios enviados desde la interfaz web
- Crea APIs para comunicación externa
- Gestiona búsquedas y filtros desde la página web
- Punto de entrada para todas las interacciones web

```python
from odoo import http
from odoo.http import request

class MiControlador(http.Controller):
    
    @http.route('/mi_modulo/api/datos', type='json', auth='user')
    def obtener_datos(self, **kwargs):
        # Lógica para procesar petición AJAX
        return {'status': 'success', 'data': []}
    
    @http.route('/mi_modulo/formulario', type='http', auth='public')
    def procesar_formulario(self, **post):
        # Procesar datos de formulario web
        return request.render('mi_modulo.template_respuesta')
```

### 📁 **data/**
**Registros que se crean automáticamente al instalar el módulo**
- Datos iniciales para poblar el módulo (ej: catálogo de vehículos, productos)
- Acciones del servidor y ventanas predefinidas
- Acciones periódicas (cron jobs)
- Configuraciones por defecto del sistema
- Cualquier registro que debe existir desde la instalación

```xml
<odoo>
    <data>
        <!-- Registros de ejemplo que se crean al instalar -->
        <record id="vehiculo_toyota" model="catalogo.vehiculos">
            <field name="name">Toyota Corolla</field>
            <field name="marca">Toyota</field>
            <field name="año">2024</field>
        </record>
        
        <!-- Acción programada -->
        <record id="cron_limpieza_logs" model="ir.cron">
            <field name="name">Limpieza de Logs</field>
            <field name="model_id" ref="model_mi_modulo_logs"/>
            <field name="code">model.limpiar_logs_antiguos()</field>
            <field name="interval_number">1</field>
            <field name="interval_type">days</field>
        </record>
    </data>
</odoo>
```

### 📁 **i18n/**
**Archivos de traducciones y multilenguaje**
- Permite traducir toda la interfaz a diferentes idiomas
- Traduce mensajes de error y validación
- Convierte etiquetas de campos y botones
- Localiza textos mostrados al usuario
- Archivos .po para cada idioma soportado

```po
# Archivo es.po (Español)
msgid "Customer Name"
msgstr "Nombre del Cliente"

msgid "This field is required"
msgstr "Este campo es obligatorio"

msgid "Save Changes"
msgstr "Guardar Cambios"
```

### 📁 **models/**
**Modelos y toda la lógica de negocio del módulo**
- Contiene clases que heredan de `models.Model`
- Define la estructura de datos (campos y atributos)
- Implementa métodos y funciones de negocio
- Establece validaciones y restricciones
- **Aquí está el corazón de la aplicación**

```python
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MiModelo(models.Model):
    _name = 'mi.modelo'
    _description = 'Descripción del Modelo'
    
    name = fields.Char('Nombre', required=True)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado')
    ], default='borrador')
    
    @api.constrains('name')
    def _check_name(self):
        if len(self.name) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres")
    
    def confirmar_registro(self):
        self.estado = 'confirmado'
```

### 📁 **security/**
**Permisos, reglas de registro y grupos de usuarios**
- Define quién puede crear, leer, escribir o eliminar registros
- Establece grupos de usuarios con diferentes niveles de acceso
- Configura reglas de registro para filtrar datos por usuario
- Controla el acceso a funcionalidades específicas del módulo

```csv
# ir.model.access.csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_mi_modelo_user,mi.modelo.user,model_mi_modelo,base.group_user,1,1,1,0
access_mi_modelo_manager,mi.modelo.manager,model_mi_modelo,group_mi_modelo_manager,1,1,1,1
```

### 📁 **static/**
**Contenido estático del proyecto**
- **CSS**: Hojas de estilo para personalizar la apariencia
- **JavaScript**: Funcionalidad dinámica de la interfaz
- **Imágenes**: Iconos, logos y recursos gráficos
- **Fuentes**: Tipos de letra personalizados
- **Assets**: Recursos que se cargan en el frontend

```
static/
├── src/
│   ├── css/
│   │   └── custom_styles.css
│   ├── js/
│   │   └── widget_personalizado.js
│   └── img/
│       └── logo_empresa.png
└── description/
    ├── icon.png           # Icono del módulo
    └── index.html         # Descripción del módulo
```

### 📁 **views/**
**Vistas e interfaces que el usuario verá**
- **Formularios**: Pantallas de edición de registros
- **Listas**: Vistas de tabla con múltiples registros
- **Búsquedas**: Filtros y opciones de búsqueda
- **Menús**: Navegación y estructura de menús
- **Reportes**: Vistas para impresión y reportes

```xml
<odoo>
    <data>
        <!-- Vista de formulario -->
        <record id="view_mi_modelo_form" model="ir.ui.view">
            <field name="name">mi.modelo.form</field>
            <field name="model">mi.modelo</field>
            <field name="arch" type="xml">
                <form string="Mi Modelo">
                    <sheet>
                        <group>
                            <field name="name"/>
                            <field name="estado"/>
                        </group>
                    </sheet>
                </form>
            </field>
        </record>
        
        <!-- Menú -->
        <menuitem id="menu_mi_modelo" 
                  name="Mi Modelo" 
                  action="action_mi_modelo" 
                  parent="menu_principal"/>
    </data>
</odoo>
```

### 📁 **wizard/**
**Ventanas emergentes (pop-ups) y asistentes**
- **Temporales**: No se guardan en base de datos
- **Interactivos**: Para confirmaciones y acciones puntuales
- **Asistentes**: Guían al usuario en procesos complejos
- **Transitorios**: Aparecen, ejecutan una acción y desaparecen

```python
from odoo import models, fields

class MiWizard(models.TransientModel):
    _name = 'mi.wizard'
    _description = 'Asistente de Confirmación'
    
    mensaje = fields.Text('Mensaje de Confirmación')
    
    def action_confirmar(self):
        # Ejecutar lógica específica
        self.env['mi.modelo'].browse(self.env.context.get('active_ids')).confirmar_registro()
        return {'type': 'ir.actions.act_window_close'}
```

## 3. Proceso de Desarrollo

### Paso 1: Crear un Nuevo Módulo
```bash
# Crear estructura básica del módulo
python odoo-bin scaffold nombre_modulo modules
```

### Paso 2: Configurar el Módulo
1. **Editar `__manifest__.py`**: Definir metadatos y dependencias
2. **Crear Modelos** en `models/`: Lógica de negocio y estructura de datos
3. **Crear Vistas** en `views/`: Interfaces de usuario
4. **Configurar Seguridad** en `security/`: Permisos y accesos
5. **Agregar Datos Iniciales** en `data/`: Registros por defecto
6. **Implementar Controladores** en `controllers/`: APIs y endpoints web
7. **Crear Wizards** en `wizard/`: Asistentes y pop-ups
8. **Añadir Assets** en `static/`: CSS, JS e imágenes
9. **Configurar Traducciones** en `i18n/`: Soporte multilenguaje

## 4. Buenas Prácticas

### Estructura de Archivos
- Mantener una organización clara y consistente
- Usar nombres descriptivos para archivos y carpetas
- Separar la lógica por responsabilidades (MVC)
- Documentar el código adecuadamente

### Desarrollo
- Seguir las convenciones de nomenclatura de Odoo
- Implementar validaciones en los modelos
- Usar grupos de seguridad apropiados
- Optimizar consultas a la base de datos
- Manejar excepciones correctamente

### Mantenimiento
- Versionar el código con control de cambios
- Realizar pruebas antes de desplegar
- Mantener compatibilidad con versiones de Odoo
- Documentar funcionalidades y cambios importantes
