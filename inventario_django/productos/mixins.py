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

# productos/mixins.py
from django.db.models import ForeignKey, OneToOneField

def scope_qs_by_empresa(request, qs):
    if qs is None:
        return qs
    emp_id = request.session.get("empresa_id")
    if not emp_id:
        return qs

    m = qs.model
    fields = {f.name: f for f in m._meta.get_fields() if hasattr(f, "name")}

    # 1) Campo directo id_empresa
    f = fields.get("id_empresa")
    if f:
        return qs.filter(id_empresa_id=emp_id) if getattr(f, "is_relation", False) else qs.filter(id_empresa=emp_id)

    # 2) FK llamada 'empresa'
    f = fields.get("empresa")
    if f and getattr(f, "is_relation", False):
        return qs.filter(empresa_id=emp_id)

    # 3) Solo si es RELACIÓN, no IntegerField
    for rel in ("equipo", "empleado", "departamento", "mantencion"):
        f = fields.get(rel) or fields.get(f"id_{rel}")
        if f and getattr(f, "is_relation", False):
            return qs.filter(**{f"{f.name}__id_empresa": emp_id}).distinct()

    return qs


class EmpresaScopeMixin(LoginRequiredMixin):
    """Mixin para aplicar el scoping en CBVs."""
    def scope_queryset(self, qs):
        return scope_qs_by_empresa(self.request, qs)


class SaveEmpresaMixin(LoginRequiredMixin):
    """Si el modelo tiene id_empresa y viene vacío, lo completa con la empresa de sesión."""
    def form_valid(self, form):
        emp_id = self.request.session.get("empresa_id")
        if emp_id:
            if hasattr(form.instance, "id_empresa_id") and not form.instance.id_empresa_id:
                form.instance.id_empresa_id = emp_id
            elif hasattr(form.instance, "id_empresa") and not getattr(form.instance, "id_empresa", None):
                form.instance.id_empresa = emp_id
        return super().form_valid(form)
