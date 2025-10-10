"""
Este archivo se utiliza para configurar la aplicación 'productos' en Django.
Contiene la configuración básica del proyecto y la inicialización de los elementos 
importantes de la aplicación, como las señales (signals) y las funciones relacionadas 
con el manejo de la base de datos al arrancar la aplicación.

### Componentes:
1. **home(request):** Vista para la página de inicio de la aplicación. 
   - Requiere que el usuario esté autenticado para acceder a la plantilla "home.html".

2. **ProductosConfig(AppConfig):** Configuración de la aplicación 'productos'.
   - **default_auto_field:** Establece el tipo de campo para las claves primarias como `BigAutoField`.
   - **name:** Define el nombre del módulo como 'productos'.
   - **verbose_name:** Establece un nombre más legible para la aplicación, que se muestra en la interfaz de administración de Django.
   - **ready():** Se ejecuta al iniciar la aplicación y registra los "signals" (señales) para la aplicación. También puede ejecutar otras inicializaciones necesarias.

### Funcionalidad Adicional:
- **Manejo de señales (signals):** El archivo importa y registra señales en la aplicación, lo que permite conectar ciertas funciones (funcionarios como "receivers") a eventos del sistema, como la creación de un objeto en la base de datos.
"""
from django.apps import AppConfig
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
        from . import signals  # registra receivers una sola vez
    
#    def ready(self):
#        try:
#            from .utils import ensure_history_view_perms
#            ensure_history_view_perms()   # idempotente
#        except (OperationalError, ProgrammingError):
#            # DB aún no lista; ignorar en arranques tempranos
#            pass