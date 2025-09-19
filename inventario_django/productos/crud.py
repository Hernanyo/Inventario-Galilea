# productos/crud.py
from .utils import crear_usuario_y_enviar_correo, sync_user_groups_for_empleado

from productos.utils import crear_usuario_y_enviar_correo
from dataclasses import dataclass, field
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey, OneToOneField
from .models_inventario import Marca, Proveedor, TipoEquipo, EstadoEquipo
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
from .models_inventario import AgregacionAtributosPorEquipo, AtributosEquipo
from django.db import transaction
# --- NUEVO: mixin para limitar por empresa (si el modelo tiene id_empresa) ---
from django.core.exceptions import FieldDoesNotExist
from .mixins import EmpresaScopeMixin
from .mixins import SaveEmpresaMixin
from .models_inventario import Empleado, Departamento  # al inicio del archivo
from .utils import crear_usuario_y_enviar_correo






from productos.models_inventario import HistorialMantencionesLog  # evitar ciclos
from productos.forms import MantencionForm

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
        "correo", "telefono", "descripcion", "observaciones", "codigo", "serie",
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


class GenericList(EmpresaScopeMixin, ModelPermsMixin, ListView):
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
        return self.scope_queryset(qs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

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

        if self.model._meta.model_name == "atributosequipo":
            from .models_inventario import TipoEquipo
            ctx["tipos_equipo"] = TipoEquipo.objects.order_by("tipo_equipo")

        return ctx


class GenericCreate(SaveEmpresaMixin, EmpresaScopeMixin, ModelPermsMixin, CreateView):
    template_name = "crud/form.html"
    action_perm = "add"
    crud_config: CrudConfig

    def get_form_class(self):
        if self.model.__name__ == "Equipo":
            return EquipoForm
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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        emp_id = self.request.session.get("empresa_id")  # ⬅️ añade esto

        # EQUIPO: ya tenías sidebar propio
        if self.model.__name__ == "Equipo":
            qs = Equipo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)              # ⬅️ filtro
            ultimos = qs.order_by("-id_equipo")[:15]
            ultima  = qs.order_by("-id_equipo").first()
            ctx["ultimos_equipos"] = ultimos
            ctx["ultima_etiqueta"] = ultima.etiqueta if ultima else None

        # MANTENCION: últimas mantenciones
        elif self.model.__name__ == "Mantencion":
            from .models_inventario import Mantencion as Mant
            qs = Mant.objects.all()
            if emp_id:
                # si el modelo no tiene id_empresa, filtramos por el equipo
                if "id_empresa" in {f.name for f in Mant._meta.get_fields()}:
                    qs = qs.filter(id_empresa_id=emp_id)
                else:
                    qs = qs.filter(id_equipo__id_empresa_id=emp_id)
            ctx["side_title"] = "Últimas mantenciones"
            ctx["side_items"] = qs.select_related("id_equipo").order_by("-id_mantencion")[:15]

        # EMPRESA: últimas empresas
        elif self.model.__name__ == "Empresa":
            from .models_inventario import Empresa as Emp
            ctx["side_title"] = "Últimas empresas"
            ctx["side_items"] = Emp.objects.order_by("-id_empresa")[:15]

        elif self.model.__name__ == "Empleado":
            from .models_inventario import Empleado as Emp
            ctx["side_title"] = "Últimos empleados"
            ctx["side_items"] = Emp.objects.order_by("-id_empleado")[:15]

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

        elif self.model.__name__ == "EstadoEquipo":
            from .models_inventario import EstadoEquipo
            qs = EstadoEquipo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos estados de equipo"
            ctx["side_items"] = qs.order_by("-id_estado_equipo")[:15]

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

        elif self.model.__name__ == "TipoEquipo":
            from .models_inventario import TipoEquipo
            qs = TipoEquipo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimos tipos de equipo"
            ctx["side_items"] = qs.order_by("-id_tipo_equipo")[:15]

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
        if self.model.__name__ in ("Mantencion", "Equipo"):
            kwargs["request"] = self.request
        return kwargs

    def get_form_class(self):
        if self.model.__name__ == "Equipo":
            return EquipoForm
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
        if self.model.__name__ == "Equipo":
            form.instance._usuario_actual = getattr(self.request.user, "empleado", None)

        resp = super().form_valid(form)

        if self.model.__name__ == "Empleado":
            obj = self.object
            # Si no tiene user y ahora hay correo → crea user + link
            if not obj.user_id and obj.correo:
                crear_usuario_y_enviar_correo(obj)
            # Si tiene user, alinea email
            if obj.user_id:
                from django.contrib.auth.models import User
                u = User.objects.filter(pk=obj.user_id).first()
                if u and u.email != (obj.correo or ""):
                    u.email = obj.correo or ""
                    u.save(update_fields=["email"])
            # Alinea grupos según rol
            sync_user_groups_for_empleado(obj)
            
        # === GUARDAR / ACTUALIZAR VALORES DE ATRIBUTOS (solo Equipo) ===
        if self.model.__name__ == "Equipo":
            equipo = self.object
            tipo_id = self.request.POST.get("id_tipo_equipo") or getattr(equipo, "id_tipo_equipo_id", None)
            if tipo_id:
                attrs = list(
                    AtributosEquipo.objects
                    .filter(id_tipo_equipo_id=tipo_id)
                    .values_list("id_atributo_equipo", flat=True)
                )
                with transaction.atomic():
                    # estrategia simple: borrar y recrear
                    AgregacionAtributosPorEquipo.objects.filter(equipo_id=equipo.id_equipo).delete()
                    nuevos = []
                    for attr_id in attrs:
                        v = self.request.POST.get(f"attr_{attr_id}", "").strip()
                        nuevos.append(AgregacionAtributosPorEquipo(
                            equipo_id=equipo.id_equipo,
                            atributo_id=attr_id,
                            valor=v or None
                        ))
                    if nuevos:
                        AgregacionAtributosPorEquipo.objects.bulk_create(nuevos, ignore_conflicts=True)

        return resp


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        emp_id = self.request.session.get("empresa_id")
        

        if self.model.__name__ == "Equipo":
            qs = Equipo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ultimos = qs.order_by("-id_equipo")[:15]
            ultima  = qs.order_by("-id_equipo").first()
            ctx["ultimos_equipos"] = ultimos
            ctx["ultima_etiqueta"] = ultima.etiqueta if ultima else None

        elif self.model.__name__ == "Mantencion":
            from .models_inventario import Mantencion as Mant
            qs = Mant.objects.all()  # <-- paréntesis cerrado
            if emp_id:
                if "id_empresa" in {f.name for f in Mant._meta.get_fields()}:
                    qs = qs.filter(id_empresa_id=emp_id)
                else:
                    qs = qs.filter(id_equipo__id_empresa_id=emp_id)
            ctx["side_title"] = "Últimas mantencionesSS"
            ctx["side_items"] = qs.select_related("id_equipo").order_by("-id_mantencion")[:15]

        elif self.model.__name__ == "Empresa":
            from .models_inventario import Empresa as Emp
            ctx["side_title"] = "Últimas empresas"
            ctx["side_items"] = Emp.objects.order_by("-id_empresa")[:15]

        elif self.model.__name__ == "Empleado":
            from .models_inventario import Empleado as Emp
            ctx["side_title"] = "Últimos empleados"
            ctx["side_items"] = Emp.objects.order_by("-id_empleado")[:15]
    

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
        return ctx
    
    def form_valid(self, form):
        was_new_user_linked = False
        if self.model.__name__ == "Empleado":
            old = self.model.objects.get(pk=self.object.pk)  # antes del save
            resp = super().form_valid(form)
            obj = self.object

            # si no tenía user y ahora sí hay correo → crear user y mandar link
            if not old.user_id and obj.correo:
                crear_usuario_y_enviar_correo(obj)
                was_new_user_linked = True

            # si ya tiene user pero cambió el correo → reflejar en auth_user.email
            if old.correo != obj.correo and obj.user_id:
                from django.contrib.auth.models import User
                u = User.objects.filter(pk=obj.user_id).first()
                if u and u.email != obj.correo:
                    u.email = obj.correo
                    u.save(update_fields=["email"])
            return resp
        else:
            return super().form_valid(form)

    
