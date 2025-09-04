# productos/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import get_object_or_404

from .views import HomeView
from .overview import CardsGridView, ListVerticalView, MetricsDashboardView
from .views_qr import qr_print_view

from productos.crud import (
    GenericList,
    build_config,
    view_class,
    export_csv_view,
    CrudConfig,
    urlpatterns as crud_urls,
)

from productos.models_inventario import (
    DetalleFactura,
    HistorialEquipos,
    Equipo,
)

app_name = "productos"

# --- Vista genérica para DetalleFactura ---
cfg_detalle = build_config(DetalleFactura)
DetalleFacturaList = view_class(DetalleFactura, cfg_detalle, GenericList)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),

    # Vistas (navbar)
    path("vistas/cuadricula/", CardsGridView.as_view(), name="vistas_grid"),
    path("vistas/lista/", ListVerticalView.as_view(), name="vistas_lista"),

    # Dashboard
    path("dashboard/", MetricsDashboardView.as_view(), name="dashboard"),

    # Alias opcional
    path("listado/", ListVerticalView.as_view(), name="list"),

    # Detalle facturas
    path("detallefacturas/", DetalleFacturaList.as_view(), name="detallefacturas_list"),

    # QR de equipos
    path("equipos/<int:pk>/qr/", qr_print_view, name="equipos_qr"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# --- Historial de Equipos (config dedicada) ---
historial_cfg = CrudConfig(
    model=HistorialEquipos,
    slug="historial_equipos",  # ojo: coincide con el botón superior
    verbose_plural="Historial de Equipos",
    list_display=[
        "id", "etiqueta", "equipo", "fecha", "responsable_anterior",
        "estado_anterior", "estado_nuevo", "responsable_actual", "empresa", "departamento", "usuario"
    ],
    search_fields=[
        "equipo__nombre_equipo", "usuario__nombre", "accion", "etiqueta", "nombre_equipo",
    ],
    ordering=["-fecha"],
)

class HistorialList(view_class(HistorialEquipos, historial_cfg, GenericList)):
    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "equipo", "usuario", "estado_anterior", "estado_nuevo",
            "responsable_actual", "empresa", "departamento", "tipo_equipo"
        )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # 🚫 No se crean registros del historial desde la UI
        self.crud_config.can_create = False
        ctx["can_create"] = False
        return ctx

urlpatterns += [
    path("historial_equipos/", HistorialList.as_view(), name="historial_equipos_list"),
    path(
        "historial_equipos/exportar/csv/",
        export_csv_view(HistorialEquipos, historial_cfg),
        name="historial_equipos_csv",
    ),
]

# --- Historial filtrado por equipo ---
class HistorialPorEquipo(HistorialList):
    def dispatch(self, request, *args, **kwargs):
        self.equipo = get_object_or_404(Equipo, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(equipo_id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["equipo"] = self.equipo
        # Reafirmamos que no se puede “crear”
        self.crud_config.can_create = False
        ctx["can_create"] = False
        return ctx
urlpatterns += [
    path("equipos/<int:pk>/historial/", HistorialPorEquipo.as_view(), name="equipo_historial_list"),
]

# --- Rutas CRUD autogeneradas ---
urlpatterns += crud_urls
