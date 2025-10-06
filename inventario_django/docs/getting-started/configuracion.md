# Configuración

## Variables de entorno (.env)
Crea un archivo `.env` en la raíz del proyecto:

```dotenv
DEBUG=True
SECRET_KEY=pon_aqui_una_clave_segura
ALLOWED_HOSTS=127.0.0.1,localhost

# Base de datos
DB_NAME=inventario
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=127.0.0.1
DB_PORT=5432

# Archivos media
MEDIA_ROOT=media
MEDIA_URL=/media/
