# productos/crud.py
#from .models_inventario import CategoriaActivo
from .models import HistorialMantencionesLog
from django.utils.dateparse import parse_date
import json

from django.contrib.auth.decorators import login_required
from .utils import crear_usuario_y_enviar_correo, sync_user_groups_for_empleado

from productos.utils import crear_usuario_y_enviar_correo
from dataclasses import dataclass, field
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey, OneToOneField
from .models_inventario import Marca, Proveedor, TipoActivo, EstadoActivo
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
from .models_inventario import Activo, HistorialActivos
from django.core.exceptions import ValidationError
from django.db import connection
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from datetime import datetime, timedelta
from django.db import connection
from django.utils import timezone
from django.db import connection
# crud.py
from productos.forms import MantencionForm, EmpleadoForm
from .models_inventario import AgregacionAtributosPorActivo, AtributosActivo
from django.db import transaction
# --- NUEVO: mixin para limitar por empresa (si el modelo tiene id_empresa) ---
from django.core.exceptions import FieldDoesNotExist
from .mixins import EmpresaScopeMixin
from .mixins import SaveEmpresaMixin
from .models_inventario import Empleado, Departamento  # al inicio del archivo
from .utils import crear_usuario_y_enviar_correo






from productos.models_inventario import HistorialMantencionesLog  # evitar ciclos
from productos.forms import MantencionForm
# arriba de _build_default_form (o dentro), suma estos imports de tipos de campo
from django.db.models import FileField, ImageField
from django.forms import ClearableFileInput

def _build_default_form(model):
    from django.db.models import DateField, DateTimeField, ForeignKey, TextField, BooleanField, IntegerField, FloatField
    widgets = {}
    for f in model._meta.fields:
        if not getattr(f, "editable", True):
            continue
        if isinstance(f, ForeignKey):
            widgets[f.name] = forms.Select(attrs={"class": "form-select"})
        elif isinstance(f, DateTimeField):
            widgets[f.name] = forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"})
        elif isinstance(f, DateField):
            widgets[f.name] = forms.DateInput(attrs={"type": "date", "class": "form-control"})
        elif isinstance(f, TextField):
            widgets[f.name] = forms.Textarea(attrs={"rows": 3, "class": "form-control"})
        elif isinstance(f, BooleanField):
            widgets[f.name] = forms.CheckboxInput(attrs={"class": "form-check-input"})
        elif isinstance(f, (IntegerField, FloatField)):
            widgets[f.name] = forms.NumberInput(attrs={"class": "form-control"})
        # 👇 **NUEVO: soporta archivos**
        elif isinstance(f, (FileField, ImageField)):
            widgets[f.name] = ClearableFileInput(attrs={"class": "form-control"})
        else:
            widgets[f.name] = forms.TextInput(attrs={"class": "form-control"})
    return modelform_factory(model, fields="__all__", widgets=widgets)

def _empresa_field_info(model) -> tuple[bool, bool]:
    """
    Devuelve (existe, es_relacion) para el campo 'id_empresa' del modelo.
    """
    try:
        f = model._meta.get_field("id_empresa")
    except FieldDoesNotExist:
        return (False, False)
    return (True, isinstance(f, (ForeignKey, OneToOneField)))

def _model_has_empresa_fk(model) -> bool:
    f = next((f for f in model._meta.get_fields() if getattr(f, "name", None) == "id_empresa"), None)
    return bool(f and getattr(f, "is_relation", False))

# ---------- Config e inferencia ----------

@dataclass
class CrudConfig:
    model: Type[Model]
    slug: str                     # p.ej. "activos"
    verbose_plural: str           # p.ej. "Activos"
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
            "nombre", "nombre_empresa", "nombre_activo",
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
        "correo", "telefono", "descripcion", "observaciones", "codigo", "serie",
        "departamento", "empresa", "marca", "tipo_activo"
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


#####################################################
#####################################################
# ---------- Filtro avanzado (helpers seguros) ----------

def _field_kind(model, field_name):
    """
    Devuelve 'fk' | 'char' | 'num' | 'bool' | 'date' | 'other'
    o None si no existe el campo en el modelo.
    """
    try:
        f = model._meta.get_field(field_name)
    except Exception:
        return None
    from django.db.models import (
        CharField, TextField, BooleanField, IntegerField, BigIntegerField, FloatField,
        DateField, DateTimeField, ForeignKey, OneToOneField
    )
    if isinstance(f, (ForeignKey, OneToOneField)):
        return "fk"
    if isinstance(f, (CharField, TextField)):
        return "char"
    if isinstance(f, (IntegerField, BigIntegerField, FloatField)):
        return "num"
    if isinstance(f, BooleanField):
        return "bool"
    if isinstance(f, (DateField, DateTimeField)):
        return "date"
    return "other"


def _build_adv_fields_from_list_display(model, list_display):
    """
    Devuelve [{"name":..., "label":..., "type":...}, ...] para columnas reales del modelo.
    No rompe si una col no es un Field real (la salta).
    """
    label_overrides = {
        "id_activo": "Id Activo",
        "nombre_activo": "Nombre Activo",
        "id_tipo_activo": "Id Tipo Activo",
        "id_estado_activo": "Id Estado Activo",
        "id_marca": "Id Marca",
        "id_proveedor": "Id Proveedor",
        "id_empleado": "Responsable",
        "observaciones": "Observaciones",
        "etiqueta": "Etiqueta",
    }
    out = []
    for col in list_display:
        kind = _field_kind(model, col)
        if not kind:
            continue
        label = label_overrides.get(col) or col.replace("_", " ").title()
        out.append({"name": col, "label": label, "type": kind})
    return out


def _adv_choices_for_fk_fields(request, model, adv_fields):
    """
    Para campos 'fk' arma choices [{value: pk, label: str(obj)}] con scope por empresa si aplica.
    """
    emp_id = request.session.get("empresa_id")
    choices = {}
    for af in adv_fields:
        if af["type"] != "fk":
            continue
        f = model._meta.get_field(af["name"])  # ForeignKey
        rel = f.remote_field.model
        qs = rel.objects.all()
        # Si el relacionado tiene id_empresa, filtra
        if hasattr(rel, "id_empresa_id") and emp_id:
            qs = qs.filter(id_empresa_id=emp_id)
        # orden legible si existe
        for cand in ("nombre", "descripcion", "razon_social", "tipo_activo", "marca", "modelo"):
            try:
                rel._meta.get_field(cand)
                qs = qs.order_by(cand)
                break
            except Exception:
                continue
        choices[af["name"]] = [{"value": obj.pk, "label": str(obj)} for obj in qs[:500]]
    return choices


