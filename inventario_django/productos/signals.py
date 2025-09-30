# productos/signals.py
from __future__ import annotations


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models_inventario import Empleado
from .utils import sync_user_groups_for_empleado, crear_usuario_y_enviar_correo

# productos/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models_inventario import Empleado
from .utils import ensure_auth_user_for_empleado, sync_user_groups_for_empleado, send_password_set_link



from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models_inventario import Activo, HistorialActivos


def _empleado_empresa_dep(empleado):
    if not empleado:
        return None, None
    return getattr(empleado, "id_empresa", None), getattr(empleado, "id_departamento", None)

def _activo_empresa_dep(instance, prev=None):
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
    """Guarda snapshot previo para comparar en post_save."""
    if instance.pk:
        try:
            instance._prev = sender.objects.select_related(
                "id_empleado", "id_estado_activo"
            ).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._prev = None
    else:
        instance._prev = None


@receiver(post_save, sender=Activo)
def activo_post_save(sender, instance: Activo, created: bool, **kwargs):
    """
    Historial por alta/cambio de estado/responsable.
    (Observaciones se maneja en receivers aparte más abajo.)
    """
    prev: Activo | None = getattr(instance, "_prev", None)
    usuario_actual = getattr(instance, "_usuario_actual", None)

    empresa_actual, dep_actual = _activo_empresa_dep(instance, prev)

    base = dict(
        activo=instance,
        etiqueta=getattr(instance, "etiqueta", "") or "",
        nombre_activo=getattr(instance, "nombre_activo", "") or "",
        tipo_activo=getattr(instance, "id_tipo_activo", None) if hasattr(instance, "id_tipo_activo") else None,
        usuario=usuario_actual,
        empresa=empresa_actual,          # 👈 usa 'empresa', no 'id_empresa'
        departamento=dep_actual,         # 👈 idem
        responsable_actual=getattr(instance, "id_empleado", None),
        fecha=timezone.now(),
    )

    if created:
        HistorialActivos.objects.create(
            estado_anterior=None,
            estado_nuevo=getattr(instance, "id_estado_activo", None),
            **base,
        )
        return

    if not prev:
        return

    prev_estado_id = getattr(prev, "id_estado_activo_id", None)
    new_estado_id  = getattr(instance, "id_estado_activo_id", None)
    prev_resp_id   = getattr(prev, "id_empleado_id", None)
    new_resp_id    = getattr(instance, "id_empleado_id", None)

    estado_cambia = prev_estado_id != new_estado_id
    resp_cambia   = prev_resp_id  != new_resp_id

    if not (estado_cambia or resp_cambia):
        return

    HistorialActivos.objects.create(
        estado_anterior=getattr(prev, "id_estado_activo", None),
        estado_nuevo=getattr(instance, "id_estado_activo", None),
        responsable_anterior_fk_id=getattr(prev, "id_empleado_id", None),
        **base,
    )


# ---------- Observaciones ----------

def _historial_snapshot_observaciones(activo: Activo, comentario: str, usuario=None):
    """
    Inserta un registro de OBSERVACIONES (estado anterior = nuevo).
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
    # Si se crea un empleado con correo y sin user → crea user + envía link
    if created and instance.correo and not instance.user:
        crear_usuario_y_enviar_correo(instance)

    # Mantener grupos según rol siempre que exista user
    try:
        sync_user_groups_for_empleado(instance)
    except Exception:
        # evita romper guardado si aún no están los grupos al boot
        pass