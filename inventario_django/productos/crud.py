# productos/crud.py parte 1
#from .models_inventario import CategoriaActivo

"""CRUD genérico para la app `productos`.

Provee:
- Clases `GenericList/Create/Update/Delete` con:
  - Búsqueda rápida y **filtro avanzado** por tipo de campo (FK/num/bool/date).
  - **Scope por empresa** (si el modelo tiene `id_empresa`/`empresa` o cuelga de `Activo`).
  - **Borrado lógico** si el modelo tiene campo `eliminado`.
  - Formularios generados automáticamente con widgets y soporte de **archivos**.
  - Exportación CSV respetando búsqueda y filtros.

- Registro automático de URL patterns para todos los modelos de `productos`.

Notas:
- La visibilidad y permisos se controlan con `ModelPermsMixin` y `EmpresaScopeMixin`.
- El menú y columnas se infieren con `CrudConfig`.
"""

# NOTA IMPORTANTE (para el yo-del-futuro 👋):
# -------------------------------------------
# - Las columnas de las tablas de lista salen de CrudConfig.list_display.
# - Si no registro un modelo a mano, list_display se rellena con infer_list_display(),
#   que mira los campos definidos en models_inventario.py (m._meta.fields).
# - Las vistas genéricas NUNCA usan list_display directamente: llaman a
#       cfg.get_list_display()
#   y lo que devuelva esa función es lo que termina en el <thead> y <tbody>.
# - Por eso, si quiero:
#   * eliminar una columna de TODOS los modelos -> lo hago aquí filtrando en get_list_display().
#   * cambiar columnas de UN modelo => mejor registrar el CrudConfig o modificar _cfg.list_display
#     dentro del for _cfg in CRUD_CONFIGS.
# - Ejemplo actual: para DetalleFactura se oculta id_activo en get_list_display().

from .models_inventario import Modelo
from django.db.models import Max
from .models import HistorialMantencionesLog
from django.utils.dateparse import parse_date
import json
#from django.contrib import messages
from django.contrib import messages as dj_messages
from django.http import HttpResponseRedirect   # 👈 Faltaba este import
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .utils import crear_usuario_y_enviar_correo, sync_user_groups_for_empleado
from productos.utils import crear_usuario_y_enviar_correo
from dataclasses import dataclass, field
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey, OneToOneField
from .models_inventario import Marca, Proveedor, TipoActivo, EstadoActivo
from typing import Sequence, List, Type
import csv
from django.http import JsonResponse
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
from productos.forms import MantencionForm, hide_deleted
# arriba de _build_default_form (o dentro), suma estos imports de tipos de campo
from django.db.models import FileField, ImageField
from django.forms import ClearableFileInput
import inspect
import re
from django.db.utils import IntegrityError   # <-- usa ESTE
from .mixins import EmpresaBoundMixin
from .models_inventario import Cargo  # para validarlo
from .models_inventario import ReglaCriticidad
from .models_inventario import PreparacionAsignacion
from .models_inventario import CondicionDetalle   # 👈 NUEVO
from .models_inventario import DetalleFactura
from .mixins import EmpresaScopeMixin
from .mixins import SaveEmpresaMixin
from .mixins import EmpresaBoundMixin
from .mixins import rol_de_usuario, ROL_ADMIN, ROL_JEFE, ROL_USUARIO, ROL_TRABAJADOR
from .mixins import filtrar_activos_por_bodegas_permitidas
from .mixins import filtrar_empleados_por_bodegas_permitidas
from .mixins import filtrar_qs_por_permiso_bodega_sobre_activo
from .mixins import filtrar_ubicaciones_por_bodegas_permitidas   # 👈 NUEVO

from django import forms
from .models_inventario import Empleado, Departamento, PermisoBodega, Ubicacion, Bodega






def _build_default_form(model):
    """Crea un `ModelForm` para `model` con widgets razonables y soporte de archivos.

    - Aplica `Select`, `DateInput`, `DateTimeInput`, `Textarea`, `NumberInput`,
      `CheckboxInput`, y `ClearableFileInput` en File/Image.
    - Excluye automáticamente `eliminado` si existe.

    Returns:
        Type[forms.ModelForm]: Clase de formulario generada.
    """
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

    
    # ⬇️ EXCLUIR “eliminado” en todos los forms genéricos
    exclude = ("eliminado",) if _has_field(model, "eliminado") else ()
    return modelform_factory(model, fields="__all__", exclude=exclude, widgets=widgets)


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
    """
    Verifica si el modelo tiene un campo de relación `id_empresa` (ya sea como FK o OneToOne).
    
    Args:
        model: El modelo Django a verificar.
    
    Returns:
        bool: True si el modelo tiene una relación `id_empresa`.
    """
    f = next((f for f in model._meta.get_fields() if getattr(f, "name", None) == "id_empresa"), None)
    return bool(f and getattr(f, "is_relation", False))

############################# 10/12 ####################################
def patch_rol_field_for_empleado(form, request):
    """
    Si el formulario es de Empleado, convierte el campo 'rol' en un ChoiceField
    y limita las opciones según el rol del usuario que está editando.
    """
    # ¿Este form es para el modelo Empleado?
    model = getattr(getattr(form, "_meta", None), "model", None)
    if model is not Empleado:
        return form

    if "rol" not in form.fields:
        return form

    ejecutor = getattr(request.user, "empleado", None)
    ejecutor_rol = getattr(ejecutor, "rol", None)

    # Opciones completas (para admin/jefe)
    full_choices = [
        (Empleado.ROL_ADMIN, "Admin"),
        (Empleado.ROL_JEFE, "Jefe"),
        (Empleado.ROL_USUARIO, "Usuario"),
        (Empleado.ROL_TRABAJADOR, "Trabajador"),
    ]

    # Opciones limitadas (para usuario/trabajador)
    limited_choices = [
        (Empleado.ROL_USUARIO, "Usuario"),
        (Empleado.ROL_TRABAJADOR, "Trabajador"),
    ]

    if ejecutor_rol in (Empleado.ROL_ADMIN, Empleado.ROL_JEFE):
        choices = full_choices
    else:
        choices = limited_choices

    old = form.fields["rol"]

    # Reemplazamos el campo por un ChoiceField, conservando label, requerido, etc.
    form.fields["rol"] = forms.ChoiceField(
        label=old.label or "Rol",
        required=old.required,
        help_text=old.help_text,
        choices=choices,
        # Valor inicial: lo que trae la instancia o lo que hubiera definido el form
        initial=getattr(form.instance, "rol", None) or old.initial,
        widget=forms.Select(attrs={"class": "form-select"}),  # 👈 igual que otros selects
    )

    return form


# Helper reutilizable para nombres de columnas
COLUMN_LABEL_OVERRIDES = {
    "id_activo": "Id Activo",
    "nombre_activo": "Modelo",
    "id_tipo_activo": "Id Tipo Activo",
    "id_estado_activo": "Id Estado Activo",
    "id_marca": "Id Marca",
    "id_proveedor": "Id Proveedor",
    "id_factura": "Factura (folio)",
    "id_empleado": "Responsable",
    "id_condicion_activo": "Condición",
    "ubicacion_label": "Ubicación",
    "id_bodega_retorno": "Bodega Retorno",
}

def pretty_column_label(col: str) -> str:
    """
    Devuelve un nombre bonito para la columna:
    - Respeta overrides específicos (COLUMN_LABEL_OVERRIDES).
    - Si empieza con 'id_', se lo saca y capitaliza el resto.
    - Si no, reemplaza '_' por espacio y Title Case.
    """
    if col in COLUMN_LABEL_OVERRIDES:
        return COLUMN_LABEL_OVERRIDES[col]

    name = col
    if name.startswith("id_"):
        name = name[3:]  # quita 'id_'

    return name.replace("_", " ").title()

