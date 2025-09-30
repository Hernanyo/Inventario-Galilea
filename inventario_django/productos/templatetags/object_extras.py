# productos/templatetags/object_extras.py
from django import template
from django.utils.html import conditional_escape, mark_safe
import re

register = template.Library()

@register.filter
def attr(obj, name):
    """
    Obtiene dinámicamente un atributo del objeto:
    {{ obj|attr:"campo" }}  ->  getattr(obj, "campo")
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
    Etiquetas legibles para columnas en list.html.
    Si no está en el mapping, aplica "replace _" y Title Case.
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
        # Otros que se vean con 'activo' en el nombre:
        "id_empleado": "Empleado",
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
    Subraya (con un <span class="hl">...</span>) las coincidencias de `q`
    dentro de `value`. Case-insensitive y seguro (escapa HTML).
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