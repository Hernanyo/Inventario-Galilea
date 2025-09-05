from .base import *

DEBUG = True

# Si no definiste ALLOWED_HOSTS en .env, acepta localhost en dev
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Email a consola en dev (si no se definió otro)
EMAIL_BACKEND = EMAIL_BACKEND or "django.core.mail.backends.console.EmailBackend"

# Cookies no seguras en dev
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True

# Logging más verboso en dev
LOGGING["root"]["level"] = "DEBUG"

AUTHENTICATION_BACKENDS = [
    "productos.auth_backends.RutBackend",           # login con RUT
    "django.contrib.auth.backends.ModelBackend",    # login normal (por si acaso)
]

