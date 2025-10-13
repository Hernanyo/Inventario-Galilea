# Resumen de Proyecto

- Django: 5.2.5
- Base dir: C:\Users\herna\OneDrive\Desktop\Inventario-Galilea\inventario_django

## INSTALLED_APPS (no Django por defecto)

- productos.apps.ProductosConfig
- django_extensions

## Base de datos (tipo)

- ENGINE: django.db.backends.postgresql
- NAME:   inventario_nueva

## Modelos y campos

### django.contrib.admin.models.LogEntry
- **id**: AutoField
- **action_time**: DateTimeField
- **user**: ForeignKey → django.contrib.auth.models.User
- **content_type**: ForeignKey → django.contrib.contenttypes.models.ContentType
- **object_id**: TextField
- **object_repr**: CharField
- **action_flag**: PositiveSmallIntegerField
- **change_message**: TextField

### django.contrib.auth.models.Permission
- **id**: AutoField
- **name**: CharField
- **content_type**: ForeignKey → django.contrib.contenttypes.models.ContentType
- **codename**: CharField

### django.contrib.auth.models.Group
- **id**: AutoField
- **name**: CharField

### django.contrib.auth.models.User
- **id**: AutoField
- **password**: CharField
- **last_login**: DateTimeField
- **is_superuser**: BooleanField
- **username**: CharField
- **first_name**: CharField
- **last_name**: CharField
- **email**: CharField
- **is_staff**: BooleanField
- **is_active**: BooleanField
- **date_joined**: DateTimeField

### django.contrib.contenttypes.models.ContentType
- **id**: AutoField
- **app_label**: CharField
- **model**: CharField

### django.contrib.sessions.models.Session
- **session_key**: CharField
- **session_data**: TextField
- **expire_date**: DateTimeField

### productos.models_inventario.Empresa
- **id_empresa**: AutoField
- **rut_empresa**: CharField
- **nombre_empresa**: CharField
- **direccion_empresa**: CharField
- **giro**: CharField
- **eliminado**: BooleanField

### productos.models_inventario.Departamento
- **id_departamento**: AutoField
- **nombre_departamento**: CharField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **eliminado**: BooleanField

### productos.models_inventario.Empleado
- **id_empleado**: AutoField
- **rut**: CharField
- **nombre**: CharField
- **apellido_paterno**: CharField
- **apellido_materno**: CharField
- **estado_activo**: BooleanField
- **cargo**: CharField
- **telefono**: CharField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **id_departamento**: ForeignKey → productos.models_inventario.Departamento
- **rol**: CharField
- **user**: OneToOneField → django.contrib.auth.models.User
- **correo**: CharField
- **eliminado**: BooleanField

### productos.models_inventario.Marca
- **id_marca**: AutoField
- **nombre_marca**: CharField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **eliminado**: BooleanField

### productos.models_inventario.EstadoActivo
- **id_estado_activo**: AutoField
- **descripcion**: CharField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **eliminado**: BooleanField

### productos.models_inventario.Proveedor
- **id_proveedor**: AutoField
- **nombre_proveedor**: CharField
- **rut_proveedor**: CharField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **eliminado**: BooleanField

### productos.models_inventario.TipoActivo
- **id_tipo_activo**: AutoField
- **tipo_activo**: CharField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **eliminado**: BooleanField

### productos.models_inventario.Activo
- **id_activo**: AutoField
- **nombre_activo**: CharField
- **id_marca**: ForeignKey → productos.models_inventario.Marca
- **id_tipo_activo**: ForeignKey → productos.models_inventario.TipoActivo
- **id_estado_activo**: ForeignKey → productos.models_inventario.EstadoActivo
- **id_empleado**: ForeignKey → productos.models_inventario.Empleado
- **id_proveedor**: ForeignKey → productos.models_inventario.Proveedor
- **etiqueta**: CharField
- **qr_code**: FileField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **id_departamento**: ForeignKey → productos.models_inventario.Departamento
- **observaciones**: TextField
- **activo_critico**: BooleanField
- **confidencialidad**: IntegerField
- **integridad**: IntegerField
- **disponibilidad**: IntegerField
- **clasificacion**: CharField
- **eliminado**: BooleanField
- **numero_serie**: CharField

