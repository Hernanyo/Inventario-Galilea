# productos/crud.py
from dataclasses import dataclass, field
from typing import Sequence, List, Type
import csv

from django.apps import apps
from django.db.models import Q, Model, CharField, TextField, BooleanField, \
                             IntegerField, FloatField, ForeignKey, DateField, DateTimeField
from django.forms import modelform_factory
from django.http import HttpResponse
from django.urls import path, reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin  # (si ModelPermsMixin lo usa)
from .mixins import ModelPermsMixin

from django import forms
from django.shortcuts import get_object_or_404, render

from .models_inventario import Equipo, HistorialEquipos


# ---------- Config e inferencia ----------

@dataclass
class CrudConfig:
    model: Type[Model]
    slug: str                     # p.ej. "equipos"
    verbose_plural: str           # p.ej. "Equipos"
    list_display: Sequence[str] = field(default_factory=list)   # columnas
    search_fields: Sequence[str] = field(default_factory=list)  # campos texto
    ordering: Sequence[str] = field(default_factory=lambda: ("id",))
    label_attr: str | None = None

    # etiqueta legible para un objeto
    def obj_label(self, obj):
        if self.label_attr:
            val = getattr(obj, self.label_attr, None)
            if val:
                return str(val)
        for name in (
            "nombre", "nombre_empresa", "nombre_equipo",
            "descripcion", "detalle", "codigo", "serie",
            "rut_empresa", "apellido"
        ):
            val = getattr(obj, name, None)
            if val:
                return str(val)
        return str(obj)

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        # permite usar verbose_name_plural desde templates/código
        return self.verbose_plural

    @property
    def model_name(self):
        # útil en templates para decidir botones especiales
        return self.model._meta.model_name


def infer_text_fields(m: Type[Model]) -> List[str]:
    names = [
        f.name for f in m._meta.get_fields()
        if getattr(f, "attname", None) and isinstance(f, (CharField, TextField))
    ]
    prefer = [n for n in ("nombre", "descripcion", "serie", "modelo") if n in names]
    rest = [n for n in names if n not in prefer]
    return prefer + rest


def infer_list_display(m: Type[Model]) -> List[str]:
    pk_name = m._meta.pk.name
    cols: List[str] = [pk_name]

    prefer_order = (
        "rut", "nombre", "apellido_paterno", "apellido_materno",
        "correo", "telefono", "descripcion", "codigo", "serie",
        "departamento", "empresa", "marca", "tipo_equipo"
    )

    # 1) preferidos si existen
    for name in prefer_order:
        f = next((f for f in m._meta.fields if f.name == name), None)
        if f and f.name not in cols and f.name != pk_name:
            cols.append(f.name)

    # 2) completa con campos "mostrables"
    for f in m._meta.fields:
        if f.name in ("id", pk_name):
            continue
        from django.db.models import (
            CharField, TextField, BooleanField, IntegerField, FloatField,
            DateField, DateTimeField, ForeignKey
        )
        if isinstance(f, (CharField, TextField, BooleanField, IntegerField, FloatField,
                          DateField, DateTimeField, ForeignKey)):
            if f.name not in cols:
                cols.append(f.name)
        if len(cols) >= 9:  # pk + 8 útiles
            break

    return cols or [pk_name]


def make_slug(m: Type[Model]) -> str:
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


# ---------- Vistas y helpers ----------

def qr_print_view(request, pk):
    obj = get_object_or_404(Equipo, pk=pk)
    context = {
        "object": obj,
        "back_url": reverse_lazy("productos:equipos_list")
    }
    return render(request, "equipos/qr_print.html", context)


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
            pk_name = self.model._meta.pk.name
            if order.lstrip("-") == "id":
                order = order.replace("id", pk_name, 1)
            qs = qs.order_by(order)
        else:
            qs = qs.order_by(*self.crud_config.ordering)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

                # 👇 ESTA ES LA CLAVE: calcula si el usuario puede crear este modelo
        can_create = self.request.user.has_perm(
            f"{self.model._meta.app_label}.add_{self.model._meta.model_name}"
        )
        # pásalo al template como parte del config (para que el template actual funcione)
        self.crud_config.can_create = can_create
        # (opcional) también en el contexto por si te sirve en otros templates
        ctx["can_create"] = can_create

        return ctx