def patch_permiso_bodega_field_for_empleado(form, request):
    """
    Añade un campo extra 'permiso_bodega' al formulario de Empleado
    para que admin/jefe puedan asignar una bodega al CREAR el empleado.
    El campo NO se guarda en Empleado; se usará en form_valid para
    crear un registro en PermisoBodega.
    """
    model = getattr(getattr(form, "_meta", None), "model", None)
    if model is not Empleado:
        return form

    # Solo admins/jefes ven este campo
    ejecutor = getattr(request.user, "empleado", None)
    ejecutor_rol = (getattr(ejecutor, "rol", "") or "").strip().lower()
    if ejecutor_rol not in (Empleado.ROL_ADMIN, Empleado.ROL_JEFE):
        # Por si acaso ya existiera, lo quitamos
        form.fields.pop("permiso_bodega", None)
        return form

    emp_id = request.session.get("empresa_id")

    # 🔹 Query de BODEGAS (NO ubicaciones)
    qs = Bodega.objects.all()
    if emp_id:
        qs = qs.filter(id_empresa_id=emp_id)

    # 🔹 EXCLUIR ELIMINADAS (eliminado = False) si existe el campo
    try:
        Bodega._meta.get_field("eliminado")
        qs = qs.filter(eliminado=False)
    except FieldDoesNotExist:
        pass

    form.fields["permiso_bodega"] = forms.ModelChoiceField(
        label="Permiso bodega",
        queryset=qs.order_by("nombre_bodega"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text=(
            "Opcional. Si eliges una bodega y el rol del empleado es 'usuario', "
            "se creará automáticamente un permiso de bodega."
        ),
    )

    return form

############################# 10/12 ####################################

# ---------- Config e inferencia ----------

@dataclass
class CrudConfig:
    """Configuración por modelo para las vistas genéricas.

    Args:
        model: Modelo de Django.
        slug: Segmento de URL (p.ej., `"activos"`).
        verbose_plural: Nombre legible (plural) para la UI.
        list_display: Columnas visibles en listados (se sanea para ocultar `eliminado`).
        search_fields: Campos de búsqueda rápida (`icontains`).
        ordering: Orden por defecto.
        label_attr: Atributo preferido para representar una fila.

    Atributos:
        can_create, can_change, can_delete, se inyecta en runtime según permisos del usuario.
    """
    model: Type[Model]
    slug: str                     # p.ej. "activos"
    verbose_plural: str           # p.ej. "Activos"
    list_display: Sequence[str] = field(default_factory=list)   # columnas
    search_fields: Sequence[str] = field(default_factory=list)  # campos texto
    ordering: Sequence[str] = field(default_factory=lambda: ("id",))
    label_attr: str | None = None

    # etiqueta legible para un objeto
    def obj_label(self, obj):
        """Devuelve una etiqueta legible para `obj`.

        Prioriza `label_attr`; si no, intenta con campos comunes (nombre, descripcion,
        serie, codigo, etc.) y finalmente `str(obj)`.
        """
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
     
    def get_list_display(self):
        """
        Columnas de lista filtradas.

        - Oculta siempre el flag `eliminado`.
        - Y para DetalleFactura, oculta también `id_activo`.
        """
        # Base: list_display sin 'eliminado'
        cols = [field for field in self.list_display if field != "eliminado"]

        # Regla especial: DetalleFactura sin columna id_activo
        if self.model._meta.model_name == "detallefactura":
            cols = [c for c in cols if c != "id_activo"]

        return cols

def infer_text_fields(m: Type[Model]) -> List[str]:
    names = [
        f.name for f in m._meta.get_fields()
        if getattr(f, "attname", None) and isinstance(f, (CharField, TextField))
    ]
    prefer = [n for n in ("nombre", "descripcion", "serie", "modelo") if n in names]
    rest = [n for n in names if n not in prefer]
    return prefer + rest


def infer_list_display(m: Type[Model]) -> List[str]:
    """Infiera columnas "útiles" para la vista de lista.

    Selecciona PK + campos legibles (texto/números/fechas/FK) hasta 9 columnas máx.
    Da prioridad a campos comunes como nombre, descripción, etc.
    """
    pk_name = m._meta.pk.name
    cols: List[str] = [pk_name]

    prefer_order = (
        "rut", "nombre", "apellido_paterno", "apellido_materno",
        "correo", "descripcion", "observaciones", "codigo", "serie",
        "departamento", "empresa", "marca", "tipo_activo", "ubicacion", "cargo", "telefono",
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
    Construye los campos de filtro avanzado a partir de los campos visibles en `list_display`.
    
    Para cada campo en `list_display`, se infiere el tipo de filtro (por ejemplo, `fk`, `char`, `num`, etc.) 
    y se genera una estructura de datos adecuada para su uso en la interfaz.
    
    Args:
        model: El modelo Django que contiene los campos.
        list_display: Los campos que se deben mostrar en la vista de lista.
    
    Returns:
        list: Lista de diccionarios con la estructura de los campos de filtro avanzado.
    """
    label_overrides = {
        "id_activo": "Id Activo",
        "nombre_activo": "Modelo",
        "id_tipo_activo": "Id Tipo Activo",
        "id_estado_activo": "Id Estado Activo",
        "id_marca": "Id Marca",
        "id_proveedor": "Id Proveedor",
        "id_factura": "Factura (folio)",   # 👈 NUEVO
        "id_empleado": "Responsable",
        "observaciones": "Observaciones",
        "etiqueta": "Etiqueta",
        "id_condicion_activo": "Condición",   # 👈 NUEVO
        "ubicacion_label": "Ubicación",
        "id_bodega_retorno": "Bodega Retorno",
    }
    out = []
    for col in list_display:
        kind = _field_kind(model, col)
        if not kind:
            continue
#        label = label_overrides.get(col) or col.replace("_", " ").title()
        label = pretty_column_label(col)
        

        out.append({"name": col, "label": label, "type": kind})
    return out


def _adv_choices_for_fk_fields(request, model, adv_fields, base_qs):
    """
    Para campos FK, arma choices [{value, label}] SOLO con los IDs que aparecen
    en el queryset de la lista (base_qs), aplicando scope por empresa y excluyendo
    eliminados cuando el modelo relacionado tenga ese campo.
    """
    emp_id = request.session.get("empresa_id")
    out = {}

    if base_qs is None:
        base_qs = model.objects.none()

    for af in adv_fields:
        if af["type"] != "fk":
            continue

        f = model._meta.get_field(af["name"])       # el FK en el modelo listado
        rel = f.remote_field.model                   # modelo relacionado

        # IDs distintos del FK que realmente aparecen en la lista actual
        ids = base_qs.values_list(f"{f.name}_id", flat=True).distinct()

        rqs = rel.objects.filter(pk__in=ids)

        # scope por empresa si aplica (id_empresa/empresa/o colgando de Activo)
        rqs = _scope_by_empresa(rqs, rel, emp_id)

        # oculta eliminados si existe el campo
        if _has_field(rel, "eliminado"):
            rqs = rqs.filter(eliminado=False)

        # orden legible si hay campos típicos
        for cand in ("nombre", "nombre_ubicacion", "tipo", "tipo_activo",
                     "razon_social", "nombre_marca", "folio", "modelo"):
            try:
                rel._meta.get_field(cand)
                rqs = rqs.order_by(cand)
                break
            except Exception:
                continue

        out[af["name"]] = [{"value": str(o.pk), "label": str(o)} for o in rqs]
    return out


def _apply_advanced_filter(qs, model, field_name, raw_value):
    """Aplica el **filtro avanzado** según el tipo del campo.

    - fk: por PK si `raw_value` es dígito; si no, por campos legibles del relacionado.
    - char: `icontains`.
    - num: exact si es dígito; si no, `none()`.
    - bool: admite `true/false/1/0/si/no`.
    - date/datetime: `YYYY-MM-DD` → `__date`; si no, `startswith`.

    Returns:
        QuerySet: queryset filtrado.
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

# ---------- Vistas y helpers ----------

###########################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><10/10 10:24
def _norm_nombre(v: str) -> str:
    # iguala a la lógica de la constraint: lower + trim + colapsar espacios
    v = (v or "").strip().lower()
    v = re.sub(r"\s+", " ", v)
    return v


def _get_emp_id_from_request_or_instance(request, form_instance):
    return (
        request.session.get("empresa_id")
        or getattr(form_instance, "id_empresa_id", None)
        or getattr(getattr(form_instance, "id_empresa", None), "id_empresa", None)
    )
###########################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><10/10 10:24

def qr_print_view(request, pk):
    obj = get_object_or_404(Activo, pk=pk)
    context = {
        "object": obj,
        "back_url": reverse_lazy("productos:activos_list")
    }
    return render(request, "activos/qr_print.html", context)

from django.core.exceptions import FieldDoesNotExist

def _has_field(model, name: str) -> bool:
    try:
        model._meta.get_field(name)
        return True
    except FieldDoesNotExist:
        return False
    
from django import forms
from django.views.generic.edit import CreateView, UpdateView

class HideEliminadoFormMixin:
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if 'eliminado' in form.fields:
            form.fields['eliminado'].widget = forms.HiddenInput()
        return form
    
from django.forms import modelform_factory

class ExcludeEliminadoFormMixin:
    def get_form_class(self):
        fields = getattr(self.crud_config, "fields", "__all__")
        exclude = list(getattr(self.crud_config, "exclude", []))
        if _has_field(self.model, "eliminado"):
            exclude.append("eliminado")
        return modelform_factory(self.model, fields=fields, exclude=tuple(exclude))

    #############################################################################12/11
# >>> NUEVO (helper) cerca de otros helpers como _has_field / _scope_by_empresa
from django.db.models import Q

def _buscar_estado_activo(emp_id, etiqueta: str):
    """Devuelve el EstadoActivo cuyo nombre/tipo/descripcion/coincida con `etiqueta` (ej. 'Disponible', 'Asignado'),
       filtrando por empresa y respetando eliminado=False si existe."""
    from .models_inventario import EstadoActivo
    qs = EstadoActivo.objects.all()
    if emp_id:
        qs = qs.filter(id_empresa_id=emp_id)
    if _has_field(EstadoActivo, "eliminado"):
        qs = qs.filter(eliminado=False)

    filtros = Q()
    for fname in ("tipo", "nombre", "estado", "descripcion"):
        try:
            EstadoActivo._meta.get_field(fname)
            filtros |= Q(**{f"{fname}__iexact": etiqueta})
        except Exception:
            pass
    return qs.filter(filtros).first() if filtros else None

    #############################################################################12/11
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey

def _scope_by_empresa(qs, model, emp_id):
    """Restringe `qs` a la empresa activa.

    Prioridad:
      1) `id_empresa` (FK o entero) en el propio modelo.
      2) `empresa` (FK).
      3) Si cuelga de `Activo`, filtra por `id_activo__id_empresa_id`.

    Returns:
        QuerySet: queryset con el alcance aplicado.
    """
    if not emp_id:
        return qs

    # 1) Campo 'id_empresa'
    try:
        f = model._meta.get_field("id_empresa")
        if isinstance(f, ForeignKey):
            return qs.filter(id_empresa_id=emp_id)
        else:
            # p.ej. Empresa.id_empresa es PK entero
            return qs.filter(id_empresa=emp_id)
    except FieldDoesNotExist:
        pass

    # 2) Campo 'empresa' (FK)
    try:
        f = model._meta.get_field("empresa")
        if isinstance(f, ForeignKey):
            return qs.filter(empresa_id=emp_id)
    except FieldDoesNotExist:
        pass

    # 3) Modelos que cuelgan de Activo
    if any(g.name == "id_activo" for g in model._meta.get_fields()):
        return qs.filter(id_activo__id_empresa_id=emp_id)

    return qs
class GenericList(EmpresaScopeMixin, ModelPermsMixin, ListView):
    """Lista genérica con búsqueda, orden y **filtro avanzado**.

    - **Scope empresa** si corresponde (ver `_scope_by_empresa`).
    - **Borrado lógico**: si el modelo tiene `eliminado`, no muestra eliminados.
    - Búsqueda rápida incluye PK/numéricos y FKs si `q` es dígito.

    Query params:
        q: texto de búsqueda.
        o: orden (campo o `-campo`).
        f, fv: campo + valor para filtro avanzado.

    Context:
        cfg (CrudConfig), list_display (sin `eliminado`), adv_fields/choices en JSON,
        permisos `can_create`/`can_change`/`can_delete`.
    """
    template_name = "crud/list.html"
    context_object_name = "items"
    paginate_by = 25
    action_perm = "view"
    crud_config: CrudConfig

    def get_queryset(self):
        """Construye el queryset aplicando:
        scope por empresa, exclusión de `eliminado`,
        búsqueda rápida (`q`), filtro avanzado (`f`/`fv`)
        y orden (`o` o `cfg.ordering`).
        """
        q = (self.request.GET.get("q") or "").strip()
        order = (self.request.GET.get("o") or "").strip()
        qs = self.model.objects.all()
        #qs = qs.filter(eliminado=False)  # Solo muestra objetos no eliminados

        
        # --- Scope por empresa (si existe) ---
        emp_id = self.request.session.get("empresa_id")
        qs = _scope_by_empresa(qs, self.model, emp_id)

        # --- Borrado lógico (solo si el modelo tiene el campo) ---
        if _has_field(self.model, "eliminado"):
            qs = qs.filter(eliminado=False)

############################ 09/12 #############################################
        # --- Filtro por permisos de bodegas según el modelo ---
        ejecutor = getattr(self.request.user, "empleado", None)

        # 1) Activos: filtro directo por ubicación/bodega
        if self.model._meta.model_name == "activo":
            qs = filtrar_activos_por_bodegas_permitidas(qs, ejecutor)

        # 2) Empleados: solo ve empleados de las ubicaciones/bodegas permitidas
        elif self.model._meta.model_name == "empleado":
            qs = filtrar_empleados_por_bodegas_permitidas(qs, ejecutor)

        # 3) Modelos que cuelgan de Activo: PlanMantencionActivo y MantencionEjecucion
        elif self.model._meta.model_name in ("planmantencionactivo", "mantencionejecucion"):
            # usa el FK `id_activo` del modelo para aplicar el mismo criterio de bodegas
            qs = filtrar_qs_por_permiso_bodega_sobre_activo(qs, ejecutor, fk_name="id_activo")
############################ 09/12 #############################################

################################### 27/11 #############################################        
        # 🔹 Filtro especial: DetalleFactura por factura seleccionada
        # URL: .../detallefacturas_list/?factura=19
        if self.model._meta.model_name == "detallefactura":
            factura_id = (self.request.GET.get("factura") or "").strip()
            if factura_id:
                qs = qs.filter(id_factura_id=factura_id)
################################### 27/11 #############################################        


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

########################### 09/12 #######################################
        # === ORDEN ===
        if order:
            pk_name = self.model._meta.pk.name
            if order.lstrip("-") == "id":
                order = order.replace("id", pk_name, 1)

            # ---------- Mapa de alias de orden → campos reales ----------
            model_name = self.model._meta.model_name
            alias_map = {}

            if model_name == "activo":
                alias_map = {
                    # encabezado "Ubicación" que usa ubicacion_label en la template
                    "ubicacion_label": "id_ubicacion__nombre_ubicacion",
                    # si más adelante quieres ordenar por otras propiedades “fake”,
                    # las agregas aquí, por ejemplo:
                    # "estado_badge": "id_estado_activo__tipo",
                }

            # Soportar también el "-" delante (orden descendente)
            sign = "-" if order.startswith("-") else ""
            key = order.lstrip("-")

            if key in alias_map:
                order = sign + alias_map[key]
            # ------------------------------------------------------------

            qs = qs.order_by(order)
        else:
            qs = qs.order_by(*self.crud_config.ordering)

########################### 09/12 #######################################

        # Alcance por empresa (u otros)
        #return self.scope_queryset(qs)
        return qs

    def get_context_data(self, **kwargs):
        """Agrega metadatos del filtro avanzado, permisos y bloques laterales
        (últimos items por tipo) cuando aplica.
        """
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        # ✅ columnas filtradas (sin 'eliminado')
        cols = self.crud_config.get_list_display()
        ctx["list_display"] = cols   # <-- pásalo al template

        # === NUEVO: datos del filtro avanzado usando cols ===
        adv_fields = _build_adv_fields_from_list_display(self.model, cols)
        ctx["adv_fields"] = adv_fields
        ctx["f"] = (self.request.GET.get("f") or "").strip()
        ctx["fv"] = (self.request.GET.get("fv") or "").strip()

        base_qs = self.object_list
        adv_choices = _adv_choices_for_fk_fields(self.request, self.model, adv_fields, base_qs)


        ctx["adv_choices_json"] = json.dumps(adv_choices, ensure_ascii=False)
        ctx["adv_fields_json"] = json.dumps(adv_fields, ensure_ascii=False)

        # permisos para botones (Nuevo/Editar/Eliminar)
        user = self.request.user
        app = self.model._meta.app_label
        model = self.model._meta.model_name

        can_create = user.has_perm(f"{app}.add_{model}")
        can_change = user.has_perm(f"{app}.change_{model}")
        can_delete = user.has_perm(f"{app}.delete_{model}")

################# 04/12 ########################################################
        # === REGLA EXTRA POR ROL: PlanMantencionActivo ===
        try:
            rol_actual = rol_de_usuario(user)
        except Exception:
            rol_actual = None
        ctx["rol_actual"] = rol_actual

        if self.model._meta.model_name == "planmantencionactivo" and rol_actual == ROL_USUARIO:
            can_change = False
            can_delete = False
################# 04/12 ########################################################

        # ⬇️ No permitir crear manualmente registros de auditoría
        if self.model._meta.model_name == "registro":
            can_create = False

############################# 09/12 ######################################
        # 🚫 Desactivar completamente Mantencion (solo lectura / o ni eso si luego ocultas el menú)
        if self.model._meta.model_name == "mantencion":
            can_create = False
            can_change = False
            can_delete = False
############################# 09/12 ######################################


        # disponibles tanto en cfg como en el contexto
        self.crud_config.can_create = can_create
        self.crud_config.can_change = can_change
        self.crud_config.can_delete = can_delete
        ctx["can_create"] = can_create
        ctx["can_change"] = can_change
        ctx["can_delete"] = can_delete

############################################################################>>>>>>>>>>>>>>>07/11
        # al final de get_context_data(...)
        if self.model._meta.model_name == "mantencionejecucion":
            self.crud_config.can_create = False
            self.crud_config.can_change = False
            self.crud_config.can_delete = False
            ctx["can_create"] = ctx["can_change"] = ctx["can_delete"] = False
############################################################################>>>>>>>>>>>>>>>07/11


        if self.model._meta.model_name == "atributosactivo":
            from .models_inventario import TipoActivo
            emp_id = self.request.session.get("empresa_id")
            te_qs = TipoActivo.objects.all()
            if emp_id:
                te_qs = te_qs.filter(id_empresa_id=emp_id)
            ctx["tipos_activo"] = te_qs.order_by("tipo_activo")
        return ctx


class GenericCreate(ExcludeEliminadoFormMixin, SaveEmpresaMixin, EmpresaScopeMixin, ModelPermsMixin, CreateView, EmpresaBoundMixin):
    """Create genérico con formularios automáticos y **soporte de archivos**.

    - Filtra combos por empresa activa.
    - Para modelos especiales (`Activo`, `Mantencion`, etc.) usa formularios
      específicos; si no, usa `_build_default_form`.
    - Al crear `Activo`, registra historial de forma segura.
    """
    template_name = "crud/form.html"
    action_perm = "add"
    crud_config: CrudConfig

    def form_invalid(self, form):
        from pprint import pprint
        print("\n=== ERRORES EN FORMULARIO ===")
        pprint(form.errors)
        pprint(form.non_field_errors())
        print("=== FIN ERRORES ===\n")
        return super().form_invalid(form)


    def get_form_class(self):
    ################################################################>>>>>>>>>>>>>15/11
        if self.model.__name__ == "ReglaCriticidad":
            return ReglaCriticidadForm
        if self.model.__name__ == "PreparacionAsignacion":
            return PreparacionAsignacionForm

    ################################################################>>>>>>>>>>>>>15/11

    ################################################################>>>>>>>>>>>>>>>>>
        if self.model.__name__ == "PlanMantencionActivo":
            from productos.forms import PlanMantencionActivoForm
            return PlanMantencionActivoForm
    ################################################################>>>>>>>>>>>>>>>>>
        if self.model.__name__ == "Activo":
            return ActivoForm
        if self.model.__name__ == "Mantencion":
            from productos.forms import MantencionForm
            return MantencionForm
        if self.model.__name__ == "Empleado":
            from productos.forms import EmpleadoForm
            return EmpleadoForm
        if self.model.__name__ == "Marca":                    # 👈 NUEVO
            from productos.forms import MarcaForm
            return MarcaForm
        if self.model.__name__ == "Ubicacion":
            from productos.forms import UbicacionForm
            return UbicacionForm
############################### 27/11 #########################################
        if self.model.__name__ == "DetalleFactura":          # 👈 NUEVO
            from productos.forms import DetalleFacturaForm
            return DetalleFacturaForm
############################### 27/11 #########################################

            return DetalleFacturaForm
        # fallback genérico para cualquier otro modelo (Departamento, Marca, etc.)
        return _build_default_form(self.model)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        emp_id = self.request.session.get("empresa_id")
#        if not emp_id: ########################### 10/12 ################
#            return form
        if emp_id:
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
                 # Si no hay emp_id, no filtramos nada y dejamos el form tal cual

        # dentro de GenericCreate.get_form(...) después de construir form
        if self.model.__name__ == "PlanMantencion":
            form.fields["hacer_vigente"] = forms.BooleanField(
                required=False,
                initial=False,
                label="Marcar como plan vigente en los activos afectados"
            )
            # Si no, lo dejamos tal cual

################################### 10/12 ############################################
        # 🔹 NUEVO: convertir 'rol' en <select> cuando el modelo es Empleado
        form = patch_rol_field_for_empleado(form, self.request)
        form = patch_permiso_bodega_field_for_empleado(form, self.request)

        # 🔹 NUEVO: si estamos creando / editando Empleado,
        # limitar las ubicaciones según PermisoBodega del usuario logueado
        if self.model.__name__ == "Empleado":
            ejecutor = getattr(self.request.user, "empleado", None)

            campo_ubic = None
            if "ubicacion" in form.fields:
                campo_ubic = "ubicacion"
            elif "id_ubicacion" in form.fields:
                campo_ubic = "id_ubicacion"

            if campo_ubic:
                qs_u = form.fields[campo_ubic].queryset
                qs_u = filtrar_ubicaciones_por_bodegas_permitidas(qs_u, ejecutor)
                form.fields[campo_ubic].queryset = qs_u
################################### 10/12 ############################################
        return form

    def get_success_url(self):
        # productos: <slug>_list  -> p.ej. productos:departamentos_list
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")
    
    def get_form_kwargs(self):
        """Incluye `POST` y **FILES** en métodos de escritura para soportar uploads."""
        kwargs = super().get_form_kwargs()
        # MUY IMPORTANTE: pasar archivos en métodos de escritura
        if self.request.method in ("POST", "PUT", "PATCH"):
            kwargs["data"] = self.request.POST
            kwargs["files"] = self.request.FILES
        FormClass = self.get_form_class()
        try:
            if "request" in inspect.signature(FormClass.__init__).parameters:
                kwargs["request"] = self.request
        except (TypeError, ValueError):
            pass
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        initial = super().get_initial()
        # ... (tu lógica existente)

        emp_id = self.request.session.get("empresa_id")

        if self.model.__name__ == "Activo":
            # Preselecciona empresa con la empresa de sesión
            if emp_id:
                initial.setdefault("id_empresa", emp_id)

            # Preselecciona Estado = “Disponible”
            ea_disp = _buscar_estado_activo(emp_id, "Disponible")
            if ea_disp:
                initial.setdefault("id_estado_activo", ea_disp.pk)


        # Permite ?plan=ID y/o ?activo=ID
        if self.model.__name__ == "PlanMantencionActivo":
            columnas = [
        ("Id Plan Mantencion Activo", "id_plan_mantencion_activo"),
        ("Id Empresa", "id_empresa"),
        ("Id Plan", "id_plan"),
        ("Id Activo", "id_activo"),
        ("Manten.", "estado_badge", "__safe__"),  # <<< usar HTML seguro (como en Activo)
        ("Es Vigente", "es_vigente"),
        ("Base Fecha", "base_fecha"),
        ("Ultima Medicion Fecha", "ultima_medicion_fecha"),
        ("Proximo Vencimiento Fecha", "proximo_vencimiento_fecha"),
    ]
            pid = self.request.GET.get("plan")
            aid = self.request.GET.get("activo")
            if pid:
                initial["id_plan"] = pid
            if aid:
                initial["id_activo"] = aid
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        emp_id = self.request.session.get("empresa_id")  # ⬅️ añade esto

                # Filtrar los tipos de activo por la empresa activa
        if self.model.__name__ == "Activo":
            from .models_inventario import TipoActivo
            qs = TipoActivo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)  # Aquí se filtra por empresa activa
            ctx["tipos_activo"] = qs.order_by("tipo_activo")

        if self.model.__name__ == "Activo":
            base = Activo.objects.all()
            if emp_id:
                base = base.filter(id_empresa_id=emp_id)
            if _has_field(Activo, "eliminado"):
                base = base.filter(eliminado=False)

            # id del último activo (mayor id_activo) por cada tipo
            last_ids = (
                base.values("id_tipo_activo_id")
                    .annotate(mx=Max("id_activo"))
                    .values_list("mx", flat=True)
            )

            ultimos = (
                Activo.objects.filter(id_activo__in=list(last_ids))
                    .select_related("id_tipo_activo")
                    .order_by("id_tipo_activo__tipo_activo")  # 1 por tipo, ordenados por nombre de tipo
            )

            # si quieres mantener la “última etiqueta global”
            ultima = base.order_by("-id_activo").first()

            ctx["ultimos_activos"] = ultimos
            ctx["ultima_etiqueta"] = ultima.etiqueta if ultima else None
    ##############################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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

        elif self.model.__name__ == "CondicionActivo":
            from .models_inventario import CondicionActivo
            qs = CondicionActivo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            ctx["side_title"] = "Últimas condiciones de activo"
            ctx["side_items"] = qs.order_by("-id_condicion_activo")[:15]

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

            # 🔒 Aplica también permisos de bodegas en el sidebar
            ejecutor = getattr(self.request.user, "empleado", None)
            qs = filtrar_empleados_por_bodegas_permitidas(qs, ejecutor)

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

#        elif self.model.__name__ == "Factura":
#            from .models_inventario import Factura as F
#            ctx["side_title"] = "Últimas facturas"
#            ctx["side_items"] = F.objects.order_by("-id_factura")[:15]

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
            ctx["side_items"] = qs.order_by("-id_factura")[:15]  # Los últimos 5 registros

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
        # === PRECHEQUEO SOLO PARA Cargo (CREATE) ===
        if self.model.__name__ == "Cargo":
            emp_id = _get_emp_id_from_request_or_instance(self.request, form.instance)

            nombre_raw = (
                getattr(form.instance, "nombre_cargo", None)
                or form.cleaned_data.get("nombre_cargo")
                or ""
            )
            norm_new = _norm_nombre(nombre_raw)

            cand_qs = Cargo.objects.filter(id_empresa_id=emp_id).only("id_cargo", "nombre_cargo", "eliminado")
            duplicate_active = None
            duplicate_deleted = None
            for c in cand_qs:
                if _norm_nombre(getattr(c, "nombre_cargo", "") or "") == norm_new:
                    if getattr(c, "eliminado", False):
                        duplicate_deleted = c
                    else:
                        duplicate_active = c
                    break

            if duplicate_active:
                form.add_error(
                    "nombre_cargo",
                    "Ya existe un cargo activo con este nombre en esta empresa."
                )
                dj_messages.error(self.request, "No se pudo crear: cargo duplicado en esta empresa.")
                return self.form_invalid(form)

            if duplicate_deleted:
                # Reactivar en vez de crear uno nuevo
                duplicate_deleted.eliminado = False
                duplicate_deleted.save(update_fields=["eliminado"])
                dj_messages.success(self.request, "Cargo reactivado (existía como eliminado).")
                self.object = duplicate_deleted
                return HttpResponseRedirect(self.get_success_url())
                
        # === PRECHEQUEO SOLO PARA Proveedor (CREATE) ===
        if self.model.__name__ == "Proveedor":
            from productos.models_inventario import Proveedor
            emp_id = _get_emp_id_from_request_or_instance(self.request, form.instance)
            # toma el nombre desde el form/instancia (según tu ModelForm)
            nombre_raw = (
                getattr(form.instance, "nombre_proveedor", None)
                or form.cleaned_data.get("nombre_proveedor")
                or form.cleaned_data.get("nombre")  # fallback si el campo se llama 'nombre'
                or ""
            )
            norm_new = _norm_nombre(nombre_raw)

            # Trae posibles candidatos en esa empresa (activos y eliminados)
            cand_qs = Proveedor.objects.filter(id_empresa_id=emp_id).only("id_proveedor", "nombre_proveedor", "eliminado")
            # Normaliza en Python para igualar la lógica del índice
            duplicate_active = None
            duplicate_deleted = None
            for p in cand_qs:
                norm_old = _norm_nombre(getattr(p, "nombre_proveedor", "") or "")
                if norm_old == norm_new:
                    if getattr(p, "eliminado", False):
                        duplicate_deleted = p
                    else:
                        duplicate_active = p
                    break

            if duplicate_active:
                # Ya existe el mismo nombre ACTIVO en esta empresa → error de validación
                form.add_error(
                    "nombre_proveedor" if "nombre_proveedor" in form.fields else "nombre",
                    "Ya existe un proveedor activo con este nombre en esta empresa."
                )
                #from django.contrib import messages
                #from django.contrib import messages as dj_messages
                dj_messages.error(self.request, "No se pudo crear: ya existe un proveedor activo con ese nombre.")
                return self.form_invalid(form)

            if duplicate_deleted:
                # OPCIÓN: reactivar en vez de crear uno nuevo
                duplicate_deleted.eliminado = False
                # si tienes más campos que quieras refrescar, hazlo aquí antes de guardar
                duplicate_deleted.save(update_fields=["eliminado"])
                #from django.contrib import messages
                #from django.contrib import messages as dj_messages
                dj_messages.success(self.request, "Proveedor reactivado (existía como eliminado).")
                # redirige como si fuera éxito de create
                self.object = duplicate_deleted
                return HttpResponseRedirect(self.get_success_url())

        # ====== resto de tu lógica de form_valid (PlanMantencion, Empleado, Activo, etc.) ======
        try:
            resp = super().form_valid(form)
        except IntegrityError:
            # Seguridad: si por carrera igual chocó el índice, devolvemos error amable
            if self.model.__name__ == "Proveedor":
                form.add_error(
                    "nombre_proveedor" if "nombre_proveedor" in form.fields else "nombre",
                    "Ya existe un proveedor con este nombre en esta empresa."
                )
                #from django.contrib import messages
                #from django.contrib import messages as dj_messages
                dj_messages.error(self.request, "No se pudo guardar: proveedor duplicado.")
                return self.form_invalid(form)
            
            if self.model.__name__ == "Cargo":
                form.add_error("nombre_cargo", "Ya existe un cargo con este nombre en esta empresa.")
                dj_messages.error(self.request, "No se pudo guardar: cargo duplicado.")
                return self.form_invalid(form)    
            
            raise
    #######################################################################################################29/10
        # ===== PlanMantencion: aplicar a Activos y manejar "vigente" (solo con los campos del plan) =====
        # ===== PlanMantencion: aplicar a Activos y manejar "vigente" =====
        if self.model.__name__ == "PlanMantencion":
            plan = self.object
            hacer_vigente = bool(form.cleaned_data.get("hacer_vigente", False))
            total, creados, vigentes = _aplicar_plan_a_activos(self.request, plan, hacer_vigente)

            msg = f"Plan aplicado a {total} activo(s). Creados/activados {creados}."
            if hacer_vigente:
                msg += f" {vigentes} marcado(s) como vigente."
            dj_messages.success(self.request, msg)

            # Evita el mensaje genérico de más abajo y cualquier lógica ajena a PlanMantencion
            return resp

        #######################################################################################################29/10


        if self.model.__name__ == "Empleado" and form.instance.correo:
            crear_usuario_y_enviar_correo(form.instance)
####################################### 10/12 ################################################
        if self.model.__name__ == "Empleado":
            emp = self.object  # el empleado recién creado
            rol_emp = (emp.rol or "").strip().lower()

            # Solo tiene sentido si el rol es 'usuario'
            if rol_emp == Empleado.ROL_USUARIO:
                bodega = form.cleaned_data.get("permiso_bodega")
                if bodega:
                    # Usamos la empresa del empleado o la de la sesión
                    emp_empresa_id = getattr(emp, "id_empresa_id", None) or \
                                     self.request.session.get("empresa_id")

                    # Creamos el permiso (si ya quieres evitar duplicados, puedes usar get_or_create)
                    PermisoBodega.objects.create(
                        id_empleado=emp,
                        id_bodega=bodega,
                        id_empresa_id=emp_empresa_id,
                    )
####################################### 10/12 ################################################


        # --- SOLO para Activo: arrastrar ubicación desde el empleado ---
        if self.model.__name__ == "Activo":
            activo = self.object  # ya guardado
            nuevo_emp = form.cleaned_data.get("id_empleado")

            # Si NO eligieron ubicación manual y el empleado tiene ubicación → copiar
            if (not form.cleaned_data.get("id_ubicacion")
                    and nuevo_emp and getattr(nuevo_emp, "ubicacion_id", None)):
                if activo.id_ubicacion_id != nuevo_emp.ubicacion_id:
                    activo.id_ubicacion_id = nuevo_emp.ubicacion_id
                    activo.save(update_fields=["id_ubicacion"])

        dj_messages.success(self.request, "Guardado correctamente.")
        return resp

###################################################################################2509

###################################################################################2509

class GenericUpdate(ExcludeEliminadoFormMixin, SaveEmpresaMixin, EmpresaScopeMixin, ModelPermsMixin, UpdateView, EmpresaBoundMixin):
    """Update genérico con soporte de archivos y lógica de negocio.

    - Filtra combos por empresa activa.
    - Sincroniza atributos dinámicos de `Activo` según `TipoActivo`.
    - En `Empleado`, alinea correo en `auth_user` y puede crear usuario si aplica.
    """
    template_name = "crud/form.html"
    action_perm = "change"
    crud_config: CrudConfig
##################################### 04/12 ###################################################
    def dispatch(self, request, *args, **kwargs):
        # 🚫 Regla específica: los usuarios normales NO pueden editar PlanMantencionActivo
        if self.model.__name__ == "PlanMantencionActivo":
            if rol_de_usuario(request.user) == ROL_USUARIO:
                return HttpResponseForbidden("No tienes permisos para editar este registro.")
        return super().dispatch(request, *args, **kwargs)
##################################### 04/12 ###################################################


    def get_queryset(self):
            qs = self.model.objects.all()
            return self.scope_queryset(qs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.model.__name__ in ("Mantencion", "Activo", "PlanMantencionActivo"):
            kwargs["request"] = self.request
#        if self.model.__name__ in ("Mantencion", "Activo"):
#            kwargs["request"] = self.request
        # MUY IMPORTANTE: pasar archivos
        if self.request.method in ("POST", "PUT", "PATCH"):
            kwargs["data"] = self.request.POST
            kwargs["files"] = self.request.FILES
        return kwargs

    def get_form_class(self):
    ################################################################>>>>>>>>>>>>>15/11
        if self.model.__name__ == "ReglaCriticidad":
            return ReglaCriticidadForm
        # 🔹 NUEVO: usar el formulario custom para PreparacionAsignacion
        if self.model.__name__ == "PreparacionAsignacion":
            return PreparacionAsignacionForm

    ################################################################>>>>>>>>>>>>>15/11
    ################################################################>>>>>>>>>>>>>>>>>
        if self.model.__name__ == "PlanMantencionActivo":
            from productos.forms import PlanMantencionActivoForm
            return PlanMantencionActivoForm
    ################################################################>>>>>>>>>>>>>>>>>
        if self.model.__name__ == "Activo":
            return ActivoForm
        if self.model.__name__ == "Mantencion":     # ← y esto
            from productos.forms import MantencionForm
            return MantencionForm
        #return _build_default_form(self.model)
        if self.model.__name__ == "Empleado":
            from productos.forms import EmpleadoForm        # ← usar el de forms.py
            return EmpleadoForm
        if self.model.__name__ == "Marca":                    # 👈 NUEVO
            from productos.forms import MarcaForm
            return MarcaForm
        if self.model.__name__ == "Ubicacion":
            from productos.forms import UbicacionForm
            return UbicacionForm
############################### 27/11 #########################################
        if self.model.__name__ == "DetalleFactura":          # 👈 NUEVO
            from productos.forms import DetalleFacturaForm
            return DetalleFacturaForm
############################### 27/11 #########################################
        return _build_default_form(self.model)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        emp_id = self.request.session.get("empresa_id")
#        if not emp_id:
#            return form

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
                
        if self.model.__name__ == "PlanMantencion":
            form.fields["hacer_vigente"] = forms.BooleanField(
                required=False,
                initial=False,
                label="Marcar como plan vigente en los activos afectados"
            )
            # Si no, lo dejamos tal cual

        ################################### 10/12 ############################################
        # 🔹 NUEVO: convertir 'rol' en <select> cuando el modelo es Empleado
        form = patch_rol_field_for_empleado(form, self.request)

        # 🔹 NUEVO: si estamos creando / editando Empleado,
        # limitar las ubicaciones según PermisoBodega del usuario logueado
        if self.model.__name__ == "Empleado":
            ejecutor = getattr(self.request.user, "empleado", None)

            campo_ubic = None
            if "ubicacion" in form.fields:
                campo_ubic = "ubicacion"
            elif "id_ubicacion" in form.fields:
                campo_ubic = "id_ubicacion"

            if campo_ubic:
                qs_u = form.fields[campo_ubic].queryset
                qs_u = filtrar_ubicaciones_por_bodegas_permitidas(qs_u, ejecutor)
                form.fields[campo_ubic].queryset = qs_u
        ################################### 10/12 ############################################
        return form


    def get_success_url(self):
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

    def form_valid(self, form):
        # --- PRECHEQUEO SOLO PARA Cargo (UPDATE) ---
        if self.model.__name__ == "Cargo":
            emp_id = self.request.session.get("empresa_id") or getattr(form.instance, "id_empresa_id", None)
            nombre_raw = (
                getattr(form.instance, "nombre_cargo", None)
                or form.cleaned_data.get("nombre_cargo")
                or ""
            )
            norm_new = _norm_nombre(nombre_raw)

            qs = Cargo.objects.filter(id_empresa_id=emp_id).exclude(pk=getattr(self.object, "pk", None))
            dup = None
            for c in qs:
                if _norm_nombre(getattr(c, "nombre_cargo", "") or "") == norm_new and not getattr(c, "eliminado", False):
                    dup = c
                    break
            if dup:
                form.add_error("nombre_cargo", "Ya existe un cargo activo con este nombre en esta empresa.")
                dj_messages.warning(self.request, "No se pudo guardar: nombre de cargo duplicado.")
                return self.form_invalid(form)
            

        # --- PRECHEQUEO SOLO PARA Proveedor: evita duplicados por nombre dentro de la empresa ---
        if self.model.__name__ == "Proveedor":
            emp_id = self.request.session.get("empresa_id") or getattr(form.instance, "id_empresa_id", None)
            # nombre: toma el que exista (según tu ModelForm)
            nombre_raw = (
                getattr(form.instance, "nombre_proveedor", None)
                or form.cleaned_data.get("nombre_proveedor")
                or form.cleaned_data.get("nombre")     # <-- fallback si el campo es "nombre"
                or ""
            )
            norm_new = _norm_nombre(nombre_raw)

            qs = Proveedor.objects.filter(id_empresa_id=emp_id).exclude(pk=getattr(self.object, "pk", None))
            dup = None
            for p in qs:
                if _norm_nombre(getattr(p, "nombre_proveedor", "") or "") == norm_new and not getattr(p, "eliminado", False):
                    dup = p
                    break
            if dup:
                form.add_error("nombre_proveedor" if "nombre_proveedor" in form.fields else "nombre",
                            "Ya existe un proveedor activo con este nombre en esta empresa.")
                dj_messages.warning(self.request, "No se pudo guardar: nombre duplicado.")
                return self.form_invalid(form)
        # -----------------------------------------------------------------------
        try:
            resp = super().form_valid(form)   # <-- define resp aquí
        except IntegrityError:
            if self.model.__name__ == "Proveedor":
                form.add_error(
                    "nombre_proveedor" if "nombre_proveedor" in form.fields else "nombre",
                    "Ya existe un proveedor activo con este nombre en esta empresa."
                )
                dj_messages.error(self.request, "No se pudo guardar: ya existe un proveedor con ese nombre.")
                return self.form_invalid(form)

            if self.model.__name__ == "Cargo":
                form.add_error("nombre_cargo", "Ya existe un cargo con este nombre en esta empresa.")
                dj_messages.error(self.request, "No se pudo guardar: cargo duplicado.")
                return self.form_invalid(form)
            raise
    ###############################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>30/10
        if self.model.__name__ == "PlanMantencion":
            plan = self.object
            hacer_vigente = bool(form.cleaned_data.get("hacer_vigente", False))
            total, creados, vigentes = _aplicar_plan_a_activos(self.request, plan, hacer_vigente)

            msg = f"Plan aplicado a {total} activo(s). Creados/activados {creados}."
            if hacer_vigente:
                msg += f" {vigentes} marcado(s) como vigente."
            dj_messages.success(self.request, msg)
            return resp
    ###############################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>30/10
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

        # === HEREDAR UBICACIÓN DEL EMPLEADO EN UPDATE (sin pisar selección manual) ===
        if self.model.__name__ == "Activo":
            activo = self.object
            nuevo_emp = form.cleaned_data.get("id_empleado")
            posted_ubic = form.cleaned_data.get("id_ubicacion")  # lo que vino del form (si el usuario eligió algo)

            # Si hay empleado con ubicación, y el usuario NO cambió id_ubicacion manualmente,
            # copiamos la ubicación del empleado al activo.
            if nuevo_emp and getattr(nuevo_emp, "ubicacion_id", None):
                if ("id_ubicacion" not in form.changed_data) or not posted_ubic:
                    if activo.id_ubicacion_id != nuevo_emp.ubicacion_id:
                        activo.id_ubicacion_id = nuevo_emp.ubicacion_id
                        activo.save(update_fields=["id_ubicacion"])

        if self.model.__name__ == "Empleado":
            obj = self.object
            old = None

            try:
                old = self.model.objects.get(pk=self.get_object().pk)
            except Exception:
                old = None

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
            #sync_user_groups_for_empleado(obj) GENERA ERRORES INHABILITADO POR AHORA

        # === GUARDAR / ACTUALIZAR VALORES DE ATRIBUTOS (solo Activo) ===
        if self.model.__name__ == "Activo":
            activo = self.object

            # 1) detectamos tipo actual y si el formulario realmente envió atributos
            #posted_attr_keys = [k for k in self.request.POST.keys() if k.startswith("attr_")]
            posted_attr_keys = [k for k in self.request.POST.keys() if k.startswith("attr_")]
            

            posted_tipo = self.request.POST.get("id_tipo_activo")
            tipo_id = posted_tipo or getattr(activo, "id_tipo_activo_id", None)

            # 2) ¿cambió el tipo?
            prev_obj = None
            prev_tipo_id = None
            try:
                prev_obj = self.get_object()
                prev_tipo_id = getattr(prev_obj, "id_tipo_activo_id", None)
            except Exception:
                pass
            tipo_cambiado = (posted_tipo and str(prev_tipo_id or "") != str(posted_tipo))

            # 3) Si NO hay campos attr_* en el POST y NO cambió el tipo → no tocar nada
            if not posted_attr_keys and not tipo_cambiado:
                pass
            else:
                from .models_inventario import AtributosActivo, AgregacionAtributosPorActivo
                from django.db import transaction

                # atributos definidos para el tipo seleccionado
                attrs_ids = list(
                    AtributosActivo.objects
                    .filter(id_tipo_activo_id=tipo_id)
                    .values_list("id_atributo_activo", flat=True)
                )

                # estado actual guardado
                actuales = {
                    r.atributo_id: r
                    for r in AgregacionAtributosPorActivo.objects.filter(activo_id=activo.id_activo)
                }

                with transaction.atomic():
                    # 3.a) Actualizar/crear sólo los que vinieron en el formulario
                    for attr_id in attrs_ids:
                        raw = self.request.POST.get(f"attr_{attr_id}", None)
                        if raw is None and not tipo_cambiado:
                            # no se posteó este atributo y no cambió el tipo → lo dejamos igual
                            continue
                        val = (raw or "").strip() if raw is not None else ""

                        row = actuales.get(attr_id)
                        if row:
                            # sólo guardamos si realmente cambió el valor
                            if (row.valor or "") != (val or ""):
                                row.valor = (val or None)
                                row.save(update_fields=["valor"])
                        else:
                            # crear sólo si hay valor
                            if val:
                                AgregacionAtributosPorActivo.objects.create(
                                    activo_id=activo.id_activo,
                                    atributo_id=attr_id,
                                    valor=val
                                )

                    # 3.b) Si CAMBIÓ el tipo → eliminar los atributos que ya no apliquen
                    if tipo_cambiado:
                        ids_validos = set(attrs_ids)
                        sobra = [
                            r.pk for r in actuales.values()
                            if r.atributo_id not in ids_validos
                        ]
                        if sobra:
                            # esto sí generará registros ELIMINAR, pero sólo cuando cambia el tipo (esperado)
                            AgregacionAtributosPorActivo.objects.filter(pk__in=sobra).delete()
        dj_messages.success(self.request, "Cambios guardados correctamente.")
        return resp



    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        emp_id = self.request.session.get("empresa_id")
        
        ### Hola hola
#######################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        if self.model.__name__ == "Activo":
            base = Activo.objects.all()
            if emp_id:
                base = base.filter(id_empresa_id=emp_id)
            if _has_field(Activo, "eliminado"):
                base = base.filter(eliminado=False)

            # id del último activo (mayor id_activo) por cada tipo
            last_ids = (
                base.values("id_tipo_activo_id")
                    .annotate(mx=Max("id_activo"))
                    .values_list("mx", flat=True)
            )

            ultimos = (
                Activo.objects.filter(id_activo__in=list(last_ids))
                    .select_related("id_tipo_activo")
                    .order_by("id_tipo_activo__tipo_activo")  # 1 por tipo, ordenados por nombre de tipo
            )

            # si quieres mantener la “última etiqueta global”
            ultima = base.order_by("-id_activo").first()

            ctx["ultimos_activos"] = ultimos
            ctx["ultima_etiqueta"] = ultima.etiqueta if ultima else None
#######################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

        if self.model.__name__ == "Activo" and obj:
            from .models_inventario import AgregacionAtributosPorActivo as AAPA
            pares = AAPA.objects.filter(activo_id=obj.id_activo).values_list("atributo_id", "valor")
            ctx["attr_values"] = {f"attr_{aid}": val for aid, val in pares}

        elif self.model.__name__ == "Mantencion":
            from .models_inventario import Mantencion as Mant
            qs = Mant.objects.all()  # <-- paréntesis cerrado
            if emp_id:
                if "id_empresa" in {f.name for f in Mant._meta.get_fields()}:
                    qs = qs.filter(id_empresa_id=emp_id)
                else:
                    qs = qs.filter(id_activo__id_empresa_id=emp_id)
            ctx["side_title"] = "Últimas mantenciones"
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

            # 🔒 Mismo criterio de permisos de bodegas
            ejecutor = getattr(self.request.user, "empleado", None)
            qs = filtrar_empleados_por_bodegas_permitidas(qs, ejecutor)


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

        elif self.model.__name__ == "AtributosActivo":  # Aquí se aplica el filtro solo para AtributosActivo
            from .models_inventario import TipoActivo
            qs = TipoActivo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)  # Filtro por empresa activa
            ctx["tipos_activo"] = qs.order_by("tipo_activo")
        return ctx

# productos/crud.py parte 2
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from .models_inventario import (
    Activo, Empleado, Departamento,
    Modelo, Marca, TipoActivo, EstadoActivo,
    CondicionActivo, Proveedor, Factura, Ubicacion,
    AtributosActivo, AgregacionAtributosPorActivo
)

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models_inventario import (
    Activo, Empleado, Departamento, Ubicacion,
    Proveedor, Factura, Marca, TipoActivo, EstadoActivo, CondicionActivo,
    Modelo, AtributosActivo, AgregacionAtributosPorActivo
)


class ActivoForm(forms.ModelForm):
    """Formulario de `Activo` con reglas de negocio y filtrado por empresa."""
################################### 29/11 ###########################################
    # 👇 NUEVO: campo solo de formulario, NO de modelo
    cantidad = forms.IntegerField(
        label="Cantidad de activos a crear",
        min_value=1,
        required=False,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control"})
    )
################################### 29/11 ###########################################

    class Meta:
        model = Activo
        fields = [
            "id_tipo_activo",
            "id_marca",
            "nombre_activo",
            "id_estado_activo",
            "id_ubicacion",
            #"id_condicion_activo",
            "id_condicion_detalle",        # ✅ AHORA            
            "id_empleado",
            "id_proveedor",
            "id_factura",
            "etiqueta",
            "numero_serie",
            "observaciones",
            "id_empresa",
            "id_departamento",
            "activo_critico",
            "clasificacion",
            "confidencialidad",
            "integridad",
            "disponibilidad",
        ]
        
        widgets = {
            "id_empresa": forms.Select(attrs={"class": "form-select searchable"}),
            "id_departamento": forms.Select(attrs={"class": "form-select searchable"}),
            "id_tipo_activo": forms.Select(attrs={"class": "form-select searchable"}),
            "nombre_activo": forms.Select(attrs={"class": "form-select searchable"}),  # se reemplaza en __init__
            "id_marca": forms.Select(attrs={"class": "form-select searchable"}),
            "id_estado_activo": forms.Select(attrs={"class": "form-select searchable"}),
            "id_ubicacion": forms.Select(attrs={"class": "form-select searchable"}),
            #"id_condicion_activo": forms.Select(attrs={"class": "form-select searchable"}),
            "id_condicion_detalle": forms.Select(attrs={"class": "form-select searchable"}),    # ✅
            "id_empleado": forms.Select(attrs={"class": "form-select searchable"}),
            "id_proveedor": forms.Select(attrs={"class": "form-select searchable"}),
            "id_factura": forms.Select(attrs={"class": "form-select searchable"}),
            "etiqueta": forms.TextInput(attrs={"class": "form-control"}),
            "numero_serie": forms.TextInput(attrs={"class": "form-control"}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "activo_critico": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "clasificacion": forms.Select(
                choices=[
                    ("confidencial", "Confidencial"),
                    ("uso_interno", "Uso Interno"),
                    ("publico", "Público"),
                ],
                attrs={"class": "form-select"},
            ),
            "confidencialidad": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 4, "step": 1}),
            "integridad": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 4, "step": 1}),
            "disponibilidad": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 4, "step": 1}),
        }
         
