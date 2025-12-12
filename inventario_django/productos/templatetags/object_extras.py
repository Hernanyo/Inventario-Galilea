# productos/templatetags/object_extras.py
from django import template
from django.utils.html import conditional_escape, mark_safe
import re

register = template.Library()

@register.filter
def attr(obj, name):
    """
    Obtiene dinámicamente un atributo del objeto.

    Este filtro permite obtener cualquier atributo de un objeto de manera dinámica en los templates.
    Ejemplo de uso en templates: 
    {{ obj|attr:"campo" }}  ->  getattr(obj, "campo")

    Si el atributo no existe o el objeto es None, devuelve una cadena vacía.
    Si el atributo es callable (un método), intenta invocar el método y devolver su resultado.

    Args:
        obj (object): El objeto sobre el que se quiere obtener el atributo.
        name (str): El nombre del atributo que se desea obtener.

    """
    if obj is None or not name:
        return ""
    # getattr con fallback vacío para no romper templates
    val = getattr(obj, name, "")
    # Evita mostrar métodos
    if callable(val):
        try:
            return val()
        except Exception:
            return ""
    return val

############################## 10/12 #######################################
@register.filter
def column_label(col_name: str) -> str:
    """
    Etiquetas legibles para columnas en `list.html`.

    - Usa un mapping explícito para columnas importantes.
    - Si no hay mapping y el nombre empieza por `id_`, se quita ese prefijo.
    - Reemplaza "_" por espacio y pasa a Title Case.
    """
    if not col_name:
        return ""

    col_name = str(col_name)

    mapping = {
        # Activos
        "id_activo": "Activo",
        # ahora este campo lo usamos como modelo
        "nombre_activo": "Modelo",
        "activo": "Detalle Activo",

        # Tipos/estados de activo
        "id_tipo_activo": "Tipo Activo",
        "tipo_activo": "Tipo Activo",
        "id_estado_activo": "Estado Activo",
        "id_condicion_activo": "Condición",

        # Relaciones comunes
        "id_empleado": "Empleado",
        "id_marca": "Marca",
        "id_proveedor": "Proveedor",

        # Campos “especiales”
        "observaciones": "Observaciones",
        "id_bodega_retorno": "Bodega Retorno",
        "ubicacion_label": "Ubicación",
        # agrega aquí más overrides si los necesitas
    }

    # 1) Si existe en el mapping, usamos ese label
    if col_name in mapping:
        return mapping[col_name]

    # 2) Si empieza por "id_", quitamos el prefijo
    if col_name.startswith("id_"):
        col_name = col_name[3:]

    # 3) Fallback genérico: reemplaza "_" por espacio y Title Case
    return col_name.replace("_", " ").title()

############################## 10/12 #######################################

#11111111111111111#############################################################################
@register.filter(needs_autoescape=True)
def underline_match(value, q, autoescape=True):
    """
    Subraya las coincidencias de `q` dentro de `value`.

    Este filtro subraya todas las ocurrencias de la cadena `q` dentro del valor `value`, de forma insensible a mayúsculas/minúsculas.
    Las coincidencias son envueltas en un `<span class="hl">...</span>` para aplicar estilos de subrayado.
    El filtro también asegura que el valor sea seguro para HTML.

    Args:
        value (str): El valor en el que buscar las coincidencias.
        q (str): La cadena que se busca dentro de `value`.
        autoescape (bool, optional): Si debe escapar automáticamente el valor. Por defecto es `True`.
    """
    if not q or value is None:
        return value
    try:
        s = str(value)
    except Exception:
        return value

    esc = conditional_escape if autoescape else (lambda x: x)
    s_esc = esc(s)
    q_esc = re.escape(esc(q))

    # reemplazo case-insensitive
    pattern = re.compile(q_esc, re.IGNORECASE)
    result = pattern.sub(r'<span class="hl">\g<0></span>', s_esc)
    return mark_safe(result)
#222222222222222222222222222222222222##############################################################################


@register.filter
def get_item(d, key):
    try:
        return d.get(key, "")
    except Exception:
        return ""