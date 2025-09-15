# productos/signals.py
from __future__ import annotations

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from .models_inventario import Equipo, HistorialEquipos


def _empleado_empresa_dep(empleado):
    if not empleado:
        return None, None
    return getattr(empleado, "id_empresa", None), getattr(empleado, "id_departamento", None)

def _equipo_empresa_dep(instance, prev=None):
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


@receiver(pre_save, sender=Equipo)
def equipo_pre_save(sender, instance: Equipo, **kwargs):
    """Guarda snapshot previo para comparar en post_save."""
    if instance.pk:
        try:
            instance._prev = sender.objects.select_related(
                "id_empleado", "id_estado_equipo"
            ).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._prev = None
    else:
        instance._prev = None


@receiver(post_save, sender=Equipo)
def equipo_post_save(sender, instance: Equipo, created: bool, **kwargs):
    """
    Historial por alta/cambio de estado/responsable.
    (Observaciones se maneja en receivers aparte más abajo.)
    """
    prev: Equipo | None = getattr(instance, "_prev", None)
    usuario_actual = getattr(instance, "_usuario_actual", None)

    empresa_actual, dep_actual = _equipo_empresa_dep(instance, prev)

    base = dict(
        equipo=instance,
        etiqueta=getattr(instance, "etiqueta", "") or "",
        nombre_equipo=getattr(instance, "nombre_equipo", "") or "",
        tipo_equipo=getattr(instance, "id_tipo_equipo", None) if hasattr(instance, "id_tipo_equipo") else None,
        usuario=usuario_actual,
        empresa=empresa_actual,          # 👈 usa 'empresa', no 'id_empresa'
        departamento=dep_actual,         # 👈 idem
        responsable_actual=getattr(instance, "id_empleado", None),
        fecha=timezone.now(),
    )

    if created:
        HistorialEquipos.objects.create(
            estado_anterior=None,
            estado_nuevo=getattr(instance, "id_estado_equipo", None),
            **base,
        )
        return

    if not prev:
        return

    prev_estado_id = getattr(prev, "id_estado_equipo_id", None)
    new_estado_id  = getattr(instance, "id_estado_equipo_id", None)
    prev_resp_id   = getattr(prev, "id_empleado_id", None)
    new_resp_id    = getattr(instance, "id_empleado_id", None)

    estado_cambia = prev_estado_id != new_estado_id
    resp_cambia   = prev_resp_id  != new_resp_id

    if not (estado_cambia or resp_cambia):
        return

    HistorialEquipos.objects.create(
        estado_anterior=getattr(prev, "id_estado_equipo", None),
        estado_nuevo=getattr(instance, "id_estado_equipo", None),
        responsable_anterior_fk_id=getattr(prev, "id_empleado_id", None),
        **base,
    )


# ---------- Observaciones ----------

def _historial_snapshot_observaciones(equipo: Equipo, comentario: str, usuario=None):
    """
    Inserta un registro de OBSERVACIONES (estado anterior = nuevo).
    """
    try:
        HistorialEquipos.objects.create(
            equipo=equipo,
            etiqueta=getattr(equipo, "etiqueta", None),
            nombre_equipo=getattr(equipo, "nombre_equipo", None),
            fecha=timezone.now(),
            responsable_anterior_fk=getattr(equipo, "id_empleado", None),
            estado_anterior=getattr(equipo, "id_estado_equipo", None),
            estado_nuevo=getattr(equipo, "id_estado_equipo", None),
            responsable_actual=getattr(equipo, "id_empleado", None),
            empresa=getattr(equipo, "id_empresa", None),       # 👈 consistencia con 'base'
            departamento=getattr(equipo, "id_departamento", None),
            usuario=usuario,                                    # 👈 guarda quién hizo el cambio
            accion="OBSERVACIONES",
            tipo_equipo=getattr(equipo, "id_tipo_equipo", None),
            comentario = (comentario or "")[:2000],
        )

    except Exception as e:
        # Para depurar si algo vuelve a fallar
        print("[HistorialEquipos][OBSERVACIONES] error:", e)



@receiver(pre_save, sender=Equipo)
def _equipo_detectar_cambio_observaciones(sender, instance: Equipo, **kwargs):
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


@receiver(post_save, sender=Equipo)
def _equipo_log_cambio_observaciones(sender, instance: Equipo, created: bool, **kwargs):
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