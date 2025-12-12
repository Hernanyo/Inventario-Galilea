# productos/overview.py
from django.views.generic import TemplateView
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .crud import get_crud_configs, _scope_by_empresa
from .mixins import filtrar_activos_por_bodegas_permitidas, filtrar_empleados_por_bodegas_permitidas


# Modelos opcionales para métricas
try:
    from .models_inventario import (
        Empleado, Departamento, Activo, TipoActivo,
        Mantencion, EstadoMantencion
    )
except Exception:
    Empleado = Departamento = Activo = TipoActivo = Mantencion = EstadoMantencion = None


@method_decorator(login_required(login_url="login"), name="dispatch")
class CardsGridView(TemplateView):
    """
    Vista que renderiza una cuadrícula de módulos (pantalla de tarjetas).
    
    Utiliza la configuración de CRUDs para mostrar un conteo de los registros 
    en cada módulo. Los módulos son representados como tarjetas, con la cantidad 
    de registros que contienen. Requiere que el usuario esté autenticado.

    **Template:** `overview/cards_grid.html`
    """
    template_name = "overview/cards_grid.html"

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de la vista, que incluye la lista de tarjetas con el 
        conteo de registros por cada módulo CRUD configurado.

        :param kwargs: Argumentos adicionales para el contexto.
        :return: Contexto con la lista de módulos y su conteo de registros.
        """

        ctx = super().get_context_data(**kwargs)
        cards = []
        for cfg in get_crud_configs():
            try:
                count = cfg.model.objects.count()
            except Exception:
                count = 0
            cards.append({"cfg": cfg, "count": count})
        ctx["cards"] = cards
        return ctx


@method_decorator(login_required(login_url="login"), name="dispatch")
class ListVerticalView(TemplateView):
    """
    Vista que renderiza un listado vertical compacto de módulos.
    
    Similar a la vista `CardsGridView`, pero muestra la información de los 
    módulos en un formato de lista vertical. Requiere que el usuario esté autenticado.

    **Template:** `overview/list_vertical.html`
    """
    template_name = "overview/list_vertical.html"

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de la vista, similar a `CardsGridView`, pero en formato 
        de lista vertical.

        :param kwargs: Argumentos adicionales para el contexto.
        :return: Contexto con la lista de módulos y su conteo de registros.
        """
        ctx = super().get_context_data(**kwargs)
        cards = []
        for cfg in get_crud_configs():
            try:
                count = cfg.model.objects.count()
            except Exception:
                count = 0
            cards.append({"cfg": cfg, "count": count})
        ctx["cards"] = cards
        return ctx


@method_decorator(login_required(login_url="login"), name="dispatch")
class MetricsDashboardView(TemplateView):
    """
    Vista que renderiza un dashboard con KPIs y métricas de los módulos.
    
    Muestra estadísticas clave sobre los registros en los modelos CRUD, incluyendo 
    conteos totales y distribuciones por categorías como empleados, activos y mantenciones. 
    Requiere que el usuario esté autenticado.

    **Template:** `overview/dashboard_metrics.html`
    """
    template_name = "overview/dashboard_metrics.html"

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto de la vista, que incluye métricas clave de los modelos 
        y estadísticas sobre empleados, activos y mantenciones.

        :param kwargs: Argumentos adicionales para el contexto.
        :return: Contexto con KPIs, conteos de registros por modelo y distribuciones por categorías.
        """
        ctx = super().get_context_data(**kwargs)

        # Conteos por modelo
        model_counts = []
        total = 0
        for cfg in get_crud_configs():
            try:
                c = cfg.model.objects.count()
            except Exception:
                c = 0
            model_counts.append((str(cfg.model._meta.verbose_name_plural), c))
            total += c

        ctx["kpis"] = [("Módulos", len(model_counts)), ("Registros totales", total)]
        ctx["model_counts"] = model_counts

        # Empleados por depto
        if Empleado and Departamento and hasattr(Empleado, "id_departamento"):
            q = (Empleado.objects
                 .values("id_departamento__nombre_departamento")
                 .annotate(n=Count("id_empleado"))
                 .order_by("id_departamento__nombre_departamento"))
            ctx["emp_by_dept"] = {
                "labels": [r["id_departamento__nombre_departamento"] or "Sin depto" for r in q],
                "data":   [r["n"] for r in q],
            }

        # Activos por tipo
        if Activo and TipoActivo and hasattr(Activo, "id_tipo_activo"):
            q = (Activo.objects
                 .values("id_tipo_activo__tipo_activo")
                 .annotate(n=Count("id_activo"))
                 .order_by("id_tipo_activo__tipo_activo"))
            ctx["activos_by_tipo"] = {
                "labels": [r["id_tipo_activo__tipo_activo"] or "Sin tipo" for r in q],
                "data":   [r["n"] for r in q],
            }

        # Mantenciones por estado
        if Mantencion and EstadoMantencion and hasattr(Mantencion, "id_estado_mantencion"):
            q = (Mantencion.objects
                 .values("id_estado_mantencion__tipo")
                 .annotate(n=Count("id_mantencion"))
                 .order_by("id_estado_mantencion__tipo"))
            ctx["mant_by_estado"] = {
                "labels": [r["id_estado_mantencion__tipo"] or "Sin estado" for r in q],
                "data":   [r["n"] for r in q],
            }

        return ctx