def _apply_advanced_filter(qs, model, field_name, raw_value):
    """
    Aplica filtro seguro según el tipo del campo.
    - fk: si fv es dígito filtra por pk; si no, intenta buscar por campos 'nombre/descripcion/...'
    - char: icontains
    - num: exact (si es dígito); si no, none()
    - bool: true/false/1/0/si/no
    - date/datetime: intenta parsear YYYY-MM-DD -> __date, si no, startswith como string
    """
    if not field_name:
        return qs
    kind = _field_kind(model, field_name)
    if not kind:
        return qs

    fv = (raw_value or "").strip()
    if fv == "":
        return qs

    from django.db.models import Q, CharField, TextField, ForeignKey, OneToOneField, DateField, DateTimeField
    f = model._meta.get_field(field_name)

    if kind in ("char",):
        return qs.filter(**{f"{field_name}__icontains": fv})

    if kind == "num":
        return qs.filter(**{field_name: fv}) if fv.isdigit() else qs.none()

    if kind == "bool":
        v = fv.lower()
        t = {"true", "1", "t", "y", "yes", "si", "sí"}
        fa = {"false", "0", "f", "n", "no"}
        if v in t:
            return qs.filter(**{field_name: True})
        if v in fa:
            return qs.filter(**{field_name: False})
        return qs

    if kind == "date":
        d = parse_date(fv)
        if d:
            return qs.filter(**{f"{field_name}__date": d})
        return qs.filter(**{f"{field_name}__startswith": fv})

    if kind == "fk":
        if fv.isdigit():
            return qs.filter(**{field_name: int(fv)})
        # búsqueda “humana” en el relacionado si no vino id
        rel = f.remote_field.model
        for cand in ("nombre", "descripcion", "razon_social", "tipo_activo", "marca", "modelo"):
            try:
                rel._meta.get_field(cand)
                return qs.filter(**{f"{field_name}__{cand}__icontains": fv})
            except Exception:
                continue
        return qs

    # other -> no filtra
    return qs
#####################################################
#####################################################
# ---------- Vistas y helpers ----------

def qr_print_view(request, pk):
    obj = get_object_or_404(Activo, pk=pk)
    context = {
        "object": obj,
        "back_url": reverse_lazy("productos:activos_list")
    }
    return render(request, "activos/qr_print.html", context)


class GenericList(EmpresaScopeMixin, ModelPermsMixin, ListView):
    template_name = "crud/list.html"
    context_object_name = "items"
    paginate_by = 25
    action_perm = "view"
    crud_config: CrudConfig

#111111111111111111111111111##########################################################################################################
    def get_queryset(self):
        q = (self.request.GET.get("q") or "").strip()
        order = (self.request.GET.get("o") or "").strip()
        qs = self.model.objects.all()

        # === BÚSQUEDA RÁPIDA: textos + (si q es número) IDs/numéricos/FKs ===
        if q:
            cond = Q()

            # 1) Texto sobre search_fields
            if getattr(self.crud_config, "search_fields", None):
                for f in self.crud_config.search_fields:
                    cond |= Q(**{f"{f}__icontains": q})

            # 2) Si q es número: PK + numéricos + FKs
            if q.isdigit():
                num = int(q)
                pk_name = self.model._meta.pk.name
                cond |= Q(**{pk_name: num})

                from django.db.models import IntegerField, BigIntegerField, ForeignKey
                for f in self.model._meta.fields:
                    if f.name == pk_name:
                        continue
                    if isinstance(f, (IntegerField, BigIntegerField)):
                        cond |= Q(**{f.name: num})
                    elif isinstance(f, ForeignKey):
                        cond |= Q(**{f.name: num})  # usar el nombre del FK (no *_id)

            qs = qs.filter(cond)

        # === FILTRO AVANZADO: ?f=<campo>&fv=<valor> ===
        f = (self.request.GET.get("f") or "").strip()
        fv = (self.request.GET.get("fv") or "").strip()

        if f and fv != "":
            # Si viene "id" desde algún select, reemplazar por el nombre real del PK
            if f == "id":
                f = self.model._meta.pk.name

            base = f.split("__")[0]  # por si algún día usamos lookups relacionados
            try:
                field = self.model._meta.get_field(base)
            except Exception:
                field = None

            from django.db.models import (
                CharField, TextField, IntegerField, BigIntegerField, BooleanField,
                DateField, DateTimeField, ForeignKey
            )
            from django.utils.dateparse import parse_date

            if field is not None:
                # Texto
                if isinstance(field, (CharField, TextField)):
                    qs = qs.filter(**{f"{f}__icontains": fv})

                # Numérico
                elif isinstance(field, (IntegerField, BigIntegerField)):
                    try:
                        qs = qs.filter(**{f: int(fv)})
                    except ValueError:
                        qs = qs.none()

                # Booleano
                elif isinstance(field, BooleanField):
                    v = fv.strip().lower()
                    truthy = {"true", "1", "t", "sí", "si", "y", "yes"}
                    falsy  = {"false", "0", "f", "no", "n"}
                    if v in truthy:
                        qs = qs.filter(**{f: True})
                    elif v in falsy:
                        qs = qs.filter(**{f: False})
                    # si no matchea, no filtra

                # Fecha / FechaHora
                elif isinstance(field, (DateField, DateTimeField)):
                    d = parse_date(fv)
                    if d:
                        if isinstance(field, DateTimeField):
                            qs = qs.filter(**{f"{f}__date": d})
                        else:
                            qs = qs.filter(**{f: d})
                    else:
                        qs = qs.filter(**{f"{f}__startswith": fv})

                # ForeignKey
                elif isinstance(field, ForeignKey):
                    if fv.isdigit():
                        qs = qs.filter(**{f: int(fv)})  # nombre del FK
                    else:
                        rel_model = field.remote_field.model
                        for cand in ("nombre", "descripcion", "tipo_activo",
                                    "razon_social", "empresa", "marca", "modelo"):
                            try:
                                rel_model._meta.get_field(cand)
                                qs = qs.filter(**{f"{f}__{cand}__icontains": fv})
                                break
                            except Exception:
                                continue
                # otros tipos: sin filtro

        # Orden
        if order:
            pk_name = self.model._meta.pk.name
            if order.lstrip("-") == "id":
                order = order.replace("id", pk_name, 1)
            qs = qs.order_by(order)
        else:
            qs = qs.order_by(*self.crud_config.ordering)

        # Alcance por empresa (u otros)
        return self.scope_queryset(qs)
