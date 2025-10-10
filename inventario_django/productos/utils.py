# utils.py
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission

from django.contrib.auth.models import Group, Permission
from django.contrib.auth.models import User, Group
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.conf import settings

from io import BytesIO
import qrcode
from django.core.files import File
# en productos/urls.py (o mejor en un utils.py), añade:
from django.db import connection
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.db.models import Q



def generar_qr(obj):
    """
    Genera un código QR a partir de la etiqueta del objeto y lo guarda en el campo `qr_code`.

    Esta función crea un código QR con la etiqueta del objeto proporcionado y lo guarda como una imagen en el campo `qr_code` del objeto.

    Parameters:
        obj (Model): Objeto que contiene el campo `etiqueta` que será convertido en QR.

    """
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(obj.etiqueta)  # usar la etiqueta como contenido del QR
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar en un buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    filename = f"qr_{obj.pk}.png"

    # Guardar la imagen en el campo qr_code
    obj.qr_code.save(filename, File(buffer), save=False)

def log_mantencion_event(user, m, accion: str, detalle: str = ""):
    """
    Guarda una 'foto' de la mantención en el historial.

    Esta función graba un registro detallado de los cambios en una mantención en la base de datos,
    incluyendo información sobre el activo, estado, prioridad y responsables.

    Parameters:
        user (User): Usuario que ejecuta la acción.
        m (Mantencion): Instancia de la mantención que está siendo registrada.
        accion (str): Acción realizada (e.g., "CREAR", "EDITAR").
        detalle (str): Detalles adicionales de la acción (opcional).


    """
    username = getattr(user, "username", None) or None
    # valores “congelados”
    etiqueta = getattr(getattr(m, "id_activo", None), "etiqueta", None)
    activo_nombre = getattr(getattr(m, "id_activo", None), "nombre_activo", None)

    # intenta leer strings de tipo/prioridad/estado si tus FKs existen;
    # si tus modelos tienen otros nombres de campo, ajusta aquí.
    tipo_txt = getattr(getattr(m, "id_tipo_mantencion", None), "tipo", None)
    prioridad_txt = getattr(getattr(m, "id_prioridad", None), "tipo", None)
    estado_txt = getattr(getattr(m, "id_estado_mantencion", None), "tipo", None)

    # responsables (si los tienes en la tabla)
    def nombre_emp(emp):
        if not emp:
            return None
        partes = [emp.nombre, emp.apellido_paterno, emp.apellido_materno or ""]
        return " ".join(p for p in partes if p)

    responsable_txt = nombre_emp(getattr(m, "id_empleado_responsable", None))
    solicitante_txt = nombre_emp(getattr(m, "id_empleado_solicitante", None))

    with connection.cursor() as c:
        c.execute("""
            INSERT INTO inventario.historial_mantenciones_log
            (id_mantencion, accion, detalle, usuario_app_username,
             id_activo, etiqueta, activo_nombre,
             tipo_mantencion, prioridad, estado_actual,
             responsable_nombre, solicitante_nombre, descripcion)
            VALUES (%s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s)
        """, [
            m.id_mantencion, accion, detalle, username,
            getattr(getattr(m, "id_activo", None), "id_activo", None),
            etiqueta, activo_nombre,
            tipo_txt, prioridad_txt, estado_txt,
            responsable_txt, solicitante_txt,
            getattr(m, "descripcion", None),
        ])

def crear_usuario_y_enviar_correo(empleado):
    """
    Crea un usuario en el sistema y envía un correo de activación de cuenta.

    Si el empleado no tiene correo asociado, no se realiza ninguna acción. Si el correo está vacío,
    se crea un usuario con el `RUT` como nombre de usuario y se envía un enlace para que el empleado defina su contraseña.

    Parameters:
        empleado (Empleado): El empleado para el que se creará el usuario.


    """
    if not empleado.correo:
        return

    # username = RUT, email = correo
    user, created = User.objects.get_or_create(
        username=empleado.rut,
        defaults={
            "first_name": empleado.nombre,
            "last_name": empleado.apellido_paterno,
            "email": empleado.correo,
            "is_active": True,
        }
    )

    # enlazar al empleado si no estaba enlazado
    if not empleado.user_id:
        empleado.user = user
        empleado.save(update_fields=["user"])

    # generar link de “set/reset password”
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    reset_path = reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": token})
    reset_link = f"{settings.SITE_URL}{reset_path}"

    # DEV: imprime en consola
    print(f"[DEV] Enviar a {empleado.correo}: {reset_link}")

    # PROD (cuando uses SMTP):
    # send_mail("Crea tu contraseña", f"Configura tu acceso: {reset_link}",
    #           settings.DEFAULT_FROM_EMAIL, [empleado.correo])

