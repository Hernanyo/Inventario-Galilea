# inventario_djanfo/productos/urls.py
#from productos.models_inventario import CategoriaActivo
from productos.crud import GenericList, view_class
from django.urls import path, include
from .views_atributos import atributos_nuevo_wizard
from django.views.generic import RedirectView
from .views import (
    HomeView, CompanySelectView, company_clear,
    ActivosDisponiblesView, ActivosDesasignarView,
    mantencion_nueva, mantencion_editar, api_atributos_por_tipo,
)

# 👇 Importa las vistas que están en crud.py
from .crud import (
    urlpatterns as crud_urls,
    qr_print_view,
    historial_mantencion,
    ultimos_cambios_mantenciones,
)
from django.urls import path, include
from django.contrib.auth import views as auth_views
from productos.views_company import company_select, set_company
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.shortcuts import get_object_or_404
from .views import ActivosDesasignarView
from .views_auth import seleccionar_empresa
from productos.views_company import company_select, company_change   # <--- AÑADIR AQUÍ
from .views_auth import seleccionar_empresa, cambiar_empresa  # <----- AÑADIR
from django.urls import path
from . import views
from .views_atributos import (editar_atributos_por_tipo, ver_atributos_por_tipo,   # ← agrega esta
                              )
# arriba, con los otros imports
from productos.views import ActivosDisponiblesView
from productos.models_inventario import Activo
from productos.crud import GenericList, build_config, view_class
from productos.views import api_atributos_por_tipo
from .views_atributos import editar_atributos_por_tipo  # y cualquier otra vista de ese archivo
from productos.forms import MantencionForm
from productos.models_inventario import (
    DetalleFactura,
    HistorialActivos,
    Activo,
    Mantencion,
    HistorialMantencionesLog,
)

from .views import HomeView
from .overview import CardsGridView, ListVerticalView, MetricsDashboardView
from .views_qr import qr_print_view
from .views import CompanySelectView, company_clear
from .views_auth import seleccionar_empresa, cambiar_empresa
from django.views.generic import ListView
from .mixins import EmpresaScopeMixin, scope_qs_by_empresa


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

# --- Autenticación y selección de empresa (PREPENDER) ---
auth_selector_patterns = [
    path("ingreso/", seleccionar_empresa, name="company_select"),
    path("ingreso/cambiar/", cambiar_empresa, name="company_change"),
    path("login/",  auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="productos:company_select"), name="logout"),
]

# --- Vista genérica para DetalleFactura ---
cfg_detalle = build_config(DetalleFactura)
DetalleFacturaList = view_class(DetalleFactura, cfg_detalle, GenericList)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),

    # Dashboard
    path("dashboard/", MetricsDashboardView.as_view(), name="dashboard"),

    # Alias opcional
    path("listado/", ListVerticalView.as_view(), name="list"),

    # Detalle facturas
    path("detallefacturas/", DetalleFacturaList.as_view(), name="detallefacturas_list"),

    # QR de activos
    path("activos/<int:pk>/qr/", qr_print_view, name="activos_qr"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = auth_selector_patterns + urlpatterns

# --- Historial de Activos (config dedicada) ---
historial_cfg = CrudConfig(
    model=HistorialActivos,
    slug="historial_activos",
    verbose_plural="Historial de Activos",
    list_display=[
        "id", "etiqueta", "activo", "fecha", "responsable_anterior",
        "estado_anterior", "estado_nuevo", "responsable_actual", "empresa",
        "departamento", "usuario", "comentario",
    ],
    search_fields=[
        "activo__nombre_activo", "usuario__nombre", "etiqueta",
        "nombre_activo", "comentario",
    ],
    ordering=["-fecha"],
)

class HistorialList(view_class(HistorialActivos, historial_cfg, GenericList)):
    """
    Vista que muestra el historial de los activos registrados en el sistema.
    Permite visualizar el historial de cambios de estado, responsable y observaciones
    de cada activo.
    """
    action_perm = None
    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "activo", "usuario", "estado_anterior", "estado_nuevo",
            "responsable_actual", "id_empresa", "departamento", "tipo_activo",
        )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.crud_config.can_create = False
        ctx["can_create"] = False
        return ctx

urlpatterns += [
    path("historial_activos/", HistorialList.as_view(), name="historial_activos_list"),
    path(
        "historial_activos/exportar/csv/",
        export_csv_view(HistorialActivos, historial_cfg),
        name="historial_activos_csv",
    ),
]

