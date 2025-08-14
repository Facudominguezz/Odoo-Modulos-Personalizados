from odoo import api, fields, models, _
from odoo.exceptions import UserError

class EtiquetaPlantillaCategoria(models.Model):
    _name = "etiqueta.plantilla.categoria"
    _description = "Plantilla de Etiqueta por Categoría de Producto"
    _rec_name = "nombre"
    _order = "categoria_id,nombre"

    nombre = fields.Char(
        string="Nombre de la Plantilla",
        required=True,
        help="Nombre descriptivo de la plantilla (ej. 'Etiqueta estándar calzado').",
    )

    categoria_id = fields.Many2one(
        "product.category",
        string="Categoría de Producto",
        required=True,
        index=True,
        help="Categoría a la que aplica esta plantilla. Se admite jerarquía (incluye subcategorías).",
    )

    # Campos estándar a incluir en la etiqueta (booleans expandibles)
    mostrar_nombre = fields.Boolean(string="Mostrar Nombre", default=True)
    mostrar_referencia_interna = fields.Boolean(string="Mostrar Referencia Interna", default=False)
    mostrar_codigo_barras = fields.Boolean(string="Mostrar Código de Barras", default=True)
    mostrar_precio_venta = fields.Boolean(string="Mostrar Precio de Venta", default=False)
    mostrar_udm = fields.Boolean(string="Mostrar UdM", default=False)

    # Atributos comunes calculados (solo lectura, para referencia)
    atributos_comunes_ids = fields.Many2many(
        "product.attribute",
        "etiqueta_cat_common_attr_rel",
        "plantilla_id",
        "attribute_id",
        string="Atributos Comunes (referencia)",
        compute="_compute_atributos_comunes",
        store=False,
        help="Atributos que aparecen en TODOS los productos de la categoría (incluyendo subcategorías).",
    )

    linea_ids = fields.One2many(
        "etiqueta.plantilla.categoria.line",
        "plantilla_id",
        string="Atributos a Incluir",
        help="Seleccione qué atributos incluir en la etiqueta para esta categoría.",
    )

    nota = fields.Text(string="Notas / Instrucciones", help="Observaciones de la plantilla.")

    _sql_constraints = [
        ("categoria_unica", "unique(categoria_id)", "Ya existe una plantilla para esta categoría."),
    ]

    @api.depends("categoria_id")
    def _compute_atributos_comunes(self):
        for registro in self:
            if not registro.categoria_id:
                registro.atributos_comunes_ids = [(5, 0, 0)]
                continue

            # Buscar productos en la categoría y subcategorías
            dominio = [("categ_id", "child_of", registro.categoria_id.id), ("active", "in", [True, False])]
            productos = self.env["product.template"].search(dominio)

            if not productos:
                registro.atributos_comunes_ids = [(5, 0, 0)]
                continue
            
            datos_productos = self._extraer_datos_para_etiqueta(productos)

            # Construir conjuntos de atributos por producto
            conjuntos_atributos = []
            for plantilla_producto in productos:
                # Atributos presentes en el template (product.template.attribute.line)
                atributos = plantilla_producto.attribute_line_ids.mapped("attribute_id").ids
                conjuntos_atributos.append(set(atributos))

            # Intersección de atributos en TODOS los productos
            ids_atributos_comunes = set.intersection(*conjuntos_atributos) if conjuntos_atributos else set()
            registro.atributos_comunes_ids = [(6, 0, list(ids_atributos_comunes))]
    
    

    @api.onchange("categoria_id")
    def _onchange_categoria_id(self):
        """Al cambiar de categoría, recalcula los atributos comunes y sugiere líneas."""
        for registro in self:
            registro._compute_atributos_comunes()
            # Propuesta inicial de líneas = atributos comunes (si no hay líneas aún)
            if not registro.linea_ids and registro.atributos_comunes_ids:
                nuevas_lineas = []
                for atributo in registro.atributos_comunes_ids:
                    nuevas_lineas.append((0, 0, {
                        "atributo_id": atributo.id,
                        "incluir": True,
                    }))
                registro.linea_ids = nuevas_lineas

    def action_recalcular_atributos_comunes(self):
        """Botón para recalcular atributos y (opcionalmente) sincronizar líneas con comunes."""
        for registro in self:
            registro._compute_atributos_comunes()
            # No sobrescribimos líneas existentes, solo informamos si no hay comunes
            if not registro.atributos_comunes_ids:
                raise UserError(_("No se encontraron atributos comunes en la categoría seleccionada."))


