# productos/overview.py
from django.views.generic import TemplateView
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .crud import get_crud_configs

# Modelos opcionales para métricas
try:
    from .models_inventario import (
        Empleado, Departamento, Equipo, TipoEquipo,
        Mantencion, EstadoMantencion
    )
except Exception:
    Empleado = Departamento = Equipo = TipoEquipo = Mantencion = EstadoMantencion = None


@method_decorator(login_required(login_url="login"), name="dispatch")
class CardsGridView(TemplateView):
    """Cuadrícula de módulos (antigua pantalla de tarjetas)."""
    template_name = "overview/cards_grid.html"

    def get_context_data(self, **kwargs):
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
    """Listado vertical compacto de módulos."""
    template_name = "overview/list_vertical.html"

    def get_context_data(self, **kwargs):
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
    """Dashboard con KPIs y gráficos."""
    template_name = "overview/dashboard_metrics.html"

    def get_context_data(self, **kwargs):
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

        # Equipos por tipo
        if Equipo and TipoEquipo and hasattr(Equipo, "id_tipo_equipo"):
            q = (Equipo.objects
                 .values("id_tipo_equipo__tipo_equipo")
                 .annotate(n=Count("id_equipo"))
                 .order_by("id_tipo_equipo__tipo_equipo"))
            ctx["equipos_by_tipo"] = {
                "labels": [r["id_tipo_equipo__tipo_equipo"] or "Sin tipo" for r in q],
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