class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        # Importante: incluimos Empresa y Departamento en el formulario
        fields = [
            "nombre_equipo",
            "id_marca",
            "id_tipo_equipo",
            "id_estado_equipo",
            "id_empleado",       # responsable (opcional)
            "id_proveedor",
            "etiqueta",
            "observaciones",
            "id_empresa",        # NUEVO: siempre visible en el form
            "id_departamento",   # NUEVO: siempre visible en el form
        ]
        # (opcional) puedes añadir widgets si quieres inputs más bonitos:
        # widgets = {
        #     "nombre_equipo": forms.TextInput(attrs={"class": "input input-bordered"}),
        # }
    def __init__(self, *args, request=None, **kwargs):
            super().__init__(*args, **kwargs)

            emp_id = None
            if request is not None and hasattr(request, "session"):
                emp_id = request.session.get("empresa_id")

            # Inicializa y (opcional) bloquea empresa en el form
            if emp_id and "id_empresa" in self.fields:
                self.fields["id_empresa"].initial = emp_id
                # self.fields["id_empresa"].disabled = True  # opcional

            # Empleados solo de la empresa
            if "id_empleado" in self.fields:
                qs = Empleado.objects.filter(activo=True)
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

            # Tipos de equipo solo de la empresa
            if "id_tipo_equipo" in self.fields:
                from .models_inventario import TipoEquipo
                qs = TipoEquipo.objects.all()
                if emp_id:
                    qs = qs.filter(id_empresa_id=emp_id)
                self.fields["id_tipo_equipo"].queryset = qs.order_by("tipo_equipo")

            # Estados de equipo solo de la empresa
            if "id_estado_equipo" in self.fields:
                from .models_inventario import EstadoEquipo
                qs = EstadoEquipo.objects.all()
                if emp_id:
                    qs = qs.filter(id_empresa_id=emp_id)
                self.fields["id_estado_equipo"].queryset = qs.order_by("descripcion")

            
                
    def clean(self):
        cleaned = super().clean()
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
    
    # No generamos QR aquí: lo hace el modelo en Equipo.save()
    # Si no necesitas lógica extra, puedes omitir completamente este save().
    def save(self, commit=True):
        obj = super().save(commit=False)
        if commit:
            obj.save()
        return obj

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
    Inserta una 'foto' del estado de la mantención en historial_mantenciones_log.
    Usa INSERT...SELECT para que el DEFAULT now() de fecha_evento se aplique.
    """

    # nombre visible: Full Name > nombre del Empleado vinculado > username
    if getattr(user, "is_authenticated", False):
        display_name = (user.get_full_name() or "").strip() or (str(getattr(user, "empleado", "")) or user.get_username())
    else:
        display_name = None

    with connection.cursor() as c:
        c.execute("""
            INSERT INTO inventario.historial_mantenciones_log
            (
                id_mantencion,
                accion,
                detalle,
                usuario_app_username,
                id_equipo,
                etiqueta,
                equipo_nombre,
                tipo_mantencion,
                prioridad,
                estado_actual,
                responsable_nombre,
                solicitante_nombre,
                descripcion
            )
            SELECT
                m.id_mantencion,
                %s,                         -- accion
                %s,                         -- detalle
                %s,                         -- usuario que gatilla el evento
                e.id_equipo,
                e.etiqueta,
                e.nombre_equipo,
                tm.nombre,                  -- tipo de mantención (texto)
                pr.nombre,                  -- prioridad (texto)
                est.tipo,                   -- estado (texto)
                TRIM(CONCAT_WS(' ', resp.nombre, resp.apellido_paterno, resp.apellido_materno)) AS responsable_nombre,
                COALESCE(
                    NULLIF(TRIM(CONCAT_WS(' ', sol.nombre, sol.apellido_paterno, sol.apellido_materno)), ''),
                    u.username
                ) AS solicitante_nombre,
                m.descripcion
            FROM inventario.mantencion m
            LEFT JOIN inventario.equipo               e   ON e.id_equipo = m.id_equipo
            LEFT JOIN inventario.tipo_mantencion      tm  ON tm.id_tipo_mantencion = m.id_tipo_mantencion
            LEFT JOIN inventario.prioridad_mantencion pr  ON pr.id_prioridad        = m.id_prioridad
            LEFT JOIN inventario.estado_mantencion    est ON est.id_estado_mantencion = m.id_estado_mantencion
            LEFT JOIN inventario.empleado             resp ON resp.id_empleado = m.responsable_id
            -- 👇 AQUI va tu línea: toma el Empleado vinculado al auth_user solicitante
            LEFT JOIN inventario.empleado             sol  ON sol.user_id = m.solicitante_user_id
            -- 👇 y mantenemos también auth_user para fallback a username
            LEFT JOIN auth_user                        u   ON u.id = m.solicitante_user_id
            WHERE m.id_mantencion = %s
        """, [
            (accion or "").upper(),
            (detalle or ""),
            display_name, 
            mantencion_obj.id_mantencion,
        ])
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

def _dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def historial_mantencion(request, id_mantencion: int):
    """
    Muestra el historial de una mantención específica (botón de detalle).
    Restringe por empresa actual usando el equipo de la mantención.
    """
    emp_id = request.session.get("empresa_id")
    if not emp_id:
        raise Http404("Empresa no seleccionada.")

    # 1) Validar que la mantención exista y pertenezca a la empresa actual
    with connection.cursor() as c:
        c.execute("""
            SELECT m.id_mantencion, m.id_equipo, m.descripcion, m.fecha
            FROM inventario.mantencion m
            JOIN inventario.equipo e ON e.id_equipo = m.id_equipo
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
    restringido a la empresa en sesión (via equipo).
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
              m.id_equipo,
              est.tipo                    AS estado_actual,
              h.old_values,
              h.new_values
            FROM inventario.historial_mantenciones h
            JOIN inventario.mantencion m ON m.id_mantencion = h.id_mantencion
            JOIN inventario.equipo     e ON e.id_equipo     = m.id_equipo
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


CRUD_CONFIGS = _collect_unique_crud_configs()

# Ordenar Equipos por ID descendente por defecto (lo nuevo arriba)
for _cfg in CRUD_CONFIGS:
    if _cfg.model._meta.model_name == "equipo":
        _cfg.ordering = ("-id_equipo",)
    if _cfg.model._meta.model_name == "mantencion":
        _cfg.ordering = ("-id_mantencion",)
    if _cfg.model._meta.model_name == "factura":
        _cfg.ordering = ("-id_factura",)
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
