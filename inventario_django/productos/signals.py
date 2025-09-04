from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models_inventario import Equipo, HistorialEquipos

def _get_prev(instance):
    try:
        return Equipo.objects.get(pk=instance.pk)
    except Equipo.DoesNotExist:
        return None

@receiver(pre_save, sender=Equipo)
def equipo_pre_save(sender, instance: Equipo, **kwargs):
    # Guarda snapshot previo para comparar en post_save
    instance._prev = _get_prev(instance)

@receiver(post_save, sender=Equipo)
def equipo_post_save(sender, instance: Equipo, created: bool, **kwargs):
    prev: Equipo | None = getattr(instance, "_prev", None)
    usuario_actual = getattr(instance, "_usuario_actual", None)  # lo setean tus vistas Create/Update

    base = dict(
        equipo=instance,
        etiqueta=instance.etiqueta or "",
        nombre_equipo=instance.nombre_equipo or "",
        tipo_equipo=getattr(instance, "id_tipo_equipo", None),
        usuario=usuario_actual,                      # Empleado que realizó el cambio (si viene desde la vista)
        empresa=None,
        departamento=None,
        responsable_actual=instance.id_empleado,     # responsable actual (nuevo)
        fecha=timezone.now(),
    )

    # Alta (creación): una sola fila
    if created:
        HistorialEquipos.objects.create(
            accion="agregado",
            estado_anterior=None,
            estado_nuevo=instance.id_estado_equipo,
            comentario="",
            **base,
        )
        return

    if not prev:
        return

    # ¿Qué cambió?
    cambio_estado = prev.id_estado_equipo_id != instance.id_estado_equipo_id
    cambio_resp   = prev.id_empleado_id      != instance.id_empleado_id

    # Si no cambió ni estado ni responsable, no registres nada
    if not cambio_estado and not cambio_resp:
        return

    # Comentario con responsable anterior, si aplica
    comentario = ""
    if cambio_resp and prev.id_empleado_id:
        comentario = f"RESP_ANT={prev.id_empleado_id}"

    # UNA SOLA FILA con toda la info
    HistorialEquipos.objects.create(
        accion="actualización",  # no se muestra en tu lista, pero queda como referencia
        estado_anterior=prev.id_estado_equipo if cambio_estado else prev.id_estado_equipo,
        estado_nuevo=instance.id_estado_equipo if cambio_estado else instance.id_estado_equipo,
        comentario=comentario,
        **base,
    )
