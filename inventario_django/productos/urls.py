# productos/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.shortcuts import get_object_or_404
from .views import EquiposDesasignarView

from django.urls import path
from . import views

from .views_atributos import (
    editar_atributos_por_tipo,
    ver_atributos_por_tipo,   # ← agrega esta
)



# arriba, con los otros imports
from productos.views import EquiposDisponiblesView
from productos.models_inventario import Equipo
from productos.crud import GenericList, build_config, view_class
from productos.views import api_atributos_por_tipo
from .views_atributos import editar_atributos_por_tipo  # y cualquier otra vista de ese archivo



from productos.forms import MantencionForm
from productos.models_inventario import (
    DetalleFactura,
    HistorialEquipos,
    Equipo,
    Mantencion,
    HistorialMantencionesLog,
)

from .views import HomeView
from .overview import CardsGridView, ListVerticalView, MetricsDashboardView
from .views_qr import qr_print_view

from productos.crud import (
    GenericList,
    GenericCreate,
    GenericUpdate,
    build_config,
    view_class,
    export_csv_view,
    CrudConfig,
    urlpatterns as crud_urls,
    log_mantencion_event,   # <- nombre correcto
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
    slug="historial_equipos",
    verbose_plural="Historial de Equipos",
    list_display=[
        "id", "etiqueta", "equipo", "fecha", "responsable_anterior",
        "estado_anterior", "estado_nuevo", "responsable_actual", "empresa",
        "departamento", "usuario",
    ],
    search_fields=[
        "equipo__nombre_equipo", "usuario__nombre", "accion", "etiqueta",
        "nombre_equipo",
    ],
    ordering=["-fecha"],
)

class HistorialList(view_class(HistorialEquipos, historial_cfg, GenericList)):
    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "equipo", "usuario", "estado_anterior", "estado_nuevo",
            "responsable_actual", "empresa", "departamento", "tipo_equipo",
        )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
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
        self.crud_config.can_create = False
        ctx["can_create"] = False
        return ctx

urlpatterns += [
    path("equipos/<int:pk>/historial/", HistorialPorEquipo.as_view(), name="equipo_historial_list"),
]

# --- Rutas CRUD autogeneradas (todas las demás tablas) ---
urlpatterns += crud_urls

# --- Historial de Mantenciones (usa la tabla snapshot física) ---
hist_mant_cfg = CrudConfig(
    model=HistorialMantencionesLog,
    slug="historial_mantenciones",
    verbose_plural="Historial de Mantenciones",
    list_display=[
        "id_equipo",
        "etiqueta",
        "equipo_nombre",
        "fecha_evento",
        # "accion",  # si lo quieres visible en CSV, descomentar
        "tipo_mantencion",
        "prioridad",
        "estado_actual",
        "asignado_a",
        #"responsable_nombre",
        #"solicitante_nombre",
        "descripcion",
        "detalle",
        "usuario_app_username",
    ],
    search_fields=[
        "etiqueta",
        "equipo_nombre",
        "descripcion",
        "tipo_mantencion",
        "prioridad",
        "estado_actual",
        "accion",
        "usuario_app_username",
        "responsable_nombre",
        "solicitante_nombre",
    ],
    ordering=["-fecha_evento"],
)

mant_cfg = CrudConfig(
    model=Mantencion,
    slug="mantencions",
    verbose_plural="Mantenciones",
    list_display=[
        "id_mantencion", "id_equipo", "fecha",
        "id_estado_mantencion", "id_tipo_mantencion", "id_prioridad",
    ],
    search_fields=["descripcion", "id_equipo__etiqueta", "id_equipo__nombre_equipo"],
    ordering=["-fecha"],
)

class MantencionCreate(view_class(Mantencion, mant_cfg, GenericCreate)):
    form_class = MantencionForm
    def form_valid(self, form):
        form.instance.solicitante_user = self.request.user   # ← AQUÍ
        resp = super().form_valid(form)
        log_mantencion_event(self.request.user, self.object, "CREAR", "Alta de mantención")
        return resp

