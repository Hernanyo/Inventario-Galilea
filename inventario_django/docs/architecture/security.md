# Seguridad

## Autenticación y permisos
- **Backend**: `CustomAuthenticationBackend` permite login por **RUT** o **correo** (valida contra `auth_user`).
- **Usuarios ↔ Empleados**: `Empleado.user` (OneToOne). `EmpleadoForm.save()` crea automáticamente el `auth.User` si falta.

## Multi-empresa (tenancy lógico)
  - `empresa_id` en sesión; middleware aplica filtros por defecto.
- **CSRF y formularios**: CSRF activo; validaciones de tamaño/extensión de archivos.
- **Borrado lógico**: Campo `eliminado` + exclusión por defecto en queries.
- **Buenas prácticas**: `select_related/prefetch_related` para rendimiento.
  - Logs de errores y métricas para diagnósticos.
- **Session scope**: `empresa_id`, `empresa_nombre`, `empresa_slug`.
- **RequireCompanyMiddleware**: si el usuario está autenticado y no hay empresa en sesión, redirige al selector.
- **Filtrado por empresa**: `scope_qs_by_empresa(request, qs)` detecta `id_empresa` o relaciones que lo contienen y aplica filtro. `EmpresaScopeMixin/CompanyRequiredMixin` aplican lo anterior en CBVs y exigen empresa en sesión.

## Autorización (permisos)
- `ModelPermsMixin` (opcional por vista) valida el permiso `<app>.<acción>_<modelo>`.
- Vistas protegidas con `login_required` / `PermissionRequiredMixin`.
- Permisos por acción (listar/crear/editar/eliminar).

## Auditoría
- **Registro maestro** (`Registro` / `TipoRegistro`):
  - Signals **globales** `pre_save/post_save/post_delete` generan entradas con `datos_anteriores` y `datos_nuevos` (JSON).
  - Eventos especiales en **Factura**: `ADJUNTAR` y `QUITAR_ADJUNTO` cuando sólo cambia el archivo adjunto.
- **Historial de Activos**: Los cambios en activos se registran automáticamente en el historial. Esto incluye cambios en **estado**, **responsable**, **nombre**, **etiqueta**, **tipo**, **marca**, **proveedor**, **empresa/depto**, y **observaciones** (en un registro separado llamado "OBSERVACIONES").
- **Historial de Mantenciones**: Los cambios de estado y responsable también generan registros en el historial. Cada cambio relevante, incluyendo las ediciones de la mantención, es auditable.

## Trazabilidad de usuario
- `SetAppUsernameMiddleware` setea `SET LOCAL app.username` (útil para logs DB).
- `CurrentUserMiddleware` expone el usuario actual a funciones de auditoría.
