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