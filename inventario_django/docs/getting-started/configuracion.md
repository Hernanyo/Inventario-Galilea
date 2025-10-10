### 1) Variables de entorno (.env)

Crea un archivo .env en la carpeta del proyecto donde está manage.py (por ejemplo inventario_django/.env).
Este archivo no debe subirse a Git.

!!! warning ".env y Git"
Asegúrate de tener estas líneas en .gitignore para evitar que se suba al repositorio:
.env */.env

### 1.1 .env para desarrollo
### Django
DEBUG=True
SECRET_KEY=pon_aqui_una_clave_segura
ALLOWED_HOSTS=127.0.0.1,localhost
TIME_ZONE=America/Santiago
LANGUAGE_CODE=es-cl

### Base de datos (PostgreSQL local)
DB_NAME=inventario
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=127.0.0.1
DB_PORT=5432

### Archivos
MEDIA_ROOT=media
MEDIA_URL=/media/
STATIC_URL=/static/

### (opcional) Email de pruebas
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

### 1.2 .env para producción (ejemplo)
### Django
DEBUG=False
SECRET_KEY=cambia_esta_clave_por_una_muuy_larga_y_unica
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
TIME_ZONE=America/Santiago
LANGUAGE_CODE=es-cl

### Base de datos (Servidor gestionado / Docker, etc.)
DB_NAME=inventario
DB_USER=inventario_user
DB_PASSWORD=contraseña_fuerte
DB_HOST=10.0.0.12
DB_PORT=5432

### Archivos
MEDIA_ROOT=/var/www/inventario/media
MEDIA_URL=/media/
STATIC_URL=/static/
STATIC_ROOT=/var/www/inventario/static

### Email real (opcional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.tu-proveedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=notificaciones@tu-dominio.com
EMAIL_HOST_PASSWORD=contraseña_email
EMAIL_USE_TLS=True

### Seguridad adicional (opcional)
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

### 2) Variables disponibles
| Variable                 | Tipo   |   Req.   | Default (dev)          | Descripción                                                         |
| ------------------------ | ------ | :------: | ---------------------- | ------------------------------------------------------------------- |
| **DEBUG**                | bool   |    Sí    | `True`                 | En producción debe ser `False`.                                     |
| **SECRET_KEY**           | str    |    Sí    | —                      | Clave criptográfica de Django. Única por despliegue.                |
| **ALLOWED_HOSTS**        | lista  |    Sí    | `127.0.0.1, localhost` | Dominios o IPs válidos para servir la app.                          |
| **TIME_ZONE**            | str    |    No    | `America/Santiago`     | Zona horaria.                                                       |
| **LANGUAGE_CODE**        | str    |    No    | `es-cl`                | Idioma por defecto.                                                 |
| **DB_NAME**              | str    |    Sí    | `inventario`           | Nombre de la base de datos PostgreSQL.                              |
| **DB_USER**              | str    |    Sí    | `postgres`             | Usuario de base de datos.                                           |
| **DB_PASSWORD**          | str    |    Sí    | —                      | Contraseña de la base de datos.                                     |
| **DB_HOST**              | str    |    Sí    | `127.0.0.1`            | Host o servicio de la base de datos.                                |
| **DB_PORT**              | int    |    Sí    | `5432`                 | Puerto de conexión a la base de datos.                              |
| **MEDIA_ROOT**           | path   |    Sí    | `media`                | Carpeta donde se guardan los archivos subidos.                      |
| **MEDIA_URL**            | url    |    Sí    | `/media/`              | URL pública para servir archivos multimedia.                        |
| **STATIC_URL**           | url    |    No    | `/static/`             | URL pública para archivos estáticos.                                |
| **STATIC_ROOT**          | path   |   Prod   | —                      | Carpeta donde se recolectan los estáticos (`collectstatic`).        |
| **EMAIL_***              | varios | Opcional | `consola (dev)`        | Configuración SMTP real en producción.                              |
| **CSRF_TRUSTED_ORIGINS** | lista  |   Prod   | —                      | Orígenes de confianza para CSRF cuando usas HTTPS o dominio propio. |


Formato de listas: separadas por coma, por ejemplo
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

### 3) Base de datos (PostgreSQL)

Crea DB/usuario con privilegios (ver guía de Instalación).

Verifica conectividad:

pg_isready -h 127.0.0.1 -p 5432


Si usas proveedores cloud (RDS, ElephantSQL, etc.), ajusta DB_HOST, DB_PORT, DB_USER, DB_PASSWORD.

!!! tip
Si alguna vez migras a DATABASE_URL (estilo postgres://usuario:pass@host:puerto/db), podrás adaptarlo en settings con utilidades como dj-database-url. Por ahora el proyecto usa variables separadas.

### 4) Archivos estáticos y media
Media (MEDIA_ROOT): archivos subidos por usuarios (p.ej. facturas adjuntas, códigos QR generados).
Static (STATIC_URL/STATIC_ROOT): assets del proyecto (CSS/JS/imágenes de templates).
En producción:
python manage.py collectstatic
Configura el servidor web (Nginx/Apache) para servir /static/ y /media/ desde disco.

### 5) Seguridad (producción)
DEBUG=False
ALLOWED_HOSTS con tu dominio/IP.
SECRET_KEY única y segura.
CSRF_TRUSTED_ORIGINS con tus URLs HTTPS.
Revisa chequeos de despliegue:
python manage.py check --deploy

### 6) Autenticación y sesión
El proyecto usa autenticación estándar de Django. Puedes ajustar (opcional):
### Cookies de sesión (opcional endurecer en prod)
SESSION_COOKIE_AGE=1209600        # 14 días
SESSION_COOKIE_SECURE=True        # si usas HTTPS
CSRF_COOKIE_SECURE=True           # si usas HTTPS

### 7) Multi-empresa y auditoría (contexto)

Multi-empresa: un middleware establece la empresa activa en la sesión; los listados/acciones se filtran por empresa.
Auditoría (Registro de Acciones): señales (signals) registran eventos clave (crear/editar/adjuntar/quitar archivo, etc.). No requiere variables; está activo por defecto.

### 8) Comprobaciones rápidas

.env creado y no comprometido en Git.
BD accesible y credenciales correctas.
MEDIA_ROOT existe y es escribible (en Windows se crea sola; en Linux usa mkdir -p).
En producción: DEBUG=False, ALLOWED_HOSTS completo, collectstatic ejecutado.

### 9) Problemas comunes

??? failure "Error de conexión a la BD"
- Verifica DB_HOST/DB_PORT/DB_USER/DB_PASSWORD.
- El servicio PostgreSQL debe estar arriba.
- Prueba con psql -h 127.0.0.1 -U postgres -d inventario.

??? failure "No se ven estáticos en producción"
- Ejecuta collectstatic.
- Configura Nginx/Apache para servir STATIC_ROOT y MEDIA_ROOT.

??? failure "CSRF en producción"
- Agrega tu dominio a ALLOWED_HOSTS y a CSRF_TRUSTED_ORIGINS (con https://).