### productos.models_inventario.AtributosActivo
- **id_atributo_activo**: AutoField
- **id_tipo_activo**: ForeignKey → productos.models_inventario.TipoActivo
- **atributo**: CharField
- **valor**: CharField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **eliminado**: BooleanField

### productos.models_inventario.AgregacionAtributosPorActivo
- **id**: AutoField
- **activo**: ForeignKey → productos.models_inventario.Activo
- **atributo**: ForeignKey → productos.models_inventario.AtributosActivo
- **valor**: CharField

### productos.models_inventario.EstadoMantencion
- **id_estado_mantencion**: AutoField
- **tipo**: CharField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **eliminado**: BooleanField

### productos.models_inventario.TipoMantencion
- **id_tipo_mantencion**: AutoField
- **nombre**: CharField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **eliminado**: BooleanField

### productos.models_inventario.PrioridadMantencion
- **id_prioridad**: AutoField
- **nombre**: CharField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **eliminado**: BooleanField

### productos.models_inventario.Mantencion
- **id_mantencion**: AutoField
- **id_activo**: ForeignKey → productos.models_inventario.Activo
- **id_estado_mantencion**: ForeignKey → productos.models_inventario.EstadoMantencion
- **id_tipo_mantencion**: ForeignKey → productos.models_inventario.TipoMantencion
- **id_prioridad**: ForeignKey → productos.models_inventario.PrioridadMantencion
- **fecha**: DateField
- **descripcion**: TextField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **responsable**: ForeignKey → productos.models_inventario.Empleado
- **solicitante_user**: ForeignKey → django.contrib.auth.models.User
- **eliminado**: BooleanField

### productos.models_inventario.Factura
- **id_factura**: AutoField
- **id_proveedor**: ForeignKey → productos.models_inventario.Proveedor
- **fecha_emision**: DateField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **folio**: CharField
- **observacion**: TextField
- **archivo_adjunto**: FileField
- **eliminado**: BooleanField

### productos.models_inventario.DetalleFactura
- **id_detalle_factura**: AutoField
- **id_factura**: ForeignKey → productos.models_inventario.Factura
- **id_activo**: ForeignKey → productos.models_inventario.Activo
- **nombre_activo**: CharField
- **cantidad**: IntegerField
- **valor_unitario**: IntegerField
- **valor_neto**: IntegerField
- **iva**: IntegerField
- **valor_total**: IntegerField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **eliminado**: BooleanField

### productos.models_inventario.HistorialActivos
- **id**: AutoField
- **activo**: ForeignKey → productos.models_inventario.Activo
- **etiqueta**: CharField
- **nombre_activo**: CharField
- **modelo**: CharField
- **tipo_activo**: ForeignKey → productos.models_inventario.TipoActivo
- **accion**: CharField
- **usuario**: ForeignKey → productos.models_inventario.Empleado
- **fecha**: DateTimeField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa
- **departamento**: ForeignKey → productos.models_inventario.Departamento
- **ubicacion**: CharField
- **estado_anterior**: ForeignKey → productos.models_inventario.EstadoActivo
- **estado_nuevo**: ForeignKey → productos.models_inventario.EstadoActivo
- **responsable_actual**: ForeignKey → productos.models_inventario.Empleado
- **comentario**: TextField
- **responsable_anterior_fk**: ForeignKey → productos.models_inventario.Empleado

### productos.models_inventario.HistorialMantencionesLog
- **id_evento**: AutoField
- **id_mantencion**: IntegerField
- **fecha_evento**: DateTimeField
- **accion**: CharField
- **detalle**: TextField
- **usuario_app_username**: CharField
- **id_activo**: IntegerField
- **etiqueta**: CharField
- **activo_nombre**: CharField
- **tipo_mantencion**: CharField
- **prioridad**: CharField
- **estado_actual**: CharField
- **responsable_nombre**: TextField
- **solicitante_nombre**: TextField
- **descripcion**: TextField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa

### productos.models_inventario.TipoRegistro
- **id_tipo_registro**: AutoField
- **nombre**: CharField
- **descripcion**: TextField
- **eliminado**: BooleanField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa

