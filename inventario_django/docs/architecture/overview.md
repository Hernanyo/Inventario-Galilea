\# Arquitectura — Visión General



```mermaid

flowchart LR

&nbsp; A\[Navegador<br/>(Usuario)] -->|HTTP/HTTPS| B\[Django (Inventario)]

&nbsp; B -->|ORM| C\[(PostgreSQL)]

&nbsp; B -->|Media| D\[(Almacenamiento de archivos)]

&nbsp; B --> E\[Señales/Auditoría<br/>Registro de acciones]

&nbsp; E --> C



