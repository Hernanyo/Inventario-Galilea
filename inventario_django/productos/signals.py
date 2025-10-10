# productos/signals.py
from __future__ import annotations

from .models_inventario import Empresa  # arriba con el resto
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models_inventario import Empleado
from .utils import sync_user_groups_for_empleado, crear_usuario_y_enviar_correo
from threading import local
from django.db.models.signals import pre_save, post_save

from .models_inventario import Activo, HistorialActivos

# productos/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models_inventario import Empleado
from .utils import ensure_auth_user_for_empleado, sync_user_groups_for_empleado, send_password_set_link

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models_inventario import Activo, HistorialActivos


def _as_str(obj):
    """
    Convierte un objeto en un string, retornando una cadena vacía si es None.
    
    :param obj: Objeto a convertir a string.
    :return: String vacío si el objeto es None, de lo contrario, su representación en string.
    """
    return "" if obj is None else str(obj)


def _empleado_empresa_dep(empleado):
    """
    Obtiene la empresa y el departamento de un empleado.

    :param empleado: Instancia de `Empleado`.
    :return: Tupla con `id_empresa` y `id_departamento` del empleado.
    """
    if not empleado:
        return None, None
    return getattr(empleado, "id_empresa", None), getattr(empleado, "id_departamento", None)

def _activo_empresa_dep(instance, prev=None):
    """
    Obtiene la empresa y el departamento de un activo, priorizando los valores actuales, 
    luego los valores del responsable y finalmente los valores previos.

    :param instance: Instancia de `Activo`.
    :param prev: Instancia previa de `Activo` para obtener valores anteriores.
    :return: Tupla con `id_empresa` y `id_departamento` del activo.
    """
    emp = getattr(instance, "id_empresa", None)
    dep = getattr(instance, "id_departamento", None)
    if emp or dep:
        return emp, dep
    emp_a, dep_a = _empleado_empresa_dep(getattr(instance, "id_empleado", None))
    if emp_a or dep_a:
        return emp_a, dep_a
    if prev:
        return _empleado_empresa_dep(getattr(prev, "id_empleado", None))
    return None, None


@receiver(pre_save, sender=Activo)
def activo_pre_save(sender, instance: Activo, **kwargs):
    """
    Guarda un snapshot previo del activo para ser utilizado en post_save para comparación.

    :param sender: El modelo que dispara la señal.
    :param instance: Instancia del objeto `Activo` antes de guardar.
    :param kwargs: Argumentos adicionales.
    """
    if instance.pk:
        try:
            instance._prev = sender.objects.select_related(
                "id_empleado", "id_estado_activo"
            ).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._prev = None
    else:
        instance._prev = None

