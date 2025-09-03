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
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import ModelPermsMixin
# solo si no existe
from django import forms
from .models_inventario import Equipo
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from .models_inventario import HistorialEquipos
from django.urls import path
#from .crud import GenericList, view_class


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

    
    # devuelve una etiqueta legible para un objeto
    def obj_label(self, obj):
        # 1) si especificas label_attr en el registro de este modelo
        if self.label_attr:
            val = getattr(obj, self.label_attr, None)
            if val:
                return str(val)

        # 2) heurística general: intenta con estos campos comunes
        for name in (
            "nombre", "nombre_empresa", "nombre_equipo",
            "descripcion", "detalle", "codigo", "serie",
            "rut_empresa", "apellido"
        ):
            val = getattr(obj, name, None)
            if val:
                return str(val)

        # 3) último recurso
        return str(obj)

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    @property
    def verbose_name_plural(self):
        return self.model._meta.verbose_name_plural

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
    cols: List[str] = [pk_name]

    # Campos que queremos priorizar si existen
    prefer_order = (
        "rut", "nombre", "apellido_paterno", "apellido_materno",
        "correo", "telefono", "descripcion", "codigo", "serie",
        "departamento", "empresa", "marca", "tipo_equipo"
    )

    # 1) agrega preferidos en orden si existen y no son el PK
    for name in prefer_order:
        f = next((f for f in m._meta.fields if f.name == name), None)
        if f and f.name not in cols and f.name != pk_name:
            cols.append(f.name)

    # 2) completa con el resto de campos “mostrables”
    for f in m._meta.fields:
        if f.name in ("id", pk_name):   # <-- evita duplicar el PK
            continue
        from django.db.models import (
            CharField, TextField, BooleanField, IntegerField, FloatField,
            DateField, DateTimeField, ForeignKey
        )
        if isinstance(f, (CharField, TextField, BooleanField, IntegerField, FloatField,
                          DateField, DateTimeField, ForeignKey)):
            if f.name not in cols:
                cols.append(f.name)

        # sube el límite si quieres ver aún más columnas
        if len(cols) >= 9:  # pk + 8 útiles
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
# class GenericUpdateView(LoginRequiredMixin, UpdateView):
#     template_name = "crud/form.html"

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         obj = ctx.get("object") or getattr(self, "object", None)
#         ctx["cfg"] = self.crud_config
#         ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""   # <—
#         return ctx

# class GenericDeleteView(LoginRequiredMixin, DeleteView):
#     template_name = "crud/delete.html"
#     success_url = None  # la defines como ya la tienes

#     def get_context_data(self, **kwargs):
#         ctx = super().get_context_data(**kwargs)
#         obj = ctx.get("object") or getattr(self, "object", None)
#         ctx["cfg"] = self.crud_config
#         ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""   # <—
#         return ctx

def qr_print_view(request, pk):
    from .models_inventario import Equipo
    obj = get_object_or_404(Equipo, pk=pk)
    context = {
        "object": obj,
        "back_url": reverse_lazy("productos:equipos_list")  # slug correcto
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
        return ctx

class GenericCreate(ModelPermsMixin, CreateView):
    template_name = "crud/form.html"
    action_perm = "add"
    crud_config: CrudConfig

    def get_form_class(self):
        if self.model.__name__ == "Equipo":
            return EquipoForm
        from django.forms import modelform_factory
        return modelform_factory(self.model, fields="__all__")

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)  # <-- primero esto
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        if self.model.__name__ == "Equipo":
            from .models_inventario import Equipo
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
        from django.forms import modelform_factory
        return modelform_factory(self.model, fields="__all__")

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)  # <-- primero esto
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        if self.model.__name__ == "Equipo":
            from .models_inventario import Equipo
            ultimos_5 = Equipo.objects.order_by("-id_equipo")[:5]
            ultima = Equipo.objects.order_by("-id_equipo").first()
            ctx["ultimos_equipos"] = ultimos_5
            ctx["ultima_etiqueta"] = ultima.etiqueta if ultima else None

        return ctx
    
@dataclass
class CrudConfig:
    model: Type[Model]
    slug: str
    verbose_plural: str
    list_display: Sequence[str] = field(default_factory=list)
    search_fields: Sequence[str] = field(default_factory=list)
    ordering: Sequence[str] = field(default_factory=lambda: ("id",))
    label_attr: str | None = None

    @property
    def verbose_name_plural(self):
        # Esto hace que cualquier código que use verbose_name_plural siga funcionando
        return self.verbose_plural

    @property
    def model_name(self):
        # Para usar en templates como en list.html
        return self.model._meta.model_name

    # <-- Asegúrate de incluir esto:
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
    
class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        exclude = ["qr_code"]  # excluimos el campo qr_code, se generará automáticamente

    def save(self, commit=True):
        obj = super().save(commit=False)
        import qrcode
        from io import BytesIO
        import base64

        # Generar QR si no tiene
        if not obj.qr_code:
            qr = qrcode.QRCode(box_size=10, border=4)
            qr.add_data(obj.etiqueta)  # Aquí usas la etiqueta del equipo
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
    # usa el template que tengas creado; si tu archivo se llama delete.html, cambia esto
    template_name = "crud/delete.html"
    action_perm = "delete"
    crud_config: CrudConfig

    def get_success_url(self):
        from django.urls import reverse_lazy
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["cfg"] = self.crud_config
        return ctx

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
            path(f"{cfg.slug}/",                ListCls.as_view(),   name=f"{cfg.slug}_list"),
            path(f"{cfg.slug}/nuevo/",          CreateCls.as_view(), name=f"{cfg.slug}_create"),
            path(f"{cfg.slug}/<int:pk>/editar/",UpdateCls.as_view(), name=f"{cfg.slug}_update"),
            path(f"{cfg.slug}/<int:pk>/eliminar/", DeleteCls.as_view(), name=f"{cfg.slug}_delete"),
            path(f"{cfg.slug}/exportar/csv/",   csv_view,            name=f"{cfg.slug}_csv"),
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


HistorialListView = view_class(HistorialEquipos, historial_cfg, GenericList)

urlpatterns += [
    path("historial-equipos/", HistorialListView.as_view(), name="historial_equipos_list")
]
CRUD_CONFIGS = _collect_unique_crud_configs()

def get_crud_configs():
    return CRUD_CONFIGS

