\# Preguntas Frecuentes (FAQ)



\*\*¿Se puede borrar definitivamente un registro?\*\*  

Por defecto en la aplicación se usa borrado lógico (campo `eliminado`). El borrado físico se restringe, de ser necesario se puede realizar por medio de modificaciones en la base de datos.



\*\*¿Cómo adjunto una factura?\*\*  

Desde la lista de facturas: botón \*\*Adjuntar Factura\*\*, tambien es posible dentro del formulario de editar factura.



\*\*¿Por qué el “Registro de Acciones” no tiene Editar/Eliminar?\*\*  

Funciona como \*log\* (auditoría). Solo se permite realizar comentarios en algún registro.


\*\*¿Cómo seleccionar la empresa activa?\*\*  

Al iniciar sesión, se selecciona empresa a ingresar. Selección de empresa en el header (se guarda en sesión).



\*\*¿Exportar CSV respeta filtros?\*\*  

Sí: búsqueda + filtros activos.

# Programar una mantención

1. Ir a **Mantenciones** → **Nueva mantención**.
2. Completar Activo, Tipo, Prioridad y Responsable.
3. Guardar y revisar el **Historial** de la mantención.


# Exportar CSV respetando filtros

1. En cualquier lista, usa **Buscar** o **Filtro avanzado**.
2. Click en **Exportar CSV**.
3. Se descarga un archivo con las columnas de la vista (`list_display`).