class GenericCreate(ModelPermsMixin, CreateView):
    template_name = "crud/form.html"
    action_perm = "add"
    crud_config: CrudConfig

    def get_form_class(self):
        if self.model.__name__ == "Equipo":
            return EquipoForm
        return modelform_factory(self.model, fields="__all__")

    def get_success_url(self):
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

    def form_valid(self, form):
        if self.model.__name__ == "Equipo":
            # guarda el usuario actual (Empleado vinculado)
            form.instance._usuario_actual = getattr(self.request.user, "empleado", None)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        if self.model.__name__ == "Equipo":
            ultimos_5 = Equipo.objects.order_by("-id_equipo")[:5]
            ultima = Equipo.objects.order_by("-id_equipo").first()
            ctx["ultimos_equipos"] = ultimos_5
            ctx["ultima_etiqueta"] = ultima.etiqueta if ultima else None

        return ctx


class GenericUpdate(ModelPermsMixin, UpdateView):
    template_name = "crud/form.html"
    action_perm = "change"
    crud_config: CrudConfig

    def get_form_class(self):
        if self.model.__name__ == "Equipo":
            return EquipoForm
        return modelform_factory(self.model, fields="__all__")

    def get_success_url(self):
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

    def form_valid(self, form):
        if self.model.__name__ == "Equipo":
            form.instance._usuario_actual = getattr(self.request.user, "empleado", None)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        if self.model.__name__ == "Equipo":
            ultimos_5 = Equipo.objects.order_by("-id_equipo")[:5]
            ultima = Equipo.objects.order_by("-id_equipo").first()
            ctx["ultimos_equipos"] = ultimos_5
            ctx["ultima_etiqueta"] = ultima.etiqueta if ultima else None

        return ctx


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        exclude = ["qr_code"]  # se genera automáticamente

    def save(self, commit=True):
        obj = super().save(commit=False)
        import qrcode
        from io import BytesIO
        import base64

        # Generar QR si no tiene
        if not obj.qr_code and obj.etiqueta:
            qr = qrcode.QRCode(box_size=10, border=4)
            qr.add_data(obj.etiqueta)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            obj.qr_code = img_str

        if commit:
            obj.save()
        return obj


class GenericDelete(ModelPermsMixin, DeleteView):
    template_name = "crud/delete.html"
    action_perm = "delete"
    crud_config: CrudConfig

    def get_success_url(self):
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["cfg"] = self.crud_config
        return ctx


# ---------- Export CSV ----------

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
                val = getattr(r, col, "")
                out.append("" if val is None else str(val))
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
            path(f"{cfg.slug}/",                  ListCls.as_view(),    name=f"{cfg.slug}_list"),
            path(f"{cfg.slug}/nuevo/",            CreateCls.as_view(),  name=f"{cfg.slug}_create"),
            path(f"{cfg.slug}/<int:pk>/editar/",  UpdateCls.as_view(),  name=f"{cfg.slug}_update"),
            path(f"{cfg.slug}/<int:pk>/eliminar/",DeleteCls.as_view(),  name=f"{cfg.slug}_delete"),
            path(f"{cfg.slug}/exportar/csv/",     csv_view,             name=f"{cfg.slug}_csv"),
        ]
    return patterns


# Se exporta listo para incluir desde productos/urls.py
urlpatterns = make_urlpatterns()


# --- al final de productos/crud.py ---

def _collect_unique_crud_configs():
    configs = []
    for p in urlpatterns:
        vc = getattr(p.callback, "view_class", None)
        cfg = getattr(vc, "crud_config", None)
        if cfg:
            configs.append(cfg)

    # dedup por modelo (único por app_label.model_name)
    uniq, seen = [], set()
    for cfg in configs:
        key = cfg.model._meta.label_lower  # p.ej. "productos.empresa"
        if key in seen:
            continue
        seen.add(key)
        uniq.append(cfg)
    return uniq


# Config opcional para el menú (si quisieras mostrar Historial en HomeView)
historial_cfg = CrudConfig(
    model=HistorialEquipos,
    slug="historial-equipos",
    verbose_plural="Historial de Equipos",
    list_display=[
        "equipo", "accion", "usuario", "fecha", "estado_anterior", "estado_nuevo"
    ],
    search_fields=["equipo__nombre_equipo", "usuario__nombre", "accion"],
    ordering=["-fecha"]
)

CRUD_CONFIGS = _collect_unique_crud_configs()

def get_crud_configs():
    return CRUD_CONFIGS