class MantencionUpdate(view_class(Mantencion, mant_cfg, GenericUpdate)):
    form_class = MantencionForm
    def form_valid(self, form):
        resp = super().form_valid(form)
        log_mantencion_event(self.request.user, self.object, "ACTUALIZAR", "Edición de mantención")
        return resp

class HistorialMantencionesList(view_class(HistorialMantencionesLog, hist_mant_cfg, GenericList)):
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.crud_config.can_create = False
        ctx["can_create"] = False
        return ctx

class HistorialMantencionDetalle(HistorialMantencionesList):
    def dispatch(self, request, *args, **kwargs):
        self.id_mantencion = kwargs["id_mantencion"]
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(id_mantencion=self.id_mantencion)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.crud_config.can_create = False
        ctx["can_create"] = False
        ctx["subtitle"] = f"Mantención #{self.id_mantencion}"
        return ctx

urlpatterns += [
    path(
        "historial_mantenciones/",
        HistorialMantencionesList.as_view(),
        name="historial_mantenciones_list",
    ),
    path(
        "historial_mantenciones/exportar/csv/",
        export_csv_view(HistorialMantencionesLog, hist_mant_cfg),
        name="historial_mantenciones_csv",
    ),
    path(
        "mantenciones/<int:id_mantencion>/historial/",
        HistorialMantencionDetalle.as_view(),
        name="historial_mantencion",
    ),
    # Rutas personalizadas para usar MantencionForm + logging
    path("mantencions/create/", MantencionCreate.as_view(), name="mantencions_create"),
    path("mantencions/<int:pk>/update/", MantencionUpdate.as_view(), name="mantencions_update"),

    path("equipos/disponibles/", EquiposDisponiblesView.as_view(), name="equipos_disponibles"),

]

# Disponibles = estado 'bodega' y sin responsable
class EquiposDisponiblesList(view_class(Equipo, build_config(Equipo), GenericList)):
    def get_queryset(self):
        qs = super().get_queryset().select_related("id_marca", "id_tipo_equipo", "id_estado_equipo", "id_empleado")
        return qs.filter(
            id_estado_equipo__descripcion__iexact="bodega",
            id_empleado__isnull=True,
        ).order_by("-id_equipo")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["subtitle"] = "Solo equipos disponibles (Bodega • sin responsable)"
        return ctx


# En uso = asignados (responsable NO nulo)
class EquiposEnUsoList(view_class(Equipo, build_config(Equipo), GenericList)):
    def get_queryset(self):
        qs = super().get_queryset().select_related("id_marca", "id_tipo_equipo", "id_estado_equipo", "id_empleado")
        return qs.filter(
            id_empleado__isnull=False
        ).order_by("-id_equipo")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["subtitle"] = "Solo equipos en uso (asignados a alguien)"
        return ctx

# Rutas filtradas clásicas (si quieres mantenerlas, usa otros paths para no pisar el anterior)
urlpatterns += [
#     path("equipos/disponibles/lista/", EquiposDisponiblesList.as_view(), name="equipos_disponibles_lista"),
     path("equipos/en-uso/",           EquiposEnUsoList.as_view(),      name="equipos_en_uso"),
     path("equipos/desasignar/", EquiposDesasignarView.as_view(), name="equipos_desasignar"),
]

urlpatterns += [
    path("api/atributos-por-tipo/", api_atributos_por_tipo, name="api_atributos_por_tipo"),
]

urlpatterns += [
    path(
        "tipoequipos/<int:tipo_id>/atributos/",
        editar_atributos_por_tipo,
        name="editar_atributos_por_tipo",
    ),
]

# productos/urls.py
#path(
#    "atributos-por-tipo/<int:tipo_id>/",
#    views.atributos_por_tipo,
#    name="atributos_por_tipo",
#)
urlpatterns += [
path(
    "atributosequipos/por-tipo/<int:tipo_id>/",
    editar_atributos_por_tipo,
    name="atributos_por_tipo",
),
]

# productos/urls.py (agrega esta línea donde tienes las otras de atributos)
urlpatterns += [
    path("tipoequipos/<int:tipo_id>/atributos/ver/", ver_atributos_por_tipo, name="ver_atributos_por_tipo"),
]