# inventario_djanfo/productos/urls.py
#from productos.models_inventario import CategoriaActivo
from productos.crud import GenericList, view_class, api_modelos_por_tipo, api_siguiente_etiqueta
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
    #historial_mantencion,
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
from productos.crud import api_marcas_por_tipo
from productos.crud import api_modelos_por_tipo



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
    #path("dashboard/", MetricsDashboardView.as_view(), name="dashboard"),

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
        "asignadO",
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
        "id_mantencion",
        "id_activo",
        "asignado",
        "responsable",
        "id_estado_mantencion",
        "id_tipo_mantencion",
        "id_prioridad",
        "fecha",


    ],
    search_fields=[
        "descripcion",
        "id_activo__etiqueta",
        "id_activo__nombre_activo",
        "asignado__nombre",
        "asignado__apellido_paterno",
        "responsable__nombre",
        "responsable__apellido_paterno",
    ],
    ordering=["-id_mantencion"], 
)

# (opcional pero recomendado) en el mismo archivo o en views.py si prefieres:
class MantencionList(view_class(Mantencion, mant_cfg, GenericList)):
    """
    Vista que muestra la lista de mantenciones registradas en el sistema.
    Permite ordenar las mantenciones por el ID si no se proporciona un parámetro de orden.
    """
    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "id_activo",
            "asignado",
            "responsable",
            "id_estado_mantencion",
            "id_tipo_mantencion",
            "id_prioridad",
            "id_empresa",
        )
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
    
        # 👇 agrega esto:
    def get_initial(self):
        initial = super().get_initial()
        activo_id = self.request.GET.get("id_activo")
        if activo_id:
            initial["id_activo"] = activo_id
        return initial

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

# Disponibles = estado 'disponible' y sin responsable
class ActivosDisponiblesList(view_class(Activo, build_config(Activo), GenericList)):
    """
    Vista que muestra los activos disponibles en disponible sin asignar a ningún responsable.
    """
    def get_queryset(self):
        qs = super().get_queryset().select_related("id_marca", "id_tipo_activo", "id_estado_activo", "id_empleado")
        return qs.filter(
            id_estado_activo__descripcion__iexact="disponible",
            id_empleado__isnull=True,
        ).order_by("-id_activo")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["subtitle"] = "Solo activos disponibles (disponible • sin responsable)"
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
     #######path("activos/desasignar/", ActivosDesasignarView.as_view(), name="activos_desasignar"),

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
    ####path("mantenciones/<int:id_mantencion>/historial/", historial_mantencion, name="mantencion_historial"),
    ####path("mantenciones/<int:pk>/historial/", views.HistorialMantencionIndividual.as_view(), name="historial_mantencion"),
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

from . import views

urlpatterns += [
    # ... tus rutas existentes ...
    path(
        "activos/exportar/criticos-excel/",
        views.exportar_activos_criticos_excel,
        name="exportar_activos_criticos_excel",
    ),
]

path(
    "mantenciones/<int:id_mantencion>/historial/",
    HistorialMantencionDetalle.as_view(),
    name="historial_mantencion",
)

path(
    "mantenciones/<int:pk>/historial/",
    HistorialMantencionDetalle.as_view(),
    name="historial_mantencion_pk",
)
urlpatterns += [
    # ... tus otras rutas ...
    path("api/atributos-por-tipo/", api_atributos_por_tipo, name="api_atributos_por_tipo"),
]

# productos/urls.py  (o donde registras tus rutas del CRUD)
from productos.views import activo_detail


urlpatterns += [
    path("activos/<int:pk>/", activo_detail, name="activos_detail"),
]

# productos/urls.py
from productos.views import empleado_detail

urlpatterns += [
    path("empleados/<int:pk>/", empleado_detail, name="empleados_detail"),
]


# productos/urls.py
from .views import ActivosCriticosList

urlpatterns += [
    path("activos/criticos/", ActivosCriticosList.as_view(), name="activos_criticos"),
    # Ya tienes el exportador:
    # path("activos/exportar/criticos-excel/", views.exportar_activos_criticos_excel, name="exportar_activos_criticos_excel"),
]



# productos/urls.py
from .views import (
    DesasignarPorEmpleadoView,
    activos_de_empleado_json,
    DesasignarEmpleadoPostView,
)

urlpatterns += [
    # Pantalla que lista empleados con activos asignados
    path("activos/desasignar/", DesasignarPorEmpleadoView.as_view(), name="activos_desasignar"),
    # API (JSON) para cargar el modal con activos de un empleado
    path("api/empleados/<int:empleado_id>/activos/", activos_de_empleado_json, name="api_activos_de_empleado",),
    # POST que procesa la desasignación para ese empleado
    path("activos/desasignar/empleado/<int:empleado_id>/", DesasignarEmpleadoPostView.as_view(), name="activos_desasignar_de_empleado",),
]


    ###################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# API: activos disponibles (filtrados por tipo) para la empresa actual