##2222222222222222222222222222222#########################################################################################################

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        # permisos para botones (Nuevo/Editar/Eliminar)
        user = self.request.user
        app = self.model._meta.app_label
        model = self.model._meta.model_name

        can_create = user.has_perm(f"{app}.add_{model}")
        can_change = user.has_perm(f"{app}.change_{model}")
        can_delete = user.has_perm(f"{app}.delete_{model}")

        # disponibles tanto en cfg como en el contexto
        self.crud_config.can_create = can_create
        self.crud_config.can_change = can_change
        self.crud_config.can_delete = can_delete
        ctx["can_create"] = can_create
        ctx["can_change"] = can_change
        ctx["can_delete"] = can_delete

        ###########################################################################################################
        # === NUEVO: datos del filtro avanzado (no rompe si no se usa) ===
        adv_fields = _build_adv_fields_from_list_display(self.model, self.crud_config.list_display)
        ctx["adv_fields"] = adv_fields
        ctx["f"] = (self.request.GET.get("f") or "").strip()
        ctx["fv"] = (self.request.GET.get("fv") or "").strip()
        # choices para FKs (en JSON para usar desde JS si quieres)
        adv_choices = _adv_choices_for_fk_fields(self.request, self.model, adv_fields)
        ctx["adv_choices_json"] = json.dumps(adv_choices, ensure_ascii=False)
        
        ctx["adv_fields_json"] = json.dumps(adv_fields, ensure_ascii=False)
        
        #############################################################################################################

        if self.model._meta.model_name == "atributosactivo":
            from .models_inventario import TipoActivo
            emp_id = self.request.session.get("empresa_id")
            te_qs = TipoActivo.objects.all()
            if emp_id:
                te_qs = te_qs.filter(id_empresa_id=emp_id)
            ctx["tipos_activo"] = te_qs.order_by("tipo_activo")
        return ctx


class GenericCreate(SaveEmpresaMixin, EmpresaScopeMixin, ModelPermsMixin, CreateView):
    template_name = "crud/form.html"
    action_perm = "add"
    crud_config: CrudConfig

    def get_form_class(self):
        if self.model.__name__ == "Activo":
            return ActivoForm
        if self.model.__name__ == "Mantencion":
            from productos.forms import MantencionForm
            return MantencionForm
        if self.model.__name__ == "Empleado":
            from productos.forms import EmpleadoForm
            return EmpleadoForm
        # fallback genérico para cualquier otro modelo (Departamento, Marca, etc.)
        return _build_default_form(self.model)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        emp_id = self.request.session.get("empresa_id")
        if not emp_id:
            return form

        for field in form.fields.values():
            qs = getattr(field, "queryset", None)
            if qs is None:
                continue

            mdl = qs.model

            # Si el combo es Empresa -> filtra por pk
            if mdl._meta.model_name == "empresa":
                field.queryset = mdl.objects.filter(pk=emp_id)
                continue

            # Si el modelo del combo TIENE FK id_empresa -> filtra por esa FK
            if _model_has_empresa_fk(mdl):
                field.queryset = qs.filter(id_empresa_id=emp_id)
            else:
                # si existiera id_empresa como entero en ese modelo relacionado:
                exists, _ = _empresa_field_info(mdl)
                if exists:
                    field.queryset = qs.filter(id_empresa=emp_id)

            # Si no, lo dejamos tal cual
        return form

    def get_success_url(self):
        # productos: <slug>_list  -> p.ej. productos:departamentos_list
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # MUY IMPORTANTE: pasar archivos en métodos de escritura
        if self.request.method in ("POST", "PUT", "PATCH"):
            kwargs["data"] = self.request.POST
            kwargs["files"] = self.request.FILES
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        emp_id = self.request.session.get("empresa_id")  # ⬅️ añade esto
#1#############################################################################################24-09-2025
                # Filtrar los tipos de activo por la empresa activa
        if self.model.__name__ == "Activo":
            from .models_inventario import TipoActivo
            qs = TipoActivo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)  # Aquí se filtra por empresa activa
            ctx["tipos_activo"] = qs.order_by("tipo_activo")
