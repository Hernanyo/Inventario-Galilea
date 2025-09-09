from django.db import connection
class SetAppUsernameMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        username = getattr(request.user, "username", None)
        if username:
            with connection.cursor() as c:
                c.execute("SET LOCAL app.username = %s", [username])
        return self.get_response(request)