### productos.models_inventario.Registro
- **id_registro**: AutoField
- **usuario**: ForeignKey → productos.models_inventario.Empleado
- **tipo_registro**: ForeignKey → productos.models_inventario.TipoRegistro
- **fecha**: DateTimeField
- **content_type**: ForeignKey → django.contrib.contenttypes.models.ContentType
- **object_id**: PositiveIntegerField
- **descripcion**: TextField
- **datos_anteriores**: JSONField
- **datos_nuevos**: JSONField
- **comentario**: TextField
- **eliminado**: BooleanField
- **id_empresa**: ForeignKey → productos.models_inventario.Empresa

## URLs

- `admin/`  [index] → django.contrib.admin.sites.AdminSite.index
- `admin/login/`  [login] → django.contrib.admin.sites.AdminSite.login
- `admin/logout/`  [logout] → django.contrib.admin.sites.AdminSite.logout
- `admin/password_change/`  [password_change] → django.contrib.admin.sites.AdminSite.password_change
- `admin/password_change/done/`  [password_change_done] → django.contrib.admin.sites.AdminSite.password_change_done
- `admin/autocomplete/`  [autocomplete] → django.contrib.admin.sites.AdminSite.autocomplete_view
- `admin/jsi18n/`  [jsi18n] → django.contrib.admin.sites.AdminSite.i18n_javascript
- `admin/r/<path:content_type_id>/<path:object_id>/`  [view_on_site] → django.contrib.contenttypes.views.shortcut
- `admin/auth/group/`  [auth_group_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/auth/group/add/`  [auth_group_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/auth/group/<path:object_id>/history/`  [auth_group_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/auth/group/<path:object_id>/delete/`  [auth_group_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/auth/group/<path:object_id>/change/`  [auth_group_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/auth/group/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/auth/user/<id>/password/`  [auth_user_password_change] → django.contrib.auth.admin.UserAdmin.user_change_password
- `admin/auth/user/`  [auth_user_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/auth/user/add/`  [auth_user_add] → django.contrib.auth.admin.UserAdmin.add_view
- `admin/auth/user/<path:object_id>/history/`  [auth_user_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/auth/user/<path:object_id>/delete/`  [auth_user_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/auth/user/<path:object_id>/change/`  [auth_user_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/auth/user/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/empresa/`  [productos_empresa_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/empresa/add/`  [productos_empresa_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/empresa/<path:object_id>/history/`  [productos_empresa_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/empresa/<path:object_id>/delete/`  [productos_empresa_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/empresa/<path:object_id>/change/`  [productos_empresa_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/empresa/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/departamento/`  [productos_departamento_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/departamento/add/`  [productos_departamento_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/departamento/<path:object_id>/history/`  [productos_departamento_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/departamento/<path:object_id>/delete/`  [productos_departamento_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/departamento/<path:object_id>/change/`  [productos_departamento_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/departamento/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/empleado/`  [productos_empleado_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/empleado/add/`  [productos_empleado_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/empleado/<path:object_id>/history/`  [productos_empleado_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/empleado/<path:object_id>/delete/`  [productos_empleado_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/empleado/<path:object_id>/change/`  [productos_empleado_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/empleado/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/marca/`  [productos_marca_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/marca/add/`  [productos_marca_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/marca/<path:object_id>/history/`  [productos_marca_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/marca/<path:object_id>/delete/`  [productos_marca_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/marca/<path:object_id>/change/`  [productos_marca_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/marca/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/estadoactivo/`  [productos_estadoactivo_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/estadoactivo/add/`  [productos_estadoactivo_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/estadoactivo/<path:object_id>/history/`  [productos_estadoactivo_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/estadoactivo/<path:object_id>/delete/`  [productos_estadoactivo_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/estadoactivo/<path:object_id>/change/`  [productos_estadoactivo_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/estadoactivo/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/proveedor/`  [productos_proveedor_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/proveedor/add/`  [productos_proveedor_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/proveedor/<path:object_id>/history/`  [productos_proveedor_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/proveedor/<path:object_id>/delete/`  [productos_proveedor_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/proveedor/<path:object_id>/change/`  [productos_proveedor_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/proveedor/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/tipoactivo/`  [productos_tipoactivo_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/tipoactivo/add/`  [productos_tipoactivo_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/tipoactivo/<path:object_id>/history/`  [productos_tipoactivo_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/tipoactivo/<path:object_id>/delete/`  [productos_tipoactivo_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/tipoactivo/<path:object_id>/change/`  [productos_tipoactivo_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/tipoactivo/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/activo/`  [productos_activo_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/activo/add/`  [productos_activo_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/activo/<path:object_id>/history/`  [productos_activo_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/activo/<path:object_id>/delete/`  [productos_activo_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/activo/<path:object_id>/change/`  [productos_activo_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/activo/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/atributosactivo/`  [productos_atributosactivo_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/atributosactivo/add/`  [productos_atributosactivo_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/atributosactivo/<path:object_id>/history/`  [productos_atributosactivo_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/atributosactivo/<path:object_id>/delete/`  [productos_atributosactivo_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/atributosactivo/<path:object_id>/change/`  [productos_atributosactivo_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/atributosactivo/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/estadomantencion/`  [productos_estadomantencion_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/estadomantencion/add/`  [productos_estadomantencion_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/estadomantencion/<path:object_id>/history/`  [productos_estadomantencion_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/estadomantencion/<path:object_id>/delete/`  [productos_estadomantencion_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/estadomantencion/<path:object_id>/change/`  [productos_estadomantencion_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/estadomantencion/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/mantencion/`  [productos_mantencion_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/mantencion/add/`  [productos_mantencion_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/mantencion/<path:object_id>/history/`  [productos_mantencion_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/mantencion/<path:object_id>/delete/`  [productos_mantencion_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/mantencion/<path:object_id>/change/`  [productos_mantencion_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/mantencion/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/factura/`  [productos_factura_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/factura/add/`  [productos_factura_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/factura/<path:object_id>/history/`  [productos_factura_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/factura/<path:object_id>/delete/`  [productos_factura_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/factura/<path:object_id>/change/`  [productos_factura_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/factura/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/productos/detallefactura/`  [productos_detallefactura_changelist] → django.contrib.admin.options.ModelAdmin.changelist_view
- `admin/productos/detallefactura/add/`  [productos_detallefactura_add] → django.contrib.admin.options.ModelAdmin.add_view
- `admin/productos/detallefactura/<path:object_id>/history/`  [productos_detallefactura_history] → django.contrib.admin.options.ModelAdmin.history_view
- `admin/productos/detallefactura/<path:object_id>/delete/`  [productos_detallefactura_delete] → django.contrib.admin.options.ModelAdmin.delete_view
- `admin/productos/detallefactura/<path:object_id>/change/`  [productos_detallefactura_change] → django.contrib.admin.options.ModelAdmin.change_view
- `admin/productos/detallefactura/<path:object_id>/`  [] → django.views.generic.base.RedirectView
- `admin/^(?P<app_label>auth|productos)/$`  [app_list] → django.contrib.admin.sites.AdminSite.app_index
- `admin/(?P<url>.*)$`  [] → django.contrib.admin.sites.AdminSite.catch_all_view
- `login/`  [login] → django.contrib.auth.views.LoginView
- `logout/`  [logout] → django.contrib.auth.views.LogoutView
- `ingreso/`  [company_select] → productos.views_auth.seleccionar_empresa
- `ingreso/cambiar/`  [company_change] → productos.views_auth.cambiar_empresa
- `login/`  [login] → django.contrib.auth.views.LoginView
- `logout/`  [logout] → django.contrib.auth.views.LogoutView
- ``  [home] → productos.views.HomeView
- `dashboard/`  [dashboard] → productos.overview.MetricsDashboardView
- `listado/`  [list] → productos.overview.ListVerticalView
- `detallefacturas/`  [detallefacturas_list] → productos.crud.DetalleFacturaGenericList
- `activos/<int:pk>/qr/`  [activos_qr] → productos.views_qr.qr_print_view
- `^media/(?P<path>.*)$`  [] → django.views.static.serve
- `historial_activos/`  [historial_activos_list] → productos.urls.HistorialList
- `historial_activos/exportar/csv/`  [historial_activos_csv] → productos.crud.export_csv_view.<locals>.view
- `activos/<int:pk>/historial/`  [activo_historial_list] → productos.urls.HistorialPorActivo
- `atributosactivos/nuevo/`  [atributosactivos_create] → productos.views_atributos.atributos_nuevo_wizard
- `empresas/`  [empresas_list] → productos.crud.EmpresaGenericList
- `empresas/nuevo/`  [empresas_create] → productos.crud.EmpresaGenericCreate
- `empresas/<int:pk>/editar/`  [empresas_update] → productos.crud.EmpresaGenericUpdate
- `empresas/<int:pk>/eliminar/`  [empresas_delete] → productos.crud.EmpresaGenericDelete
- `empresas/exportar/csv/`  [empresas_csv] → productos.crud.export_csv_view.<locals>.view
- `departamentos/`  [departamentos_list] → productos.crud.DepartamentoGenericList
- `departamentos/nuevo/`  [departamentos_create] → productos.crud.DepartamentoGenericCreate
- `departamentos/<int:pk>/editar/`  [departamentos_update] → productos.crud.DepartamentoGenericUpdate
- `departamentos/<int:pk>/eliminar/`  [departamentos_delete] → productos.crud.DepartamentoGenericDelete
- `departamentos/exportar/csv/`  [departamentos_csv] → productos.crud.export_csv_view.<locals>.view
- `empleados/`  [empleados_list] → productos.crud.EmpleadoGenericList
- `empleados/nuevo/`  [empleados_create] → productos.crud.EmpleadoGenericCreate
- `empleados/<int:pk>/editar/`  [empleados_update] → productos.crud.EmpleadoGenericUpdate
- `empleados/<int:pk>/eliminar/`  [empleados_delete] → productos.crud.EmpleadoGenericDelete
- `empleados/exportar/csv/`  [empleados_csv] → productos.crud.export_csv_view.<locals>.view
- `marcas/`  [marcas_list] → productos.crud.MarcaGenericList
- `marcas/nuevo/`  [marcas_create] → productos.crud.MarcaGenericCreate
- `marcas/<int:pk>/editar/`  [marcas_update] → productos.crud.MarcaGenericUpdate
- `marcas/<int:pk>/eliminar/`  [marcas_delete] → productos.crud.MarcaGenericDelete
- `marcas/exportar/csv/`  [marcas_csv] → productos.crud.export_csv_view.<locals>.view
- `estadoactivos/`  [estadoactivos_list] → productos.crud.EstadoActivoGenericList
- `estadoactivos/nuevo/`  [estadoactivos_create] → productos.crud.EstadoActivoGenericCreate
- `estadoactivos/<int:pk>/editar/`  [estadoactivos_update] → productos.crud.EstadoActivoGenericUpdate
- `estadoactivos/<int:pk>/eliminar/`  [estadoactivos_delete] → productos.crud.EstadoActivoGenericDelete
- `estadoactivos/exportar/csv/`  [estadoactivos_csv] → productos.crud.export_csv_view.<locals>.view
- `proveedors/`  [proveedors_list] → productos.crud.ProveedorGenericList
- `proveedors/nuevo/`  [proveedors_create] → productos.crud.ProveedorGenericCreate
- `proveedors/<int:pk>/editar/`  [proveedors_update] → productos.crud.ProveedorGenericUpdate
- `proveedors/<int:pk>/eliminar/`  [proveedors_delete] → productos.crud.ProveedorGenericDelete
- `proveedors/exportar/csv/`  [proveedors_csv] → productos.crud.export_csv_view.<locals>.view
- `tipoactivos/`  [tipoactivos_list] → productos.crud.TipoActivoGenericList
- `tipoactivos/nuevo/`  [tipoactivos_create] → productos.crud.TipoActivoGenericCreate
- `tipoactivos/<int:pk>/editar/`  [tipoactivos_update] → productos.crud.TipoActivoGenericUpdate
- `tipoactivos/<int:pk>/eliminar/`  [tipoactivos_delete] → productos.crud.TipoActivoGenericDelete
- `tipoactivos/exportar/csv/`  [tipoactivos_csv] → productos.crud.export_csv_view.<locals>.view
- `activos/`  [activos_list] → productos.crud.ActivoGenericList
- `activos/nuevo/`  [activos_create] → productos.crud.ActivoGenericCreate
- `activos/<int:pk>/editar/`  [activos_update] → productos.crud.ActivoGenericUpdate
- `activos/<int:pk>/eliminar/`  [activos_delete] → productos.crud.ActivoGenericDelete
- `activos/exportar/csv/`  [activos_csv] → productos.crud.export_csv_view.<locals>.view
- `atributosactivos/`  [atributosactivos_list] → productos.crud.AtributosActivoGenericList
- `atributosactivos/nuevo/`  [atributosactivos_create] → productos.crud.AtributosActivoGenericCreate
- `atributosactivos/<int:pk>/editar/`  [atributosactivos_update] → productos.crud.AtributosActivoGenericUpdate
- `atributosactivos/<int:pk>/eliminar/`  [atributosactivos_delete] → productos.crud.AtributosActivoGenericDelete
- `atributosactivos/exportar/csv/`  [atributosactivos_csv] → productos.crud.export_csv_view.<locals>.view
- `agregacionatributosporactivos/`  [agregacionatributosporactivos_list] → productos.crud.AgregacionAtributosPorActivoGenericList
- `agregacionatributosporactivos/nuevo/`  [agregacionatributosporactivos_create] → productos.crud.AgregacionAtributosPorActivoGenericCreate
- `agregacionatributosporactivos/<int:pk>/editar/`  [agregacionatributosporactivos_update] → productos.crud.AgregacionAtributosPorActivoGenericUpdate
- `agregacionatributosporactivos/<int:pk>/eliminar/`  [agregacionatributosporactivos_delete] → productos.crud.AgregacionAtributosPorActivoGenericDelete
- `agregacionatributosporactivos/exportar/csv/`  [agregacionatributosporactivos_csv] → productos.crud.export_csv_view.<locals>.view
- `estadomantencions/`  [estadomantencions_list] → productos.crud.EstadoMantencionGenericList
- `estadomantencions/nuevo/`  [estadomantencions_create] → productos.crud.EstadoMantencionGenericCreate
- `estadomantencions/<int:pk>/editar/`  [estadomantencions_update] → productos.crud.EstadoMantencionGenericUpdate
- `estadomantencions/<int:pk>/eliminar/`  [estadomantencions_delete] → productos.crud.EstadoMantencionGenericDelete
- `estadomantencions/exportar/csv/`  [estadomantencions_csv] → productos.crud.export_csv_view.<locals>.view
- `tipomantencions/`  [tipomantencions_list] → productos.crud.TipoMantencionGenericList
- `tipomantencions/nuevo/`  [tipomantencions_create] → productos.crud.TipoMantencionGenericCreate
- `tipomantencions/<int:pk>/editar/`  [tipomantencions_update] → productos.crud.TipoMantencionGenericUpdate
- `tipomantencions/<int:pk>/eliminar/`  [tipomantencions_delete] → productos.crud.TipoMantencionGenericDelete
- `tipomantencions/exportar/csv/`  [tipomantencions_csv] → productos.crud.export_csv_view.<locals>.view
- `prioridadmantencions/`  [prioridadmantencions_list] → productos.crud.PrioridadMantencionGenericList
- `prioridadmantencions/nuevo/`  [prioridadmantencions_create] → productos.crud.PrioridadMantencionGenericCreate
- `prioridadmantencions/<int:pk>/editar/`  [prioridadmantencions_update] → productos.crud.PrioridadMantencionGenericUpdate
- `prioridadmantencions/<int:pk>/eliminar/`  [prioridadmantencions_delete] → productos.crud.PrioridadMantencionGenericDelete
- `prioridadmantencions/exportar/csv/`  [prioridadmantencions_csv] → productos.crud.export_csv_view.<locals>.view
- `mantencions/`  [mantencions_list] → productos.crud.MantencionGenericList
- `mantencions/nuevo/`  [mantencions_create] → productos.crud.MantencionGenericCreate
- `mantencions/<int:pk>/editar/`  [mantencions_update] → productos.crud.MantencionGenericUpdate
- `mantencions/<int:pk>/eliminar/`  [mantencions_delete] → productos.crud.MantencionGenericDelete
- `mantencions/exportar/csv/`  [mantencions_csv] → productos.crud.export_csv_view.<locals>.view
- `facturas/`  [facturas_list] → productos.crud.FacturaGenericList
- `facturas/nuevo/`  [facturas_create] → productos.crud.FacturaGenericCreate
- `facturas/<int:pk>/editar/`  [facturas_update] → productos.crud.FacturaGenericUpdate
- `facturas/<int:pk>/eliminar/`  [facturas_delete] → productos.crud.FacturaGenericDelete
- `facturas/exportar/csv/`  [facturas_csv] → productos.crud.export_csv_view.<locals>.view
- `detallefacturas/`  [detallefacturas_list] → productos.crud.DetalleFacturaGenericList
- `detallefacturas/nuevo/`  [detallefacturas_create] → productos.crud.DetalleFacturaGenericCreate
- `detallefacturas/<int:pk>/editar/`  [detallefacturas_update] → productos.crud.DetalleFacturaGenericUpdate
- `detallefacturas/<int:pk>/eliminar/`  [detallefacturas_delete] → productos.crud.DetalleFacturaGenericDelete
- `detallefacturas/exportar/csv/`  [detallefacturas_csv] → productos.crud.export_csv_view.<locals>.view
- `historialactivos/`  [historialactivos_list] → productos.crud.HistorialActivosGenericList
- `historialactivos/nuevo/`  [historialactivos_create] → productos.crud.HistorialActivosGenericCreate
- `historialactivos/<int:pk>/editar/`  [historialactivos_update] → productos.crud.HistorialActivosGenericUpdate
- `historialactivos/<int:pk>/eliminar/`  [historialactivos_delete] → productos.crud.HistorialActivosGenericDelete
- `historialactivos/exportar/csv/`  [historialactivos_csv] → productos.crud.export_csv_view.<locals>.view
- `historialmantencioneslogs/`  [historialmantencioneslogs_list] → productos.crud.HistorialMantencionesLogGenericList
- `historialmantencioneslogs/nuevo/`  [historialmantencioneslogs_create] → productos.crud.HistorialMantencionesLogGenericCreate
- `historialmantencioneslogs/<int:pk>/editar/`  [historialmantencioneslogs_update] → productos.crud.HistorialMantencionesLogGenericUpdate
- `historialmantencioneslogs/<int:pk>/eliminar/`  [historialmantencioneslogs_delete] → productos.crud.HistorialMantencionesLogGenericDelete
- `historialmantencioneslogs/exportar/csv/`  [historialmantencioneslogs_csv] → productos.crud.export_csv_view.<locals>.view
- `tiporegistros/`  [tiporegistros_list] → productos.crud.TipoRegistroGenericList
- `tiporegistros/nuevo/`  [tiporegistros_create] → productos.crud.TipoRegistroGenericCreate
- `tiporegistros/<int:pk>/editar/`  [tiporegistros_update] → productos.crud.TipoRegistroGenericUpdate
- `tiporegistros/<int:pk>/eliminar/`  [tiporegistros_delete] → productos.crud.TipoRegistroGenericDelete
- `tiporegistros/exportar/csv/`  [tiporegistros_csv] → productos.crud.export_csv_view.<locals>.view
- `registros/<int:pk>/comentar/`  [registros_comentar] → productos.crud.registro_comentar
- `registros/`  [registros_list] → productos.crud.RegistroGenericList
- `registros/nuevo/`  [registros_create] → productos.crud.RegistroGenericCreate
- `registros/<int:pk>/editar/`  [registros_update] → productos.crud.RegistroGenericUpdate
- `registros/<int:pk>/eliminar/`  [registros_delete] → productos.crud.RegistroGenericDelete
- `registros/exportar/csv/`  [registros_csv] → productos.crud.export_csv_view.<locals>.view
- `historial_mantenciones/`  [historial_mantenciones_list] → productos.urls.HistorialMantencionesList
- `historial_mantenciones/exportar/csv/`  [historial_mantenciones_csv] → productos.crud.export_csv_view.<locals>.view
- `mantenciones/<int:id_mantencion>/historial/`  [historial_mantencion] → productos.urls.HistorialMantencionDetalle
- `mantencions/create/`  [mantencions_create] → productos.urls.MantencionCreate
- `mantencions/<int:pk>/update/`  [mantencions_update] → productos.urls.MantencionUpdate
- `activos/disponibles/`  [activos_disponibles] → productos.views.ActivosDisponiblesView
- `activos/en-uso/`  [activos_en_uso] → productos.urls.ActivosEnUsoList
- `activos/desasignar/`  [activos_desasignar] → productos.views.ActivosDesasignarView
- `api/atributos-por-tipo/`  [api_atributos_por_tipo] → productos.views.api_atributos_por_tipo
- `tipoactivos/<int:tipo_id>/atributos/`  [editar_atributos_por_tipo] → productos.views_atributos.editar_atributos_por_tipo
- `atributosactivos/por-tipo/<int:tipo_id>/`  [atributos_por_tipo] → productos.views_atributos.editar_atributos_por_tipo
- `tipoactivos/<int:tipo_id>/atributos/ver/`  [ver_atributos_por_tipo] → productos.views_atributos.ver_atributos_por_tipo
- `empresas/set/`  [set_company] → productos.views_company.set_company
- `activos/<int:activo_id>/historial/`  [activos_historial] → productos.views.historial_mantenciones_activo
- `mantenciones/<int:id_mantencion>/historial/`  [mantencion_historial] → productos.crud.historial_mantencion
- `mantenciones/<int:pk>/historial/`  [historial_mantencion] → productos.views.HistorialMantencionIndividual
- `mantencions/`  [mantencions_list] → productos.crud.MantencionGenericList
- `atributosactivos/`  [atributosactivos_list] → productos.views_atributos.atributosactivos_list
- `tipoactivos/<int:tipo_id>/atributos/`  [editar_atributos_por_tipo] → productos.views_atributos.editar_atributos_por_tipo
- `tipoactivos/<int:tipo_id>/atributos/ver/`  [ver_atributos_por_tipo] → productos.views_atributos.ver_atributos_por_tipo
- `atributosactivos/nuevo/`  [atributosactivos_create] → productos.views_atributos.atributos_nuevo_wizard
- `api/atributos-por-tipo/`  [api_atributos_por_tipo] → productos.views.api_atributos_por_tipo
- `factura/<int:factura_id>/adjuntar/`  [factura_attach_file] → productos.views.factura_attach_file
- `^media/(?P<path>.*)$`  [] → django.views.static.serve
- `facturas/`  [facturas_list] → productos.views.FacturaListView
- `facturas/<int:id_factura>/`  [facturas_detail] → productos.views.FacturaDetailView
- `factura/<int:factura_id>/adjuntar/`  [factura_attach_file] → productos.views.factura_attach_file
- `registros/`  [registros_list] → productos.views.RegistroListView
- `facturas/<int:factura_id>/quitar-adjunto/`  [factura_quitar_adjunto] → productos.views.factura_quitar_adjunto
- `activos/exportar/criticos-excel/`  [exportar_activos_criticos_excel] → productos.views.exportar_activos_criticos_excel
- `password_reset/`  [password_reset] → django.contrib.auth.views.PasswordResetView
- `password_reset/done/`  [password_reset_done] → django.contrib.auth.views.PasswordResetDoneView
- `reset/<uidb64>/<token>/`  [password_reset_confirm] → django.contrib.auth.views.PasswordResetConfirmView
- `reset/done/`  [password_reset_complete] → django.contrib.auth.views.PasswordResetCompleteView

## Templates (carpeta templates/)

- templates\base.html
- templates\home.html
- templates\home_cards.html
- templates\listado_vertical.html
- templates\accounts\company_select.html
- templates\accounts\login.html
- templates\accounts\recuperar_contraseña\password_reset.html
- templates\accounts\recuperar_contraseña\password_reset_complete.html
- templates\accounts\recuperar_contraseña\password_reset_confirm.html
- templates\accounts\recuperar_contraseña\password_reset_done.html
- templates\activos\confirm_delete.html
- templates\activos\detalle.html
- templates\activos\disponibles.html
- templates\activos\disponibles_asignar.html
- templates\activos\en_uso_desasignar.html
- templates\activos\list.html
- templates\activos\qr_print.html
- templates\atributos\editar_por_categoria.html
- templates\atributos\editar_por_tipo.html
- templates\atributos\nuevo_selector_categoria.html
- templates\atributos\nuevo_selector_tipo.html
- templates\atributos\ver_por_subtipo.html
- templates\atributos\ver_por_tipo.html
- templates\auth\seleccionar_empresa.html
- templates\crud\confirm_delete.html
- templates\crud\dashboard.html
- templates\crud\delete.html
- templates\crud\form.html
- templates\crud\list.html
- templates\empresa\select_company.html
- templates\includes\action_bar.html
- templates\includes\mantenciones\historial_por_equipo.html
- templates\overview\cards_grid.html
- templates\overview\dashboard.html
- templates\overview\dashboard_metrics.html
- templates\overview\home_sidebar.html
- templates\overview\list_vertical.html
- templates\productos\facturas_list.html
- templates\productos\factura_adjuntar.html
- templates\productos\factura_detail.html
- templates\productos\registros_list.html
- templates\productos\subtipos_list.html
