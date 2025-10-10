# Overview

::: productos.overview
    options:
      show_object_full_path: false
      members_order: source

## Tabla de aspectos clave del código:
| **Clase**              | **Descripción**                                                                                       | **Método principal**               | **Acción**                                                                                                                                                     |
| ---------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CardsGridView`        | Renderiza una cuadrícula de módulos (pantalla de tarjetas) con conteo de registros por cada modelo.   | `get_context_data(self, **kwargs)` | Obtiene y renderiza el contexto con las tarjetas de cada módulo y su conteo de registros.                                                                      |
| `ListVerticalView`     | Muestra un listado vertical compacto de módulos con conteo de registros.                              | `get_context_data(self, **kwargs)` | Obtiene y renderiza el contexto con los registros de los módulos en formato de lista vertical.                                                                 |
| `MetricsDashboardView` | Renderiza un dashboard con KPIs y gráficos, incluyendo métricas de empleados, activos y mantenciones. | `get_context_data(self, **kwargs)` | Obtiene y renderiza métricas clave, como el conteo de registros por modelo y distribuciones estadísticas (empleados por departamento, activos por tipo, etc.). |