def _ensure_role_groups():
    # crea/actualiza grupos de rol
    perms = Permission.objects.filter(content_type__app_label="productos")
    g_admin, _ = Group.objects.get_or_create(name="rol_admin")
    g_user, _  = Group.objects.get_or_create(name="rol_usuario")
    g_guest, _ = Group.objects.get_or_create(name="rol_invitado")

    g_admin.permissions.set(perms)
    g_user.permissions.set(
        perms.filter(
            Q(codename__startswith="view_") |
            Q(codename__startswith="add_")  |
            Q(codename__startswith="change_")
        )
    )
    g_guest.permissions.set(perms.filter(codename__startswith="view_"))


def ensure_auth_user_for_empleado(empleado):
    """
    Crea o recupera un usuario de autenticación asociado a un empleado.

    Esta función crea un usuario de autenticación si no existe y lo asocia al empleado usando
    el campo `rut` del empleado como nombre de usuario.

    Parameters:
        empleado (Empleado): El empleado para el que se debe asegurar el usuario.

    Returns:
        user (User): El usuario creado o recuperado.
        was_created (bool): Indica si el usuario fue creado o ya existía.
    """
    user, was_created = User.objects.get_or_create(
        username=empleado.rut,               # LOGIN por RUT (coincide con tu RutBackend)
        defaults={
            "first_name": empleado.nombre,
            "last_name": empleado.apellido_paterno,
            "email": (empleado.correo or ""),
            "is_active": True,
        }
    )
    # Mantén email sincronizado si faltaba
    if empleado.correo and not user.email:
        user.email = empleado.correo
        user.save(update_fields=["email"])

    # Linkea al empleado si no está linkeado
    if not empleado.user_id or empleado.user_id != user.id:
        empleado.user = user
        empleado.save(update_fields=["user"])

    return user, was_created


def sync_user_groups_for_empleado(empleado):
    """
    Asigna los grupos según el rol del empleado.

    Dependiendo del rol del empleado (`admin`, `invitado`, `usuario`), esta función asigna el grupo correspondiente.
    Además, ajusta el campo `is_staff` para los administradores.

    Parameters:
        empleado (Empleado): El empleado cuya asignación de grupos y permisos se actualizará.


    """
    if not empleado.user:
        return

    rol = (empleado.rol or "").strip().lower()
    target = None
    if rol == "admin":
        target = "rol_admin"
    elif rol == "invitado":
        target = "rol_invitado"
    else:
        target = "rol_usuario"

    # Quita todos y asigna el grupo objetivo
    g_admin, _ = Group.objects.get_or_create(name="rol_admin")
    g_user, _  = Group.objects.get_or_create(name="rol_usuario")
    g_guest,_  = Group.objects.get_or_create(name="rol_invitado")

    empleado.user.groups.clear()

    # Usamos solo el nombre del grupo, no el objeto completo
    if target == "rol_admin":
        empleado.user.groups.add(g_admin.id)  # Usando ID
        empleado.user.is_staff = True
    elif target == "rol_invitado":
        empleado.user.groups.add(g_guest.id)  # Usando ID
        empleado.user.is_staff = False
    else:
        empleado.user.groups.add(g_user.id)  # Usando ID
        empleado.user.is_staff = False

    empleado.user.save(update_fields=["is_staff"])


def send_password_set_link(user):
    """
    Genera un enlace para que el usuario defina su contraseña.

    Este enlace se genera utilizando el sistema de tokens de Django y se imprime en la consola.

    Parameters:
        user (User): El usuario para el cual se genera el enlace de restablecimiento de contraseña.

    """

    uidb64 = str(user.pk)  # para dev simple; en prod usa urlsafe_base64_encode
    token = default_token_generator.make_token(user)
    url = f"{settings.SITE_URL}{reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})}"
    print(f"[DEV] Link para definir contraseña de {user.username}: {url}")

def ensure_history_view_perms():
    """
    Asegura que los permisos de vista para el historial de activos y mantenciones estén presentes.

    La función verifica que los permisos para ver los registros de historial de activos y mantenciones
    estén asignados a los grupos de usuarios correspondientes.

    """
    app_label = "productos"
    model_codenames = [
        "historialactivos",            # -> view_historialactivos
        "historialmantencioneslog",    # -> view_historialmantencioneslog
    ]
    # crea/obtiene los Permission por si el modelo es unmanaged
    for model_lower in model_codenames:
        ct, _ = ContentType.objects.get_or_create(app_label=app_label, model=model_lower)
        Permission.objects.get_or_create(
            content_type=ct,
            codename=f"view_{model_lower}",
            defaults={"name": f"Can view {model_lower}"}
        )

    # asígnalos a los grupos de la app
    groups = ["rol_usuario", "rol_admin"]   # añade aquí cualquier otro grupo que uses
    perms = list(Permission.objects.filter(
        content_type__app_label=app_label,
        codename__in=["view_historialactivos", "view_historialmantencioneslog"]
    ))
    for gname in groups:
        g, _ = Group.objects.get_or_create(name=gname)
        g.permissions.add(*perms)