#    # Descomentar en caso de querer ver mensajes dentro de loscampos
#    def _pretty_empty_labels(self, mapping=None, default_label="— Seleccione —"):
#            mapping = mapping or {}
#            for name, field in self.fields.items():
#                if isinstance(field, forms.ModelChoiceField):
#                    field.empty_label = mapping.get(name, default_label)  # Asigna el empty_label a cada campo


    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id_tipo_activo"].label = "Tipo de activo"
        self.fields["id_marca"].label = "Marca"
        self.fields["nombre_activo"].label = "Modelo"
        self.fields["id_estado_activo"].label = "Estado activo"
        self.fields["id_ubicacion"].label = "Ubicación"
        self.fields["id_empleado"].label = "Empleado"
        self.fields["id_proveedor"].label = "Proveedor"
        self.fields["id_empresa"].label = "Empresa"
        self.fields["id_departamento"].label = "Departamento"

        self.request = request
        emp_id = request.session.get("empresa_id") if request else None
################################### 29/11 ###########################################
        # 👇 NUEVO: comportamiento del campo cantidad
        if "cantidad" in self.fields:
            if self.instance and getattr(self.instance, "id_activo", None):
                # Si estoy EDITANDO un activo existente → oculto y fijo en 1
                self.fields["cantidad"].widget = forms.HiddenInput()
                self.fields["cantidad"].initial = 1
                self.fields["cantidad"].required = False
            else:
                # En CREACIÓN → visible, default 1
                if not self.fields["cantidad"].initial:
                    self.fields["cantidad"].initial = 1
                self.fields["cantidad"].required = False
