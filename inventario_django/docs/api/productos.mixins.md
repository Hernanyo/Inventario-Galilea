# Mixins

::: productos.mixins
    options:
      show_object_full_path: false
      members_order: source

## Tabla de aspectos clave del código:
| **Clase**              | **Descripción**                                                                                                 | **Método principal**               | **Acción**                                                                                                                                          |
| ---------------------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ModelPermsMixin`      | Exige que el usuario tenga permisos para realizar acciones específicas sobre el modelo.                         | `dispatch(self, request)`          | Verifica si el usuario tiene el permiso correspondiente basado en `action_perm`, y deniega acceso si no lo tiene.                                   |
| `CompanyRequiredMixin` | Asegura que el usuario tenga una empresa seleccionada en la sesión, redirigiendo si no es el caso.              | `dispatch(self, request)`          | Redirige al selector de empresa si el usuario no tiene una empresa activa en la sesión.                                                             |
| `scope_qs_by_empresa`  | Filtra las consultas para devolver solo objetos de la empresa activa de la sesión.                              | `scope_qs_by_empresa(request, qs)` | Filtra la queryset para incluir solo los registros que pertenecen a la empresa activa, usando el `id_empresa` en la sesión.                         |
| `EmpresaScopeMixin`    | Aplica el filtro de empresa a las consultas dentro de las vistas basadas en clases (CBVs).                      | `scope_queryset(self, qs)`         | Llama a `scope_qs_by_empresa` para filtrar las querysets en las vistas según la empresa activa.                                                     |
| `SaveEmpresaMixin`     | Completa el campo `id_empresa` al guardar el formulario si está vacío, utilizando el `empresa_id` en la sesión. | `form_valid(self, form)`           | Se asegura de que al guardar una instancia, el campo `id_empresa` se complete automáticamente con el `empresa_id` de la sesión si no está presente. |
