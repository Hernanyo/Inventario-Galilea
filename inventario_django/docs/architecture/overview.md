\# Arquitectura — Visión General



```mermaid

flowchart LR

&nbsp;   A\[Navegador (Usuario)] -->|HTTP/HTTPS| B\[Django (Inventario)]

&nbsp;   B -->|ORM| C\[(PostgreSQL)]

&nbsp;   B -->|Media| D\[(Almacenamiento de archivos /media)]

&nbsp;   B --> E\[Señales / Auditoría<br/>Registro de acciones]

&nbsp;   E --> C