# --- Historial filtrado por activo ---
class HistorialPorActivo(HistorialList):
    """
    Vista filtrada que muestra el historial de un activo específico.
    Solo muestra los eventos relacionados con el activo seleccionado.
    """
    action_perm = None
    def dispatch(self, request, *args, **kwargs):
        self.activo = get_object_or_404(Activo, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(activo_id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["activo"] = self.activo
        self.crud_config.can_create = False
        ctx["can_create"] = False
        return ctx

urlpatterns += [
    path("activos/<int:pk>/historial/", HistorialPorActivo.as_view(), name="activo_historial_list"),
]

urlpatterns += [
    path("atributosactivos/nuevo/", atributos_nuevo_wizard, name="atributosactivos_create"),
]

# --- Rutas CRUD autogeneradas (todas las demás tablas) ---
urlpatterns += crud_urls

# --- Historial de Mantenciones (usa la tabla snapshot física) ---
hist_mant_cfg = CrudConfig(
    model=HistorialMantencionesLog,
    slug="historial_mantenciones",
    verbose_plural="Historial de Mantenciones",
    list_display=[
        "id_activo",
        "etiqueta",
        "activo_nombre",
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
        "activo_nombre",
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
        "id_mantencion", "id_activo", "fecha",
        "id_estado_mantencion", "id_tipo_mantencion", "id_prioridad",
    ],
    search_fields=["descripcion", "id_activo__etiqueta", "id_activo__nombre_activo"],
    ordering=["-id_mantencion"], 
)

# (opcional pero recomendado) en el mismo archivo o en views.py si prefieres:
class MantencionList(view_class(Mantencion, mant_cfg, GenericList)):
    """
    Vista que muestra la lista de mantenciones registradas en el sistema.
    Permite ordenar las mantenciones por el ID si no se proporciona un parámetro de orden.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        # si NO hay ?o= (orden solicitado desde la UI), ordena por ID DESC
        if "o" not in self.request.GET:
            return qs.order_by("-id_mantencion")
        return qs

class MantencionCreate(view_class(Mantencion, mant_cfg, GenericCreate)):
    """
    Vista para crear una nueva mantención en el sistema.
    Registra automáticamente un evento en el historial de mantenciones al crear una mantención.
    """
    form_class = MantencionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request          # <- PASA request AL FORM
        return kwargs

    def form_valid(self, form):
        form.instance.solicitante_user = self.request.user   # ← AQUÍ
        form.instance.id_empresa_id = form.instance.id_empresa_id or self.request.session.get("empresa_id")
        resp = super().form_valid(form)
        log_mantencion_event(self.request.user, self.object, "CREAR", "Alta de mantención")
        return resp

class MantencionUpdate(view_class(Mantencion, mant_cfg, GenericUpdate)):
    """
    Vista para editar una mantención existente en el sistema.
    Registra automáticamente un evento en el historial de mantenciones al actualizar la mantención.
    """
    form_class = MantencionForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request          # <- PASA request AL FORM
        return kwargs

    def form_valid(self, form):
        resp = super().form_valid(form)
        log_mantencion_event(self.request.user, self.object, "ACTUALIZAR", "Edición de mantención")
        return resp

class HistorialMantencionesList(view_class(HistorialMantencionesLog, hist_mant_cfg, GenericList)):
    """
    Vista que muestra el historial de mantenciones registrado en el sistema.
    Deshabilita la opción de crear nuevos registros en el historial de mantenciones.
    """
    action_perm = None  
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        self.crud_config.can_create = False
        ctx["can_create"] = False
        return ctx

class HistorialMantencionDetalle(HistorialMantencionesList):
    """
    Vista que muestra el historial detallado de una mantención específica.
    Filtra el historial para mostrar solo los eventos de la mantención seleccionada.
    """
    action_perm = None 
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

    path("activos/disponibles/", ActivosDisponiblesView.as_view(), name="activos_disponibles"),

]

# Disponibles = estado 'bodega' y sin responsable
class ActivosDisponiblesList(view_class(Activo, build_config(Activo), GenericList)):
    """
    Vista que muestra los activos disponibles en bodega sin asignar a ningún responsable.
    """
    def get_queryset(self):
        qs = super().get_queryset().select_related("id_marca", "id_tipo_activo", "id_estado_activo", "id_empleado")
        return qs.filter(
            id_estado_activo__descripcion__iexact="bodega",
            id_empleado__isnull=True,
        ).order_by("-id_activo")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["subtitle"] = "Solo activos disponibles (Bodega • sin responsable)"
        return ctx


# En uso = asignados (responsable NO nulo)
class ActivosEnUsoList(view_class(Activo, build_config(Activo), GenericList)):
    """
    Vista que muestra los activos en uso, es decir, asignados a un responsable.
    """
    def get_queryset(self):
        qs = super().get_queryset().select_related("id_marca", "id_tipo_activo", "id_estado_activo", "id_empleado")
        return qs.filter(
            id_empleado__isnull=False
        ).order_by("-id_activo")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["subtitle"] = "Solo activos en uso (asignados a alguien)"
        return ctx

# Rutas filtradas clásicas (si quieres mantenerlas, usa otros paths para no pisar el anterior)
urlpatterns += [
#     path("activos/disponibles/lista/", ActivosDisponiblesList.as_view(), name="activos_disponibles_lista"),
     path("activos/en-uso/",           ActivosEnUsoList.as_view(),      name="activos_en_uso"),
     path("activos/desasignar/", ActivosDesasignarView.as_view(), name="activos_desasignar"),
]

urlpatterns += [
    path("api/atributos-por-tipo/", api_atributos_por_tipo, name="api_atributos_por_tipo"),
]

urlpatterns += [
    path(
        "tipoactivos/<int:tipo_id>/atributos/",
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
    "atributosactivos/por-tipo/<int:tipo_id>/",
    editar_atributos_por_tipo,
    name="atributos_por_tipo",
),
]

# productos/urls.py (agrega esta línea donde tienes las otras de atributos)
urlpatterns += [
    path("tipoactivos/<int:tipo_id>/atributos/ver/", ver_atributos_por_tipo, name="ver_atributos_por_tipo"),
]

urlpatterns += [
    path("empresas/set/", set_company, name="set_company"),     # ← AQUI
]


urlpatterns += [
    # Historial SOLO de las mantenciones del activo
    path("activos/<int:activo_id>/historial/", views.historial_mantenciones_activo, name="activos_historial"),
    # (Opcional) Historial detallado de una mantención específica si no estaba:
    path("mantenciones/<int:id_mantencion>/historial/", historial_mantencion, name="mantencion_historial"),
    path("mantenciones/<int:pk>/historial/", views.HistorialMantencionIndividual.as_view(), name="historial_mantencion"),
]

MantencionList = view_class(Mantencion, mant_cfg, GenericList)

urlpatterns += [
    path("mantencions/", MantencionList.as_view(), name="mantencions_list"),
]


#1#########################################################324-05-2025
from django.urls import path
from . import views_atributos
urlpatterns += [
    path("atributosactivos/", views_atributos.atributosactivos_list, name="atributosactivos_list"),
    path("tipoactivos/<int:tipo_id>/atributos/", views_atributos.editar_atributos_por_tipo, name="editar_atributos_por_tipo"),
    path("tipoactivos/<int:tipo_id>/atributos/ver/", views_atributos.ver_atributos_por_tipo, name="ver_atributos_por_tipo"),
    path("atributosactivos/nuevo/", views_atributos.atributos_nuevo_wizard, name="atributosactivos_create"),
    path("api/atributos-por-tipo/", views.api_atributos_por_tipo, name="api_atributos_por_tipo"),
]
#2#########################################################324-05-2025

urlpatterns += [
    path('factura/<int:factura_id>/adjuntar/', views.factura_attach_file, name='factura_attach_file'),
    # otras rutas
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns += [
    path("facturas/", views.FacturaListView.as_view(), name="facturas_list"),
    path("facturas/<int:id_factura>/", views.FacturaDetailView.as_view(), name="facturas_detail"),
    path("factura/<int:factura_id>/adjuntar/", views.factura_attach_file, name="factura_attach_file"),
]

###############################################################################################################
###############################################################################################################0110

# productos/urls.py
from django.urls import path
from .views import RegistroListView

urlpatterns += [
    path("registros/", RegistroListView.as_view(), name="registros_list"),
]

urlpatterns += [
    path("facturas/<int:factura_id>/quitar-adjunto/",
         views.factura_quitar_adjunto,
         name="factura_quitar_adjunto"),
]