from .views import api_activos_disponibles

urlpatterns += [
    path("api/activos/disponibles/", api_activos_disponibles, name="api_activos_disponibles"),
]

urlpatterns += [
    path("api/marcas-por-tipo/", api_marcas_por_tipo,   name="api_marcas_por_tipo"),
    path("api/modelos-por-tipo/", api_modelos_por_tipo, name="api_modelos_por_tipo"),
]

urlpatterns += [
    path("api/etiqueta/siguiente/", api_siguiente_etiqueta, name="api_siguiente_etiqueta"),
]

# productos/urls.py (o donde tengas otras vistas custom)
from productos.models_inventario import AtributoOpcionPorTipoActivo
from productos.crud import build_config, view_class, GenericList

op_cfg = build_config(AtributoOpcionPorTipoActivo)

class AtributoOpcionList(view_class(AtributoOpcionPorTipoActivo, op_cfg, GenericList)):
    def get_queryset(self):
        qs = super().get_queryset()
        attr_id = self.request.GET.get("atributo")
        if attr_id:
            qs = qs.filter(atributo_definicion_id=attr_id)
        return qs

urlpatterns += [
    path("atributoopcionportipoactivos/", AtributoOpcionList.as_view(),
         name="atributoopcionportipoactivos_list"),
]

from django.urls import path
from .views import documentos_activo_upload

urlpatterns += [
    path("activos/<int:activo_id>/documentos/", documentos_activo_upload, name="activos_documentos"),
]

urlpatterns += [
    # ... tus rutas existentes ...
    path("pma/<int:pma_id>/vigente/", views.pma_hacer_vigente, name="pma_hacer_vigente"),
    path("plan/<int:plan_id>/toggle-habilitado/", views.plan_toggle_habilitado, name="plan_toggle_habilitado"),
]

urlpatterns += [
    path(
        "planmantencions/<int:pk>/toggle/",
        views.planmantencion_toggle,
        name="planmantencion_toggle",
    ),

    # Hacer vigente un PlanMantencionActivo
    path(
        "planmantencionactivos/<int:pk>/hacer-vigente/",
        views.planmantencionactivo_hacer_vigente,
        name="planmantencionactivo_hacer_vigente",
    ),

    path('planmantencionactivo/<int:pk>/quitar-vigencia/',
         views.planmantencionactivo_quitar_vigencia,
         name='planmantencionactivo_quitar_vigencia'),
]

    ################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>04/11
urlpatterns += [
    # Otras rutas...
    path('mantencion-realizada/<int:pk>/', views.mantencion_realizada, name='mantencion_realizada'),
]

urlpatterns += [
    path("tareas-plan/<int:aplicacion_id>/", views.tareas_plan, name="tareas_plan"),
]

    ################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>05/11
urlpatterns += [
    path("api/overview/", views.overview_data, name="overview_data"),
]

#######################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>06/11
urlpatterns += [
    # ... tus rutas ...
    path("planes-aplicados/<int:pma_id>/checklist/", views.pma_checklist, name="pma_checklist"),
    path("planes-aplicados/<int:pma_id>/ejecutar/",  views.pma_ejecutar,  name="pma_ejecutar"),
]

####################################################################################>>>>>>>>>>>>>>>>>>>>>>>07/11
from .views import PmaHistorialListView#, PmaHistorialPorActivoView

urlpatterns += [
    path('mantenciones/historial-nuevo/', PmaHistorialListView.as_view(), name='pma_historial_list'),
    #path('mantenciones/historial-nuevo/activo/<int:activo_id>/', PmaHistorialPorActivoView.as_view(), name='pma_historial_por_activo'),
]

###############################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>07/11-20:06
urlpatterns += [
    # ...
    #path("mantenciones/pma/ejecucion/<int:ejec_id>/tareas.json", views.ejecucion_tareas_json, name="pma_ejec_tareas_json"),
    #path("mantencionejecucions/<int:ejec_id>/tareas.json", views.ejecucion_tareas_json, name="pma_ejec_tareas_json",),
]


urlpatterns += [
    # ...
    path("planes-aplicados/<int:aplicacion_id>/tareas/", views.tareas_plan, name="pma_tareas_plan"),
    path("planes-aplicados/<int:pma_id>/ejecutar/", views.pma_ejecutar, name="pma_ejecutar"),
    path("mantenciones/pma/ejecucion/<int:ejec_id>/tareas.json", views.ejecucion_tareas_json, name="pma_ejec_tareas_json"),
]

    ######################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>11/11 16:30
    ######################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>11/11 16:30

#############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>13/11
urlpatterns += [
    path("activos/<int:id_activo>/panel-notas/",
         views.panel_notas_activo, name="panel_notas_activo"),
    path("activos/<int:id_activo>/notas/crear/",
         views.crear_nota_activo_ajax, name="crear_nota_activo_ajax"),
]
#############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>13/11