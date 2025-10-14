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

@register.filter
def column_label(col_name: str) -> str:
    """
    Etiquetas legibles para columnas en `list.html`.

    Este filtro convierte nombres de columnas (usados en los templates) en etiquetas más legibles para el usuario.
    Si no hay un mapeo específico para el nombre de la columna, realiza un "replace _" y convierte el texto a formato "Title Case".

    Args:
        col_name (str): El nombre de la columna (ej. 'id_activo', 'nombre_activo').

    Returns:
        str: Una etiqueta legible (ej. "Id Activo", "Nombre Activo").
    """
    mapping = {
        # Activos
        "id_activo": "Id Activo",
        "nombre_activo": "Nombre Activo",
        "activo": "Detalle Activo",
        # Tipos/estados de activo
        "id_tipo_activo": "Tipo Activo",
        "tipo_activo": "Tipo Activo",
        "id_estado_activo": "Estado Activo",
        "id_condicion_activo": "Condición",     # 👈 NUEVO
        # Otros que se vean con 'activo' en el nombre:
        "id_empleado": "Asignado a",
        "id_marca": "Marca",
        "id_proveedor": "Proveedor",
        "observaciones": "Observaciones",
    }
    if not col_name:
        return ""
    return mapping.get(col_name, col_name.replace("_", " ").title())

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