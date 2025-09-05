# productos/signals.py

from __future__ import annotations

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

# Ajusta este import a donde tengas definidos los modelos
# Si los tienes en models.py, usa: from .models import Equipo, HistorialEquipos
from .models_inventario import Equipo, HistorialEquipos


def _empleado_empresa_dep(empleado):
    """
    Devuelve (empresa, departamento) desde el empleado o (None, None) si no hay.
    En tu BD los campos se llaman id_empresa / id_departamento (FK not null).
    """
    if not empleado:
        return None, None
    return getattr(empleado, "id_empresa", None), getattr(empleado, "id_departamento", None)

def _equipo_empresa_dep(instance, prev=None):
    # 1) si el equipo ya tiene empresa/depto, usar esos
    emp = getattr(instance, "id_empresa", None)
    dep = getattr(instance, "id_departamento", None)
    if emp or dep:
        return emp, dep
    # 2) sino, derivar del responsable actual o del previo
    emp_a, dep_a = _empleado_empresa_dep(getattr(instance, "id_empleado", None))
    if emp_a or dep_a:
        return emp_a, dep_a
    if prev:
        return _empleado_empresa_dep(getattr(prev, "id_empleado", None))
    return None, None


@receiver(pre_save, sender=Equipo)
def equipo_pre_save(sender, instance: Equipo, **kwargs):
    """
    Guarda un snapshot previo en instance._prev para comparar en post_save.
    Si es create, _prev queda en None.
    """
    if instance.pk:
        try:
            instance._prev = sender.objects.select_related(
                "id_empleado",
                "id_estado_equipo",
            ).get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._prev = None
    else:
        instance._prev = None


@receiver(post_save, sender=Equipo)
def equipo_post_save(sender, instance: Equipo, created: bool, **kwargs):
    """
    Crea un registro en HistorialEquipos:
    - Alta: estado_nuevo, responsable_anterior = NULL (UI muestra "Nuevo").
    - Update: solo si cambia estado o responsable.
    """
    prev: Equipo | None = getattr(instance, "_prev", None)

    # Usuario (empleado) que hizo el cambio: debe setearse en las vistas
    # con: form.instance._usuario_actual = request.user.empleado
    usuario_actual = getattr(instance, "_usuario_actual", None)

    # Empresa/Depto del responsable actual (o del previo si no hay actual)
    #empresa_actual, dep_actual = _empleado_empresa_dep(getattr(instance, "id_empleado", None))
    empresa_actual, dep_actual = _equipo_empresa_dep(instance, prev)

    empresa_prev, dep_prev = _empleado_empresa_dep(getattr(prev, "id_empleado", None) if prev else None)

    # Campos base del historial
    base = dict(
        equipo=instance,
        etiqueta=getattr(instance, "etiqueta", "") or "",
        nombre_equipo=getattr(instance, "nombre_equipo", "") or "",
        tipo_equipo=getattr(instance, "id_tipo_equipo", None) if hasattr(instance, "id_tipo_equipo") else None,
        usuario=getattr(instance, "_usuario_actual", None),
        empresa=empresa_actual,
        departamento=dep_actual,
        responsable_actual=getattr(instance, "id_empleado", None),
        fecha=timezone.now(),
    )

    # Alta
    if created:
        HistorialEquipos.objects.create(
            estado_anterior=None,
            estado_nuevo=getattr(instance, "id_estado_equipo", None),
            # responsable_anterior = NULL -> en la UI se muestra "Nuevo"
            **base,
        )
        return

    # Nada que comparar
    if not prev:
        return

    # Detectar cambios relevantes
    prev_estado_id = getattr(prev, "id_estado_equipo_id", None)
    new_estado_id = getattr(instance, "id_estado_equipo_id", None)
    prev_resp_id = getattr(prev, "id_empleado_id", None)
    new_resp_id = getattr(instance, "id_empleado_id", None)

    estado_cambia = prev_estado_id != new_estado_id
    resp_cambia = prev_resp_id != new_resp_id

    if not (estado_cambia or resp_cambia):
        return  # No registramos cambios cosméticos

    HistorialEquipos.objects.create(
        estado_anterior=getattr(prev, "id_estado_equipo", None),
        estado_nuevo=getattr(instance, "id_estado_equipo", None),
        responsable_anterior_fk_id=getattr(prev, "id_empleado_id", None),  # << clave
        **base,
    )