class EtiquetaPlantillaCategoriaLine(models.Model):
    _name = "etiqueta.plantilla.categoria.line"
    _description = "Línea de Atributos para Plantilla por Categoría"
    _order = "secuencia, id"

    plantilla_id = fields.Many2one(
        "etiqueta.plantilla.categoria", string="Plantilla", required=True, ondelete="cascade"
    )

    secuencia = fields.Integer(string="Secuencia", default=10)
    atributo_id = fields.Many2one(
        "product.attribute",
        string="Atributo",
        required=True,
        domain=lambda self: self._dominio_atributo_id(),
        help="Atributo a imprimir en la etiqueta.",
    )
    incluir = fields.Boolean(string="Incluir en etiqueta", default=True)

    @api.model
    def _dominio_atributo_id(self):
        """Restringe a atributos comunes usando relación inversa si está disponible.

        Nota: Para Odoo 18, preferimos definir el dominio en la vista con
        parent.atributos_comunes_ids y evitamos depender de active_id/default_* en contexto.
        Esta función queda como fallback cuando se cree un registro en modo standalone.
        """
        if self.env.context.get('default_plantilla_id'):
            plantilla = self.env['etiqueta.plantilla.categoria'].browse(self.env.context['default_plantilla_id'])
            if plantilla.exists() and plantilla.atributos_comunes_ids:
                return [('id', 'in', plantilla.atributos_comunes_ids.ids)]
        return []

    def _extraer_datos_para_etiqueta(self, productos):
        """Devuelve datos relevantes para etiqueta por cada product.template."""
        if not productos:
            return []

        campos_tmpl = [
            "name", "default_code", "barcode", "list_price",
            "uom_id", "categ_id", "weight", "volume",
            "qty_available", "virtual_available",
            "product_variant_id", "currency_id",
        ]
        datos_tmpl = productos.with_context(active_test=False).read(campos_tmpl)

        # Resolver nombres de M2O
        uom_ids = [d["uom_id"][0] for d in datos_tmpl if d.get("uom_id")]
        categ_ids = [d["categ_id"][0] for d in datos_tmpl if d.get("categ_id")]
        curr_ids = [d["currency_id"][0] for d in datos_tmpl if d.get("currency_id")]
        var_ids = [d["product_variant_id"][0] for d in datos_tmpl if d.get("product_variant_id")]

        uom_map = {u.id: u.display_name for u in self.env["uom.uom"].browse(uom_ids)} if uom_ids else {}
        categ_map = {c.id: c.display_name for c in self.env["product.category"].browse(categ_ids)} if categ_ids else {}
        curr_map = {c.id: c.name for c in self.env["res.currency"].browse(curr_ids)} if curr_ids else {}

        variantes = self.env["product.product"].browse(var_ids) if var_ids else self.env["product.product"]
        # Leer display_name y valores de atributos elegidos por variante
        v_info = {}
        if variantes:
            v_read = variantes.read(["display_name", "product_template_attribute_value_ids"])
            # Prefetch de PTAVs
            all_ptav_ids = [ptav_id for v in v_read for ptav_id in v.get("product_template_attribute_value_ids", [])]
            ptavs = self.env["product.template.attribute.value"].browse(all_ptav_ids)
            # Mapear PTAV -> (attr_name, value_name)
            ptav_map = {ptav.id: (ptav.attribute_id.name, ptav.product_attribute_value_id.name) for ptav in ptavs}
            for v in v_read:
                attrs = {}
                for ptav_id in v.get("product_template_attribute_value_ids", []):
                    par = ptav_map.get(ptav_id)
                    if par:
                        attrs[par[0]] = par[1]
                v_info[v["id"]] = {
                    "variant_display_name": v.get("display_name"),
                    "variant_attributes": attrs,
                }

        # Armar resultado legible para etiquetas
        resultado = []
        for d in datos_tmpl:
            var_id = d["product_variant_id"][0] if d.get("product_variant_id") else False
            vdata = v_info.get(var_id, {}) if var_id else {}
            resultado.append({
                "id": d["id"],
                "name": d.get("name"),
                "default_code": d.get("default_code"),
                "barcode": d.get("barcode"),
                "list_price": d.get("list_price"),
                "currency": curr_map.get(d["currency_id"][0]) if d.get("currency_id") else None,
                "uom_name": uom_map.get(d["uom_id"][0]) if d.get("uom_id") else None,
                "categ_name": categ_map.get(d["categ_id"][0]) if d.get("categ_id") else None,
                "weight": d.get("weight"),
                "volume": d.get("volume"),
                "qty_available": d.get("qty_available"),
                "virtual_available": d.get("virtual_available"),
                "variant_display_name": vdata.get("variant_display_name") or d.get("name"),
                "variant_attributes": vdata.get("variant_attributes", {}),
            })

        return resultado
