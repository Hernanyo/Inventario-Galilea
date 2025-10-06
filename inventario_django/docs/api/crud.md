\# API: CRUD Genérico



> Placeholder por ahora. Aquí documentaremos las clases `GenericList`, `GenericCreate`, `GenericUpdate` y `GenericDelete` del módulo `productos.crud`.



En la siguiente iteración lo conectaremos con \*\*mkdocstrings\*\* para extraer las docstrings directamente del código y mostrarlas aquí.

\# API: CRUD Genérico



Estructura común para todas las entidades:

\- \*\*List\*\*: búsqueda, orden, filtros avanzados (FK/bool), paginación.

\- \*\*Create/Update\*\*: ModelForm con estilos unificados.

\- \*\*Delete\*\*: borrado lógico cuando aplica (`eliminado`).



\*\*Personalizaciones\*\*:

\- Registro de Acciones (log) → SIN botones de Editar/Eliminar.

\- Historiales (activos/mantenciones) → solo lectura, ordenados por fecha desc.