#2#############################################################################################24-09-2025
        # ACTIVO: ya tenías sidebar propio
        if self.model.__name__ == "Activo":
            qs = Activo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)              # ⬅️ filtro
            ultimos = qs.order_by("-id_activo")[:15]
            ultima  = qs.order_by("-id_activo").first()
            ctx["ultimos_activos"] = ultimos
            ctx["ultima_etiqueta"] = ultima.etiqueta if ultima else None

        # MANTENCION: últimas mantenciones
        elif self.model.__name__ == "Mantencion":
            from .models_inventario import Mantencion as Mant
            qs = Mant.objects.all()
            if emp_id:
                # si el modelo no tiene id_empresa, filtramos por el activo
                if "id_empresa" in {f.name for f in Mant._meta.get_fields()}:
                    qs = qs.filter(id_empresa_id=emp_id)
                else:
                    qs = qs.filter(id_activo__id_empresa_id=emp_id)
            ctx["side_title"] = "Últimas mantenciones"
            ctx["side_items"] = qs.select_related("id_activo").order_by("-id_mantencion")[:15]

        # EMPRESA: últimas empresas
        elif self.model.__name__ == "Empresa":
            from .models_inventario import Empresa as Emp
            emp_id = self.request.session.get("empresa_id")
            qs = Emp.objects.all()
            if emp_id:
                qs = qs.filter(pk=emp_id)
            ctx["side_title"] = "Últimas empresas"
            ctx["side_items"] = qs.order_by("-id_empresa")[:15]

        elif self.model.__name__ == "Empleado":
            from .models_inventario import Empleado as Emp
            emp_id = self.request.session.get("empresa_id")
            qs = Emp.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos empleados"
            ctx["side_items"] = qs.order_by("-id_empleado")[:15]

        elif self.model.__name__ == "Marca":
            from .models_inventario import Marca as M
            qs = M.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)      # ⬅️ filtro
            ctx["side_title"] = "Últimas marcas"
            ctx["side_items"] = qs.order_by("-id_marca")[:15]   # ⬅️ usa qs

        elif self.model.__name__ == "Proveedor":
            from .models_inventario import Proveedor as P
            qs = P.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)      # ⬅️ filtro
            ctx["side_title"] = "Últimos proveedores"
            ctx["side_items"] = qs.order_by("-id_proveedor")[:15]  # ⬅️ usa qs

        elif self.model.__name__ == "Factura":
            from .models_inventario import Factura as F
            ctx["side_title"] = "Últimas facturas"
            ctx["side_items"] = F.objects.order_by("-id_factura")[:15]

        elif self.model.__name__ == "Departamento":
            from .models_inventario import Departamento as D
            qs = D.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos departamentos"
            ctx["side_items"] = qs.order_by("-id_departamento")[:5]  # Los últimos 5 registros
        
        elif self.model.__name__ == "Factura":
            from .models_inventario import Factura as F
            qs = F.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimas facturas"
            ctx["side_items"] = qs.order_by("-id_factura")[:5]  # Los últimos 5 registros

        elif self.model.__name__ == "EstadoActivo":
            from .models_inventario import EstadoActivo
            qs = EstadoActivo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos estados de activo"
            ctx["side_items"] = qs.order_by("-id_estado_activo")[:15]

        elif self.model.__name__ == "TipoMantencion":
            from .models_inventario import TipoMantencion
            qs = TipoMantencion.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos tipos de mantención"
            ctx["side_items"] = qs.order_by("-id_tipo_mantencion")[:15]
        
        elif self.model.__name__ == "PrioridadMantencion":
            from .models_inventario import PrioridadMantencion
            qs = PrioridadMantencion.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa=emp_id)
            ctx["side_title"] = "Últimas prioridades de mantención"
            ctx["side_items"] = qs.order_by("-id_prioridad")[:15]

        elif self.model.__name__ == "EstadoMantencion":
            from .models_inventario import EstadoMantencion
            qs = EstadoMantencion.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos estados de mantención"
            ctx["side_items"] = qs.order_by("-id_estado_mantencion")[:15]



        elif self.model.__name__ == "TipoMantencion":
            from .models_inventario import TipoMantencion
            qs = TipoMantencion.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos tipos de mantención"
            ctx["side_items"] = qs.order_by("-id_tipo_mantencion")[:15]

        elif self.model.__name__ == "TipoActivo":
            from .models_inventario import TipoActivo
            qs = TipoActivo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos tipos de activo"
            ctx["side_items"] = qs.order_by("-id_tipo_activo")[:15]

        elif self.model.__name__ == "Factura":
            ctx["side_title"] = "Últimas facturas"
            ctx["side_items"] = F.objects.order_by("-id_factura")[:15]

        elif self.model.__name__ == "DetalleFactura":
            from .models_inventario import DetalleFactura
            qs = DetalleFactura.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos detalles de factura"
            ctx["side_items"] = qs.order_by("-id_detalle_factura")[:15]
        return ctx
    
    def form_valid(self, form):
        resp = super().form_valid(form)
        if self.model.__name__ == "Empleado" and form.instance.correo:
            crear_usuario_y_enviar_correo(form.instance)
            sync_user_groups_for_empleado(form.instance)

###################################################################################2509
        # >>> NUEVO: historial “a la segura” al CREAR activo desde CRUD
        if self.model.__name__ == "Activo":
            try:
                from .models_inventario import HistorialActivos
                e = self.object
                usuario_empleado = getattr(self.request.user, "empleado", None)
                HistorialActivos.objects.create(
                    activo=e,
                    etiqueta=e.etiqueta,
                    nombre_activo=e.nombre_activo,
                    modelo=None,  # si no usas modelo en Activo
                    tipo_activo=getattr(e, "id_tipo_activo", None),
                    accion="CREACION",
                    usuario=usuario_empleado,
                    id_empresa=getattr(e, "id_empresa", None),
                    departamento=getattr(e, "id_departamento", None),
                    estado_nuevo=getattr(e, "id_estado_activo", None),
                    responsable_actual=getattr(e, "id_empleado", None),
                    comentario="Creado desde CRUD",
                )
            except Exception:
                # nunca romper el guardado por el historial
                pass
###################################################################################2509

    
        return resp


