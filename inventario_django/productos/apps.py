from django.apps import AppConfig
# productos/views.py
from django.db.utils import OperationalError, ProgrammingError
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def home(request):
    return render(request, "home.html")  # plantilla que crearás abajo


class ProductosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'productos'
    verbose_name = "Productos / Inventario"

    
    def ready(self):
        try:
            from .utils import ensure_history_view_perms
            ensure_history_view_perms()   # idempotente
        except (OperationalError, ProgrammingError):
            # DB aún no lista; ignorar en arranques tempranos
            pass

class ProductosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "productos"

    def ready(self):
        import productos.signals  # ← IMPORTANTE
