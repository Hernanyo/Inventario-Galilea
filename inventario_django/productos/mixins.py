from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

class StaffRequiredMixin(LoginRequiredMixin, PermissionRequiredMixin):
    raise_exception = True

class ModelPermsMixin(StaffRequiredMixin):
    """Arma el permiso dinámicamente: app_label.action_modelname"""
    action_perm = "view"  # view | add | change | delete
    def get_permission_required(self):
        opts = self.model._meta
        return (f"{opts.app_label}.{self.action_perm}_{opts.model_name}",)
