# productos/templatetags/object_extras.py
from django import template

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
        "id_equipo": "Id Activo",
        "nombre_equipo": "Nombre Activo",
        "equipo": "Activo",
        # Tipos/estados de activo
        "id_tipo_equipo": "Id Tipo Activo",
        "tipo_equipo": "Tipo Activo",
        "id_estado_equipo": "Id Estado Activo",
        # Otros que se vean con 'equipo' en el nombre:
        "id_empleado": "Responsable",
        "id_marca": "Id Marca",
        "id_proveedor": "Id Proveedor",
        "observaciones": "Observaciones",
    }
    if not col_name:
        return ""
    return mapping.get(col_name, col_name.replace("_", " ").title())
