from django.db import connection
from django.shortcuts import redirect


class SetAppUsernameMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        username = getattr(request.user, "username", None)
        if username:
            with connection.cursor() as c:
                c.execute("SET LOCAL app.username = %s", [username])
        return self.get_response(request)

class RequireCompanyMiddleware:
    """
    Si el usuario está autenticado y no tiene empresa elegida en sesión,
    redirige siempre al selector de empresa.
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