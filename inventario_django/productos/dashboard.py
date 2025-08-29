# productos/dashboard.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.text import capfirst
from .crud import get_crud_configs

ICON_MAP = {
    "empresa": "bi-buildings",
    "proveedor": "bi-truck",
    "departamento": "bi-diagram-3",
    "empleado": "bi-people",
    "equipo": "bi-cpu",
    "tipoequipo": "bi-hdd-stack",
    "estadoequipo": "bi-check2-circle",
    "atributosequipo": "bi-sliders",
    "factura": "bi-receipt",
    "detallefactura": "bi-list-check",
    "mantencion": "bi-tools",
    "estadomantencion": "bi-clipboard2-check",
    "marca": "bi-tag",
}

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "crud/dashboard.html"

    def _icon_for(self, model_name: str) -> str:
        key = model_name.lower()
        # busca coincidencias parciales razonables
        for k, v in ICON_MAP.items():
            if k in key:
                return v
        return "bi-grid-3x3-gap"  # default

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        cards = []
        for cfg in get_crud_configs():
            m = cfg.model
            app_label = m._meta.app_label
            model_name = m._meta.model_name
            can_view = self.request.user.has_perm(f"{app_label}.view_{model_name}")
            if not can_view:
                continue

            # permisos para botones
            can_add = self.request.user.has_perm(f"{app_label}.add_{model_name}")

            # urls del CRUD
            list_name  = f"productos:{cfg.slug}_list"
            create_name = f"productos:{cfg.slug}_create"

            cards.append({
                "title": capfirst(cfg.verbose_plural) if getattr(cfg, "verbose_plural", None) else capfirst(m._meta.verbose_name_plural),
                "count": m.objects.count(),
                "icon": self._icon_for(m._meta.model_name),
                "list_url": reverse(list_name),
                "add_url": reverse(create_name) if can_add else None,
            })

        # orden alfabético por título
        cards.sort(key=lambda c: c["title"])
        ctx["cards"] = cards
        return ctx
