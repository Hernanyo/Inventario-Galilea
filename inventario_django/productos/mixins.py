# productos/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

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
