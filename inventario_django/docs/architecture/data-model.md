\# Modelo de Datos (ER)



```mermaid

erDiagram

&nbsp; EMPRESA ||--o{ DEPARTAMENTO : "tiene"

&nbsp; EMPRESA ||--o{ EMPLEADO : "tiene"

&nbsp; EMPRESA ||--o{ ACTIVO : "posee"

&nbsp; ACTIVO }o--|| MARCA : "es\_de"

&nbsp; ACTIVO }o--|| TIPO\_ACTIVO : "es\_del\_tipo"

&nbsp; ACTIVO }o--|| ESTADO\_ACTIVO : "estado"

&nbsp; ACTIVO ||--o{ MANTENCION : "tiene"

&nbsp; FACTURA ||--o{ DETALLE\_FACTURA : "incluye"



