from pathlib import Path
import environ
import os

# === Paths ===
# Este archivo está en: inventario/settings/base.py
# Subimos 2 niveles para llegar a la raíz del proyecto (donde está manage.py)

# Redirecciones de autenticación
#LOGIN_URL = "/login/"
#LOGIN_REDIRECT_URL = "/"        # o "/dashboard/"
#LOGOUT_REDIRECT_URL = "/login/"

BASE_DIR = Path(__file__).resolve().parents[2]

# === Env ===
env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)
# Carga .env desde la raíz del proyecto
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# === Seguridad / Debug ===
SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG", default=False)

_allowed = env("DJANGO_ALLOWED_HOSTS", default="")
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]

# === Apps ===
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "productos.apps.ProductosConfig",
    "django_extensions",# << aquí
    # Agrega aquí tus apps: "productos", "cuentas", etc.
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
WSGI_APPLICATION = "inventario.wsgi.application"
ASGI_APPLICATION = "inventario.asgi.application"

# === Templates ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Incluye ambas rutas por compatibilidad con tu repo
        "DIRS": [
            BASE_DIR / "inventario_django" / "templates",
            BASE_DIR / "templates",
        ],
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

# === Base de datos ===
DB_ENGINE = env("DB_ENGINE", default="django.db.backends.sqlite3")
if DB_ENGINE.endswith("sqlite3"):
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": BASE_DIR / env("DB_NAME", default="db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="5432"),
        }
    }

    
_pg_search_path = env("DB_PG_SEARCH_PATH", default="")
if _pg_search_path:
    DATABASES["default"]["OPTIONS"] = {"options": f"-c search_path={_pg_search_path}"}

# === Passwords ===
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# === Locale ===
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# === Archivos estáticos / media ===
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = []
for p in [
    BASE_DIR / "static",
    BASE_DIR / "inventario_django" / "static",
]:
    if p.exists():
        STATICFILES_DIRS.append(p)

        
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# === Email (robusto ante valores vacíos) ===
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")

_email_port_raw = env("EMAIL_PORT", default=None)
EMAIL_PORT = int(_email_port_raw) if _email_port_raw not in (None, "", "None") else None

EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)


# === Seguridad base ===
X_FRAME_OPTIONS = "DENY"

# === Logging básico (se ajusta en dev/prod) ===
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

# Redirecciones de autenticación
#LOGIN_URL = "/login/"
#LOGIN_REDIRECT_URL = "/"       # o "/dashboard/"
#LOGOUT_REDIRECT_URL = "/login/"

LOGIN_URL = 'login'                         # a dónde mandar si no está logueado
LOGIN_REDIRECT_URL = 'productos:home'       # a dónde ir después de iniciar sesión
LOGOUT_REDIRECT_URL = 'login'               # a dónde ir después de cerrar sesión (o 'productos:home' si prefieres)