############################################# antiguo solo cambio de estados
#@receiver(post_save, sender=Activo)
#def activo_post_save(sender, instance: Activo, created: bool, **kwargs):
#    """
#    Historial por alta/cambio de estado/responsable.
#    (Observaciones se maneja en receivers aparte más abajo.)
#    """
#    prev: Activo | None = getattr(instance, "_prev", None)
#    usuario_actual = getattr(instance, "_usuario_actual", None)
#
#    empresa_actual, dep_actual = _activo_empresa_dep(instance, prev)
#
#    base = dict(
#        activo=instance,
#        etiqueta=getattr(instance, "etiqueta", "") or "",
#        nombre_activo=getattr(instance, "nombre_activo", "") or "",
#        tipo_activo=getattr(instance, "id_tipo_activo", None) if hasattr(instance, "id_tipo_activo") else None,
#        usuario=usuario_actual,
#        empresa=empresa_actual,          # 👈 usa 'empresa', no 'id_empresa'
#        departamento=dep_actual,         # 👈 idem
#        responsable_actual=getattr(instance, "id_empleado", None),
#        fecha=timezone.now()
#    )
#
#    if created:
#        HistorialActivos.objects.create(
#            estado_anterior=None,
#            estado_nuevo=getattr(instance, "id_estado_activo", None),
#            **base,
#        )
#        return
#
#    if not prev:
#        return
#
#    prev_estado_id = getattr(prev, "id_estado_activo_id", None)
#    new_estado_id  = getattr(instance, "id_estado_activo_id", None)
#    prev_resp_id   = getattr(prev, "id_empleado_id", None)
#    new_resp_id    = getattr(instance, "id_empleado_id", None)
#
#    estado_cambia = prev_estado_id != new_estado_id
#    resp_cambia   = prev_resp_id  != new_resp_id
#
#    if not (estado_cambia or resp_cambia):
#        return
#
#    HistorialActivos.objects.create(
#        estado_anterior=getattr(prev, "id_estado_activo", None),
#        estado_nuevo=getattr(instance, "id_estado_activo", None),
#        responsable_anterior_fk_id=getattr(prev, "id_empleado_id", None),
#        **base,
#    )
@receiver(post_save, sender=Activo)
def activo_post_save(sender, instance: Activo, created: bool, **kwargs):
    """
    Registra un historial por creación, cambios de estado, cambios de responsable y cambios de otros campos 
    relevantes en un activo.

    :param sender: El modelo que dispara la señal.
    :param instance: Instancia del objeto `Activo` después de guardar.
    :param created: Si el objeto fue creado.
    :param kwargs: Argumentos adicionales.
    """
    prev: Activo | None = getattr(instance, "_prev", None)
    usuario_actual = getattr(instance, "_usuario_actual", None)

    # Empresa/Depto por prioridad (modelo / responsable / previo)
    empresa_actual, dep_actual = _activo_empresa_dep(instance, prev)

    # ---- FOTO ACTUAL (siempre strings “congelados” donde el modelo lo permite) ----
    base = dict(
        activo=instance,  # FK para saber de qué activo es el evento (no se muestra en la lista)
        etiqueta=(getattr(instance, "etiqueta", "") or ""),
        nombre_activo=(getattr(instance, "nombre_activo", "") or ""),  # FOTO del nombre
        tipo_activo=getattr(instance, "id_tipo_activo", None) if hasattr(instance, "id_tipo_activo") else None,
        usuario=usuario_actual,          # Empleado que hizo el cambio (si lo seteas en la vista)
        empresa=empresa_actual,          # deja el FK (tu modelo ya lo usa así)
        departamento=dep_actual,         # idem
        responsable_actual=getattr(instance, "id_empleado", None),  # FK (tu modelo ya lo usa)
        fecha=timezone.now(),
    )

    # --- Alta ---
    if created:
        HistorialActivos.objects.create(
            estado_anterior=None,
            estado_nuevo=getattr(instance, "id_estado_activo", None),
            accion="CREACION",
            **base,
        )
        return

    if not prev:
        return

    # --- Detección de cambios (prev vs new) ---
    prev_estado_id = getattr(prev, "id_estado_activo_id", None)
    new_estado_id  = getattr(instance, "id_estado_activo_id", None)
    prev_resp_id   = getattr(prev, "id_empleado_id", None)
    new_resp_id    = getattr(instance, "id_empleado_id", None)

    estado_cambia = prev_estado_id != new_estado_id
    resp_cambia   = prev_resp_id  != new_resp_id

    # Otros campos relevantes (para comentario)
    changes = []

    def add_change(label, old, new):
        if (old or "") != (new or ""):
            changes.append(f"{label}: '{(old or '')[:80]}' → '{(new or '')[:80]}'")

    add_change("Nombre", getattr(prev, "nombre_activo", None), getattr(instance, "nombre_activo", None))
    add_change("Etiqueta", getattr(prev, "etiqueta", None), getattr(instance, "etiqueta", None))
    add_change("Marca", getattr(prev, "id_marca_id", None), getattr(instance, "id_marca_id", None))
    add_change("Tipo", getattr(prev, "id_tipo_activo_id", None), getattr(instance, "id_tipo_activo_id", None))
    add_change("Proveedor", getattr(prev, "id_proveedor_id", None), getattr(instance, "id_proveedor_id", None))
    add_change("Empresa", getattr(prev, "id_empresa_id", None), getattr(instance, "id_empresa_id", None))
    add_change("Departamento", getattr(prev, "id_departamento_id", None), getattr(instance, "id_departamento_id", None))

    otros_cambios = bool(changes)

    # Si no hubo nada relevante, no insertamos historial
    if not (estado_cambia or resp_cambia or otros_cambios):
        return

    # Etiqueta de acción (para lectura rápida en el historial)
    if estado_cambia:
        accion = "ESTADO"
    elif resp_cambia:
        accion = "RESPONSABLE"
    else:
        accion = "EDICION"

    comentario = None
    if otros_cambios:
        comentario = ("; ".join(changes))[:2000]

    # Si cambió estado o responsable, registramos con esos campos “antes/ahora”.
    # Si solo cambiaron otros campos, dejamos estado_anterior = estado_nuevo = estado actual,
    # y responsable_anterior_fk = responsable_actual (foto del momento).
    HistorialActivos.objects.create(
        estado_anterior=getattr(prev, "id_estado_activo", None) if estado_cambia else getattr(instance, "id_estado_activo", None),
        estado_nuevo=getattr(instance, "id_estado_activo", None),
        responsable_anterior_fk_id=getattr(prev, "id_empleado_id", None) if resp_cambia else getattr(instance, "id_empleado_id", None),
        comentario=comentario,
        accion=accion,
        **base,
    )

