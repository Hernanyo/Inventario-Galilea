from django.contrib import admin
from django.contrib import admin
from .models_inventario import (
    Empresa, Departamento, Empleado, Marca, EstadoActivo, Proveedor,
    TipoActivo, Activo, AtributosActivo, EstadoMantencion, Mantencion,
    Factura, DetalleFactura
)

admin.site.register(Empresa)
admin.site.register(Departamento)
admin.site.register(Empleado)
admin.site.register(Marca)
admin.site.register(EstadoActivo)
admin.site.register(Proveedor)
admin.site.register(TipoActivo)
admin.site.register(Activo)
admin.site.register(AtributosActivo)
admin.site.register(EstadoMantencion)
admin.site.register(Mantencion)
admin.site.register(Factura)
admin.site.register(DetalleFactura)
