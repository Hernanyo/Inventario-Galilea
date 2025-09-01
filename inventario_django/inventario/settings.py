"""
Django settings for inventario project.
Generado con Django 5.x (modo desarrollo)
"""

from pathlib import Path

# === Rutas base ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === Seguridad / Debug ===
SECRET_KEY = "django-insecure-0n&x(t_+7$u15_(nkd7xf$r6h5rj7%b3#tp!ei7wqpwm$rt2)0"  # cambia en producción
DEBUG = True
ALLOWED_HOSTS: list[str] = []  # agrega dominios/IPs en producción

# === Apps instaladas ===
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'productos',  # ← tu app
]


# === Middleware ===
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "inventario.urls"

# === Templates ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],   # carpeta templates a nivel de proyecto
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LOGIN_URL = 'login'                # si alguien no autenticado entra a una vista protegida
LOGIN_REDIRECT_URL = 'productos:list'    # adónde va después de iniciar sesión
LOGIN_REDIRECT_URL = "productos:home"
      # adónde va al cerrar sesión

#WSGI_APPLICATION = "inventario.wsgi.application"

# === Base de datos (PostgreSQL) ===
DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': 'inventario_db',
    'USER': 'inventario_user',
    'PASSWORD': 'admin',
    'HOST': '127.0.0.1',
    'PORT': '5432',
    'OPTIONS': {
      'options': '-c search_path=inventario,public'
    }
  }
}


# === Validadores de contraseña ===
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === Internacionalización ===
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Santiago"     # ajusta si corresponde
USE_I18N = True
USE_TZ = True


# === Archivos estáticos ===
STATIC_URL = "static/"
# Para desarrollo, si tienes una carpeta /static en la raíz:
# STATICFILES_DIRS = [BASE_DIR / "static"]

# === Clave primaria por defecto ===
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Para pruebas en consola
# Para producción usar SMTP:
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS

