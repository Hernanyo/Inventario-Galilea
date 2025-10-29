# productos/crud.py
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
from .models_inventario import Modelo
from django.db.models import Max
from .models import HistorialMantencionesLog
from django.utils.dateparse import parse_date
import json
from django.contrib import messages
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
    
#################################################################################################################
#################################################################################################################    
    def get_list_display(self):
        """Columnas de lista filtradas.

        Oculta el flag `eliminado` para no mostrarlo en la tabla.
        """
        # Excluye 'eliminado' de la lista de columnas a mostrar
        return [field for field in self.list_display if field != "eliminado"]
#################################################################################################################
#################################################################################################################

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
        "nombre_activo": "Nombre Activo",
        "id_tipo_activo": "Id Tipo Activo",
        "id_estado_activo": "Id Estado Activo",
        "id_marca": "Id Marca",
        "id_proveedor": "Id Proveedor",
        "id_factura": "Factura (folio)",   # 👈 NUEVO
        "id_empleado": "Responsable",
        "observaciones": "Observaciones",
        "etiqueta": "Etiqueta",
        "id_condicion_activo": "Condición",   # 👈 NUEVO
    }
    out = []
    for col in list_display:
        kind = _field_kind(model, col)
        if not kind:
            continue
        label = label_overrides.get(col) or col.replace("_", " ").title()
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
######################################################################################################################################
######################################################################################################################################
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

######################################################################################################################################
######################################################################################################################################
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

#111111111111111111111111111##########################################################################################################
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
        #return self.scope_queryset(qs)
        return qs
##2222222222222222222222222222222#########################################################################################################

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

        # ⬇️ No permitir crear manualmente registros de auditoría
        if self.model._meta.model_name == "registro":
            can_create = False

        # disponibles tanto en cfg como en el contexto
        self.crud_config.can_create = can_create
        self.crud_config.can_change = can_change
        self.crud_config.can_delete = can_delete
        ctx["can_create"] = can_create
        ctx["can_change"] = can_change
        ctx["can_delete"] = can_delete

        ###########################################################################################################
        ## === NUEVO: datos del filtro avanzado (no rompe si no se usa) ===
        #adv_fields = _build_adv_fields_from_list_display(self.model, self.crud_config.list_display)
        #ctx["adv_fields"] = adv_fields
        #ctx["f"] = (self.request.GET.get("f") or "").strip()
        #ctx["fv"] = (self.request.GET.get("fv") or "").strip()
        # choices para FKs (en JSON para usar desde JS si quieres)
        #adv_choices = _adv_choices_for_fk_fields(self.request, self.model, adv_fields)
        #ctx["adv_choices_json"] = json.dumps(adv_choices, ensure_ascii=False)
        #
        #ctx["adv_fields_json"] = json.dumps(adv_fields, ensure_ascii=False)
        
        #############################################################################################################

        if self.model._meta.model_name == "atributosactivo":
            from .models_inventario import TipoActivo
            emp_id = self.request.session.get("empresa_id")
            te_qs = TipoActivo.objects.all()
            if emp_id:
                te_qs = te_qs.filter(id_empresa_id=emp_id)
            ctx["tipos_activo"] = te_qs.order_by("tipo_activo")
        return ctx


