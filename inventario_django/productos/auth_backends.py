# productos/auth_backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models_inventario import Empleado
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models_inventario import Empleado


User = get_user_model()

def normalize_rut(r):
    """
    Normaliza el RUT para compararlo correctamente.

    Elimina puntos, guiones y convierte el RUT a minúsculas para hacer comparaciones consistentes.

    Args:
        r (str): El RUT a normalizar.
    """
    if not r:
        return ""
    return r.replace(".", "").replace("-", "").strip().lower()

class CustomAuthenticationBackend(ModelBackend):
    """
    Permite usar el RUT o correo electrónico en el login.

    Busca un `Empleado` por RUT o correo electrónico y valida la contraseña contra `auth_user`.

    La autenticación puede realizarse con el RUT o el correo electrónico, y se verifica si el 
    `Empleado` asociado al RUT o correo tiene una cuenta de usuario vinculada.

    Attributes:
        model: Modelo de usuario utilizado en la autenticación.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica un usuario usando el RUT o correo electrónico.

        Verifica que el nombre de usuario corresponda a un correo electrónico o un RUT. Si es 
        un correo electrónico, busca al usuario por ese campo. Si es un RUT, busca al empleado 
        asociado a ese RUT y valida la contraseña contra el usuario de ese empleado.
        """
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