class GenericUpdate(SaveEmpresaMixin, EmpresaScopeMixin, ModelPermsMixin, UpdateView):
    template_name = "crud/form.html"
    action_perm = "change"
    crud_config: CrudConfig

    def get_queryset(self):
            qs = self.model.objects.all()
            return self.scope_queryset(qs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.model.__name__ in ("Mantencion", "Activo"):
            kwargs["request"] = self.request
        # MUY IMPORTANTE: pasar archivos
        if self.request.method in ("POST", "PUT", "PATCH"):
            kwargs["data"] = self.request.POST
            kwargs["files"] = self.request.FILES
        return kwargs

    def get_form_class(self):
        if self.model.__name__ == "Activo":
            return ActivoForm
        if self.model.__name__ == "Mantencion":     # ← y esto
            from productos.forms import MantencionForm
            return MantencionForm
        #return _build_default_form(self.model)
        if self.model.__name__ == "Empleado":
            from productos.forms import EmpleadoForm        # ← usar el de forms.py
            return EmpleadoForm
        return _build_default_form(self.model)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        emp_id = self.request.session.get("empresa_id")
        if not emp_id:
            return form

        for field in form.fields.values():
            qs = getattr(field, "queryset", None)
            if qs is None:
                continue

            mdl = qs.model

            # Si el combo es Empresa -> filtra por pk
            if mdl._meta.model_name == "empresa":
                field.queryset = mdl.objects.filter(pk=emp_id)
                continue

            # Si el modelo del combo TIENE FK id_empresa -> filtra por esa FK
            if _model_has_empresa_fk(mdl):
                field.queryset = qs.filter(id_empresa_id=emp_id)
            else:
                # si existiera id_empresa como entero en ese modelo relacionado:
                exists, _ = _empresa_field_info(mdl)
                if exists:
                    field.queryset = qs.filter(id_empresa=emp_id)

            # Si no, lo dejamos tal cual
        return form

    def get_success_url(self):
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

    def form_valid(self, form):
        ###########################################################################################2509
        # >>> NUEVO: snapshot ANTES de guardar, solo para Activo
        prev_emp_id = prev_estado_id = None
        if self.model.__name__ == "Activo":
            try:
                prev_obj = self.get_object()
                prev_emp_id = prev_obj.id_empleado_id
                prev_estado_id = prev_obj.id_estado_activo_id
            except Exception:
                pass
        ###########################################################################################2509

        # >>> NUEVO: snapshot ANTES de guardar, solo para Empleado (tu lógica antigua)
        old_empleado = None
        if self.model.__name__ == "Empleado":
            try:
                old_empleado = self.model.objects.get(pk=self.get_object().pk)
            except Exception:
                old_empleado = None

        if self.model.__name__ == "Activo":
            form.instance._usuario_actual = getattr(self.request.user, "empleado", None)

        resp = super().form_valid(form)

        if self.model.__name__ == "Empleado":
            obj = self.object
            old = old_empleado

            # Si NO tenía user y ahora hay correo → crear user y mandar link
            if old and not getattr(old, "user_id", None) and obj.correo:
                crear_usuario_y_enviar_correo(obj)

            # Si ya tiene user, alinear email en auth_user SOLO si cambió
            if getattr(obj, "user_id", None):
                from django.contrib.auth.models import User
                u = User.objects.filter(pk=obj.user_id).first()
                if old and (old.correo != obj.correo) and u and u.email != (obj.correo or ""):
                    u.email = obj.correo or ""
                    u.save(update_fields=["email"])

            # Mantén tu sincronización de grupos
            sync_user_groups_for_empleado(obj)

        # === GUARDAR / ACTUALIZAR VALORES DE ATRIBUTOS (solo Activo) ===
        if self.model.__name__ == "Activo":
            activo = self.object
            tipo_id = self.request.POST.get("id_tipo_activo") or getattr(activo, "id_tipo_activo_id", None)
            if tipo_id:
                attrs = list(
                    AtributosActivo.objects
                    .filter(id_tipo_activo_id=tipo_id)
                    .values_list("id_atributo_activo", flat=True)
                )
                with transaction.atomic():
                    # estrategia simple: borrar y recrear
                    AgregacionAtributosPorActivo.objects.filter(activo_id=activo.id_activo).delete()
                    nuevos = []
                    for attr_id in attrs:
                        v = self.request.POST.get(f"attr_{attr_id}", "").strip()
                        nuevos.append(AgregacionAtributosPorActivo(
                            activo_id=activo.id_activo,
                            atributo_id=attr_id,
                            valor=v or None
                        ))
                    if nuevos:
                        AgregacionAtributosPorActivo.objects.bulk_create(nuevos, ignore_conflicts=True)

        return resp



    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        emp_id = self.request.session.get("empresa_id")
        

        if self.model.__name__ == "Activo":
            qs = Activo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ultimos = qs.order_by("-id_activo")[:15]
            ultima  = qs.order_by("-id_activo").first()
            ctx["ultimos_activos"] = ultimos
            ctx["ultima_etiqueta"] = ultima.etiqueta if ultima else None

        elif self.model.__name__ == "Mantencion":
            from .models_inventario import Mantencion as Mant
            qs = Mant.objects.all()  # <-- paréntesis cerrado
            if emp_id:
                if "id_empresa" in {f.name for f in Mant._meta.get_fields()}:
                    qs = qs.filter(id_empresa_id=emp_id)
                else:
                    qs = qs.filter(id_activo__id_empresa_id=emp_id)
            ctx["side_title"] = "Últimas mantencionesSS"
            ctx["side_items"] = qs.select_related("id_activo").order_by("-id_mantencion")[:15]

        elif self.model.__name__ == "Empresa":
            from .models_inventario import Empresa as Emp
            emp_id = self.request.session.get("empresa_id")
            qs = Emp.objects.all()
            if emp_id:
                qs = qs.filter(pk=emp_id)
            ctx["side_title"] = "Últimas empresas"
            ctx["side_items"] = qs.order_by("-id_empresa")[:15]

        elif self.model.__name__ == "Empleado":
            from .models_inventario import Empleado as Emp
            emp_id = self.request.session.get("empresa_id")
            qs = Emp.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos empleados"
            ctx["side_items"] = qs.order_by("-id_empleado")[:15]
    

        elif self.model.__name__ == "Marca":
            from .models_inventario import Marca as M
            qs = M.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimas marcas"
            ctx["side_items"] = qs.order_by("-id_marca")[:15]  # <-- usa qs

        elif self.model.__name__ == "Proveedor":
            from .models_inventario import Proveedor as P
            qs = P.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos proveedores"
            ctx["side_items"] = qs.order_by("-id_proveedor")[:15]  # <-- usa qs

        elif self.model.__name__ == "Factura":
            from .models_inventario import Factura as F
            ctx["side_title"] = "Últimas facturas"
            ctx["side_items"] = F.objects.order_by("-id_factura")[:15]

#1#######################################################################################################################24-09-2025########
        elif self.model.__name__ == "AtributosActivo":  # Aquí se aplica el filtro solo para AtributosActivo
            from .models_inventario import TipoActivo
            qs = TipoActivo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)  # Filtro por empresa activa
            ctx["tipos_activo"] = qs.order_by("tipo_activo")
        return ctx