class GenericCreate(ExcludeEliminadoFormMixin, SaveEmpresaMixin, EmpresaScopeMixin, ModelPermsMixin, CreateView):
    """Create genérico con formularios automáticos y **soporte de archivos**.

    - Filtra combos por empresa activa.
    - Para modelos especiales (`Activo`, `Mantencion`, etc.) usa formularios
      específicos; si no, usa `_build_default_form`.
    - Al crear `Activo`, registra historial de forma segura.
    """
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
        if self.model.__name__ == "Marca":                    # 👈 NUEVO
            from productos.forms import MarcaForm
            return MarcaForm
        if self.model.__name__ == "Ubicacion":
            from productos.forms import UbicacionForm
            return UbicacionForm
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

        # dentro de GenericCreate.get_form(...) después de construir form
        if self.model.__name__ == "PlanMantencion":
            form.fields["hacer_vigente"] = forms.BooleanField(
                required=False,
                initial=False,
                label="Marcar como plan vigente en los activos afectados"
            )
            # Si no, lo dejamos tal cual
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
#1#############################################################################################24-09-2025
                # Filtrar los tipos de activo por la empresa activa
        if self.model.__name__ == "Activo":
            from .models_inventario import TipoActivo
            qs = TipoActivo.objects.all()
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)  # Aquí se filtra por empresa activa
            ctx["tipos_activo"] = qs.order_by("tipo_activo")
#2#############################################################################################24-09-2025

    ##############################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
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
    #######################################################################################################29/10
        # ===== PlanMantencion: aplicar a Activos y manejar "vigente" (solo con los campos del plan) =====
        if self.model.__name__ == "PlanMantencion":
            plan = self.object
            hacer_vigente = bool(form.cleaned_data.get("hacer_vigente", False))

            from django.db import transaction
            from .models_inventario import Activo, PlanMantencionActivo as PMA, Modelo

            emp_id = self.request.session.get("empresa_id")
            activos = Activo.objects.all()
            if emp_id:
                activos = activos.filter(id_empresa_id=emp_id)
            if _has_field(Activo, "eliminado"):
                activos = activos.filter(eliminado=False)

            # --- filtrar por tipo del plan (obligatorio en tu UI)
            tipo_id = getattr(plan, "id_tipo_activo_id", None)
            if tipo_id:
                activos = activos.filter(id_tipo_activo_id=tipo_id)
            else:
                # si por alguna razón no hay tipo, no aplicamos
                messages.info(self.request, "El plan no tiene Tipo de activo; no se aplicó a ningún activo.")
                return resp

            # --- filtrar por modelo del plan cuando corresponda
            #    (si el plan tiene id_modelo -> restringe a ese nombre; si no, respeta 'aplica a todos')
            modelo_id = getattr(plan, "id_modelo_id", None)
            aplica_todos = bool(
                getattr(plan, "aplica_todos_modelos",  # nombre más probable
                    getattr(plan, "aplica_a_todos_modelos",
                        getattr(plan, "aplica_todos", True)))
            )

            if modelo_id:
                m = Modelo.objects.filter(pk=modelo_id).only("nombre_modelo").first()
                if m:
                    activos = activos.filter(nombre_activo__iexact=m.nombre_modelo)
                else:
                    activos = Activo.objects.none()
            elif not aplica_todos:
                # Si explícitamente NO aplica a todos y no se eligió modelo, no tocamos nada.
                messages.info(self.request, "Plan creado sin modelo y con 'aplica a todos' desmarcado: no se aplicó a activos.")
                return resp

            creados = 0
            marcados = 0
            total = activos.count()

            with transaction.atomic():
                for a in activos:
                    pma, created = PMA.objects.get_or_create(
                        id_activo=a,
                        id_plan=plan,
                        defaults={"eliminado": False}
                    )
                    if created:
                        creados += 1
                    else:
                        # reactivar si estaba eliminado
                        if getattr(pma, "eliminado", False):
                            pma.eliminado = False

                    if hacer_vigente:
                        (PMA.objects
                            .filter(id_activo=a, eliminado=False)
                            .exclude(pk=pma.pk)
                            .update(es_vigente=False))
                        if not getattr(pma, "es_vigente", False):
                            pma.es_vigente = True
                            marcados += 1

                    pma.save()

            # mensaje específico del plan
            msg = f"Plan aplicado a {total} activo(s). Creados/activados {creados}."
            if hacer_vigente:
                msg += f" {marcados} marcado(s) como vigente."
            messages.success(self.request, msg)
        else:
            # mensaje genérico solo para el resto de modelos
            messages.success(self.request, "Guardado correctamente.")
        #######################################################################################################29/10


        if self.model.__name__ == "Empleado" and form.instance.correo:
            crear_usuario_y_enviar_correo(form.instance)

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

        messages.success(self.request, "Guardado correctamente.")
        return resp

