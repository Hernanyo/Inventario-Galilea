from .base import *

DEBUG = False

# Seguridad fuerte en producción
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 días; luego puedes aumentar
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True

# CSRF Trusted Origins (URLs con esquema), opcional desde .env
_csrf = env("CSRF_TRUSTED_ORIGINS", default="")
if _csrf:
    CSRF_TRUSTED_ORIGINS = [u.strip() for u in _csrf.split(",") if u.strip()]

# Logging: consola + archivo rotativo
LOGGING["handlers"]["file"] = {
    "class": "logging.handlers.TimedRotatingFileHandler",
    "filename": BASE_DIR / "logs" / "django.log",
    "when": "D",
    "interval": 1,
    "backupCount": 7,
}
LOGGING["root"]["handlers"] = ["console", "file"]
LOGGING["root"]["level"] = "INFO"
