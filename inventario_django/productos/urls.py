# productos/urls.py
from django.urls import path
from .crud import urlpatterns as crud_urls
from .views import HomeView  # tu vista de Inicio (panel con sidebar)
from .overview import CardsGridView, ListVerticalView, MetricsDashboardView
from productos.models_inventario import DetalleFactura
from productos.crud import GenericList, build_config, view_class
from django.conf import settings
from django.conf.urls.static import static

app_name = "productos"

# --- Creamos la vista genérica de DetalleFactura ---
cfg_detalle = build_config(DetalleFactura)
DetalleFacturaList = view_class(DetalleFactura, cfg_detalle, GenericList)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),

    # Vistas (dropdown del navbar)
    path("vistas/cuadricula/", CardsGridView.as_view(), name="vistas_grid"),
    path("vistas/lista/", ListVerticalView.as_view(), name="vistas_lista"),

    # Dashboard (gráficos/metricas)
    path("dashboard/", MetricsDashboardView.as_view(), name="dashboard"),

    # (opcional) alias de compatibilidad si en algún lado aún usas 'list'
    path("listado/", ListVerticalView.as_view(), name="list"),

    path("detallefacturas/", DetalleFacturaList.as_view(), name="detallefacturas_list"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# rutas CRUD
urlpatterns += crud_urls
