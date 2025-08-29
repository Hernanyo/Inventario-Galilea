# productos/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count
from .crud import get_crud_configs

# modelos opcionales (según tu app)
try:
    from .models_inventario import (
        Equipo, TipoEquipo, Mantencion
    )
except Exception:
    Equipo = TipoEquipo = Mantencion = None


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "overview/home_sidebar.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Menú lateral
        menu = []
        for cfg in get_crud_configs():
            try:
                count = cfg.model.objects.count()
            except Exception:
                count = 0
            menu.append({
                "name": cfg.verbose_name_plural,
                "slug": cfg.slug,
                "count": count,
                "icon": getattr(cfg, "icon", "bi-folder2")  # fallback
            })
        ctx["menu"] = menu

        # KPIs
        total_equipos = Equipo.objects.count() if Equipo else 0
        disponibles = Equipo.objects.filter(
            id_estado_equipo__descripcion__iexact="Disponible"
        ).count() if Equipo else 0
        en_uso = Equipo.objects.filter(
            id_estado_equipo__descripcion__iexact="En uso"
        ).count() if Equipo else 0
        mant_pend = Mantencion.objects.filter(
            id_estado_mantencion__tipo__iexact="Pendiente"
        ).count() if Mantencion else 0

        ctx.update({
            "total_equipos": total_equipos,
            "disponibles": disponibles,
            "en_uso": en_uso,
            "mantenciones_pendientes": mant_pend,
        })

        # Listas recientes
        ctx["ultimos_equipos"] = (
            Equipo.objects.select_related("id_marca", "id_tipo_equipo")
            .order_by("-id_equipo")[:6]
        ) if Equipo else []

        ctx["ultimas_mantenciones"] = (
            Mantencion.objects.select_related("id_equipo", "id_estado_mantencion")
            .order_by("-id_mantencion")[:6]
        ) if Mantencion else []

        # Gráficos
        if Equipo and TipoEquipo:
            datos = (
                Equipo.objects.values("id_tipo_equipo__tipo_equipo")
                .annotate(n=Count("id_equipo"))
                .order_by("id_tipo_equipo__tipo_equipo")
            )
            ctx["chart_tipos_labels"] = [
                d["id_tipo_equipo__tipo_equipo"] or "Sin tipo" for d in datos
            ]
            ctx["chart_tipos_values"] = [d["n"] for d in datos]
        else:
            ctx["chart_tipos_labels"] = []
            ctx["chart_tipos_values"] = []

        if Mantencion:
            datos = (
                Mantencion.objects.values("id_estado_mantencion__tipo")
                .annotate(n=Count("id_mantencion"))
                .order_by("id_estado_mantencion__tipo")
            )
            ctx["chart_mant_labels"] = [
                d["id_estado_mantencion__tipo"] or "Sin estado" for d in datos
            ]
            ctx["chart_mant_values"] = [d["n"] for d in datos]
        else:
            ctx["chart_mant_labels"] = []
            ctx["chart_mant_values"] = []

        return ctx