#2#######################################################################################################################24-09-2025########   
#    def form_valid(self, form):
#        
#        was_new_user_linked = False
#        if self.model.__name__ == "Empleado":
#            old = self.model.objects.get(pk=self.object.pk)  # antes del save
#            resp = super().form_valid(form)
#            obj = self.object
#
#            # si no tenía user y ahora sí hay correo → crear user y mandar link
#            if not old.user_id and obj.correo:
#                crear_usuario_y_enviar_correo(obj)
#                was_new_user_linked = True
#
#            # si ya tiene user pero cambió el correo → reflejar en auth_user.email
#            if old.correo != obj.correo and obj.user_id:
#                from django.contrib.auth.models import User
#                u = User.objects.filter(pk=obj.user_id).first()
#               if u and u.email != obj.correo:
#                    u.email = obj.correo
#                    u.save(update_fields=["email"])
#            return resp
#        else:
#            return super().form_valid(form)

    
class ActivoForm(forms.ModelForm):
    class Meta:
        model = Activo
        fields = [
            "id_tipo_activo",
            "nombre_activo",
            "id_marca",
            "id_estado_activo",
            "id_empleado",  # responsable (opcional)
            "id_proveedor",
            "etiqueta",
            "observaciones",
            "id_empresa",  # NUEVO: siempre visible en el form
            "id_departamento",  # NUEVO: siempre visible en el form
            "activo_critico",  # El nuevo campo para marcar si el activo es crítico
            "clasificacion",
            "confidencialidad",  # Nuevo campo solo visible si se marca "activo crítico"
            "integridad",  # Nuevo campo solo visible si se marca "activo crítico"
            "disponibilidad",  # Nuevo campo solo visible si se marca "activo crítico"
        ]
        widgets = {
            "id_empresa": forms.Select(attrs={"class": "form-select"}),
            "id_estado_activo": forms.Select(attrs={"class": "form-select"}),
            "id_empleado": forms.Select(attrs={"class": "form-select"}),
            "id_proveedor": forms.Select(attrs={"class": "form-select"}),
            "id_departamento": forms.Select(attrs={"class": "form-select"}),
            "id_marca": forms.Select(attrs={"class": "form-select"}),
            "id_tipo_activo": forms.Select(attrs={"class": "form-select"}),
            "nombre_activo": forms.TextInput(attrs={"class": "form-control"}),
            "etiqueta": forms.TextInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Escribe tus observaciones aquí..."}),
            "activo_critico": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "clasificacion": forms.Select(choices=[  # Agregamos las opciones de clasificación aquí
                ('confidencial', 'Confidencial'),
                ('uso_interno', 'Uso Interno'),
                ('publico', 'Público'),
            ], attrs={"class": "form-select",}),  # Siempre visible
            "confidencialidad": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ingrese un número del 1 al 4", "min": 1, "max": 4, "step": 1, "inputmode": "numeric", "title": "Valor permitido: 1, 2, 3 o 4"}),
            "integridad": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ingrese un número del 1 al 4", "min": 1, "max": 4, "step": 1, "inputmode": "numeric", "title": "Valor permitido: 1, 2, 3 o 4"}),
            "disponibilidad": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Ingrese un número del 1 al 4", "min": 1, "max": 4, "step": 1, "inputmode": "numeric", "title": "Valor permitido: 1, 2, 3 o 4"}),
        }

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Lógica para ocultar los campos basados en el tipo de activo
        tipo_activo = self.initial.get('id_tipo_activo')

        if tipo_activo == 'Información':  # Cuando el tipo de activo sea "Información"
            self.fields['id_marca'].widget = forms.HiddenInput()
            self.fields['id_estado_activo'].widget = forms.HiddenInput()
            self.fields['id_empleado'].widget = forms.HiddenInput()
            self.fields['id_proveedor'].widget = forms.HiddenInput()
            self.fields['confidencialidad'].widget.attrs['style'] = 'display: none'
            self.fields['integridad'].widget.attrs['style'] = 'display: none'
            self.fields['disponibilidad'].widget.attrs['style'] = 'display: none'

        self.request = request
        emp_id = request.session.get("empresa_id") if request else None

        if emp_id:
            self.fields["id_empresa"].queryset = self.fields["id_empresa"].queryset.filter(id_empresa=emp_id)

        # Lógica para mostrar/ocultar los campos de seguridad solo si el activo es crítico
        if not self.instance.activo_critico:  # Si no es un activo crítico, ocultamos los campos
            self.fields["confidencialidad"].widget.attrs['style'] = 'display: none'
            self.fields["integridad"].widget.attrs['style'] = 'display: none'
            self.fields["disponibilidad"].widget.attrs['style'] = 'display: none'
        else:
            self.fields['clasificacion'].widget.attrs['class'] = 'form-select'

        # Empleados solo de la empresa
        if "id_empleado" in self.fields:
            qs = Empleado.objects.filter(estado_activo=True)
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            self.fields["id_empleado"].queryset = qs.order_by("nombre", "apellido_paterno")

        # Departamentos solo de la empresa
        if "id_departamento" in self.fields:
            dqs = Departamento.objects.all()
            if emp_id:
                dqs = dqs.filter(id_empresa_id=emp_id)
            self.fields["id_departamento"].queryset = dqs.order_by("nombre_departamento")

        # Marcas solo de la empresa
        if "id_marca" in self.fields:
            from .models_inventario import Marca
            qs = Marca.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            self.fields["id_marca"].queryset = qs.order_by("nombre_marca")

        # Proveedores solo de la empresa
        if "id_proveedor" in self.fields:
            from .models_inventario import Proveedor
            qs = Proveedor.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            self.fields["id_proveedor"].queryset = qs.order_by("nombre_proveedor")

        # Tipos de activo solo de la empresa
        if "id_tipo_activo" in self.fields:
            from .models_inventario import TipoActivo
            qs = TipoActivo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            self.fields["id_tipo_activo"].queryset = qs.order_by("tipo_activo")

        # Estados de activo solo de la empresa
        if "id_estado_activo" in self.fields:
            from .models_inventario import EstadoActivo
            qs = EstadoActivo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            self.fields["id_estado_activo"].queryset = qs.order_by("descripcion")

    def clean(self):
        cleaned = super().clean()

        # Validaciones adicionales si el activo es crítico
        if cleaned.get("activo_critico") and not cleaned.get("clasificacion"):
            self.add_error("clasificacion", "Este campo es obligatorio cuando el activo es crítico.")
            raise ValidationError("Si el activo es crítico, debes completar los campos de Confidencialidad, Integridad y Disponibilidad.")
        
        # Validación de los campos críticos
        if cleaned.get("activo_critico"):
            if not cleaned.get("confidencialidad") or not cleaned.get("integridad") or not cleaned.get("disponibilidad"):
                self.add_error("clasificacion", "Si el activo es crítico, debes completar los campos de Confidencialidad, Integridad y Disponibilidad.")
                raise ValidationError("Si el activo es crítico, debes completar los campos de Confidencialidad, Integridad y Disponibilidad.")
            
        empleado = cleaned.get("id_empleado")
        emp = cleaned.get("id_empresa")
        dep = cleaned.get("id_departamento")
        # Si no hay responsable, Empresa y Depto son obligatorios
        if empleado is None and (emp is None or dep is None):
            raise ValidationError("Si no asignas responsable, debes seleccionar Empresa y Departamento.")

        # Si hay responsable, valida que sea de la misma empresa
        if empleado is not None and emp is not None:
            if getattr(empleado, "id_empresa_id", None) != getattr(emp, "id_empresa", emp):
                raise ValidationError("El responsable seleccionado no pertenece a la empresa elegida.")

        return cleaned

    
    # No generamos QR aquí: lo hace el modelo en Activo.save()
    # Si no necesitas lógica extra, puedes omitir completamente este save().
    #def save(self, commit=True):
    #    obj = super().save(commit=False)
    #    if commit:
    #        obj.save()
    #    return obj
    
    def save(self, commit=True):
        with transaction.atomic():
            activo = super().save(commit=commit)
            if commit and self.request:
                #activo.atributos_dinamicos.all().delete()
                tipo_id = self.cleaned_data.get("id_tipo_activo")
                if tipo_id:
                    atributos = AtributosActivo.objects.filter(id_tipo_activo=tipo_id)
                    if self.request.session.get("empresa_id"):
                        atributos = atributos.filter(id_tipo_activo__id_empresa_id=self.request.session.get("empresa_id"))
                    for attr in atributos:
                        valor = self.request.POST.get(f"atributo_{attr.id_atributo_activo}")
                        if valor:
                            AgregacionAtributosPorActivo.objects.create(
                                id_activo=activo,
                                id_atributo_activo=attr,
                                valor=valor
                            )
        return activo

