### Autenticación y Acceso
| **ID**   | **Título**                 | **Rol**              | **Acción**                                          | **Beneficio**                                                    | **Criterios de aceptación**  |
|----------|----------------------------|----------------------|-----------------------------------------------------|------------------------------------------------------------------|------------------------------|
| HU-01    | Login de acceso             | Usuario registrado   | Quiero iniciar sesión en el sistema                 | Para acceder a las funcionalidades de inventario según mi rol   | - El usuario ingresa correo/usuario/RUT y contraseña válida. <br> - Redirección al panel de control según rol. <br> - Mensaje de error si los datos son incorrectos. |
| HU-02    | Recuperación de contraseña  | Usuario registrado   | Quiero poder recuperar mi contraseña olvidada       | Para poder restablecer mi acceso al sistema                     | - El usuario puede solicitar un enlace de recuperación de contraseña. <br> - El sistema envía un correo con el enlace para restablecer la contraseña. <br> - El usuario puede cambiar su contraseña y acceder al sistema nuevamente. |
| HU-03    | Cerrar sesión               | Usuario registrado   | Quiero cerrar sesión del sistema                    | Para asegurar la privacidad y proteger mis datos                 | - El usuario puede hacer clic en "Cerrar sesión" y ser redirigido a la página de inicio. |

### Gestión de Usuarios
| **ID**   | **Título**                 | **Rol**              | **Acción**                                          | **Beneficio**                                                    | **Criterios de aceptación**  |
|----------|----------------------------|----------------------|-----------------------------------------------------|------------------------------------------------------------------|------------------------------|
| HU-04    | Creación de usuarios        | Administrador        | Quiero crear un nuevo usuario y asignarle un rol    | Para que el nuevo empleado pueda acceder a la aplicación        | - El administrador puede crear un nuevo usuario proporcionando nombre, correo y rol. <br> - El nuevo usuario recibe un correo de bienvenida con instrucciones. |
| HU-05    | Asignación de roles a usuarios | Administrador      | Quiero asignar roles a los usuarios registrados     | Para definir qué funcionalidades pueden acceder los usuarios    | - El administrador puede asignar roles como "Empleado", "Administrador", al usuario. <br> - Los permisos cambian según el rol asignado. |

### Gestión de Empresas
| **ID**   | **Título**                 | **Rol**              | **Acción**                                          | **Beneficio**                                                    | **Criterios de aceptación**  |
|----------|----------------------------|----------------------|-----------------------------------------------------|------------------------------------------------------------------|------------------------------|
| HU-06    | Creación de empresa         | Administrador        | Quiero registrar una nueva empresa                  | Para gestionar los recursos y usuarios de la empresa             | - El administrador puede ingresar el nombre, dirección, RUT y datos de la nueva empresa. |
| HU-07    | Edición de empresa          | Administrador        | Quiero editar los datos de una empresa              | Para actualizar la información de la empresa                     | - El administrador puede modificar los datos como nombre, RUT, y dirección de la empresa. |
| HU-08    | Eliminación de empresa      | Administrador        | Quiero eliminar una empresa                         | Para remover una empresa que ya no se utiliza                   | - El administrador puede eliminar una empresa, siempre que no tenga datos asociados. |

### Gestión de Departamentos
| **ID**   | **Título**                 | **Rol**              | **Acción**                                          | **Beneficio**                                                    | **Criterios de aceptación**  |
|----------|----------------------------|----------------------|-----------------------------------------------------|------------------------------------------------------------------|------------------------------|
| HU-09    | Gestión de departamentos    | Administrador        | Quiero gestionar los departamentos dentro de la empresa | Para organizar los recursos y responsabilidades                  | - El administrador puede crear, editar y eliminar departamentos. <br> - Cada departamento se asocia a una empresa. |
| HU-10    | Asignación de empleados a departamentos | Administrador  | Quiero asignar empleados a departamentos específicos | Para definir la estructura organizativa y asignar tareas         | - El administrador puede asignar empleados a diferentes departamentos. <br> - El sistema muestra la lista de empleados disponibles para asignar. |


### Gestión de Empleados
| **ID**   | **Título**                 | **Rol**              | **Acción**                                          | **Beneficio**                                                    | **Criterios de aceptación**  |
|----------|----------------------------|----------------------|-----------------------------------------------------|------------------------------------------------------------------|------------------------------|
| HU-11    | Creación de empleados       | Administrador        | Quiero agregar nuevos empleados a la empresa        | Para gestionar las tareas y asignaciones de los empleados        | - El administrador puede agregar nuevos empleados con información como nombre, correo, departamento, etc. |
| HU-12    | Edición de empleados        | Administrador        | Quiero editar los detalles de un empleado           | Para actualizar la información de un empleado                   | - El administrador puede modificar los datos de un empleado existente. <br> - Los cambios afectan la asignación de activos, departamentos, etc. |
| HU-13    | Desasignación de empleados   | Administrador        | Quiero desasignar empleados de un activo o departamento | Para reorganizar la asignación de recursos en la empresa         | - El administrador puede desasignar un empleado de un activo o departamento. |

