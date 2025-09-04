from django.apps import AppConfig
# productos/views.py
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
        # Importa señales para registrar los handlers
        from . import signals  # noqa

