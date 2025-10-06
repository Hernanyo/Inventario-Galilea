\# Modelo de Datos (ER)



\# Modelo de Datos



```mermaid

erDiagram

&nbsp; EMPRESA ||--o{ DEPARTAMENTO : tiene

&nbsp; EMPRESA ||--o{ EMPLEADO : tiene

&nbsp; EMPRESA ||--o{ ACTIVO : posee

&nbsp; EMPRESA ||--o{ FACTURA : emite

&nbsp; EMPRESA ||--o{ REGISTRO : genera



&nbsp; ACTIVO }o--|| MARCA : es\_de

&nbsp; ACTIVO }o--|| TIPO\_ACTIVO : es\_del\_tipo

&nbsp; ACTIVO }o--|| ESTADO\_ACTIVO : esta\_en

&nbsp; ACTIVO ||--o{ MANTENCION : tiene

&nbsp; ACTIVO ||--o{ ATRIBUTO\_VALOR : define



&nbsp; MANTENCION }o--|| TIPO\_MANTENCION : es\_de

&nbsp; MANTENCION }o--|| ESTADO\_MANTENCION : esta\_en

&nbsp; MANTENCION }o--|| PRIORIDAD\_MANTENCION : con



&nbsp; FACTURA ||--o{ DETALLE\_FACTURA : incluye

&nbsp; DETALLE\_FACTURA }o--|| ACTIVO : de\_activo



&nbsp; REGISTRO }o--|| TIPO\_REGISTRO : clasifica

&nbsp; REGISTRO }o--|| USUARIO : realizado\_por



