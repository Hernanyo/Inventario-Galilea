# productos/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, FieldDoesNotExist
from django.shortcuts import redirect
from django.db.models import ForeignKey, OneToOneField

# ---------- Permisos / login ----------

class ModelPermsMixin(LoginRequiredMixin):
    """
    Exige login y, si la vista define action_perm = ('view'|'add'|'change'|'delete'),
    valida el permiso <app_label>.<action_perm>_<model_name>.
    """
    action_perm: str | None = None

    def dispatch(self, request, *args, **kwargs):
        if self.action_perm:
            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            codename = f"{self.action_perm}_{model_name}"
            if not request.user.has_perm(f"{app_label}.{codename}"):
                raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CompanyRequiredMixin(LoginRequiredMixin):
    """Exige que haya empresa en sesión; si no, redirige al selector."""
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("empresa_id"):
            return redirect("productos:company_select")
        return super().dispatch(request, *args, **kwargs)

# ---------- Scoping por empresa (ÚNICA versión) ----------

def scope_qs_by_empresa(request, qs):
    """
    Limita un queryset a la empresa activa en sesión.
    Soporta:
      - Modelos con id_empresa (FK o entero)
      - Modelos con empresa (FK)
      - Modelos que cuelgan de Equipo/Empleado vía relación (incluye reverse)
    """
    if qs is None:
        return qs
    emp_id = request.session.get("empresa_id")
    if not emp_id:
        return qs

    model = qs.model
    fields = {f.name: f for f in model._meta.get_fields() if hasattr(f, "name")}

    # 1) Campo directo id_empresa
    if "id_empresa" in fields:
        f = fields["id_empresa"]
        return qs.filter(id_empresa_id=emp_id) if getattr(f, "is_relation", False) else qs.filter(id_empresa=emp_id)

    # 2) Campo 'empresa' como FK
    if "empresa" in fields:
        return qs.filter(empresa_id=emp_id)

    # 3) Derivar por relaciones comunes (forward o reverse) -> usar DISTINCT
    for rel in ("id_equipo", "equipo", "id_empleado", "empleado"):
        if rel in fields:
            return qs.filter(**{f"{rel}__id_empresa": emp_id}).distinct()

    # 4) Si no hay forma clara, no tocar
    return qs


class EmpresaScopeMixin(LoginRequiredMixin):
    """Mixin para aplicar el scoping en CBVs."""
    def scope_queryset(self, qs):
        return scope_qs_by_empresa(self.request, qs)


class SaveEmpresaMixin(LoginRequiredMixin):
    """Autocompleta id_empresa al guardar si el modelo lo tiene y viene vacío."""
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
