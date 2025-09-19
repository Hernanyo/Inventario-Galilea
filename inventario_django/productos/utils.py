# utils.py
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
    username = getattr(user, "username", None) or None
    # valores “congelados”
    etiqueta = getattr(getattr(m, "id_equipo", None), "etiqueta", None)
    equipo_nombre = getattr(getattr(m, "id_equipo", None), "nombre_equipo", None)

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
             id_equipo, etiqueta, equipo_nombre,
             tipo_mantencion, prioridad, estado_actual,
             responsable_nombre, solicitante_nombre, descripcion)
            VALUES (%s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s)
        """, [
            m.id_mantencion, accion, detalle, username,
            getattr(getattr(m, "id_equipo", None), "id_equipo", None),
            etiqueta, equipo_nombre,
            tipo_txt, prioridad_txt, estado_txt,
            responsable_txt, solicitante_txt,
            getattr(m, "descripcion", None),
        ])

def crear_usuario_y_enviar_correo(empleado):
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

def sync_user_groups_for_empleado(empleado):
    """
    Saca al usuario de los grupos de rol y lo mete en el que corresponda
    según empleado.rol = admin|usuario|invitado.
    """
    if not empleado.user:
        return
    _ensure_role_groups()
    name_by_rol = {
        "admin": "rol_admin",
        "usuario": "rol_usuario",
        "invitado": "rol_invitado",
    }
    target = name_by_rol.get((empleado.rol or "usuario").lower(), "rol_usuario")

    # limpia pertenencia previa
    for gname in name_by_rol.values():
        try:
            g = Group.objects.get(name=gname)
            empleado.user.groups.remove(g)
        except Group.DoesNotExist:
            pass

    empleado.user.groups.add(Group.objects.get(name=target))
    # opcional: marca staff si es admin (sólo por comodidad en admin)
    empleado.user.is_staff = (target == "rol_admin")
    empleado.user.save(update_fields=["is_staff"])

def ensure_auth_user_for_empleado(empleado):
    """
    Crea (o trae) un auth.User con username=RUT y lo asocia a empleado.user.
    Retorna (user, was_created).
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
    Asigna grupos según empleado.rol y ajusta is_staff para admin.
    Grupos esperados: rol_admin, rol_usuario, rol_invitado
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
    if target == "rol_admin":
        empleado.user.groups.add(g_admin)
        empleado.user.is_staff = True     # puede entrar al admin si quieres
    elif target == "rol_invitado":
        empleado.user.groups.add(g_guest)
        empleado.user.is_staff = False
    else:
        empleado.user.groups.add(g_user)
        empleado.user.is_staff = False

    empleado.user.save(update_fields=["is_staff"])


def send_password_set_link(user):
    """
    En dev imprime el link de 'definir contraseña' (password reset) en consola.
    """
    uidb64 = str(user.pk)  # para dev simple; en prod usa urlsafe_base64_encode
    token = default_token_generator.make_token(user)
    url = f"{settings.SITE_URL}{reverse('password_reset_confirm', kwargs={'uidb64': uidb64, 'token': token})}"
    print(f"[DEV] Link para definir contraseña de {user.username}: {url}")