class GenericDelete(EmpresaScopeMixin, ModelPermsMixin, DeleteView):
    template_name = "crud/delete.html"
    action_perm = "delete"
    crud_config: CrudConfig
    

    def get_queryset(self):
        qs = self.model.objects.all()
        return self.scope_queryset(qs)

    def get_success_url(self):
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["cfg"] = self.crud_config
        return ctx
    
    # Otros métodos
    def dispatch(self, request, *args, **kwargs):
        if request.user.empleado.rol != 'admin':
            return HttpResponseForbidden("No tienes permisos para eliminar.")
        return super().dispatch(request, *args, **kwargs)

from django.db import connection

def log_mantencion_event(user, mantencion_obj, accion: str, detalle: str = ""):
    """
    Inserta una 'foto' del estado de la mantención en historial_mantenciones_log usando Django ORM.
    """
    # nombre visible: Full Name > nombre del Empleado vinculado > username
    if getattr(user, "is_authenticated", False):
        display_name = (user.get_full_name() or "").strip() or (str(getattr(user, "empleado", "")) or user.get_username())
    else:
        display_name = None
    
    # Obtener los datos de la mantención (activo, tipo, prioridad, etc.)
    activo = mantencion_obj.id_activo
    tipo_mantencion = mantencion_obj.id_tipo_mantencion.nombre if mantencion_obj.id_tipo_mantencion else None
    prioridad = mantencion_obj.id_prioridad.nombre if mantencion_obj.id_prioridad else None
    estado_actual = mantencion_obj.id_estado_mantencion.tipo if mantencion_obj.id_estado_mantencion else None

    # Crear un nuevo registro en HistorialMantencionesLog usando Django ORM
    historial_log = HistorialMantencionesLog.objects.create(
        id_mantencion=mantencion_obj.id_mantencion,
        fecha_evento=timezone.now(),  # Utiliza la hora actual
        accion=accion,
        detalle=detalle,
        usuario_app_username=display_name,
        id_activo=activo.id_activo if activo else None,
        etiqueta=activo.etiqueta if activo else None,
        activo_nombre=activo.nombre_activo if activo else None,
        tipo_mantencion=tipo_mantencion,
        prioridad=prioridad,
        estado_actual=estado_actual,
        responsable_nombre=mantencion_obj.responsable_nombre,  # Esto puede requerir más lógica
        solicitante_nombre=mantencion_obj.solicitante_nombre,  # Lo mismo aquí
        descripcion=mantencion_obj.descripcion,
    )
    
    return historial_log
# ---------- Export CSV ----------

def export_csv_view(model: Type[Model], cfg: CrudConfig):
    def view(request):
        if not request.user.has_perm(f"{model._meta.app_label}.view_{model._meta.model_name}"):
            return HttpResponse(status=403)

        q = request.GET.get("q", "").strip()
        rows = model.objects.all()

        # aplicar scope por empresa (helper sin hacks)
        from .mixins import scope_qs_by_empresa
        rows = scope_qs_by_empresa(request, rows)


        if q and cfg.search_fields:
            from django.db.models import Q
            cond = Q()
            for f in cfg.search_fields:
                cond |= Q(**{f"{f}__icontains": q})
            rows = rows.filter(cond)

############################################################################################################################
        # Filtro avanzado en CSV (mismo contrato f/fv)
        f = (request.GET.get("f") or "").strip()
        fv = (request.GET.get("fv") or "").strip()
        if f:
            rows = _apply_advanced_filter(rows, model, f, fv)
