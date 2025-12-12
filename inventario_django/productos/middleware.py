from django.db import connection
from django.shortcuts import redirect

###################################################################################################################################
###################################################################################################################################
# ⬇️ añade estas líneas ARRIBA DEL TODO o después de los imports
from .current_user import set_current_user

class CurrentUserMiddleware:
    """
    Middleware que establece el usuario actual en el contexto de la solicitud.

    Asocia al hilo actual el usuario que está realizando la solicitud, 
    para poder acceder a él desde cualquier parte de la aplicación 
    durante la misma solicitud.

    Su uso es para auditoría, trazabilidad, o para funciones que necesiten 
    saber qué usuario está haciendo la solicitud.

    Al final de la solicitud, limpia el usuario asociado al hilo.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_user(getattr(request, "user", None))
        try:
            return self.get_response(request)
        finally:
            set_current_user(None)

###################################################################################################################################
###################################################################################################################################


class SetAppUsernameMiddleware:
    """
    Middleware que establece el nombre de usuario actual en la sesión de la base de datos.

    Al ejecutar cada solicitud, establece el nombre de usuario (`username`) 
    en el contexto de la base de datos, permitiendo que se registre en los logs
    o se use en procedimientos internos que necesiten saber qué usuario está realizando
    la operación.
    """
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        username = getattr(request.user, "username", None)
        if username:
            with connection.cursor() as c:
                c.execute("SET LOCAL app.username = %s", [username])
        return self.get_response(request)

class RequireCompanyMiddleware:
    """
    Middleware que verifica que un usuario autenticado tenga una empresa seleccionada en su sesión.

    Si el usuario está autenticado y no tiene una empresa seleccionada en la sesión,
    se redirige al selector de empresas. Permite que ciertas rutas como login, logout, 
    y estáticos puedan ser accedidas sin tener una empresa activa en la sesión.

    Permite que los usuarios sin empresa activa puedan seleccionar la empresa antes de 
    acceder a otras partes de la aplicación.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # rutas permitidas sin empresa (selector, login/logout, estáticos)
        allowed_paths = (
            "/ingreso/",               # seleccionar_empresa (selector)
            "/ingreso/cambiar/",       # cambiar_empresa (opcional)
            "/login/",
            "/logout/",
            "/admin/login/",
            "/static/",
            "/media/",
        )
        path = request.path

        if (
            request.user.is_authenticated
            and not request.session.get("empresa_id")
            and not any(path.startswith(p) for p in allowed_paths)
        ):
            return redirect("productos:company_select")

        return self.get_response(request)
    ####################################### 07/12 #####################################3
# productos/middleware.py
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

from .models_inventario import Empleado


class BlockTrabajadorMiddleware:
    """
    Bloquea a cualquier usuario autenticado cuyo Empleado tenga rol TRABAJADOR.

    - Cierra la sesión
    - Limpia la empresa de la sesión
    - Redirige de vuelta al login con un mensaje de error
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Evitamos hacer reverse() en cada request, se resuelve una vez
        try:
            self.login_url = reverse("productos:login")
        except Exception:
            # En migraciones / arranque inicial puede no resolver; se recalcula luego.
            self.login_url = "/login/"

    def __call__(self, request):
        # Aseguramos que request.user exista
        user = getattr(request, "user", None)

        if user is not None and user.is_authenticated:
            try:
                empleado = Empleado.objects.get(user=user)
            except Empleado.DoesNotExist:
                empleado = None

            if empleado and empleado.rol == Empleado.ROL_TRABAJADOR:
                # Limpiar selección de empresa de la sesión
                for k in ("empresa_id", "empresa_nombre", "empresa_slug"):
                    request.session.pop(k, None)

                # Cerrar sesión
                logout(request)

                # Mensaje de error
                messages.error(
                    request,
                    "No tienes acceso a la aplicación de inventario. "
                    "Si crees que es un error, contacta al área de Soporte TI.",
                )

                # Evitar loop: si ya estamos en /login/, dejamos continuar
                # para que el LoginView pinte el mensaje.
                login_url = self.login_url or reverse("productos:login")
                if request.path != login_url:
                    return redirect(login_url)

        # Si no es trabajador o no está autenticado, seguir normal
        response = self.get_response(request)
        return response
