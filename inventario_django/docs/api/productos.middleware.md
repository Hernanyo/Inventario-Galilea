# Middleware

::: productos.middleware
    options:
      show_object_full_path: false
      members_order: source

## Tabla con los aspectos clave del código:
| **Clase**                  | **Descripción**                                                                       | **Método principal**      | **Acción**                                                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `CurrentUserMiddleware`    | Asocia el usuario actual al hilo de ejecución en cada solicitud y lo limpia al final. | `__call__(self, request)` | Asocia `request.user` al hilo con `set_current_user` al inicio y lo limpia al finalizar la respuesta.                    |
| `SetAppUsernameMiddleware` | Establece el nombre de usuario actual en la base de datos en cada solicitud.          | `__call__(self, request)` | Establece `request.user.username` en la base de datos con la consulta `SET LOCAL app.username`.                          |
| `RequireCompanyMiddleware` | Redirige a los usuarios sin empresa seleccionada en la sesión al selector de empresa. | `__call__(self, request)` | Redirige al selector de empresa si el usuario no tiene una empresa seleccionada y no está accediendo a rutas permitidas. |