# ---------- Observaciones ----------

def _historial_snapshot_observaciones(activo: Activo, comentario: str, usuario=None):
    """
    Inserta un registro de OBSERVACIONES (estado anterior = nuevo).
    
    Registra los cambios en el campo de observaciones del activo, creando un 
    historial con la acción correspondiente.

    :param activo: Instancia de `Activo` sobre el cual se registran las observaciones.
    :param comentario: Texto de las observaciones.
    :param usuario: Usuario que realiza el cambio.
    """
    try:
        HistorialActivos.objects.create(
            activo=activo,
            etiqueta=getattr(activo, "etiqueta", None),
            nombre_activo=getattr(activo, "nombre_activo", None),
            fecha=timezone.now(),
            responsable_anterior_fk=getattr(activo, "id_empleado", None),
            estado_anterior=getattr(activo, "id_estado_activo", None),
            estado_nuevo=getattr(activo, "id_estado_activo", None),
            responsable_actual=getattr(activo, "id_empleado", None),
            empresa=getattr(activo, "id_empresa", None),       # 👈 consistencia con 'base'
            departamento=getattr(activo, "id_departamento", None),
            usuario=usuario,                                    # 👈 guarda quién hizo el cambio
            accion="OBSERVACIONES",
            tipo_activo=getattr(activo, "id_tipo_activo", None),
            comentario = (comentario or "")[:2000],
        )

    except Exception as e:
        # Para depurar si algo vuelve a fallar
        print("[HistorialActivos][OBSERVACIONES] error:", e)



@receiver(pre_save, sender=Activo)
def _activo_detectar_cambio_observaciones(sender, instance: Activo, **kwargs):
    """
    Prepara el mensaje cuando cambian las observaciones.
    
    Compara las observaciones previas y nuevas, y si hay cambios, se prepara
    un mensaje que será registrado en el historial de observaciones.

    :param sender: El modelo que dispara la señal.
    :param instance: Instancia del objeto `Activo` antes de guardar.
    :param kwargs: Argumentos adicionales.
    """
    if not instance.pk:
        instance._obs_log_msg = None
        return

    try:
        prev = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._obs_log_msg = None
        return

    prev_obs = (prev.observaciones or "").strip()
    new_obs  = (instance.observaciones or "").strip()

    if prev_obs != new_obs:
        instance._obs_log_msg = new_obs[:800]  # << SOLO el valor nuevo
    else:
        instance._obs_log_msg = None


