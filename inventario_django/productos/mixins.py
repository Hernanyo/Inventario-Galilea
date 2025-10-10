# productos/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied, FieldDoesNotExist
from django.shortcuts import redirect
from django.db.models import ForeignKey, OneToOneField


# ---------- Permisos / login ----------

class ModelPermsMixin(LoginRequiredMixin):
    """
    Exige que el usuario esté autenticado y que tenga los permisos necesarios 
    para realizar acciones sobre un modelo en particular. Los permisos son definidos
    con la propiedad `action_perm` que se mapea a un permiso `<app_label>.<action_perm>_<model_name>`.
    
    El valor de `action_perm` puede ser 'view', 'add', 'change', o 'delete'.
    """
    def dispatch(self, request, *args, **kwargs):
        # <-- si la vista marca action_perm=None, no pedimos permisos extra
        if self.action_perm is None:
            return super().dispatch(request, *args, **kwargs)

        app = self.model._meta.app_label
        model = self.model._meta.model_name
        perm_codename = f"{app}.{self.action_perm}_{model}"
        if not request.user.has_perm(perm_codename):
            return HttpResponseForbidden("403 Forbidden")
        return super().dispatch(request, *args, **kwargs)


class CompanyRequiredMixin(LoginRequiredMixin):
    """
    Exige que el usuario tenga una empresa seleccionada en la sesión.
    Si no se encuentra configurada, redirige al selector de empresa.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.session.get("empresa_id"):
            return redirect("productos:company_select")
        return super().dispatch(request, *args, **kwargs)

# ---------- Scoping por empresa (ÚNICA versión) ----------

# productos/mixins.py
from django.db.models import ForeignKey, OneToOneField

def scope_qs_by_empresa(request, qs):
    """
    Aplica un filtro de empresa a las consultas, asegurando que los resultados
    solo incluyan los objetos de la empresa activa en la sesión.
    
    :param request: La solicitud HTTP, que debe contener la empresa activa en la sesión.
    :param qs: La queryset a filtrar por `id_empresa`.
    :return: La queryset filtrada por empresa.
    """
    if qs is None:
        return qs
    emp_id = request.session.get("empresa_id")
    if not emp_id:
        return qs

    m = qs.model
    fields = {f.name: f for f in m._meta.get_fields() if hasattr(f, "name")}

    # 1) Campo directo id_empresa (entero o FK)
    f = fields.get("id_empresa")
    if f:
        # si es FK usamos id_empresa_id; si es entero, id_empresa
        return qs.filter(id_empresa_id=emp_id) if getattr(f, "is_relation", False) else qs.filter(id_empresa=emp_id)

    # 2) FK llamada 'empresa'
    f = fields.get("empresa")
    if f and getattr(f, "is_relation", False):
        return qs.filter(empresa_id=emp_id)

    # 3) Cualquier FK cuyo modelo relacionado tenga id_empresa
    for f in m._meta.get_fields():
        if getattr(f, "is_relation", False) and getattr(f, "concrete", False):
            rel = getattr(f, "related_model", None)
            if not rel:
                continue
            rel_field_names = {rf.name for rf in rel._meta.get_fields() if hasattr(rf, "name")}
            if "id_empresa" in rel_field_names:
                # filtra a través de la relación detectada (ej: tipo_activo__id_empresa)
                return qs.filter(**{f"{f.name}__id_empresa": emp_id}).distinct()

    return qs

class EmpresaScopeMixin(LoginRequiredMixin):
    """
    Mixin para aplicar el filtro de empresa en las vistas basadas en clases (CBVs).
    Asegura que las consultas (`querysets`) solo devuelvan resultados de la empresa activa.
    """
    def scope_queryset(self, qs):
        return scope_qs_by_empresa(self.request, qs)


class SaveEmpresaMixin(LoginRequiredMixin):
    """
    Mixin que se asegura de que al guardar una instancia de modelo que tenga un campo `id_empresa`, 
    este campo se complete automáticamente con el `empresa_id` de la sesión si no está presente.
    """
    def form_valid(self, form):
        emp_id = self.request.session.get("empresa_id")
        if emp_id:
            if hasattr(form.instance, "id_empresa_id") and not form.instance.id_empresa_id:
                form.instance.id_empresa_id = emp_id
            elif hasattr(form.instance, "id_empresa") and not getattr(form.instance, "id_empresa", None):
                form.instance.id_empresa = emp_id
        return super().form_valid(form)