################################### 29/11 ###########################################
#################################################################################>>>>>>>>>>>>>>>>>>>>>>>>>><11/11 16:35
        # Placeholder por defecto
        self.fields["nombre_activo"].choices = [("", "Seleccione un modelo")]

        # Al inicio o cerca de donde seteas labels/widgets en __init__
#        if self.instance and getattr(self.instance, "nombre_activo", None):
#            self.fields["nombre_activo"].widget.attrs["data-current-name"] = self.instance.nombre_activo


#    # Descomentar en caso de querer ver mensajes dentro de loscampos
#        self._pretty_empty_labels({
#        "id_tipo_activo": "— Seleccione el tipo —",
#        "id_marca": "— Seleccione la marca —",
#        "id_estado_activo": "— Seleccione el estado —",
#        "id_ubicacion": "— Seleccione la ubicación —",
#        "id_empleado": "— Seleccione el responsable —",
#        "id_proveedor": "— Seleccione el proveedor —",
#        "id_factura": "— Seleccione la factura —",
#        "id_empresa": "— Seleccione la empresa —",
#        "id_departamento": "— Seleccione el departamento —",
#    })

        # Detectar valores actuales (POST/initial/instance) para precargar
        def _val(cam, inst_attr=None):
            return (
                self.data.get(cam)
                or self.initial.get(cam)
                or (getattr(self.instance, inst_attr, None) if self.instance and inst_attr else None)
            )

        tipo_id  = _val("id_tipo_activo", "id_tipo_activo_id")
        marca_id = _val("id_marca",       "id_marca_id")



        # 🔽 NUEVO: restringe marcas por tipo (y empresa/eliminados)
        if "id_marca" in self.fields:
            base_marcas = Marca.objects.all()
            if emp_id and _model_has_empresa_fk(Marca):
                base_marcas = base_marcas.filter(id_empresa_id=emp_id)
            if _has_field(Marca, "eliminado"):
                base_marcas = base_marcas.filter(eliminado=False)

            if tipo_id:
                mod_qs = Modelo.objects.filter(id_tipo_activo_id=tipo_id)
                if emp_id:
                    mod_qs = mod_qs.filter(id_empresa_id=emp_id)
                if _has_field(Modelo, "eliminado"):
                    mod_qs = mod_qs.filter(eliminado=False)

                marca_ids = mod_qs.values_list("id_marca_id", flat=True).distinct()
                mqs = base_marcas.filter(pk__in=marca_ids)

                # Si estoy editando y la marca actual no entra en el filtro, la agrego para no “reventar” el form
                if marca_id:
                    mqs = (mqs | base_marcas.filter(pk=marca_id)).distinct()
                self.fields["id_marca"].queryset = mqs.order_by("nombre_marca")
            else:
                # Sin tipo seleccionado: deja marcas de la empresa (no eliminadas)
                self.fields["id_marca"].queryset = base_marcas.order_by("nombre_marca")




        qs = Modelo.objects.filter(eliminado=False)
        if emp_id:
            qs = qs.filter(id_empresa_id=emp_id)
        if tipo_id:
            qs = qs.filter(id_tipo_activo_id=tipo_id)
        if marca_id:
            qs = qs.filter(id_marca_id=marca_id)

        if qs.exists():
            # value y label = nombre_modelo (guardas texto en `nombre_activo`)
            self.fields["nombre_activo"].choices = [("", "Seleccione un modelo")] + [
                (m.pk, m.nombre_modelo) for m in qs.order_by("nombre_modelo")
            ]
        # Precarga al EDITAR: si el activo guarda texto en nombre_activo, mapea a su Modelo (ID)
        if not self.data and self.instance and getattr(self.instance, "id_activo", None):
            actual_name = (self.instance.nombre_activo or "").strip()
            if actual_name:
                match = qs.filter(nombre_modelo__iexact=actual_name).first()
                if match:
                    self.initial["nombre_activo"] = match.pk
                    # Asegurar que la opción esté en choices aunque el filtro cambie
                    if (match.pk, match.nombre_modelo) not in self.fields["nombre_activo"].choices:
                        self.fields["nombre_activo"].choices.append((match.pk, match.nombre_modelo))


        # (opcional) obliga a elegir uno
        self.fields["nombre_activo"].required = True
