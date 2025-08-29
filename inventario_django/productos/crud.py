# productos/crud.py
from dataclasses import dataclass, field
from typing import Sequence, List, Dict, Type
import csv

from django.apps import apps
from django.db.models import Q, Model, CharField, TextField, BooleanField, \
                             IntegerField, FloatField, ForeignKey, DateField, DateTimeField
from django.forms import modelform_factory
from django.http import HttpResponse
from django.urls import path, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .mixins import ModelPermsMixin

# ---------- Config e inferencia ----------

@dataclass
class CrudConfig:
    model: Type[Model]
    slug: str                     # p.ej. "equipos"
    verbose_plural: str           # p.ej. "Equipos"
    list_display: Sequence[str] = field(default_factory=list)   # columnas
    search_fields: Sequence[str] = field(default_factory=list)  # campos texto
    ordering: Sequence[str] = field(default_factory=lambda: ("id",))

def infer_text_fields(m: Type[Model]) -> List[str]:
    names = [
        f.name for f in m._meta.get_fields()
        if getattr(f, "attname", None) and isinstance(f, (CharField, TextField))
    ]
    # boosts habituales si existen
    prefer = [n for n in ("nombre", "descripcion", "serie", "modelo") if n in names]
    rest = [n for n in names if n not in prefer]
    return prefer + rest

def infer_list_display(m: Type[Model]) -> List[str]:
    pk_name = m._meta.pk.name
    cols: List[str] = [ pk_name]
    for f in m._meta.fields:
        if f.name in ("id",):
            continue
        from django.db.models import (
            CharField, TextField, BooleanField, IntegerField, FloatField,
            DateField, DateTimeField, ForeignKey
        )
        if isinstance(f, (CharField, TextField, BooleanField, IntegerField, FloatField,
                          DateField, DateTimeField, ForeignKey)):
            cols.append(f.name)
        if len(cols) >= 6:  # 1 id + 5 campos útiles
            break
    return cols or [pk_name]

def make_slug(m: Type[Model]) -> str:
    # plural simple: agrega 's'. Para nombres que ya terminen en 's' se mantiene.
    base = m._meta.model_name
    return base if base.endswith("s") else f"{base}s"

def build_config(m: Type[Model]) -> CrudConfig:
    return CrudConfig(
        model=m,
        slug=make_slug(m),
        verbose_plural=m._meta.verbose_name_plural.title(),
        list_display=infer_list_display(m),
        search_fields=infer_text_fields(m),
        ordering=(m._meta.pk.name,),
    )

# ---------- Vistas genéricas ----------

class GenericList(ModelPermsMixin, ListView):
    template_name = "crud/list.html"
    context_object_name = "items"
    paginate_by = 25
    action_perm = "view"
    crud_config: CrudConfig

    def get_queryset(self):
        q = self.request.GET.get("q", "").strip()
        order = self.request.GET.get("o", "")
        qs = self.model.objects.all()
        if q and self.crud_config.search_fields:
            cond = Q()
            for f in self.crud_config.search_fields:
                cond |= Q(**{f"{f}__icontains": q})
            qs = qs.filter(cond)
        if order:
            # Compatibilidad: si alguien pasa "id", usar el PK real
            pk_name = self.model._meta.pk.name
            if order.lstrip("-") == "id":
                order = order.replace("id", pk_name, 1)
            qs = qs.order_by(order)
        else:
            qs = qs.order_by(*self.crud_config.ordering)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["cfg"] = self.crud_config
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        return ctx

class GenericCreate(ModelPermsMixin, CreateView):
    template_name = "crud/form.html"
    action_perm = "add"
    crud_config: CrudConfig

    def get_form_class(self):
        return modelform_factory(self.model, fields="__all__")

    def get_success_url(self):
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

class GenericUpdate(ModelPermsMixin, UpdateView):
    template_name = "crud/form.html"
    action_perm = "change"
    crud_config: CrudConfig

    def get_form_class(self):
        return modelform_factory(self.model, fields="__all__")

    def get_success_url(self):
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

class GenericDelete(ModelPermsMixin, DeleteView):
    template_name = "crud/confirm_delete.html"
    action_perm = "delete"
    crud_config: CrudConfig

    def get_success_url(self):
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

def export_csv_view(model: Type[Model], cfg: CrudConfig):
    def view(request):
        if not request.user.has_perm(f"{model._meta.app_label}.view_{model._meta.model_name}"):
            return HttpResponse(status=403)
        q = request.GET.get("q", "").strip()
        rows = model.objects.all()
        if q and cfg.search_fields:
            cond = Q()
            for f in cfg.search_fields:
                cond |= Q(**{f"{f}__icontains": q})
            rows = rows.filter(cond)

        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="{cfg.slug}.csv"'
        w = csv.writer(resp)
        w.writerow(cfg.list_display)
        for r in rows:
            out = []
            for col in cfg.list_display:
                out.append(getattr(r, col, ""))
            w.writerow(out)
        return resp
    return view

# ---------- Registro automático de modelos y URL patterns ----------

def discover_producto_models() -> List[Type[Model]]:
    """Toma todos los modelos de la app 'productos' (incluye models_inventario si está importado)."""
    return list(apps.get_app_config("productos").get_models())

def view_class(model, cfg, base_cls):
    # Crea una subclase dinámica con el modelo y la cfg incrustados
    return type(
        f"{model.__name__}{base_cls.__name__}",
        (base_cls,),
        {"model": model, "crud_config": cfg}
    )

def make_urlpatterns(include: Sequence[Type[Model]] | None = None):
    models = include if include else discover_producto_models()
    patterns = []
    for m in models:
        cfg = build_config(m)

        ListCls   = view_class(m, cfg, GenericList)
        CreateCls = view_class(m, cfg, GenericCreate)
        UpdateCls = view_class(m, cfg, GenericUpdate)
        DeleteCls = view_class(m, cfg, GenericDelete)
        csv_view  = export_csv_view(m, cfg)

        patterns += [
            path(f"{cfg.slug}/",                ListCls.as_view(),   name=f"{cfg.slug}_list"),
            path(f"{cfg.slug}/nuevo/",          CreateCls.as_view(), name=f"{cfg.slug}_create"),
            path(f"{cfg.slug}/<int:pk>/editar/",UpdateCls.as_view(), name=f"{cfg.slug}_update"),
            path(f"{cfg.slug}/<int:pk>/eliminar/", DeleteCls.as_view(), name=f"{cfg.slug}_delete"),
            path(f"{cfg.slug}/exportar/csv/",   csv_view,            name=f"{cfg.slug}_csv"),
        ]
    return patterns

# Se exporta listo para incluir desde productos/urls.py
urlpatterns = make_urlpatterns()

# Al final de productos/crud.py
CRUD_CONFIGS = [p.callback.view_class.crud_config for p in urlpatterns if hasattr(getattr(p.callback, "view_class", None), "crud_config")]
def get_crud_configs():
    return CRUD_CONFIGS

