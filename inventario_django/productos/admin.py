"""
Este archivo se utiliza para registrar los modelos en el panel de administración de Django.
Permite gestionar los modelos de la base de datos de manera visual y sencilla, habilitando
las funcionalidades de creación, edición y eliminación de registros.

| **Modelo**        | **Descripción**                                                                 |
|-------------------|---------------------------------------------------------------------------------|
| Empresa           | Permite gestionar las empresas registradas en la base de datos.                 |
| Departamento      | Permite gestionar los departamentos dentro de cada empresa.                    |
| Empleado          | Permite gestionar los empleados registrados en la empresa.                     |
| Marca             | Permite gestionar las marcas de productos o servicios.                         |
| EstadoActivo      | Permite gestionar los estados de los activos (por ejemplo: "En uso", "En bodega").|
| Proveedor         | Permite gestionar la información de los proveedores asociados.                 |
| TipoActivo        | Permite gestionar los tipos de activos (por ejemplo: "Notebook", "Monitor").   |
| Activo            | Permite gestionar los activos registrados en la empresa.                      |
| AtributosActivo   | Permite gestionar los atributos asociados a los activos.                       |
| EstadoMantencion  | Permite gestionar los estados de las mantenciones.                             |
| Mantencion        | Permite gestionar las mantenciones realizadas a los activos.                   |
| Factura           | Permite gestionar las facturas asociadas a las compras o servicios.            |
| DetalleFactura    | Permite gestionar los detalles de cada factura (por ejemplo: productos facturados).|

Cada registro permite realizar operaciones de visualización, creación, edición y eliminación.
"""
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