#################################################################################>>>>>>>>>>>>>>>>>>>>>>>>>><11/11 16:35



        # 👇 Oculta en selects cualquier opción marcada eliminado=True
        hide_deleted(self, "id_ubicacion", "id_estado_activo", "id_marca", "id_proveedor", "id_empleado")

        # Ocultar campos según tipo "Información" (si lo usas)
        tipo_activo_ini = self.initial.get("id_tipo_activo")
        if tipo_activo_ini == "Información":
            for n in ("id_marca", "id_estado_activo", "id_empleado", "id_proveedor"):
                if n in self.fields:
                    self.fields[n].widget = forms.HiddenInput()
            for n in ("confidencialidad", "integridad", "disponibilidad"):
                self.fields[n].widget.attrs["style"] = "display:none"

        # Scope por empresa en FKs comunes
        if emp_id and "id_empresa" in self.fields:
            self.fields["id_empresa"].queryset = self.fields["id_empresa"].queryset.filter(id_empresa=emp_id)

        if "id_empleado" in self.fields:
            empleados_qs = Empleado.objects.filter(estado_activo=True)
            if emp_id:
                empleados_qs = empleados_qs.filter(id_empresa_id=emp_id)
            self.fields["id_empleado"].queryset = empleados_qs.order_by("nombre", "apellido_paterno")

        if "id_factura" in self.fields:
            from .models_inventario import Factura
            fqs = Factura.objects.all()
            if emp_id:
                fqs = fqs.filter(id_empresa_id=emp_id)
            self.fields["id_factura"].queryset = fqs.order_by("-fecha_emision", "folio")
            self.fields["id_factura"].label = "Factura (folio)"
            self.fields["id_factura"].help_text = "Opcional. Selecciona por folio; puedes dejarlo en blanco."

#        if "id_condicion_activo" in self.fields:
#            from .models_inventario import CondicionActivo
#            cqs = CondicionActivo.objects.all()
#            if emp_id:
#                cqs = cqs.filter(id_empresa_id=emp_id)
#            self.fields["id_condicion_activo"].queryset = cqs.order_by("descripcion")
                # Condición (detalle) visible para el usuario
##################################################### 20/10 ###################################                
        if "id_condicion_detalle" in self.fields:
            qs_cond = CondicionDetalle.objects.all()

            # Filtrar por empresa, si el modelo la tiene
            if emp_id and _model_has_empresa_fk(CondicionDetalle):
                qs_cond = qs_cond.filter(id_empresa_id=emp_id)

            # Ocultar eliminados si el modelo tiene campo `eliminado`
            if _has_field(CondicionDetalle, "eliminado"):
                qs_cond = qs_cond.filter(eliminado=False)

            # Orden genérico
            qs_cond = qs_cond.order_by("pk")
            self.fields["id_condicion_detalle"].queryset = qs_cond

            # Nombre amigable
            self.fields["id_condicion_detalle"].label = "Condición"

            # (Opcional) preseleccionar "Nuevo [Sin Preparar]" solo en creación
            if not self.instance.pk and not self.data:
                try:
                    default_detalle = qs_cond.filter(
                        condicion_activo__codigo_sistema="NUEVO",
                        descripcion__icontains="Sin Preparar",
                    ).first()
                    if default_detalle:
                        self.fields["id_condicion_detalle"].initial = default_detalle.pk
                except Exception:
                    # Si los nombres de campos no coinciden, simplemente no fija inicial.
                    pass
##################################################### 20/10 ###################################   

        if "id_departamento" in self.fields:
            dqs = Departamento.objects.all()
            if emp_id:
                dqs = dqs.filter(id_empresa_id=emp_id)
            self.fields["id_departamento"].queryset = dqs.order_by("nombre_departamento")


########################################### 08/12 ##########################################
        if "id_ubicacion" in self.fields:
            from .models_inventario import Ubicacion

            base = Ubicacion.objects.all()
            if emp_id:
                base = base.filter(id_empresa_id=emp_id)

            # 1) Drop-down normal: SOLO no eliminadas
            #    y, mientras haces la limpieza, ocultamos las ubicaciones legacy con "(Bodega)" en el nombre
            qs_ok = (
                base
                .filter(eliminado=False)
                .exclude(nombre_ubicacion__icontains="(bodega)")  # 👈 legacy fuera del combo
                .order_by("nombre_ubicacion")
            )
            self.fields["id_ubicacion"].queryset = qs_ok

            # 2) Si estoy EDITANDO y el activo apunta a una ubicación eliminada, la incluyo solo para este form
            cur_id = getattr(self.instance, "id_ubicacion_id", None)
            if cur_id:
                cur_del = base.filter(pk=cur_id, eliminado=True).first()
                if cur_del:
                    self.fields["id_ubicacion"].queryset = (qs_ok | base.filter(pk=cur_id)).distinct()
                    self.fields["id_ubicacion"].help_text = (
                        "La ubicación actual está marcada como eliminada. Debes reemplazarla para guardar."
                    )

            # 3) En CREACIÓN (no edición, sin POST): preseleccionar "Matriz" como ubicación por defecto
            if not self.instance.pk and not self.data:
                ubic_default = (
                    qs_ok
                    .filter(nombre_ubicacion__iexact="Matriz")
                    .order_by("id_ubicacion")
                    .first()
                )
                if ubic_default:
                    self.fields["id_ubicacion"].initial = ubic_default.pk

########################################### 08/12 ##########################################

#        if "id_marca" in self.fields:
#            mqs = Marca.objects.all()
#            if emp_id:
#                mqs = mqs.filter(id_empresa_id=emp_id)
#            self.fields["id_marca"].queryset = mqs.order_by("nombre_marca")

#        # ====== Campo "nombre_activo" como lista de Modelos (y precarga en edición) ======
#        if "nombre_activo" in self.fields:
#            # Detecta tipo actual: POST > initial > instancia
#            # Detecta el tipo seleccionado (POST, initial o instancia)
#            tipo_id = (
#                self.data.get("id_tipo_activo")
#                or self.initial.get("id_tipo_activo")
#                or getattr(self.instance, "id_tipo_activo_id", None)
#            )
#            # Si vino instancia, normaliza a PK
#            if hasattr(tipo_id, "pk"):
#                tipo_id = tipo_id.pk
#
#            modelos_qs = Modelo.objects.all()
#            if emp_id:
#                modelos_qs = modelos_qs.filter(id_empresa_id=emp_id)
#            if tipo_id:
#                modelos_qs = modelos_qs.filter(id_tipo_activo_id=tipo_id)
#
#            # Campo como ModelChoiceField
#            # ... después de construir `qs` y setear `choices` ...
#            self.fields["nombre_activo"].required = True
#
#            # Precarga en edición (si hay un valor ya guardado en texto)
#            if not self.data and self.instance and getattr(self.instance, "id_activo", None):
#                actual = (self.instance.nombre_activo or "").strip()
#                if actual:
#                    match = (modelos_qs.filter(nombre_modelo__iexact=actual)
#                            .values_list("nombre_modelo", flat=True)
#                            .first())
#                    if match:
#                        self.initial["nombre_activo"] = match
#                    else:
#                        self.fields["nombre_activo"].help_text = (
#                            f'Valor actual guardado: “{actual}”. Selecciona el modelo equivalente.'
#                        )
#
#            # Precargar valor actual al EDITAR (el modelo se guarda como TEXTO en Activo)
#            if not self.data and self.instance and getattr(self.instance, "id_activo", None):
#                actual = (self.instance.nombre_activo or "").strip()
#                if actual:
#                    # sé tolerante a mayúsculas/acentos/espacios
#                    match = (modelos_qs
#                            .filter(nombre_modelo__iexact=actual)
#                            .first())
#                    if match:
#                        self.initial["nombre_activo"] = match.pk
#                        # Si no viene marca inicial, y el modelo tiene, precárgala
#                        if "id_marca" in self.fields and not self.initial.get("id_marca"):
#                            if getattr(match, "id_marca_id", None):
#                                self.initial["id_marca"] = match.id_marca_id
#                    else:
#                        self.fields["nombre_activo"].help_text = (
#                            f'Valor actual guardado: “{actual}”. Selecciona el modelo equivalente.'
#                        )

        # Oculta métricas de seguridad si no es crítico
        if not getattr(self.instance, "activo_critico", False):
            for n in ("confidencialidad", "integridad", "disponibilidad"):
                self.fields[n].widget.attrs["style"] = "display:none"
        else:
            self.fields["clasificacion"].widget.attrs["class"] = "form-select"

        # Precarga de atributos dinámicos (si editas)
        try:
            if self.instance and getattr(self.instance, "id_activo", None):
                from .models_inventario import AgregacionAtributosPorActivo as AAPA
                pares = AAPA.objects.filter(activo_id=self.instance.id_activo).values_list("atributo_id", "valor")
                for aid, val in pares:
                    self.initial[f"attr_{aid}"] = val
        except Exception:
            pass




    def clean_nombre_activo(self):
        """
        Normaliza lo que venga del select:
        - Si viene una instancia de Modelo -> guarda su nombre.
        - Si viene un número (id) -> busca el nombre y lo guarda.
        - Si viene texto -> guarda el texto.
        - En edición, si viene vacío, conserva el valor que ya tenía.
        """
        try:
            from .models_inventario import Modelo as _Modelo
        except Exception:
            _Modelo = Modelo

        v = self.cleaned_data.get("nombre_activo")

        # 1) Instancia de Modelo
        if isinstance(v, _Modelo):
            return v.nombre_modelo

        # 2) String / valor posteado
        s = (str(v).strip() if v is not None else "")

        # 2.a) Vacío: en edición conserva, en creación queda vacío
        if not s:
            if self.instance and getattr(self.instance, "id_activo", None):
                return self.instance.nombre_activo or ""
            return ""

        # 2.b) Si es id numérico -> mapear a nombre
        if s.isdigit():
            m = _Modelo.objects.filter(pk=int(s)).only("nombre_modelo").first()
            return m.nombre_modelo if m else s  # fallback seguro

        # 2.c) Texto ya es el nombre del modelo
        return s


    def clean_numero_serie(self):
        return (self.cleaned_data.get("numero_serie") or "").strip()

    def clean(self):
        cleaned = super().clean()
        ub = cleaned.get("id_ubicacion")
        if ub is not None and getattr(ub, "eliminado", False):
            self.add_error("id_ubicacion", "Esta ubicación está eliminada. Selecciona otra.")
        if cleaned.get("activo_critico"):
            if not (cleaned.get("confidencialidad") and cleaned.get("integridad") and cleaned.get("disponibilidad")):
                self.add_error("clasificacion", "Si el activo es crítico, completa Confidencialidad/Integridad/Disponibilidad.")
                raise ValidationError("Campos de criticidad incompletos.")

        # === AQUÍ CAMBIAMOS LA LÓGICA ===
        empleado = cleaned.get("id_empleado")
        emp = cleaned.get("id_empresa")
        dep = cleaned.get("id_departamento")

       # 1) Si NO hay responsable -> exigir solo Empresa (Departamento opcional)
        if empleado is None and emp is None:
            raise ValidationError("Si no asignas responsable, debes al menos seleccionar la Empresa.")
        
        
        if empleado is not None and emp is not None:
            if getattr(empleado, "id_empresa_id", None) != getattr(emp, "id_empresa", emp):
                raise ValidationError("El responsable seleccionado no pertenece a la empresa elegida.")
        return cleaned

    def save(self, commit=True):