@receiver(post_save, sender=Activo)
def _activo_log_cambio_observaciones(sender, instance: Activo, created: bool, **kwargs):
    """
    Registra un evento en el historial cuando se detecta un cambio en las observaciones.

    Si se ha creado un nuevo `Activo`, guarda el mensaje de las observaciones
    en el historial de activos. Si no es nuevo, registra los cambios en las 
    observaciones.

    :param sender: El modelo que dispara la señal.
    :param instance: Instancia del objeto `Activo` después de guardar.
    :param created: Si el objeto fue creado.
    :param kwargs: Argumentos adicionales.
    """

    if created:
        init = (instance.observaciones or "").strip()
        if init:
            _historial_snapshot_observaciones(
                instance,
                init[:800],
                getattr(instance, "_usuario_actual", None),
            )
        return


    msg = getattr(instance, "_obs_log_msg", None)
    if msg:
        instance._obs_log_msg = None
        _historial_snapshot_observaciones(
            instance,
            msg,
            getattr(instance, "_usuario_actual", None),
        )
        instance._obs_log_msg = None

@receiver(post_save, sender=Empleado)
def empleado_post_save(sender, instance: Empleado, created, **kwargs):
    """
    Crea un usuario para el empleado si no tiene uno asociado, y sincroniza los 
    grupos de usuario según el rol del empleado.

    :param sender: El modelo que dispara la señal.
    :param instance: Instancia del objeto `Empleado`.
    :param created: Si el objeto fue creado.
    :param kwargs: Argumentos adicionales.
    """
    # Si se crea un empleado con correo y sin user → crea user + envía link
    if created and instance.correo and not instance.user:
        crear_usuario_y_enviar_correo(instance)

    # Mantener grupos según rol siempre que exista user
    try:
        sync_user_groups_for_empleado(instance)
    except Exception:
        # evita romper guardado si aún no están los grupos al boot
        pass


###########################################################################################################################
###########################################################################################################################
###########################################################################################################################
# ====== AUDITORÍA MAESTRA (Registro/TipoRegistro) ======

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

from .models_inventario import Registro, TipoRegistro

from django.contrib.auth.models import User 
from django.contrib.contenttypes.models import ContentType 
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.sessions.models import Session  # ⬅️ importante
from django.db.migrations.recorder import MigrationRecorder
from django.contrib.auth.models import User, Group, Permission
from django.forms.models import model_to_dict
import datetime
from django.contrib.auth.models import Group

# Para obtener el usuario actual desde middleware
#try:
#    from .current_user import get_current_user
#except Exception:
#    def get_current_user():
#        return None

def _audit_tables_ready() -> bool:
    """
    Verifica si las tablas necesarias para la auditoría están listas para registrar eventos.

    :return: True si las tablas de auditoría están disponibles, False de lo contrario.
    """
    try:
        tables = set(connection.introspection.table_names())
        return Registro._meta.db_table in tables and TipoRegistro._meta.db_table in tables
    except Exception:
        return False
########################################################################################################
########################################################################################################
def _as_fk_id(value):
    """Devuelve el ID de un FK sea que venga como instancia o como entero."""
    if value is None:
        return None
    return getattr(value, "pk", value)  # instancia → pk, si ya es int, lo deja

def _get_or_create_tipo(nombre: str, emp_id: int | None):
    # global: ignora la empresa; 1 sola fila por nombre
    tipo = TipoRegistro.objects.filter(nombre__iexact=nombre).first()
    if tipo:
        return tipo
    return TipoRegistro.objects.create(nombre=nombre)  # deja id_empresa = NULL
##########################################################################################################
##########################################################################################################


# Evitar loguear sobre nuestras propias tablas y sobre las tablas de migraciones
IGNORED_SENDERS = {
    Registro, TipoRegistro,
    getattr(MigrationRecorder, "Migration", None),  # django_migrations
    Session, User, Group, Permission,             # ⬅️ clave de sesión es string
}



