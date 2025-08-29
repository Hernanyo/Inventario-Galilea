# productos/templatetags/object_extras.py
from django import template
register = template.Library()

@register.filter
def attr(obj, name):
    """{{ obj|attr:'campo' }} -> obj.campo (vacío si no existe)"""
    return getattr(obj, name, "")