################################ 29/11 ##########################################
        # Saber si es creación (instancia sin PK antes de guardar)
        es_creacion = self.instance.pk is None
################################ 29/11 ##########################################

        # 1) Sincronizar condición maestro/detalle ANTES de guardar
        detalle = self.cleaned_data.get("id_condicion_detalle")

        if detalle is not None:
            # Lo que ve el usuario
            self.instance.id_condicion_detalle = detalle
            # Compatibilidad con la tabla maestra (FK en CondicionDetalle → CondicionActivo)
            # Ojo: el campo en CondicionDetalle se llama `condicion_activo`
            self.instance.id_condicion_activo = detalle.condicion_activo
        else:
            # Si no eligieron nada, dejamos ambos en None
            self.instance.id_condicion_detalle = None
            self.instance.id_condicion_activo = None
################################ 29/11 ##########################################
        # 👇 NUEVO: normalizar cantidad
        raw_cantidad = self.cleaned_data.get("cantidad") or 1
        try:
            cantidad = int(raw_cantidad)
        except (TypeError, ValueError):
            cantidad = 1
        if cantidad < 1:
            cantidad = 1

        # Helper interno para generar etiquetas únicas para los clones
        ActivoModel = self._meta.model

        def generar_etiqueta_clone(base, indice):
            """
            Genera la etiqueta para el clon sumando 1 a la parte numérica final.

            Ejemplos:
              base='NBK00030', indice=2  -> NBK00031
              base='NBK00030', indice=3  -> NBK00032

            Si no hay números al final, devuelve la base tal cual.
            """

            if not base:
                return "SIN-ETIQ"

            base_s = base.strip()

            # Intentar separar prefijo (letras) + número (dígitos)
            m = re.match(r"^([A-Za-z]*)(\d+)$", base_s)
            if not m:
                # Si el formato no encaja (no termina en número), devolvemos la base
                # (aquí podrías poner otra lógica si quieres, pero no la complicamos)
                return base_s

            prefijo, num_str = m.groups()
            ancho = len(num_str)
            num_base = int(num_str)

            # índice 2 => +1 (siguiente número)
            # índice 3 => +2, etc.
            n = num_base + (indice - 1)

            # Aseguramos que la etiqueta no exista ya en la BD
            cand = f"{prefijo}{n:0{ancho}d}"
            while ActivoModel.objects.filter(etiqueta=cand).exists():
                n += 1
                cand = f"{prefijo}{n:0{ancho}d}"

            return cand
################################ 29/11 ##########################################


        # 2) Guardado normal + atributos dinámicos
        with transaction.atomic():
            activo = super().save(commit=commit)
################################ 29/11 ##########################################
            # ====== Atributos dinámicos para el activo principal ======
            saved_attr_vals = []  # 👈 guardamos para replicar en clones
################################ 29/11 ##########################################
            if commit and self.request:
                tipo_id = self.cleaned_data.get("id_tipo_activo")
                if tipo_id:
                    atributos = AtributosActivo.objects.filter(id_tipo_activo=tipo_id)
                    if self.request.session.get("empresa_id"):
                        atributos = atributos.filter(
                            id_tipo_activo__id_empresa_id=self.request.session.get("empresa_id")
                        )

                    existentes = {
                        aa.atributo_id: aa
                        for aa in AgregacionAtributosPorActivo.objects.filter(activo_id=activo.id_activo)
                    }

                    for attr in atributos:
                        key = f"attr_{attr.id_atributo_activo}"
                        valor = (self.request.POST.get(key) or "").strip()
################################ 29/11 ##########################################
                        # guardamos para clones
                        saved_attr_vals.append((attr.id_atributo_activo, valor))
################################ 29/11 ##########################################
                        fila = existentes.get(attr.id_atributo_activo)

                        if fila:
                            if (fila.valor or "") != valor:
                                fila.valor = valor or None
                                fila.save(update_fields=["valor"])
                        else:
                            if valor:
                                AgregacionAtributosPorActivo.objects.create(
                                    activo_id=activo.id_activo,
                                    atributo_id=attr.id_atributo_activo,
                                    valor=valor,
                                )
################################ 29/11 ##########################################
            # ====== Lógica de clones por lote ======
            # - Si no es creación -> NO clonar (solo se edita)
            # - Si commit=False -> no crear clones
            # - Si cantidad <= 1 -> nada que hacer
            if (not es_creacion) or (not commit) or cantidad <= 1:
                return activo

            # Desde aquí: creación de N activos (el principal + clones)
            base_etiqueta = activo.etiqueta

            for idx in range(2, cantidad + 1):
                # Clonamos el activo principal desde la BD
                original = ActivoModel.objects.get(pk=activo.pk)
                original.pk = None
                # Por si el PK es id_activo
                if hasattr(original, "id_activo"):
                    original.id_activo = None

                # Nueva etiqueta única
                original.etiqueta = generar_etiqueta_clone(base_etiqueta, idx)
                original.save()

                # Copiar atributos dinámicos al clon
                if commit and self.request and saved_attr_vals:
                    for atributo_id, valor in saved_attr_vals:
                        if valor:
                            AgregacionAtributosPorActivo.objects.create(
                                activo_id=original.id_activo,
                                atributo_id=atributo_id,
                                valor=valor,
                            )
################################ 29/11 ##########################################

        return activo


##############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><15/11
######################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>15/11
class ReglaCriticidadForm(forms.ModelForm):
    """Formulario para crear/editar reglas de criticidad por tipo de activo y cargo."""

    # Usamos ModelChoiceField para mostrar un <select> de cargos
    cargo_nombre = forms.ModelChoiceField(
        label="Cargo nombre",
        queryset=Cargo.objects.none(),  # se completa en __init__
        widget=forms.Select(attrs={"class": "form-select searchable"}),
        required=True,
        help_text="Seleccione un cargo; se guardará el nombre tal como aparece en Empleado.cargo.",
    )

    class Meta:
        model = ReglaCriticidad
        fields = [
            "id_empresa",
            "id_tipo_activo",
            "cargo_nombre",
            "confidencialidad",
            "integridad",
            "disponibilidad",
            "clasificacion",
        ]

        widgets = {
            "id_empresa": forms.Select(attrs={"class": "form-select searchable"}),
            "id_tipo_activo": forms.Select(attrs={"class": "form-select searchable"}),

            "confidencialidad": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 4, "step": 1}
            ),
            "integridad": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 4, "step": 1}
            ),
            "disponibilidad": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 4, "step": 1}
            ),
            "clasificacion": forms.Select(
                choices=[
                    ("confidencial", "Confidencial"),
                    ("uso_interno", "Uso Interno"),
                    ("publico", "Público"),
                ],
                attrs={"class": "form-select"},
            ),
        }

    def __init__(self, *args, **kwargs):
        """
        Permitimos pasar 'empresa' desde la vista para limitar los cargos al id_empresa.
        Si no viene, intentamos usar la empresa de la instancia (en edición).
        """
        empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        qs = Cargo.objects.filter(eliminado=False)

        # Si la vista pasó empresa, filtramos por ella
        if empresa is not None:
            qs = qs.filter(id_empresa=empresa)
        # Si estamos editando y la regla ya tiene empresa, usamos esa
        elif self.instance and self.instance.id_empresa_id:
            qs = qs.filter(id_empresa=self.instance.id_empresa)

        qs = qs.order_by("nombre_cargo")    
        
        self.fields["cargo_nombre"].queryset = qs.order_by("nombre_cargo")
        self.fields["cargo_nombre"].empty_label = "-- Seleccione un cargo --"


        # === NUEVO: repoblar el select al editar ==========================
        # Si estamos editando (instance con PK) y hay un cargo_nombre guardado,
        # buscamos el Cargo cuyo nombre coincida y lo ponemos como initial.
        if self.instance and self.instance.pk and self.instance.cargo_nombre:
            nombre_guardado = " ".join(
                (self.instance.cargo_nombre or "").split()
            )  # normalizamos igual que en clean

            cargo_inicial = qs.filter(
                nombre_cargo__iexact=nombre_guardado
            ).first()

            if cargo_inicial:
                # Esto hace que el <select> aparezca con el cargo correcto seleccionado
                self.initial["cargo_nombre"] = cargo_inicial
        # ==================================================================

    # Este clean transforma el Cargo seleccionado en un string *normalizado*
    # que es lo que espera el CharField `cargo_nombre` en el modelo.
    def clean_cargo_nombre(self):
        cargo_obj = self.cleaned_data["cargo_nombre"]  # es un objeto Cargo
        nombre = cargo_obj.nombre_cargo or ""

        # Normalizamos: quitamos espacios al principio/fin
        # y colapsamos espacios múltiples en uno solo.
        nombre_normalizado = " ".join(nombre.split())
        return nombre_normalizado

    def clean_confidencialidad(self):
        value = self.cleaned_data.get("confidencialidad")
        if value is not None and (value < 1 or value > 4):
            raise forms.ValidationError("El valor de Confidencialidad debe estar entre 1 y 4.")
        return value

    def clean_integridad(self):
        value = self.cleaned_data.get("integridad")
        if value is not None and (value < 1 or value > 4):
            raise forms.ValidationError("El valor de Integridad debe estar entre 1 y 4.")
        return value

    def clean_disponibilidad(self):
        value = self.cleaned_data.get("disponibilidad")
        if value is not None and (value < 1 or value > 4):
            raise forms.ValidationError("El valor de Disponibilidad debe estar entre 1 y 4.")
        return value
