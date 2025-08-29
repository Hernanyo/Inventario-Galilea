# productos/urls.py
from django.urls import path
from django.views.generic import RedirectView
from .crud import urlpatterns as crud_urls  # mantiene todas las rutas CRUD
from .dashboard import DashboardView

app_name = "productos"

urlpatterns = [
    # El “home” y el alias list van al dashboard
    path("",      DashboardView.as_view(), name="list"),
    path("home/", DashboardView.as_view(), name="home"),
]

# y luego todas las rutas generadas del CRUD
urlpatterns += crud_urls