def _coerce_value(v):
    # simplificador: convierte datetimes y objetos a valores serializables
    if isinstance(v, (datetime.datetime, datetime.date, datetime.time)):
        return v.isoformat()
    # ForeignKeys vienen como ids si usamos model_to_dict, pero por si acaso:
    if hasattr(v, 'pk'):
        return v.pk
    # Evita objetos no serializables (Groups, Users, etc.)
    if isinstance(v, (list, tuple)):
        return [_coerce_value(x) for x in v]
    if isinstance(v, dict):
        return {k: _coerce_value(x) for k, x in v.items()}
    return v  # str/int/bool/None

def _safe_snapshot(instance):
    data = model_to_dict(instance)
    for f in instance._meta.fields:
        # Para FileField/ImageField guarda solo el nombre
        if hasattr(f, "upload_to"):
            val = getattr(instance, f.name, None)
            data[f.name] = getattr(val, "name", None)
    # coerción final
    return {k: _coerce_value(v) for k, v in data.items()}



@receiver(pre_save)
def audit_pre_save_snapshot_all(sender, instance, **kwargs):
    if sender in IGNORED_SENDERS or kwargs.get("raw"):
        return
    try:
        old = sender.objects.get(pk=instance.pk) if instance.pk else None
    except sender.DoesNotExist:
        old = None
    instance._audit_old_snapshot = _safe_snapshot(old) if old else None

# helper para empresa
def _resolve_empresa(instance):
    try:
        if isinstance(instance, Empresa):
            return instance
    except Exception:
        pass
    for attr in ("id_empresa", "empresa", "empresa_fk", "empresa_id"):
        if hasattr(instance, attr):
            return getattr(instance, attr)
    # intenta por empleado/responsable
    for trail in ["id_empleado", "responsable_actual", "usuario"]:
        if hasattr(instance, trail):
            emp = getattr(instance, trail)
            if emp and hasattr(emp, "id_empresa"):
                return emp.id_empresa
    return None

def _resolve_empleado_from_request_user():
    # si usas current_user middleware que devuelve django User
    try:
        from .current_user import get_current_user
        u = get_current_user()
        if u and hasattr(u, "empleado"):
            return u.empleado
    except Exception:
        pass
    return None
