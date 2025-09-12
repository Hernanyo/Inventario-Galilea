# productos/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect  # <----- AÑADIR
from django.urls import resolve, reverse  # <----- AÑADIR

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

class EmpresaRequiredMixin:
    """
    Exige una empresa en sesión. Si no hay, redirige al selector de empresas.
    Evita bucles permitiendo pasar a las vistas de selección/cambio.
    """
    allow_without_empresa = {'productos:company_select', 'productos:company_change'}  # <----- AÑADIR

    def dispatch(self, request, *args, **kwargs):
        # Detectar el nombre de la ruta actual para evitar bucles
        try:
            match = resolve(request.path_info)
            current_name = f"{match.namespace}:{match.url_name}" if match.namespace else match.url_name
        except Exception:
            current_name = None

        # Permitir el selector y el cambio de empresa sin empresa en sesión
        if current_name in self.allow_without_empresa:
            return super().dispatch(request, *args, **kwargs)

        # Si no hay empresa en sesión, redirigir al selector (con ?next=)
        if not request.session.get("empresa_id"):
            url = reverse("productos:company_select")
            next_qs = f"?next={request.get_full_path()}" if request.method == "GET" else ""
            return redirect(url + next_qs)

        return super().dispatch(request, *args, **kwargs)