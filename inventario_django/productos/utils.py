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

from productos.models_inventario import Empleado
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


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
    NO crea usuarios.

    Asume que el Empleado YA tiene un auth.User asociado (lo crea EmpleadoForm.save)
    y solo genera el link de reseteo de contraseña.

    En desarrollo, imprime el link en consola.
    En producción, puedes usar send_mail para enviarlo por correo.

    """
################################ 05/12 #########################    
    # ⛔ Empleado/Trabajador no debe tener login
    if empleado.rol == Empleado.ROL_TRABAJADOR:  # Verifica si es trabajador (empleado sin acceso)
        return  # No hace nada si es trabajador (sin acceso)
################################ 05/12 #########################    
    if not empleado.correo:
        return

#    # username = RUT, email = correo
#    user, created = User.objects.get_or_create(
#        username=empleado.rut,
#        defaults={
#            "first_name": empleado.nombre,
#            "last_name": empleado.apellido_paterno,
#            "email": empleado.correo,
#            "is_active": True,
#        }
#    )
#    # enlazar al empleado si no estaba enlazado
#    if not empleado.user_id:
#        empleado.user = user
#        empleado.save(update_fields=["user"])

    user = getattr(empleado, "user", None)
    email = (empleado.correo or "").strip().lower()

    # Si no hay user o correo, no hacemos nada
    if not user or not email:
        return

    # Generar token de reset
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

    reset_path = reverse(
        "password_reset_confirm",
        kwargs={"uidb64": uidb64, "token": token},
    )

    # Usamos SITE_URL desde settings, como tenías antes
    site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
    reset_link = f"{site_url}{reset_path}"

    # DEV: imprime en consola
    print(f"[DEV] Enviar a {email}: {reset_link}")

    # PROD: cuando tengas configurado SMTP, puedes descomentar esto:
    # send_mail(
    #     subject="Crea tu contraseña",
    #     message=f"Configura tu acceso: {reset_link}",
    #     from_email=settings.DEFAULT_FROM_EMAIL,
    #     recipient_list=[email],
    #     fail_silently=False,
    # )

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
################################ 04/12 #########################    
    if not empleado.permite_login:
        return None, False
################################ 04/12 #########################    

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
    Asigna grupos y flags de Django según empleado.rol.

    - admin  -> grupo rol_admin, is_staff=True, is_active=True
    - jefe   -> grupo rol_admin, is_staff=True, is_active=True (mismas funciones que admin, pero
                limitaremos empresas en la vista de selección)
    - usuario -> grupo rol_usuario, is_staff=False (o True si quieres que vea admin), is_active=True
    - invitado -> grupo rol_invitado, is_staff=False, is_active=True
    - empleado -> NO debe tener login: se desactivan grupos y se deja is_active=False
    """
######################################## 04/12 #################################### 
    if not empleado.user:
        # Si no tiene user asociado, nada que hacer aquí.
        return

    rol = (empleado.rol or "").strip().lower()

    # Cargamos/creamos grupos
    g_admin, _ = Group.objects.get_or_create(name="rol_admin")
    g_user,  _ = Group.objects.get_or_create(name="rol_usuario")
    g_guest, _ = Group.objects.get_or_create(name="rol_invitado")

    # Limpiamos grupos anteriores siempre
    empleado.user.groups.clear()

    # --- ADMIN / JEFE ---
    if rol == Empleado.ROL_ADMIN or rol == Empleado.ROL_JEFE:
        empleado.user.groups.add(g_admin)
        empleado.user.is_staff = True
        empleado.user.is_active = True

    # --- USUARIO ---
    elif rol == Empleado.ROL_USUARIO:
        empleado.user.groups.add(g_user)
        # Aquí decides si quieres que un "usuario" vea el admin.
        empleado.user.is_staff = False
        empleado.user.is_active = True

    # --- INVITADO (si lo usas) ---
    elif rol == "invitado":
        empleado.user.groups.add(g_guest)
        empleado.user.is_staff = False
        empleado.user.is_active = True

    # --- TRABAJADOR (NO LOGIN) u otros valores raros ---
    elif rol == Empleado.ROL_TRABAJADOR:
        empleado.user.is_staff = False
        empleado.user.is_active = False
    else:
        # valor desconocido -> lo dejo sin acceso también
        empleado.user.is_staff = False
        empleado.user.is_active = False

    empleado.user.save(update_fields=["is_staff", "is_active"])
