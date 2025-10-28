
```mermaid
%%{init: {"flowchart": {"htmlLabels": false}} }%%
flowchart TB
  classDef big fill:#eef2ff,stroke:#94a3b8,stroke-width:1px,color:#111827

  A["Importar crud.py"]:::big --> B["make_urlpatterns()"]:::big
  B --> C["Descubrir modelos de la app"]:::big
  C --> D{"Iterar por cada modelo"}:::big

  D --> E["Crear CrudConfig (columnas, búsqueda, orden, slug)"]:::big
  E --> F["Generar vistas: List / Create / Update / Delete"]:::big
  E --> G["Crear vista: Export CSV"]:::big
  F --> H["Agregar rutas a urlpatterns"]:::big
  G --> H

  H --> I{"¿Caso especial?"}:::big
  I --> J["Registro: solo lectura + ruta de comentarios"]:::big
  I --> K["Historial: solo listado"]:::big
  I --> L["Normal: permisos estándar"]:::big

  H --> M["Recolectar CRUD_CONFIGS"]:::big
  M --> N["Ajustes finos por modelo"]:::big

  subgraph "Ajustes por modelo"
    direction LR
    N1["Activo: badge de estado; factura tras proveedor; condición/ubicación; orden id desc"]:::big
    N2["PMA: ocultar estado; badge en planes"]:::big
    N3["Factura: mostrar RUT proveedor"]:::big
    N4["Empleado: columnas fijas; orden recientes"]:::big
    N5["Registros: orden fecha desc"]:::big
  end

  N --> N1
  N --> N2
  N --> N3
  N --> N4
  N --> N5

  N5 --> Z["Listas, filtros y rutas listas por módulo"]:::big
```

Descripción.
Al iniciar, el CRUD se auto-configura: detecta los modelos, genera su configuración (qué columnas se ven, cómo se buscan y ordenan), crea las páginas de listar/crear/editar/eliminar y la exportación a CSV, y registra las rutas. Si un modelo requiere trato especial (p. ej., registros de auditoría), se deja solo lectura. Luego aplica ajustes finos por modelo (como badges de estado, RUT del proveedor, orden por fecha, etc.). Con eso, cada módulo queda listo para usar sin programar pantallas una a una.



```mermaid
%%{init: {"flowchart": {"htmlLabels": false}} }%%
flowchart LR
  classDef big fill:#eef2ff,stroke:#94a3b8,stroke-width:1px,color:#111827

  S["GET /nuevo o /editar"]:::big --> P{"¿Formulario específico?"}:::big
  P -->|Sí| SF["Usar ActivoForm / MantencionForm / EmpleadoForm"]:::big
  P -->|No| GF["Generar formulario genérico (build_default_form, widgets y archivos, ocultar campo eliminado)"]:::big

  SF --> V
  GF --> V
  V["Filtrar FKs por empresa activa y preparar vista: prellenar nombre; ocultar métricas; permitir ubicación eliminada solo al editar"]:::big --> U["Usuario envía"]:::big

  U --> OK{"¿Validación correcta?"}:::big
  OK -->|No| ERR["Mostrar errores"]:::big
  OK -->|Sí| SAVE["Guardar registro"]:::big
  SAVE --> R{"Reglas según modelo"}:::big

  R --> ACT["Activo: arrastrar ubicación del responsable; guardar atributos dinámicos; limpiar serie/nombre"]:::big
  R --> EMP["Empleado: crear usuario si aplica; sincronizar correo"]:::big
  R --> MAN["Mantención: registrar en historial"]:::big
  R --> GEN["Genérico"]:::big

  ACT --> MSG["Mensaje de éxito"]:::big
  EMP --> MSG
  MAN --> MSG
  GEN --> MSG
  MSG --> BACK["Volver a listado"]:::big
```
Descripción
Al crear o editar, el sistema usa un formulario a medida si existe; si no, arma uno genérico. Siempre filtra datos por la empresa activa y prepara ayudas (pre-llenados y ocultar métricas innecesarias). Se valida lo ingresado y, si está correcto, se guarda aplicando la lógica propia de cada módulo (por ejemplo, atributos dinámicos en Activos, creación/sincronización de usuario en Empleados y registro de eventos en Mantenciones) y se vuelve al listado.