###################################################################################################################
###################################################################################################################
@receiver(post_save)
def audit_post_save_all(sender, instance, created, **kwargs):
    if sender in IGNORED_SENDERS or kwargs.get("raw") or not _audit_tables_ready():
        return

    try:
        # 1) Autor y empresa (scope)
        empleado_autor = _resolve_empleado_from_request_user()
        empresa_obj_or_id = _resolve_empresa(instance)
        emp_id = _as_fk_id(empresa_obj_or_id) or getattr(empleado_autor, "id_empresa_id", None)

        # 2) Snapshots (para diffs y adjuntos)
        old_snap = getattr(instance, "_audit_old_snapshot", None) or {}
        new_snap = _safe_snapshot(instance)

        # 3) Tipo base (CREAR/EDITAR) con overrides (ELIMINAR, adjuntos Factura)
        force = getattr(instance, "_audit_force_tipo", None)

        # Detectar soft-delete si el modelo tiene 'eliminado'
        soft_deleted = False
        if "eliminado" in new_snap:
            prev_elim = old_snap.get("eliminado", None)
            new_elim  = new_snap.get("eliminado", None)
            soft_deleted = (prev_elim is False and new_elim is True)

        # Prioridad: flag > soft-delete > crear/editar
        tipo_nombre = (
            force if force
            else ("ELIMINAR" if soft_deleted else ("CREAR" if created else "EDITAR"))
        )

        # Descripción por defecto según tipo base
        descripcion = {
            "CREAR":    f"Se creó {sender._meta.verbose_name.title()} #{instance.pk}",
            "EDITAR":   f"Se editó {sender._meta.verbose_name.title()} #{instance.pk}",
            "ELIMINAR": f"Se eliminó {sender._meta.verbose_name.title()} #{instance.pk}",
        }.get(tipo_nombre, f"Acción {tipo_nombre} sobre {sender._meta.verbose_name.title()} #{instance.pk}")

        # 4) Reglas de adjunto (solo Factura, no aplica si es ELIMINAR)
        is_factura = sender._meta.model_name == "factura"
        extra_file_event = False
        old_for_base = old_snap
        new_for_base = new_snap
        file_action_nombre = None
        archivo_old = None
        archivo_new = None

        if tipo_nombre != "ELIMINAR" and is_factura and not created:
            archivo_old = old_snap.get("archivo_adjunto")
            archivo_new = new_snap.get("archivo_adjunto")
            file_changed = (archivo_old != archivo_new)

            if file_changed:
                # ¿Cambió solo el archivo?
                changed_keys = [k for k in new_snap.keys() if old_snap.get(k) != new_snap.get(k)]
                other_changes = [k for k in changed_keys if k != "archivo_adjunto"]

                file_action_nombre = "ADJUNTAR" if archivo_new else "QUITAR_ADJUNTO"

                if not other_changes:
                    # Solo cambió el archivo → reemplaza EDITAR por ADJUNTAR/QUITAR_ADJUNTO
                    tipo_nombre = file_action_nombre
                    descripcion = (
                        f"Se adjuntó archivo a Factura #{instance.pk}"
                        if archivo_new else
                        f"Se quitó adjunto de Factura #{instance.pk}"
                    )
                    old_for_base = {"archivo_adjunto": archivo_old}
                    new_for_base = {"archivo_adjunto": archivo_new}
                else:
                    # Hubo más cambios además del archivo → registramos EDITAR y un 2º evento específico
                    extra_file_event = True

        # 5) Registro base
        tipo_base = _get_or_create_tipo(tipo_nombre, emp_id)
        Registro.objects.create(
            tipo_registro=tipo_base,
            descripcion=descripcion,
            usuario=empleado_autor,
            id_empresa_id=emp_id,
            content_type=ContentType.objects.get_for_model(sender),
            object_id=instance.pk,
            datos_anteriores=old_for_base,
            datos_nuevos=new_for_base,
        )

        # 6) Registro extra por adjunto (si hubo cambios además del archivo)
        if extra_file_event and file_action_nombre:
            tipo_file = _get_or_create_tipo(file_action_nombre, emp_id)
            Registro.objects.create(
                tipo_registro=tipo_file,
                descripcion=(
                    f"Se adjuntó archivo a Factura #{instance.pk}"
                    if archivo_new else
                    f"Se quitó adjunto de Factura #{instance.pk}"
                ),
                usuario=empleado_autor,
                id_empresa_id=emp_id,
                content_type=ContentType.objects.get_for_model(sender),
                object_id=instance.pk,
                datos_anteriores={"archivo_adjunto": archivo_old},
                datos_nuevos={"archivo_adjunto": archivo_new},
            )

    except Exception as e:
        # No bloquear la operación principal por fallas de auditoría
        print("[AUDIT][post_save] error:", e)

@receiver(post_delete)
def audit_post_delete_all(sender, instance, **kwargs):
    if sender in IGNORED_SENDERS or kwargs.get("raw") or not _audit_tables_ready():
        return

    try:
        empleado_autor = _resolve_empleado_from_request_user()
        empresa_obj_or_id = _resolve_empresa(instance)
        emp_id = _as_fk_id(empresa_obj_or_id) or getattr(empleado_autor, "id_empresa_id", None)

        tipo = _get_or_create_tipo("ELIMINAR", emp_id)

        Registro.objects.create(
            tipo_registro=tipo,
            descripcion=f"Se eliminó {sender._meta.verbose_name.title()} #{instance.pk}",
            usuario=empleado_autor,
            id_empresa_id=emp_id,  # <<<<<< clave: asignar por *_id
            content_type=ContentType.objects.get_for_model(sender),
            object_id=instance.pk,
            datos_anteriores=_safe_snapshot(instance),
            datos_nuevos=None,
        )
    except Exception as e:
        print("[AUDIT][post_delete] error:", e)

###################################################################################################################
###################################################################################################################