### Gestión de Activos
| **ID**   | **Título**                 | **Rol**              | **Acción**                                          | **Beneficio**                                                    | **Criterios de aceptación**  |
|----------|----------------------------|----------------------|-----------------------------------------------------|------------------------------------------------------------------|------------------------------|
| HU-14    | Creación de activos         | Administrador        | Quiero crear nuevos activos                         | Para gestionar los recursos materiales de la empresa             | - El administrador puede ingresar detalles de un nuevo activo, como nombre, tipo, marca, estado, etc. |
| HU-15    | Asignación de activos a empleados | Administrador | Quiero asignar activos a los empleados             | Para llevar un control de qué empleado está utilizando qué activo | - El administrador puede asignar un activo a un empleado específico. <br> - El sistema muestra el estado del activo y el responsable asignado. |
| HU-16    | Edición de activos          | Administrador        | Quiero editar los detalles de un activo             | Para actualizar la información de los recursos materiales        | - El administrador puede modificar los detalles de un activo, como estado, asignación, etc. |
| HU-17    | Eliminación de activos      | Administrador        | Quiero eliminar un activo                           | Para remover activos que ya no se necesitan                     | - El administrador puede eliminar activos del inventario, siempre que no estén asignados o involucrados en procesos pendientes. |

### Gestión de Facturas
| **ID**   | **Título**                 | **Rol**              | **Acción**                                          | **Beneficio**                                                    | **Criterios de aceptación**  |
|----------|----------------------------|----------------------|-----------------------------------------------------|------------------------------------------------------------------|------------------------------|
| HU-18    | Creación de facturas        | Administrador        | Quiero registrar nuevas facturas                    | Para llevar el control de las compras y pagos realizados         | - El administrador puede registrar detalles de una nueva factura, como número, proveedor, fecha, monto, etc. |
| HU-19    | Edición de facturas         | Administrador        | Quiero editar las facturas registradas              | Para actualizar los detalles de una factura existente           | - El administrador puede editar los detalles de las facturas existentes. |
| HU-20    | Eliminación de facturas     | Administrador        | Quiero eliminar una factura                         | Para borrar facturas erróneas o que no corresponden              | - El administrador puede eliminar una factura, siempre que no esté asociada a procesos de pagos. |
| HU-21    | Adjuntar factura a activos  | Administrador        | Quiero asociar una factura a un activo               | Para vincular la factura de compra de un activo                  | - El administrador puede asociar una factura con un activo específico. |

### Gestión de Historiales
| **ID**   | **Título**                 | **Rol**              | **Acción**                                          | **Beneficio**                                                    | **Criterios de aceptación**  |
|----------|----------------------------|----------------------|-----------------------------------------------------|------------------------------------------------------------------|------------------------------|
| HU-22    | Registro de historial de activos | Administrador | Quiero registrar las acciones relacionadas a un activo | Para llevar un registro de los cambios de estado de los activos | - El sistema guarda automáticamente un historial de las acciones realizadas sobre cada activo (creación, asignación, cambio de estado). |
| HU-23    | Registro de historial de mantenciones | Administrador | Quiero registrar las acciones realizadas durante las mantenciones | Para llevar un control de las intervenciones realizadas a los activos | - El sistema guarda un historial detallado de las mantenciones realizadas a los activos, incluyendo fecha, tipo de intervención y responsable. |
| HU-24    | Registro de acciones de empleados | Administrador | Quiero registrar las acciones realizadas por cada empleado | Para auditar las actividades y asignaciones de los empleados | - El sistema registra todas las acciones realizadas por los empleados, como creación, modificación o eliminación de registros. |

### Gestión de Comentarios
| **ID**   | **Título**                 | **Rol**              | **Acción**                                          | **Beneficio**                                                    | **Criterios de aceptación**  |
|----------|----------------------------|----------------------|-----------------------------------------------------|------------------------------------------------------------------|------------------------------|
| HU-25    | Crear comentario en registros | Administrador | Quiero añadir comentarios a un registro de acción | Para realizar anotaciones sobre cambios importantes en los registros | - El administrador puede añadir comentarios a los registros de acción relacionados con activos, empleados, facturas, etc. |
| HU-26    | Editar comentario en registros | Administrador | Quiero editar un comentario en un registro de acción | Para corregir o actualizar la información de los comentarios anteriores | - El administrador puede modificar los comentarios ya existentes en los registros de acción. |
| HU-27    | Eliminar comentario en registros | Administrador | Quiero eliminar un comentario en un registro de acción | Para eliminar comentarios irrelevantes o incorrectos | - El administrador puede eliminar comentarios en los registros de acción de manera segura. |
