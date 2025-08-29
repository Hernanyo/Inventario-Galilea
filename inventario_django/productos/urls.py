# productos/urls.py
from django.urls import path
from .crud import urlpatterns as crud_urls
from .views import HomeView  # tu vista de Inicio (panel con sidebar)
from .overview import CardsGridView, ListVerticalView, MetricsDashboardView

app_name = "productos"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),

    # Vistas (dropdown del navbar)
    path("vistas/cuadricula/", CardsGridView.as_view(), name="vistas_grid"),
    path("vistas/lista/", ListVerticalView.as_view(), name="vistas_lista"),

    # Dashboard (gráficos/metricas)
    path("dashboard/", MetricsDashboardView.as_view(), name="dashboard"),

    # (opcional) alias de compatibilidad si en algún lado aún usas 'list'
    path("listado/", ListVerticalView.as_view(), name="list"),
]

# rutas CRUD
urlpatterns += crud_urls