#################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>15/11
class PreparacionAsignacionForm(forms.ModelForm):
    # Sobrescribimos el CharField cargo_nombre con un ModelChoiceField
    cargo = forms.ModelChoiceField(
        label="Cargo",
        queryset=Cargo.objects.none(),  # se rellena en __init__
        widget=forms.Select(attrs={"class": "form-select searchable"}),
        required=True,
        help_text="Nombre del cargo tal como se usa en Empleado.cargo.",
    )

    class Meta:
        model = PreparacionAsignacion
        fields = [
            "id_empresa",
            "id_tipo_activo",
            "cargo",
            "nombre",
            "habilitada",
        ]
        widgets = {
            "id_empresa": forms.Select(attrs={"class": "form-select searchable"}),
            "id_tipo_activo": forms.Select(attrs={"class": "form-select searchable"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "habilitada": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        """
        Igual que en ReglaCriticidadForm:

        - Si la vista nos pasa `empresa`, filtramos cargos por esa empresa.
        - Si estamos editando y la preparación ya tiene empresa, usamos esa.
        """
        empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)

        qs = Cargo.objects.filter(eliminado=False)

        if empresa is not None:
            qs = qs.filter(id_empresa=empresa)
        elif self.instance and self.instance.id_empresa_id:
            qs = qs.filter(id_empresa=self.instance.id_empresa_id)

        self.fields["cargo"].queryset = qs.order_by("nombre_cargo")
        self.fields["cargo"].empty_label = "-- Seleccione un cargo --"

        qs = qs.order_by("nombre_cargo")    

        if self.instance and self.instance.pk and self.instance.cargo:
            nombre_guardado = " ".join((self.instance.cargo or "").split())
            cargo_inicial = qs.filter(nombre_cargo__iexact=nombre_guardado).first()
            if cargo_inicial:
                self.initial["cargo"] = cargo_inicial
      

    def clean_cargo_nombre(self):
        """
        Convertimos el Cargo seleccionado en el string normalizado
        que se guarda en el CharField `cargo_nombre` del modelo.
        """
        cargo_obj = self.cleaned_data["cargo"]
        nombre = cargo_obj.nombre_cargo or ""
        # normalizar espacios
        return " ".join(nombre.split())



##############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><15/11



class GenericDelete(EmpresaScopeMixin, ModelPermsMixin, DeleteView):
    """Delete genérico con **borrado lógico** si el modelo tiene `eliminado`.

    - Si existe `eliminado`: marca y guarda (forzando tipo de evento para auditoría).
    - Si no existe: hard delete normal (super().delete()).
    - Restringe `dispatch` a `empleado.rol == "admin"`.
    """
    template_name = "crud/delete.html"
    action_perm = "delete"
    crud_config: CrudConfig

    def get_queryset(self):
        # Respeta el scope por empresa
        return self.scope_queryset(self.model.objects.all())

    def get_success_url(self):
        return reverse_lazy(f"productos:{self.crud_config.slug}_list")

    # ⬇️ Clave: NO llamar a super().delete() si hay borrado lógico
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        if hasattr(self.object, "eliminado"):
            if not getattr(self.object, "eliminado", False):
                # esto hará que el signal registre ELIMINAR
                setattr(self.object, "_audit_force_tipo", "ELIMINAR")
                self.object.eliminado = True
#                self.object.save(update_fields=["eliminado"])

                # ============================
                # NUEVO: preparar update_fields ##################### 23/11 #################### 20:02
                # ============================
                update_fields = ["eliminado"]

                # Si el modelo es Activo, marcar condición "No Disponible [Eliminado]"
                if isinstance(self.object, Activo):
                    emp_id = request.session.get("empresa_id")

                    detalle_eliminado = (
                        CondicionDetalle.objects
                        .filter(
                            eliminado=False,
                            id_empresa_id=emp_id,
                            condicion_activo__descripcion__iexact="No Disponible",
                        )
                        # asumimos que la descripción contiene "eliminado",
                        # por ejemplo: "No Disponible [Eliminado]"
                        .filter(descripcion__icontains="eliminado")
                        .order_by("id_condicion_detalle")
                        .first()
                    )

                    if detalle_eliminado:
                        self.object.id_condicion_activo = detalle_eliminado.condicion_activo
                        self.object.id_condicion_detalle = detalle_eliminado
                        update_fields += ["id_condicion_activo", "id_condicion_detalle"]

                # Guardar solo los campos modificados
                self.object.save(update_fields=update_fields)

                # ============================
                # FIN BLOQUE NUEVO     ##################### 23/11 #################### 20:02
                # ============================



                dj_messages.success(request, "Registro eliminado.")
            else:
                dj_messages.info(request, "El registro ya estaba eliminado.")
            return HttpResponseRedirect(self.get_success_url())

        # Si el modelo no tiene 'eliminado' → hard delete normal
        return super().delete(request, *args, **kwargs)

    # Si tu botón confirma via POST al form → reutiliza delete()
    def form_valid(self, form):
        return self.delete(self.request, *self.args, **self.kwargs)

##################################### 04/12 ###################################################
    def dispatch(self, request, *args, **kwargs):
        # seguridad básica; evita AttributeError si no hay empleado
        emp = getattr(request.user, "empleado", None)
        if not emp:
            return HttpResponseForbidden("No tienes permisos para eliminar.")

        # ======================================================
        # Bloqueo específico: PlanMantencionActivo + rol USUARIO
        # ======================================================
        try:
            rol = rol_de_usuario(request.user)
        except Exception:
            rol = None

        if (
            self.model._meta.model_name == "planmantencionactivo"
            and rol == ROL_USUARIO
        ):
            return HttpResponseForbidden("No tienes permisos para eliminar este registro.")

        # Regla general actual: solo admin puede eliminar
        if getattr(emp, "rol", "") != "admin":
            return HttpResponseForbidden("No tienes permisos para eliminar.")

        return super().dispatch(request, *args, **kwargs)
##################################### 04/12 ###################################################


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["cfg"] = self.crud_config
        ctx["eliminado"] = True
        return ctx
    
from django.db import connection


from django.utils import timezone

def log_mantencion_event(request_user, mantencion_obj, accion: str, detalle: str = ""):
    """
    Guarda un evento en el historial de una mantención, incluyendo detalles del activo, tipo de mantención y responsable.
    
    Esta función crea un registro en el modelo `HistorialMantencionesLog` para rastrear eventos asociados a mantenciones, como cambios de estado y acciones realizadas.
    
    Args:
        request_user: El usuario que realiza la acción.
        mantencion_obj: El objeto de mantención sobre el que se realiza la acción.
        accion: La acción realizada (por ejemplo, "CREACIÓN", "ACTUALIZACIÓN").
        detalle: Detalles adicionales sobre la acción realizada (opcional).
    
    Returns:
        HistorialMantencionesLog: El registro creado en el historial de mantenciones.
    """
    from .models_inventario import HistorialMantencionesLog  # import local para evitar ciclos

    def visible_user_name(u):
        if not u:
            return ""
        try:
            full = (u.get_full_name() or "").strip()
        except Exception:
            full = ""
        if full:
            return full
        emp = getattr(u, "empleado", None)
        return str(emp) if emp else getattr(u, "username", "") or str(u)

    # --- Base ---
    activo = getattr(mantencion_obj, "id_activo", None)
    etiqueta = getattr(activo, "etiqueta", None)
    activo_nombre = getattr(activo, "nombre_activo", None) or (str(activo)[:150] if activo else None)

    # Strings "bonitos" de FKs (si existen)
    tipo_mantencion = str(getattr(mantencion_obj, "id_tipo_mantencion", "")) \
        if getattr(mantencion_obj, "id_tipo_mantencion_id", None) else None
    prioridad = str(getattr(mantencion_obj, "id_prioridad", "")) \
        if getattr(mantencion_obj, "id_prioridad_id", None) else None
    estado_actual = str(getattr(mantencion_obj, "id_estado_mantencion", "")) \
        if getattr(mantencion_obj, "id_estado_mantencion_id", None) else None

    # Responsable (puede no tener propiedad *_nombre)
    responsable = getattr(mantencion_obj, "responsable", None)
    responsable_nombre = (
        getattr(mantencion_obj, "responsable_nombre", None) or (str(responsable) if responsable else "")
    )

    # Solicitante (FK a auth.User). Si no hay propiedad *_nombre, lo calculamos.
    solicitante_user = getattr(mantencion_obj, "solicitante_user", None)
    solicitante_nombre = (
        getattr(mantencion_obj, "solicitante_nombre", None) or visible_user_name(solicitante_user)
    )

    obj = HistorialMantencionesLog.objects.create(
        id_mantencion=mantencion_obj.id_mantencion,
        fecha_evento=timezone.now(),
        accion=accion,
        detalle=detalle or "",
        usuario_app_username=visible_user_name(request_user),

        id_activo=getattr(activo, "id_activo", None),
        etiqueta=etiqueta,
        activo_nombre=activo_nombre,

        tipo_mantencion=tipo_mantencion,
        prioridad=prioridad,
        estado_actual=estado_actual,

        responsable_nombre=responsable_nombre,
        solicitante_nombre=solicitante_nombre,

        descripcion=getattr(mantencion_obj, "descripcion", "") or "",
        id_empresa_id=getattr(mantencion_obj, "id_empresa_id", None),
    )
    return obj

# --- Comentario para Registro (log) ---
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden
#from django.contrib import messages
from django.contrib import messages as dj_messages

@login_required
@require_POST
def registro_comentar(request, pk):
    """Actualiza el `comentario` de un `Registro`.

    Valida empresa activa si el modelo la posee.
    """
    from .models_inventario import Registro  # evita imports circulares
    emp_id = request.session.get("empresa_id")

    reg = get_object_or_404(Registro, pk=pk)

    # (opcional) restringe por empresa si tu modelo la tiene
    if hasattr(reg, "id_empresa_id") and emp_id and reg.id_empresa_id != emp_id:
        return HttpResponseForbidden("No permitido")

    comentario = (request.POST.get("comentario") or "").strip()
    reg.comentario = comentario or None
    reg.save(update_fields=["comentario"])
    dj_messages.success(request, "Comentario actualizado.")
    return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER") or "/")
# ---------- Export CSV ----------


# crud.py
import csv
from dataclasses import asdict
from datetime import date, datetime
from typing import Any, Iterable, List, Optional, Sequence, Type
from django.db.models import Model
from django.http import HttpResponse

# … (resto de imports que ya tienes)

def _get_attr(obj: Any, path: str, default: Any = "") -> Any:
    """Obtiene un atributo con soporte de 'ruta.con.puntos' y callables."""
    cur = obj
    for part in path.split("."):
        if cur is None:
            return default
        cur = getattr(cur, part, default)
        if callable(cur):
            try:
                cur = cur()
            except TypeError:
                # métodos que requieren args: ignoramos
                return default
    return default if cur is None else cur

def _format_value(v: Any, date_fmt: str = "%Y-%m-%d", dt_fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Normaliza valores a str bonita para CSV (bool, fechas, decimales, etc.)."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "Sí" if v else "No"
    if isinstance(v, (date, datetime)):
        if isinstance(v, datetime):
            return v.strftime(dt_fmt)
        return v.strftime(date_fmt)
    return str(v)

def _headers_for(model: Type[Model], fields: Sequence[str], override: Optional[Sequence[str]] = None) -> List[str]:
    """Construye encabezados: usa verbose_name cuando exista; permite override."""
    if override:
        return list(override)
    out = []
    for f in fields:
        verbose = None
        # si viene con punto, intenta el primer tramo como campo del modelo
        try:
            base = f.split(".")[0]
            field_obj = model._meta.get_field(base)
            verbose = getattr(field_obj, "verbose_name", None)
        except Exception:
            verbose = None
        if verbose:
            out.append(str(verbose).capitalize())
        else:
            out.append(f.replace("_", " ").capitalize())
    return out


def export_csv_view(model: Type[Model], cfg: "CrudConfig"):
    """
    Crea una vista que exporta la lista a CSV de forma **genérica** y amigable con Excel.

    Respeta: búsqueda (`q`), filtro avanzado (`f`/`fv`) y *scope* por empresa.
    Por defecto exporta `cfg.list_display` con encabezados derivados de `verbose_name`.

    Personalizaciones opcionales por modelo (si existen como atributos en `cfg`):
      - `csv_fields: list[str]`  → campos/paths a exportar (por defecto `list_display`)
      - `csv_headers: list[str]` → encabezados manuales (mismo largo que `csv_fields`)
      - `csv_filename: str`      → nombre base de archivo (por defecto `cfg.slug`)
      - `csv_delimiter: str`     → delimitador (por defecto `;`)
      - `csv_date_format: str`   → formato de fecha (por defecto `%Y-%m-%d`)
      - `csv_datetime_format: str`→ formato de datetime (por defecto `%Y-%m-%d %H:%M`)

    Returns:
        HttpResponse: attachment CSV.
    """
    # Defaults sensatos + overrides si están definidos en cfg
    fields: List[str] = list(getattr(cfg, "csv_fields", None) or cfg.list_display)
    headers: List[str] = _headers_for(model, fields, getattr(cfg, "csv_headers", None))
    filename: str = getattr(cfg, "csv_filename", None) or f"{cfg.slug}.csv"
    delimiter: str = getattr(cfg, "csv_delimiter", ";")
    date_fmt: str = getattr(cfg, "csv_date_format", "%Y-%m-%d")
    dt_fmt: str = getattr(cfg, "csv_datetime_format", "%Y-%m-%d %H:%M")

    def view(request):
        # Permiso ver
        if not request.user.has_perm(f"{model._meta.app_label}.view_{model._meta.model_name}"):
            return HttpResponse(status=403)

        rows = model.objects.all()

        # Scope empresa
        from .mixins import scope_qs_by_empresa
        rows = scope_qs_by_empresa(request, rows)

        # Búsqueda simple
        q = (request.GET.get("q") or "").strip()
        if q and cfg.search_fields:
            from django.db.models import Q
            cond = Q()
            for f in cfg.search_fields:
                cond |= Q(**{f"{f}__icontains": q})
            rows = rows.filter(cond)

        # Filtro avanzado (contrato f/fv)
        f = (request.GET.get("f") or "").strip()
        fv = (request.GET.get("fv") or "").strip()
        if f:
            rows = _apply_advanced_filter(rows, model, f, fv)

        # Respuesta CSV con BOM para Excel
        resp = HttpResponse(content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        resp.write("\ufeff")  # BOM

        writer = csv.writer(resp, delimiter=delimiter, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)

        # Si en list_display hay métodos/propiedades, también funcionan
        for obj in rows:
            row_out = []
            for field in fields:
                # get_FOO_display si corresponde
                value = None
                if "." not in field and hasattr(obj, f"get_{field}_display"):
                    try:
                        value = getattr(obj, f"get_{field}_display")()
                    except Exception:
                        value = None
                if value is None:
                    value = _get_attr(obj, field, "")
                row_out.append(_format_value(value, date_fmt, dt_fmt))
            writer.writerow(row_out)
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
############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>07/11
# --- STUBS PMA (colócalo ANTES de make_urlpatterns() / urlpatterns) ---
from django.http import JsonResponse

def pma_ejecucion_tareas_json(request, ejec_id):
    # Placeholder temporal. Devuelve estructura vacía para que no falle el import.
    return JsonResponse({"ok": True, "ejec_id": ejec_id, "tareas": []})
##################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>07/11

def make_urlpatterns(include: Sequence[Type[Model]] | None = None):
    """Genera URL patterns (CRUD + CSV) para los modelos dados o todos los de `productos`.

    - Ajusta permisos/acciones para modelos especiales (p. ej., `registro`).
    - Añade ruta `comentar` para `registro`.
    """
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

################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>07/11-20:26
        # ==================== MANEJO ESPECIAL LOG PMA ====================
        if m._meta.model_name == "mantencionejecucion":
            # 1) Usa un template PROPIO sin botones CRUD
            ListCls.template_name = "mantenciones/pma_historial_list.html"
            # 2) No registres create/update/delete para este modelo (solo listar y CSV)
            patterns += [
                path(f"{cfg.slug}/",              ListCls.as_view(), name=f"{cfg.slug}_list"),
                path(f"{cfg.slug}/exportar/csv/", csv_view,          name=f"{cfg.slug}_csv"),
                # Endpoint JSON del modal
                path(f"{cfg.slug}/<int:ejec_id>/tareas.json", pma_ejecucion_tareas_json, name="pma_ejec_tareas_json"),
            ]
            continue
        # ================================================================
################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>07/11-20:26


        # Añadir restricción para el modelo 'registro'
        if m._meta.model_name == "registro":  # Asegúrate de que el model_name es "registro"
            ListCls.action_perm = None  # Desactivar las acciones de editar y eliminar para Registro
            #UpdateCls.action_perm = None
            #DeleteCls.action_perm = None


        # 👉 Ruta especial para comentar Registros (slug es 'registros')
        if m._meta.model_name == "registro":
            from .crud import registro_comentar  # este archivo
            patterns.append(
                path(f"{cfg.slug}/<int:pk>/comentar/", registro_comentar, name=f"{cfg.slug}_comentar")
            )
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
    """
    Convierte los resultados de un cursor de base de datos en una lista de diccionarios.
    
    Cada diccionario contiene una fila de resultados, con las claves siendo los nombres de las columnas y los valores los datos de esa fila.
    
    Args:
        cursor: El cursor de la base de datos que contiene los resultados de la consulta.
    
    Returns:
        list: Una lista de diccionarios con los resultados de la consulta.
    """
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
    "condicionactivo": "condiciones_activo",  # 👈 NUEVO
    # 👇 NUEVOS
    "mantencionejecucion": "pma_historial",
    "mantencionejecuciontarea": "pma_tareas",

}

def make_slug(m: Type[Model]) -> str:
    base = m._meta.model_name
    if base in SLUG_ALIASES:
        return SLUG_ALIASES[base]
    return base if base.endswith("s") else f"{base}s"

CRUD_CONFIGS = _collect_unique_crud_configs()

# Ordenar Activos por ID descendente por defecto (lo nuevo arriba)
for _cfg in CRUD_CONFIGS:
    

    if _cfg.model._meta.model_name == "empleado":
        # Define exactamente las columnas que quieres (pueden ser > 9)
        _cfg.list_display = [
            _cfg.model._meta.pk.name,     # id_empleado
            "rut",
            "nombre",
            "apellido_paterno",
            "apellido_materno",
            "cargo",                       # usa el nombre real del campo en tu modelo
            "ubicacion",                   # 👈 tu FK nueva
            "id_departamento",             # si quieres mostrar el depto
            #"id_empresa",                  # si quieres mostrar la empresa
            "correo",
            "telefono",
            "estado_activo",
        ]

        # Orden por defecto (lo más nuevo arriba)
        _cfg.ordering = ("-id_empleado",)

    # 👉 Registros: mostrar lo más nuevo primero
    if _cfg.model._meta.model_name == "registro":
        field_names = {f.name for f in _cfg.model._meta.fields}
        if "fecha" in field_names:
            _cfg.ordering = ("-fecha", f"-{_cfg.model._meta.pk.name}")
        else:
            # Fallback por si no hubiera 'fecha'
            _cfg.ordering = (f"-{_cfg.model._meta.pk.name}",)

    if _cfg.model._meta.model_name == "activo":
        cols = list(_cfg.list_display)
        # Inserta estado_planes_badge en el lugar deseado (por ejemplo, después de "nombre_activo")
        if "estado_planes_badge" not in cols:
            cols.insert(2, "estado_planes_badge")  # o en el lugar que desees
        _cfg.list_display = cols
    
    if _cfg.model._meta.model_name == "planmantencionactivo":
        cols = list(_cfg.list_display)
        
        # Excluir la columna 'estado' si existe en el list_display
        if "estado" in cols:
            cols.remove("estado")
        # Asegúrate de que 'estado_planes_badge' esté en el lugar correcto
        if "estado_badge" not in cols:
            cols.insert(7, "estado_badge")
        _cfg.list_display = cols
        # ⬇⬇ NUEVO: mostrar primero los últimos que se crearon
        _cfg.ordering = ("-id_plan_mantencion_activo",)

        
    if _cfg.model._meta.model_name == "activo":
        cols = list(_cfg.get_list_display())
        # Inserta 'id_factura' después de 'id_proveedor' si existe
        try:
            i = cols.index("id_proveedor")
            if "id_factura" not in cols:
                cols.insert(i + 1, "id_factura")
        except ValueError:
            if "id_factura" not in cols:
                cols.append("id_factura")
        _cfg.list_display = cols


    # Activo: mostrar la columna "Condición" en la lista
    # Activo: mostrar la columna "Condición" usando id_condicion_detalle
    if _cfg.model._meta.model_name == "activo":
        cols = list(_cfg.list_display)

        # Si aún existe la antigua columna, la sacamos para no duplicar
        if "id_condicion_activo" in cols:
            cols.remove("id_condicion_activo")

        try:
            # La idea es mostrar la condición justo después del estado del activo
            i = cols.index("id_estado_activo")
            if "id_condicion_detalle" not in cols:
                cols.insert(i + 1, "id_condicion_detalle")
        except ValueError:
            # Si por algún motivo no está id_estado_activo, la agregamos al final
            if "id_condicion_detalle" not in cols:
                cols.append("id_condicion_detalle")

        _cfg.list_display = cols

    if _cfg.model._meta.model_name == "activo":
        cols = list(_cfg.list_display)
        if "estado_planes_badge" not in cols:
            cols.insert(2, "estado_planes_badge")  # ponla donde te acomode
        _cfg.list_display = cols


    if _cfg.model._meta.model_name == "activo":
        # Partimos de la versión YA modificada arriba
        cols = list(_cfg.list_display)

        # Dónde colocar 'id_ubicacion' (preferimos después de departamento; si no, estado; si no, empleado)
        anchor_order = ("id_departamento", "id_estado_activo", "id_empleado")
        insert_at = None
        for a in anchor_order:
            try:
                insert_at = cols.index(a)
                break
            except ValueError:
                continue

        if "id_ubicacion" not in cols:
            if insert_at is not None:
                cols.insert(insert_at + 1, "id_ubicacion")
            else:
                cols.append("id_ubicacion")

        _cfg.list_display = cols

        # (Opcional) permitir buscar por nombre de la ubicación
        extra_search = ["id_ubicacion__nombre_ubicacion"]
        _cfg.search_fields = list(dict.fromkeys(list(_cfg.search_fields) + extra_search))

##################################### 08/12 ############################################
    # NUEVO: usar la propiedad ubicacion_label en lugar de la FK cruda id_ubicacion
    if _cfg.model._meta.model_name == "activo":
        cols = list(_cfg.list_display)
        try:
            idx = cols.index("id_ubicacion")
        except ValueError:
            # Si por alguna razón no está la columna, no tocamos nada
            pass
        else:
            # Reemplazamos la columna por la propiedad del modelo
            cols[idx] = "ubicacion_label"
            _cfg.list_display = cols
##################################### 08/12 ############################################

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
    if _cfg.model._meta.model_name == "ubicacion":
        _cfg.ordering = ("-id_ubicacion",)
    if _cfg.model._meta.model_name == "cargo":
        _cfg.ordering = ("-id_cargo",)

        # === Historial de Activos: mostrar la FOTO del nombre, no la FK ===
    if _cfg.model._meta.model_name == "historialactivos":
        cols = list(_cfg.list_display)

        # Reemplaza la columna 'activo' por 'nombre_activo' (foto congelada)
        if "activo" in cols:
            i = cols.index("activo")
            cols[i] = "nombre_activo"
        else:
            # por si el infer no incluyó la foto, la metemos arriba
            if "nombre_activo" not in cols:
                cols.insert(1, "nombre_activo")

        # Asegura 'etiqueta' cerca de nombre (útil para identificar)
        if "etiqueta" not in cols:
            cols.insert(1, "etiqueta")

        _cfg.list_display = cols

        # Búsqueda por los campos denormalizados (foto)
        _cfg.search_fields = list(dict.fromkeys(
            ["etiqueta", "nombre_activo"] + list(_cfg.search_fields)
        ))

        # Ordena por lo más reciente primero
        _cfg.ordering = ("-fecha",)  # o ("-fecha", f"-{_cfg.model._meta.pk.name}")


        # 👇 AQUI define los campos buscables CORRECTOS
        _cfg.search_fields = [
            "folio",
            "observacion",
            "id_empresa__nombre_empresa",
            "id_proveedor__nombre_proveedor",
            "id_proveedor__rut_proveedor",   # <— este es el bueno
        ]
########################## 27/11 ###############################
########################## 27/11 ###############################
    if _cfg.model._meta.model_name == "proveedor":
        _cfg.ordering = ("-id_proveedor",)
    if _cfg.model._meta.model_name == "marca":
        _cfg.ordering = ("-id_marca",)
    if _cfg.model._meta.model_name == "empleado":
        _cfg.ordering = ("-id_empleado",)
#######Aca se pone para invertir el orden jejeje 
    if _cfg.model._meta.model_name == "mantencionejecucion":
        _cfg.ordering = ("-fecha_ejecucion",)
    ##########################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>12/11
    ##########################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>12/11
# productos/crud.py
from django.views.decorators.http import require_GET

@login_required
@require_GET
def api_marcas_por_tipo(request):
    emp_id  = request.session.get("empresa_id")
    tipo_id = request.GET.get("tipo_id")

    try:
        tipo_id = int(tipo_id)
    except (TypeError, ValueError):
        return JsonResponse({"items": []})

    # Modelos válidos por tipo (+empresa + no eliminados)
    m_qs = Modelo.objects.filter(id_tipo_activo_id=tipo_id)
    if _has_field(Modelo, "eliminado"):
        m_qs = m_qs.filter(eliminado=False)
    if emp_id:
        m_qs = m_qs.filter(id_empresa_id=emp_id)

    marca_ids = m_qs.values_list("id_marca_id", flat=True).distinct()

    # Traemos las marcas existentes (respeta empresa si aplica)
    qs = Marca.objects.filter(pk__in=marca_ids)
    if emp_id and _model_has_empresa_fk(Marca):
        qs = qs.filter(id_empresa_id=emp_id)
    if _has_field(Marca, "eliminado"):
        qs = qs.filter(eliminado=False)

    items = [{"value": m.pk, "label": m.nombre_marca} for m in qs.order_by("nombre_marca")]
    return JsonResponse({"items": items})

    ##########################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>12/11
    ##########################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>12/11


# cerca de tus otras vistas utilitarias/API:
@login_required
def api_modelos_por_tipo(request):
    emp_id  = request.session.get("empresa_id")
    tipo_id = request.GET.get("tipo_id")
    marca_id = request.GET.get("marca_id")


    # tipo_id debe ser int o devolvemos vacío
    try:
        tipo_id = int(tipo_id)
    except (TypeError, ValueError):
        return JsonResponse({"items": []})

    qs = (
        Modelo.objects
        .select_related("id_marca")                  # 👈 para traer la marca en la misma query
        .filter(id_tipo_activo_id=tipo_id)
    )
    
    if marca_id and str(marca_id).isdigit():
        qs = qs.filter(id_marca_id=int(marca_id))

    if emp_id:
        qs = qs.filter(id_empresa_id=emp_id)

    # Si tu modelo tiene borrado lógico
    if _has_field(Modelo, "eliminado"):
        qs = qs.filter(eliminado=False)

    items = []
    for m in qs.order_by("nombre_modelo"):
        items.append({
            "id": m.pk,  
            "value": m.pk,
            "label": m.nombre_modelo,
            "marca_id": m.id_marca_id,                                  # 👈 NUEVO
            "marca_nombre": m.id_marca.nombre_marca if m.id_marca else None,  # 👈 NUEVO
        })

    return JsonResponse({"items": items})

def get_crud_configs():
    return CRUD_CONFIGS


    #########################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# crud.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .utils import siguiente_etiqueta

@login_required
def api_siguiente_etiqueta(request):
    """
    Devuelve la siguiente etiqueta sugerida para un tipo de activo,
    filtrando por empresa en sesión.
    """
    tipo_id = request.GET.get("tipo_id")
    emp_id = request.session.get("empresa_id")

    qs = Activo.objects.all()

    if emp_id:
        qs = qs.filter(id_empresa_id=emp_id)

    if tipo_id:
        qs = qs.filter(id_tipo_activo_id=tipo_id)

    # Opcional: si usas borrado lógico
    if "eliminado" in [f.name for f in Activo._meta.fields]:
        qs = qs.filter(eliminado=False)

    qs = qs.exclude(etiqueta__isnull=True).exclude(etiqueta__exact="")

    last = qs.order_by("-etiqueta").first()

    # 1) Si no hay ninguna etiqueta previa, define tu valor inicial
    if not last:
        # 👉 CAMBIA ESTO por el formato que tú usas como primera etiqueta
        return JsonResponse({"next": "NBK00001"})

    etq = (last.etiqueta or "").strip()

    # 2) Intentar separar prefijo (letras) + número (dígitos)
    m = re.match(r"^([A-Za-z]*)(\d+)$", etq)
    if not m:
        # Si el formato no se reconoce, devolvemos la última tal cual
        return JsonResponse({"next": etq})

    prefijo, num_str = m.groups()
    siguiente_num = int(num_str) + 1
    siguiente = f"{prefijo}{siguiente_num:0{len(num_str)}d}"

    return JsonResponse({"next": siguiente})
    #############################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# ...
def _aplicar_plan_a_activos(request, plan, hacer_vigente: bool):
    """
    Aplica `plan` a los Activos de la empresa (filtrando por tipo y, si corresponde, por modelo).
    Si `hacer_vigente` es True, baja otros planes del activo, marca este como vigente,
    y recalcula/persiste la próxima mantención usando la lógica central del modelo.
    Devuelve (total_activos_filtrados, creados_o_activados, marcados_vigentes).
    """
    from .models_inventario import Activo, PlanMantencionActivo as PMA, Modelo

    def _save_fields_if_exist(obj, fields):
        # Guarda solo los campos que existan en el modelo (evita crashear por nombres distintos)
        cand = []
        for f in fields:
            try:
                obj.__class__._meta.get_field(f)
                cand.append(f)
            except Exception:
                pass
        if cand:
            obj.save(update_fields=tuple(dict.fromkeys(cand)))
        else:
            obj.save()

    emp_id = request.session.get("empresa_id")
    activos = Activo.objects.all()
    if emp_id:
        activos = activos.filter(id_empresa_id=emp_id)
    if _has_field(Activo, "eliminado"):
        activos = activos.filter(eliminado=False)

    # Tipo obligatorio
    tipo_id = getattr(plan, "id_tipo_activo_id", None)
    if not tipo_id:
        dj_messages.info(request, "El plan no tiene Tipo de activo; no se aplicó a ningún activo.")
        return (0, 0, 0)
    activos = activos.filter(id_tipo_activo_id=tipo_id)

    # ¿Restringe por modelo?
    aplica_todos = bool(
        getattr(plan, "aplica_a_todos_modelos",
            getattr(plan, "aplica_todos_modelos",
                getattr(plan, "aplica_todos", True)))
    )
    modelo_id = getattr(plan, "id_modelo_id", None)

    if not aplica_todos and modelo_id:
        m = Modelo.objects.filter(pk=modelo_id).only("nombre_modelo").first()
        activos = activos.filter(nombre_activo__iexact=m.nombre_modelo) if m else Activo.objects.none()
    elif not aplica_todos and not modelo_id:
        dj_messages.info(request, "Plan sin modelo y con 'aplica a todos' desmarcado: no se aplicó a ningún activo.")
        return (0, 0, 0)

    total = activos.count()
    creados_activados = 0
    marcados_vigente = 0

    # Heurística segura: si el plan es por tiempo y falta base_fecha, la inicializamos.
    es_tiempo = bool(getattr(getattr(plan, "tipo_medicion", None), "es_tiempo", False))

    from django.db import transaction
    from django.utils import timezone

    with transaction.atomic():
        for a in activos:
            pma, created = PMA.objects.get_or_create(
                id_activo=a,
                id_plan=plan,
                defaults={"eliminado": False}
            )
            # Reactivar si estaba eliminado
            if not created and getattr(pma, "eliminado", False):
                pma.eliminado = False
                created = True  # lo contamos como "activado"

            # Inicializar base_fecha solo si corresponde y no existe
            if es_tiempo and not getattr(pma, "base_fecha", None):
                # Usa fecha de inicio si existe, si no, hoy
                setattr(pma, "base_fecha", getattr(plan, "fecha_inicio", None) or timezone.now().date())

            # Manejo de vigente
            if hacer_vigente:
                (PMA.objects
                    .filter(id_activo=a, eliminado=False)
                    .exclude(pk=pma.pk)
                    .update(es_vigente=False))
                if not getattr(pma, "es_vigente", False):
                    pma.es_vigente = True
                    marcados_vigente += 1

            # Recalcular próxima mantención con la lógica del modelo (si existe)
            if hasattr(pma, "refrescar_estado_y_vencimiento"):
                try:
                    pma.refrescar_estado_y_vencimiento(persist=False)  # calcula en memoria
                except Exception:
                    # no abortar por un error de cálculo
                    pass

            # Persistir cambios (incluye posibles campos denormalizados)
            _save_fields_if_exist(pma, [
                "eliminado", "es_vigente", "base_fecha",
                "proximo_vencimiento_fecha", "proximo_vencimiento_valor", "estado",
                # agrega aquí otros campos que tu método setee, si aplica
            ])

            if created:
                creados_activados += 1

    return (total, creados_activados, marcados_vigente)

#################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>07/11-20:23
#################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>07/11-20:23
#################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>07/11-20:23
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404

@login_required
@require_GET
def pma_ejecucion_tareas_json(request, ejec_id: int):
    """
    Devuelve las tareas asociadas a una ejecución (log) de mantención.
    """
    from .models_inventario import MantencionEjecucion, MantencionEjecucionTarea
    emp_id = request.session.get("empresa_id")

    ejec = (MantencionEjecucion.objects
            .select_related("id_activo")
            .filter(pk=ejec_id)
            .first())
    if not ejec:
        raise Http404("Ejecución no encontrada.")
    # Restringe por empresa a través del activo
    if emp_id and getattr(ejec.id_activo, "id_empresa_id", None) != emp_id:
        raise Http404("No permitido para la empresa actual.")

    rows = (MantencionEjecucionTarea.objects
            .filter(ejecucion_id=ejec_id)
            .order_by("id_tarea_plan_id")
            .values("id_tarea_plan_id", "descripcion", "obligatorio", "marcada", "observacion"))
    return JsonResponse({"items": list(rows)})

