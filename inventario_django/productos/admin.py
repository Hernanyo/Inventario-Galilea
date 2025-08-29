from django.contrib import admin
from django.contrib import admin
from .models_inventario import (
    Empresa, Departamento, Empleado, Marca, EstadoEquipo, Proveedor,
    TipoEquipo, Equipo, AtributosEquipo, EstadoMantencion, Mantencion,
    Factura, DetalleFactura
)

admin.site.register(Empresa)
admin.site.register(Departamento)
admin.site.register(Empleado)
admin.site.register(Marca)
admin.site.register(EstadoEquipo)
admin.site.register(Proveedor)
admin.site.register(TipoEquipo)
admin.site.register(Equipo)
admin.site.register(AtributosEquipo)
admin.site.register(EstadoMantencion)
admin.site.register(Mantencion)
admin.site.register(Factura)
admin.site.register(DetalleFactura)