######################################## 04/12 #################################### 


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
###################################################################################
#########################################################################################
# --- EXPORTS / HELPERS PARA CSV EXCEL ---------------------------------------

from typing import Iterable, Optional
from django.db.models import Prefetch

def get_attr_value_de_activo(activo, nombres_posibles: Iterable[str]) -> str:
    """
    Devuelve el valor del atributo dinámico (AgregacionAtributosPorActivo) cuyo
    nombre coincida con alguno de `nombres_posibles` (case/acentos/espacios flexibles).

    Args:
        activo (models.Activo): Activo objetivo (con relación `agregacionatributosporactivo_set`).
        nombres_posibles (Iterable[str]): Nombres alternativos aceptados (ej. ['número de serie','serial','sn']).

    Returns:
        str: Valor del atributo si existe; si no, cadena vacía.
    """
    from .models_inventario import AgregacionAtributosPorActivo  # import local

    normaliza = (
        lambda s: "".join(
            ch for ch in (s or "").lower()
            .replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")
            .replace("_"," ").replace("-"," ")
        ) if s else ""
    )

    candidatos = {normaliza(n) for n in nombres_posibles}
    # Reutiliza valores ya traídos (si prefetch) o hace query liviana
    vals = getattr(activo, "_valores_attr_cache", None)
    if vals is None:
        qs = (AgregacionAtributosPorActivo.objects
              .filter(activo=activo)
              .select_related("atributo"))
        vals = [(normaliza(x.atributo.atributo), x.valor or "") for x in qs]
        activo._valores_attr_cache = vals

    for nombre_norm, valor in vals:
        if nombre_norm in candidatos:
            return valor or ""
    return ""



    #######################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><
# productos/utils.py
from django.db.models.functions import Substr, Length, Cast, Coalesce
from django.db.models import IntegerField, Max
from .models_inventario import Activo, TipoActivo

# productos/utils.py
import re
from productos.models_inventario import Activo, TipoActivo

def siguiente_etiqueta(emp_id: int, tipo_id: int) -> str | None:
    """
    Calcula la próxima etiqueta para el tipo dado dentro de la empresa.
    Usa TipoActivo.estructura_etiqueta como prefijo (si existe) o las 3 primeras
    letras del tipo, y suma 1 al último correlativo encontrado.
    """
    try:
        tipo = TipoActivo.objects.get(pk=tipo_id)
    except TipoActivo.DoesNotExist:
        return None

    # Prefijo desde estructura_etiqueta o fallback a 3 letras del tipo
    prefix = (tipo.estructura_etiqueta or tipo.tipo_activo[:3]).upper()

    # Filtra activos de esa empresa y tipo
    qs = Activo.objects.filter(id_empresa_id=emp_id, id_tipo_activo_id=tipo_id)

    # Busca la última etiqueta con ese prefijo
    last = (
        qs.filter(etiqueta__startswith=prefix)
          .order_by("-id_activo")
          .values_list("etiqueta", flat=True)
          .first()
    )

    next_num = 1
    if last:
        # Si la etiqueta es p.ej. NBK00015 -> saca 15 y suma 1
        m = re.match(rf"^{re.escape(prefix)}(\d+)$", last)
        if m:
            next_num = int(m.group(1)) + 1

    # ancho 5 como en tus datos (NBK00015, IMP00008, etc.)
    return f"{prefix}{next_num:05d}"

################################################ 05/12 ##############################
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

############################ 10/12 #############################################
@receiver(post_save, sender=Empleado)
def sync_empleado_user_active(sender, instance: Empleado, **kwargs):
    """
    Mantiene user.is_active alineado con Empleado.permite_login.

    - Si es TRABAJADOR -> siempre sin acceso (is_active = False)
    - Para el resto de roles -> respeta el flag permite_login
    No crea ni borra usuarios; solo activa/desactiva si existe enlace.
    """
    user = instance.user
    if not user:
        return

    rol = (instance.rol or "").strip().lower()

    # Trabajador nunca debería tener login
    if rol == Empleado.ROL_TRABAJADOR:
        should_be_active = False
    else:
        should_be_active = bool(instance.permite_login)

    if user.is_active != should_be_active:
        user.is_active = should_be_active
        user.save(update_fields=["is_active"])