# productos/auth_backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models_inventario import Empleado
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models_inventario import Empleado


User = get_user_model()

def normalize_rut(r):
    """Normaliza el RUT para compararlo correctamente."""
    if not r:
        return ""
    return r.replace(".", "").replace("-", "").strip().lower()

class CustomAuthenticationBackend(ModelBackend):
    """
    Permite usar el RUT o correo electrónico en el login.
    Busca Empleado por RUT o correo electrónico y valida la contraseña contra auth_user.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        
        # Si el 'username' es un correo electrónico
        if '@' in username:
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None
        else:
            # Si el 'username' es un RUT
            emp = Empleado.objects.filter(rut__iexact=username).first()
            if not emp or not emp.user:
                return None
            user = emp.user

        # Verificar si la contraseña es correcta
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
