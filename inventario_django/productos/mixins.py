# productos/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect  # <----- AÑADIR
from django.urls import resolve, reverse  # <----- AÑADIR
from django.contrib import messages
from django.shortcuts import redirect

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


class EmpresaScopeMixin(CompanyRequiredMixin):
    """
    Provee scope_queryset(qs) para filtrar por empresa actual.
    Intenta usar 'id_empresa' si existe; si no, 'empresa' (FK clásica).
    """
    _field_cache = {}

    def scope_queryset(self, qs):
        emp_id = self.request.session.get("empresa_id")
        if not emp_id or qs is None:
            return qs

        model = qs.model
        key = model._meta.label_lower

        # cachea qué campo usar para este modelo
        field = self._field_cache.get(key)
        if field is None:
            names = {f.name for f in model._meta.get_fields()}
            if "id_empresa" in names:
                field = "id_empresa"
            elif "empresa" in names:
                field = "empresa"   # usaremos empresa_id en el filtro
            else:
                field = ""          # modelo sin campo empresa
            self._field_cache[key] = field

        if field == "id_empresa":
            return qs.filter(id_empresa=emp_id)
        elif field == "empresa":
            return qs.filter(empresa_id=emp_id)
        else:
            return qs  # no hay campo empresa en este modelo; no filtra
        
# --- AÑADIR ---
class SaveEmpresaMixin:
    """
    Si el modelo tiene campo 'id_empresa', lo completa desde la sesión.
    Usar en CreateView/UpdateView.
    """
    def form_valid(self, form):
        emp_id = self.request.session.get("empresa_id")
        if emp_id and hasattr(form.instance, "id_empresa") and form.instance.id_empresa_id is None:
            form.instance.id_empresa_id = emp_id
        return super().form_valid(form)
