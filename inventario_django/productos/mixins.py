# productos/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect  # <----- AÑADIR
from django.urls import resolve, reverse  # <----- AÑADIR
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import FieldDoesNotExist
from django.db.models import ForeignKey, OneToOneField


class ModelPermsMixin(LoginRequiredMixin):
    """
    Exige login y, si la vista define action_perm = ('view'|'add'|'change'|'delete'),
    valida el permiso <app_label>.<action_perm>_<model_name>.
    """
    action_perm: str | None = None  # 'view' | 'add' | 'change' | 'delete'

    def dispatch(self, request, *args, **kwargs):
        if self.action_perm:
            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            codename = f"{self.action_perm}_{model_name}"
            if not request.user.has_perm(f"{app_label}.{codename}"):
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class CompanyRequiredMixin(LoginRequiredMixin):
    """
    Exige que haya empresa en sesión; si no, redirige al selector.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("empresa_id"):
            return redirect("productos:company_select")
        return super().dispatch(request, *args, **kwargs)

def scope_qs_by_empresa(request, qs):
    emp_id = request.session.get("empresa_id")
    if not emp_id:
        return qs
    model = qs.model
    # No filtrar Empresa
    if model._meta.model_name == "empresa":
        return qs

    # 1) id_empresa directo (FK o entero)
    try:
        f = model._meta.get_field("id_empresa")
        if isinstance(f, (ForeignKey, OneToOneField)):
            return qs.filter(id_empresa_id=emp_id)
        else:
            return qs.filter(id_empresa=emp_id)
    except Exception:
        pass

    # 2) Derivar por relaciones comunes
    for rel in ("id_equipo", "equipo", "id_empleado", "empleado"):
        try:
            model._meta.get_field(rel)
            return qs.filter(**{f"{rel}__id_empresa": emp_id})
        except Exception:
            continue

    return qs


class EmpresaScopeMixin(LoginRequiredMixin):
    def scope_queryset(self, qs):
        return scope_qs_by_empresa(self.request, qs)

    def scope_queryset(self, qs):
        emp_id = getattr(self.request, "session", {}).get("empresa_id")
        if not emp_id:
            return qs

        model = qs.model
        names = {f.name for f in model._meta.get_fields()}

        # caso 1: el modelo tiene la FK directa a empresa
        if "id_empresa" in names:
            return qs.filter(id_empresa_id=emp_id)
        if "empresa" in names:
            return qs.filter(empresa_id=emp_id)

        # caso 2: el modelo cuelga de Equipo (como Mantencion)
        if "id_equipo" in names:
            return qs.filter(id_equipo__id_empresa_id=emp_id)
        if "equipo" in names:
            return qs.filter(equipo__id_empresa_id=emp_id)

        # (opcionales) otros caminos habituales:
        if "id_empleado" in names:
            return qs.filter(id_empleado__id_empresa_id=emp_id)
        if "empleado" in names:
            return qs.filter(empleado__id_empresa_id=emp_id)

        return qs

# Si usas también el helper en export CSV, déjalo consistente:
def scope_qs_by_empresa(request, qs):
    """
    Limita un queryset a la empresa activa en sesión.
    Soporta:
      - Modelos con id_empresa FK -> usa id_empresa_id
      - Modelos con id_empresa PK/Integer -> usa id_empresa
      - Modelos con empresa FK -> usa empresa_id
      - Modelos que cuelgan de equipo -> usa id_equipo__id_empresa
    Si no hay empresa en sesión, retorna qs sin tocar.
    """
    emp_id = request.session.get("empresa_id")
    if not emp_id:
        return qs

    m = qs.model
    fields = {f.name: f for f in m._meta.get_fields() if hasattr(f, "name")}

    if "id_empresa" in fields:
        f = fields["id_empresa"]
        # Si es relación (FK a Empresa)
        if getattr(f, "is_relation", False):
            return qs.filter(id_empresa_id=emp_id)
        # Si es PK/Integer, no relación
        return qs.filter(id_empresa=emp_id)

    if "empresa" in fields:
        return qs.filter(empresa_id=emp_id)

    if "id_equipo" in fields:
        return qs.filter(id_equipo__id_empresa=emp_id)

    # Sin forma clara de scoping -> no tocar
    return qs

class EmpresaScopeMixin(LoginRequiredMixin):
    def scope_queryset(self, qs):
        return scope_qs_by_empresa(self.request, qs)

class SaveEmpresaMixin(LoginRequiredMixin):
    def form_valid(self, form):
        emp_id = self.request.session.get("empresa_id")
        if emp_id:
            inst = form.instance
            try:
                f = inst._meta.get_field("id_empresa")
            except FieldDoesNotExist:
                f = None
            if f is not None:
                if getattr(f, "is_relation", False):
                    if getattr(inst, "id_empresa_id", None) in (None, ""):
                        inst.id_empresa_id = emp_id
                else:
                    if getattr(inst, "id_empresa", None) in (None, ""):
                        inst.id_empresa = emp_id
        return super().form_valid(form)

# productos/mixins.py
def scope_qs_by_empresa(request, qs):
    """
    Aplica el filtro por empresa actual a un queryset, para usar también en views
    que no son CBV (por ejemplo, en exportadores CSV).
    """
    emp_id = request.session.get("empresa_id")
    if not emp_id:
        return qs

    model = qs.model
 # No filtrar la tabla Empresa (se debe ver completa)
    if model._meta.model_name == "empresa":
        return qs

    # 1) Campo directo id_empresa (FK o entero)
    try:
        f = model._meta.get_field("id_empresa")
        # Si es relación (FK/OneToOne), usa *_id; si no, igualdad directa
        if isinstance(f, (ForeignKey, OneToOneField)):
            return qs.filter(id_empresa_id=emp_id)
        else:
            return qs.filter(id_empresa=emp_id)
    except Exception:
        pass

    # 2) Derivar por relaciones comunes: equipo / empleado
    for rel in ("id_equipo", "equipo", "id_empleado", "empleado"):
        try:
            model._meta.get_field(rel)
            return qs.filter(**{f"{rel}__id_empresa": emp_id})
        except Exception:
            continue

    # 3) Si no encontramos cómo, devolvemos sin filtrar
    return qs

class EmpresaScopeMixin(LoginRequiredMixin):
    """
    Mixin que aplica scope por empresa a listados en general.
    """
    def scope_queryset(self, qs):
        return scope_qs_by_empresa(self.request, qs)