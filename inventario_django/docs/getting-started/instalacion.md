
Esta guía te lleva a poner el proyecto en marcha en tu equipo para desarrollo.

### Requisitos

Python 3.11+ (recomendado)

PostgreSQL 13+

Git (opcional, recomendado)

Windows / macOS / Linux (funciona en los tres)

!!! tip "Comprobaciones rápidas"
bash python --version psql --version git --version

### 1) Clonar el repositorio
git clone https://github.com/Hernanyo/Inventario-Galilea.git
cd Inventario-Galilea/inventario_django

### 2) Crear y activar entorno virtual

=== "Windows (PowerShell)"
powershell python -m venv .venv .\.venv\Scripts\Activate.ps1
Para salir: deactivate

=== "macOS / Linux"
bash python3 -m venv .venv source .venv/bin/activate
Para salir: deactivate

!!! warning "Si PowerShell bloquea la activación"
Abre PowerShell como Administrador y ejecuta:
powershell Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

### 3) Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

### 4) Configurar base de datos PostgreSQL

Crea la base y el usuario (puedes usar pgAdmin si prefieres GUI).

=== "psql (línea de comandos)"
```sql
-- Entrar a psql (por ejemplo): psql -U postgres
CREATE DATABASE inventario WITH TEMPLATE=template1 ENCODING='UTF8';

CREATE USER inventario_user WITH PASSWORD 'cambia_esta_contraseña';
ALTER ROLE inventario_user SET client_encoding TO 'utf8';
ALTER ROLE inventario_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE inventario_user SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE inventario TO inventario_user;
```

### 5) Variables de entorno (.env)
Crea un archivo .env en la carpeta inventario_django (donde está manage.py) con:

- Django
DEBUG=True
SECRET_KEY=pon_aqui_una_clave_segura
ALLOWED_HOSTS=127.0.0.1,localhost
TIME_ZONE=America/Santiago

- Base de datos
DB_NAME=inventario
DB_USER=inventario_user
DB_PASSWORD=cambia_esta_contraseña
DB_HOST=127.0.0.1
DB_PORT=5432

- Archivos
MEDIA_ROOT=media
MEDIA_URL=/media/

### 6) Inicializar base y crear superusuario
- python manage.py migrate
- python manage.py createsuperuser

### Opcional (cuando modifiques modelos en el futuro):

- python manage.py makemigrations
- python manage.py migrate

### 7) Ejecutar el servidor de desarrollo
- python manage.py runserver
- App: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin

### (Opcional) Ver la documentación

- En otra terminal (con el entorno activado):
- mkdocs serve -a 127.0.0.1:8001
- Visita: http://127.0.0.1:8001/

## Problemas comunes

??? failure "No compila psycopg2 en Windows"
- Usa psycopg2-binary (si está en requirements.txt) o instala Visual C++ Build Tools si fuese necesario.

??? failure "No se activa el entorno virtual en PowerShell"
- Ejecuta: powershell Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

??? question "Puerto ocupado"
- Ejecuta con otro puerto: bash python manage.py runserver 0.0.0.0:8080

??? failure "Error conectando a PostgreSQL"
- Verifica credenciales/host/puerto y que el servicio está activo: bash pg_isready -h 127.0.0.1 -p 5432

Atajo útil
pip install -r requirements.txt && python manage.py migrate && python manage.py runserver

## Producción (resumen)

- DEBUG=False, ALLOWED_HOSTS=tu_dominio
- DB gestionada (PostgreSQL)
- Servidor de aplicaciones (gunicorn/uvicorn) detrás de Nginx/Apache
- python manage.py collectstatic
- Permisos y backups de MEDIA_ROOT + base de datos
- HTTPS en el proxy (Nginx/Apache)