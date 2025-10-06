# Arquitectura — Visión General

```mermaid
flowchart LR
  A[Navegador<br/>(Usuario)] -->|HTTP/HTTPS| B[Django (Inventario)]
  B -->|ORM| C[(PostgreSQL)]
  B -->|Media| D[(Almacenamiento de archivos)]
  B --> E[Señales/Auditoría<br/>Registro de acciones]
  E --> C
@'
# Instalación

1. Clonar repositorio y crear entorno virtual.
2. Instalar dependencias (`pip install -r requirements.txt`).
3. Configurar variables de entorno (DB, DEBUG, etc.).
4. Ejecutar migraciones y levantar servidor.

```bash
python manage.py migrate
python manage.py runserver




### 2) Reescribe `docs\architecture\overview.md`
```powershell
@'
# Arquitectura — Visión General

```mermaid
flowchart LR
  A[Navegador<br/>(Usuario)] -->|HTTP/HTTPS| B[Django (Inventario)]
  B -->|ORM| C[(PostgreSQL)]
  B -->|Media| D[(Almacenamiento de archivos)]
  B --> E[Señales/Auditoría<br/>Registro de acciones]
  E --> C



### 3) Crea *placeholders* para las páginas que faltan del `nav` (así mkdocs no falla)
```powershell
@'
# Configuración

- **Multi-empresa:** selección de empresa vía sesión (`empresa_id`).
- **Borrado lógico:** campo `eliminado` (oculto en formularios) y filtrado por defecto.
- **Adjuntos de factura:** botones *Adjuntar/Reemplazar* y *Quitar factura*.