############################################################################################################################

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

        # --- 👇 SOLO LOGIN REQUERIDO PARA LOS HISTORIALES ---
        if m._meta.model_name == "historialactivos":
            ListCls.action_perm = None
        if cfg.slug == "historial_mantenciones":
            ListCls.action_perm = None
        # ----------------------------------------------------


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
    model=HistorialActivos,
    slug="historial-activos",
    verbose_plural="Historial de Activos",
    list_display=[
        "activo", "accion", "usuario", "fecha", "estado_anterior", "estado_nuevo"
    ],
    search_fields=["activo__nombre_activo", "usuario__nombre", "accion"],
    ordering=["-fecha"]
)

def _dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def historial_mantencion(request, id_mantencion: int):
    """
    Muestra el historial de una mantención específica (botón de detalle).
    Restringe por empresa actual usando el activo de la mantención.
    """
    emp_id = request.session.get("empresa_id")
    if not emp_id:
        raise Http404("Empresa no seleccionada.")

    # 1) Validar que la mantención exista y pertenezca a la empresa actual
    with connection.cursor() as c:
        c.execute("""
            SELECT m.id_mantencion, m.id_activo, m.descripcion, m.fecha
            FROM inventario.mantencion m
            JOIN inventario.activo e ON e.id_activo = m.id_activo
            WHERE m.id_mantencion = %s
              AND e.id_empresa = %s
        """, [id_mantencion, emp_id])
        mant = _dictfetchall(c)

    if not mant:
        raise Http404("Mantención no encontrada para la empresa actual.")

    mantencion = mant[0]

    # 2) Traer historial desde la vista (filtramos por id_mantencion;
    #    ya validamos empresa arriba)
    with connection.cursor() as c:
        c.execute("""
            SELECT
              fecha_evento,
              accion,
              COALESCE(detalle, '') AS detalle,
              COALESCE(usuario_app_username, 'sistema') AS usuario_app_username,
              estado_actual,
              old_values,
              new_values
            FROM inventario.vw_historial_mantenciones
            WHERE id_mantencion = %s
            ORDER BY fecha_evento DESC
        """, [id_mantencion])
        historial = _dictfetchall(c)

    ctx = {
        "mantencion": mantencion,
        "historial": historial,
    }
    return render(request, "mantenciones/historial_mantencion.html", ctx)

# productos/crud.py
def ultimos_cambios_mantenciones(request):
    """
    Tablero global: últimos cambios en mantenciones (por defecto últimos 7 días, top 100),
    restringido a la empresa en sesión (via activo).
    """
    emp_id = request.session.get("empresa_id")
    if not emp_id:
        raise Http404("Empresa no seleccionada.")

    dias = int(request.GET.get("dias", "7"))
    limite = int(request.GET.get("limit", "100"))

    with connection.cursor() as c:
        c.execute("""
            SELECT
              h.fecha_evento,
              h.accion,
              COALESCE(h.detalle, '')     AS detalle,
              h.id_mantencion,
              m.id_activo,
              est.tipo                    AS estado_actual,
              h.old_values,
              h.new_values
            FROM inventario.historial_mantenciones h
            JOIN inventario.mantencion m ON m.id_mantencion = h.id_mantencion
            JOIN inventario.activo     e ON e.id_activo     = m.id_activo
            LEFT JOIN inventario.estado_mantencion est
                   ON est.id_estado_mantencion = m.id_estado_mantencion
            WHERE h.fecha_evento >= NOW() - (%s || ' days')::interval
              AND e.id_empresa = %s
            ORDER BY h.fecha_evento DESC
            LIMIT %s
        """, [dias, emp_id, limite])
        eventos = _dictfetchall(c)

    ctx = {
        "eventos": eventos,
        "dias": dias,
        "limite": limite,
    }
    return render(request, "mantenciones/ultimos_cambios_mantenciones.html", ctx)

SLUG_ALIASES = {
    "activo": "activos",
    "tipoactivo": "tipos_activo",
    "atributosactivo": "atributos_activo",
}

def make_slug(m: Type[Model]) -> str:
    base = m._meta.model_name
    if base in SLUG_ALIASES:
        return SLUG_ALIASES[base]
    return base if base.endswith("s") else f"{base}s"

CRUD_CONFIGS = _collect_unique_crud_configs()

# Ordenar Activos por ID descendente por defecto (lo nuevo arriba)
for _cfg in CRUD_CONFIGS:
    if _cfg.model._meta.model_name == "factura":
        cols = list(_cfg.list_display)
        # insertamos la nueva columna después de id_proveedor (si existe)
        try:
            i = cols.index("id_proveedor")
            # evita duplicados si ya lo agregaste antes
            if "proveedor_rut" not in cols:
                cols.insert(i + 1, "proveedor_rut")
        except ValueError:
            # si por alguna razón no está id_proveedor, la agregamos hacia el inicio
            if "proveedor_rut" not in cols:
                cols.insert(1, "proveedor_rut")
        _cfg.list_display = cols

        # (opcional) permitir buscar por RUT en la caja “Buscar…”
        extra_search = ["id_proveedor__rut"]
        _cfg.search_fields = list(dict.fromkeys(list(_cfg.search_fields) + extra_search))

    if _cfg.model._meta.model_name == "activo":
        _cfg.ordering = ("-id_activo",)
    if _cfg.model._meta.model_name == "mantencion":
        _cfg.ordering = ("-id_mantencion",)
    if _cfg.model._meta.model_name == "factura":
        _cfg.ordering = ("-id_factura",)


        # 👇 AQUI define los campos buscables CORRECTOS
        _cfg.search_fields = [
            "folio",
            "observacion",
            "id_empresa__nombre_empresa",
            "id_proveedor__nombre_proveedor",
            "id_proveedor__rut_proveedor",   # <— este es el bueno
        ]



    if _cfg.model._meta.model_name == "detallefactura":
        _cfg.ordering = ("-id_detalle_factura",)
    if _cfg.model._meta.model_name == "proveedor":
        _cfg.ordering = ("-id_proveedor",)
    if _cfg.model._meta.model_name == "marca":
        _cfg.ordering = ("-id_marca",)
    if _cfg.model._meta.model_name == "empleado":
        _cfg.ordering = ("-id_empleado",)



def get_crud_configs():
    return CRUD_CONFIGS