###################################################################################2509
#        # >>> NUEVO: historial “a la segura” al CREAR activo desde CRUD
#        if self.model.__name__ == "Activo":
#            try:
#                from .models_inventario import HistorialActivos
#                e = self.object
#                usuario_empleado = getattr(self.request.user, "empleado", None)
#                HistorialActivos.objects.create(
#                    activo=e,
#                    etiqueta=e.etiqueta,
#                    nombre_activo=e.nombre_activo,
#                    modelo=None,  # si no usas modelo en Activo
#                    tipo_activo=getattr(e, "id_tipo_activo", None),
#                    accion="CREACION",
#                    usuario=usuario_empleado,
#                    id_empresa=getattr(e, "id_empresa", None),
#                    departamento=getattr(e, "id_departamento", None),
#                    estado_nuevo=getattr(e, "id_estado_activo", None),
#                    responsable_actual=getattr(e, "id_empleado", None),
#                    comentario="Creado desde CRUD",
#                )
#            except Exception:
#                # nunca romper el guardado por el historial
#                pass
#        messages.success(self.request, "Guardado correctamente.")
#        return resp
###################################################################################2509

class GenericUpdate(ExcludeEliminadoFormMixin, SaveEmpresaMixin, EmpresaScopeMixin, ModelPermsMixin, UpdateView):
    """Update genérico con soporte de archivos y lógica de negocio.

    - Filtra combos por empresa activa.
    - Sincroniza atributos dinámicos de `Activo` según `TipoActivo`.
    - En `Empleado`, alinea correo en `auth_user` y puede crear usuario si aplica.
    """
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
        if self.model.__name__ == "Marca":                    # 👈 NUEVO
            from productos.forms import MarcaForm
            return MarcaForm
        if self.model.__name__ == "Ubicacion":
            from productos.forms import UbicacionForm
            return UbicacionForm
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
                
        if self.model.__name__ == "PlanMantencion":
            form.fields["hacer_vigente"] = forms.BooleanField(
                required=False,
                initial=False,
                label="Marcar como plan vigente en los activos afectados"
            )
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
        messages.success(self.request, "Cambios guardados correctamente.")
        return resp



    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        ctx["cfg"] = self.crud_config

        emp_id = self.request.session.get("empresa_id")
        
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
    class Meta:
        model = Activo
        fields = [
            "id_tipo_activo",
            "nombre_activo",
            "id_marca",
            "id_estado_activo",
            "id_ubicacion",
            "id_condicion_activo",
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
            "id_condicion_activo": forms.Select(attrs={"class": "form-select searchable"}),
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

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        emp_id = request.session.get("empresa_id") if request else None

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
            qs = Empleado.objects.filter(estado_activo=True)
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)
            self.fields["id_empleado"].queryset = qs.order_by("nombre", "apellido_paterno")

        if "id_factura" in self.fields:
            from .models_inventario import Factura
            fqs = Factura.objects.all()
            if emp_id:
                fqs = fqs.filter(id_empresa_id=emp_id)
            self.fields["id_factura"].queryset = fqs.order_by("-fecha_emision", "folio")
            self.fields["id_factura"].label = "Factura (folio)"
            self.fields["id_factura"].help_text = "Opcional. Selecciona por folio; puedes dejarlo en blanco."

        if "id_condicion_activo" in self.fields:
            from .models_inventario import CondicionActivo
            cqs = CondicionActivo.objects.all()
            if emp_id:
                cqs = cqs.filter(id_empresa_id=emp_id)
            self.fields["id_condicion_activo"].queryset = cqs.order_by("descripcion")

        if "id_departamento" in self.fields:
            dqs = Departamento.objects.all()
            if emp_id:
                dqs = dqs.filter(id_empresa_id=emp_id)
            self.fields["id_departamento"].queryset = dqs.order_by("nombre_departamento")

        if "id_ubicacion" in self.fields:
            from .models_inventario import Ubicacion
            base = Ubicacion.objects.all()
            if emp_id:
                base = base.filter(id_empresa_id=emp_id)

            # 1) Drop-down normal: SOLO no eliminadas
            qs_ok = base.filter(eliminado=False).order_by("nombre_ubicacion")
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

        if "id_marca" in self.fields:
            from .models_inventario import Marca
            mqs = Marca.objects.all()
            if emp_id:
                mqs = mqs.filter(id_empresa_id=emp_id)
            self.fields["id_marca"].queryset = mqs.order_by("nombre_marca")

        # ====== Campo "nombre_activo" como lista de Modelos (y precarga en edición) ======
        if "nombre_activo" in self.fields:
            # Detecta tipo actual: POST > initial > instancia
            # Detecta el tipo seleccionado (POST, initial o instancia)
            tipo_id = (
                self.data.get("id_tipo_activo")
                or self.initial.get("id_tipo_activo")
                or getattr(self.instance, "id_tipo_activo_id", None)
            )
            # Si vino instancia, normaliza a PK
            if hasattr(tipo_id, "pk"):
                tipo_id = tipo_id.pk

            modelos_qs = Modelo.objects.all()
            if emp_id:
                modelos_qs = modelos_qs.filter(id_empresa_id=emp_id)
            if tipo_id:
                modelos_qs = modelos_qs.filter(id_tipo_activo_id=tipo_id)

            # Campo como ModelChoiceField
            self.fields["nombre_activo"] = forms.ModelChoiceField(
                queryset=modelos_qs.order_by("nombre_modelo"),
                empty_label="Seleccione un modelo",
                required=False,
                widget=forms.Select(attrs={
                    "class": "form-select",
                    "disabled": "disabled" if not tipo_id else None,
                })
            )

            # Precargar valor actual al EDITAR (el modelo se guarda como TEXTO en Activo)
            if not self.data and self.instance and getattr(self.instance, "id_activo", None):
                actual = (self.instance.nombre_activo or "").strip()
                if actual:
                    # sé tolerante a mayúsculas/acentos/espacios
                    match = (modelos_qs
                            .filter(nombre_modelo__iexact=actual)
                            .first())
                    if match:
                        self.initial["nombre_activo"] = match.pk
                        # Si no viene marca inicial, y el modelo tiene, precárgala
                        if "id_marca" in self.fields and not self.initial.get("id_marca"):
                            if getattr(match, "id_marca_id", None):
                                self.initial["id_marca"] = match.id_marca_id
                    else:
                        self.fields["nombre_activo"].help_text = (
                            f'Valor actual guardado: “{actual}”. Selecciona el modelo equivalente.'
                        )

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

    def clean_numero_serie(self):
        return (self.cleaned_data.get("numero_serie") or "").strip()

    def clean_nombre_activo(self):
        v = self.cleaned_data.get("nombre_activo")
        try:
            from .models_inventario import Modelo as _Modelo
        except Exception:
            _Modelo = Modelo
        # Si eligió un Modelo → guardar su nombre en el CharField
        if isinstance(v, _Modelo):
            # (Opcional) también podrías forzar la marca aquí si quieres
            return v.nombre_modelo
        # Si viene vacío: en edición conserva; en creación queda vacío
        if v in (None, ""):
            if self.instance and getattr(self.instance, "id_activo", None):
                return self.instance.nombre_activo or ""
            return ""
        return v

    def clean(self):
        cleaned = super().clean()
        ub = cleaned.get("id_ubicacion")
        if ub is not None and getattr(ub, "eliminado", False):
            self.add_error("id_ubicacion", "Esta ubicación está eliminada. Selecciona otra.")
        if cleaned.get("activo_critico"):
            if not (cleaned.get("confidencialidad") and cleaned.get("integridad") and cleaned.get("disponibilidad")):
                self.add_error("clasificacion", "Si el activo es crítico, completa Confidencialidad/Integridad/Disponibilidad.")
                raise ValidationError("Campos de criticidad incompletos.")

        empleado = cleaned.get("id_empleado")
        emp = cleaned.get("id_empresa")
        dep = cleaned.get("id_departamento")
        if empleado is None and (emp is None or dep is None):
            raise ValidationError("Si no asignas responsable, debes seleccionar Empresa y Departamento.")
        if empleado is not None and emp is not None:
            if getattr(empleado, "id_empresa_id", None) != getattr(emp, "id_empresa", emp):
                raise ValidationError("El responsable seleccionado no pertenece a la empresa elegida.")
        return cleaned

    def save(self, commit=True):
        with transaction.atomic():
            activo = super().save(commit=commit)
            if commit and self.request:
                tipo_id = self.cleaned_data.get("id_tipo_activo")
                if tipo_id:
                    atributos = AtributosActivo.objects.filter(id_tipo_activo=tipo_id)
                    if self.request.session.get("empresa_id"):
                        atributos = atributos.filter(id_tipo_activo__id_empresa_id=self.request.session.get("empresa_id"))
                    existentes = {aa.atributo_id: aa
                                  for aa in AgregacionAtributosPorActivo.objects.filter(activo_id=activo.id_activo)}
                    for attr in atributos:
                        key = f"attr_{attr.id_atributo_activo}"
                        valor = (self.request.POST.get(key) or "").strip()
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
                                    valor=valor
                                )
        return activo



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
                self.object.save(update_fields=["eliminado"])
                messages.success(request, "Registro eliminado.")
            else:
                messages.info(request, "El registro ya estaba eliminado.")
            return HttpResponseRedirect(self.get_success_url())

        # Si el modelo no tiene 'eliminado' → hard delete normal
        return super().delete(request, *args, **kwargs)

    # Si tu botón confirma via POST al form → reutiliza delete()
    def form_valid(self, form):
        return self.delete(self.request, *self.args, **self.kwargs)

    def dispatch(self, request, *args, **kwargs):
        # seguridad básica; evita AttributeError si no hay empleado
        emp = getattr(request.user, "empleado", None)
        if not emp or getattr(emp, "rol", "") != "admin":
            return HttpResponseForbidden("No tienes permisos para eliminar.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        obj = ctx.get("object") or getattr(self, "object", None)
        ctx["object_label"] = self.crud_config.obj_label(obj) if obj else ""
        ctx["cfg"] = self.crud_config
        ctx["eliminado"] = True
        return ctx
    
from django.db import connection

#def log_mantencion_event(user, mantencion_obj, accion: str, detalle: str = ""):
#    """
#    Inserta una 'foto' del estado de la mantención en historial_mantenciones_log usando Django ORM.
#    """
#    # nombre visible: Full Name > nombre del Empleado vinculado > username
#    if getattr(user, "is_authenticated", False):
#        display_name = (user.get_full_name() or "").strip() or (str(getattr(user, "empleado", "")) or user.get_username())
#    else:
#        display_name = None
#    
#    # Obtener los datos de la mantención (activo, tipo, prioridad, etc.)
#    activo = mantencion_obj.id_activo
#    tipo_mantencion = mantencion_obj.id_tipo_mantencion.nombre if mantencion_obj.id_tipo_mantencion else None
#    prioridad = mantencion_obj.id_prioridad.nombre if mantencion_obj.id_prioridad else None
#    estado_actual = mantencion_obj.id_estado_mantencion.tipo if mantencion_obj.id_estado_mantencion else None#

    # Crear un nuevo registro en HistorialMantencionesLog usando Django ORM
#    historial_log = HistorialMantencionesLog.objects.create(
#        id_mantencion=mantencion_obj.id_mantencion,
#        fecha_evento=timezone.now(),  # Utiliza la hora actual
#        accion=accion,
#        detalle=detalle,
#        usuario_app_username=display_name,
#        id_activo=activo.id_activo if activo else None,
#        etiqueta=activo.etiqueta if activo else None,
#        activo_nombre=activo.nombre_activo if activo else None,
#        tipo_mantencion=tipo_mantencion,
#        prioridad=prioridad,
#        estado_actual=estado_actual,
#        responsable_nombre=mantencion_obj.responsable_nombre,  # Esto puede requerir más lógica
#        solicitante_nombre=mantencion_obj.solicitante_nombre,  # Lo mismo aquí
#        descripcion=mantencion_obj.descripcion,
#    )
    
#    return historial_log           03/10/2025
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
from django.contrib import messages

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
    messages.success(request, "Comentario actualizado.")
    return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER") or "/")

######################################################################################################################
##################################################################################################
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

############################################################################################################################
######################################################################################################################################

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

######################################################################################################################
######################################################################################################################
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

######################################################################################################################
######################################################################################################################
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
        # Inserta estado_planes_badge en el lugar deseado (por ejemplo, después de "nombre_activo")
        if "estado_planes_badge" not in cols:
            cols.insert(7, "estado_badge")  # o en el lugar que desees
        _cfg.list_display = cols
    
    if _cfg.model._meta.model_name == "planmantencionactivo":
        cols = list(_cfg.list_display)
        
        # Excluir la columna 'estado' si existe en el list_display
        if "estado" in cols:
            cols.remove("estado")

        # Asegúrate de que 'estado_planes_badge' esté en el lugar correcto
        if "estado_badge" not in cols:
            cols.append("estado_badge")

        _cfg.list_display = cols

        
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
    if _cfg.model._meta.model_name == "activo":
        cols = list(_cfg.list_display)
        try:
            i = cols.index("id_estado_activo")
            if "id_condicion_activo" not in cols:
                cols.insert(i + 1, "id_condicion_activo")
        except ValueError:
            if "id_condicion_activo" not in cols:
                cols.append("id_condicion_activo")
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

        # Si tienes 'responsable_anterior_fk' y prefieres mostrar el string legible:
        # (quítalo si tu modelo no lo tiene)
        # try:
        #     cols[cols.index("responsable_anterior_fk")] = "responsable_anterior"
        # except ValueError:
        #     pass

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



    if _cfg.model._meta.model_name == "detallefactura":
        _cfg.ordering = ("-id_detalle_factura",)
    if _cfg.model._meta.model_name == "proveedor":
        _cfg.ordering = ("-id_proveedor",)
    if _cfg.model._meta.model_name == "marca":
        _cfg.ordering = ("-id_marca",)
    if _cfg.model._meta.model_name == "empleado":
        _cfg.ordering = ("-id_empleado",)

# cerca de tus otras vistas utilitarias/API:
@login_required
def api_modelos_por_tipo(request):
    emp_id  = request.session.get("empresa_id")
    tipo_id = request.GET.get("tipo_id")

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

    if emp_id:
        qs = qs.filter(id_empresa_id=emp_id)

    # Si tu modelo tiene borrado lógico
    if _has_field(Modelo, "eliminado"):
        qs = qs.filter(eliminado=False)

    items = []
    for m in qs.order_by("nombre_modelo"):
        items.append({
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
    emp_id = request.session.get("empresa_id")
    tipo_id = request.GET.get("tipo_id")
    if not (emp_id and tipo_id):
        return JsonResponse({"next": None})

    try:
        tipo_id = int(tipo_id)
    except ValueError:
        return JsonResponse({"next": None})

    return JsonResponse({"next": siguiente_etiqueta(emp_id, tipo_id)})

    #############################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# ...

