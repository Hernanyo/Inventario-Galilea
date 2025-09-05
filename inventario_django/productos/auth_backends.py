# productos/auth_backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models_inventario import Empleado

User = get_user_model()

def normalize_rut(r):
    if not r:
        return ""
    return r.replace(".", "").replace("-", "").strip().lower()

class RutBackend(ModelBackend):
    """
    Permite usar el RUT en el campo 'username' del login.
    Busca Empleado por rut (mismo formato guardado) y valida password contra auth_user.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        # Opción simple: exige mismo formato que guardado (o normaliza ambos si lo estandarizas)
        emp = Empleado.objects.filter(rut__iexact=username).first()
        if not emp or not emp.user:
            return None
        user = emp.user
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
