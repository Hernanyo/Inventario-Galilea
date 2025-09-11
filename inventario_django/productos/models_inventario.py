# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
# productos/__init__.py
# ✅ CORRECTO:
from django.db import models
from django.utils import timezone




class Empresa(models.Model):
    id_empresa = models.AutoField(primary_key=True)
    rut_empresa = models.CharField(unique=True, max_length=20)
    nombre_empresa = models.CharField(max_length=200)
    direccion_empresa = models.CharField(max_length=250, blank=True, null=True)
    giro = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'empresa'

    def __str__(self):
        return self.nombre_empresa


class Departamento(models.Model):
    id_departamento = models.AutoField(primary_key=True)
    nombre_departamento = models.CharField(max_length=150)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')

    class Meta:
        managed = False
        db_table = 'departamento'
        unique_together = (('id_empresa', 'nombre_departamento'),)

    def __str__(self):
        # Muestra el nombre y la empresa entre paréntesis
        return f"{self.nombre_departamento} ({self.id_empresa})"


class Empleado(models.Model):
    id_empleado = models.AutoField(primary_key=True)
    rut = models.CharField(unique=True, max_length=20)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    activo = models.BooleanField()
    cargo = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')
    id_departamento = models.ForeignKey(Departamento, models.DO_NOTHING, db_column='id_departamento')
    # Campo nuevo para roles
    rol = models.CharField(max_length=20, default='usuario')  # admin, usuario, invitado
    user = models.OneToOneField(
        "auth.User",
        models.DO_NOTHING,
        db_column="user_id",
        blank=True, null=True,
        related_name="empleado",
    )


    class Meta:
        managed = False
        db_table = 'empleado'

    def __str__(self):
        ap_m = self.apellido_materno or ""
        return f"{self.nombre} {self.apellido_paterno} {ap_m}".strip()


class Marca(models.Model):
    id_marca = models.AutoField(primary_key=True)
    nombre_marca = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'marca'

    def __str__(self):
        return self.nombre_marca


class EstadoEquipo(models.Model):
    id_estado_equipo = models.AutoField(primary_key=True)
    descripcion = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'estado_equipo'

    def __str__(self):
        return self.descripcion


class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    nombre_proveedor = models.CharField(max_length=200)
    rut_proveedor = models.CharField(unique=True, max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'proveedor'
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre_proveedor


class TipoEquipo(models.Model):
    id_tipo_equipo = models.AutoField(primary_key=True)
    tipo_equipo = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'tipo_equipo'

    def __str__(self):
        return self.tipo_equipo


class Equipo(models.Model):
    id_equipo = models.AutoField(primary_key=True)
    nombre_equipo = models.CharField(max_length=150)
    id_marca = models.ForeignKey(Marca, models.DO_NOTHING, db_column='id_marca')
    id_tipo_equipo = models.ForeignKey(TipoEquipo, models.DO_NOTHING, db_column='id_tipo_equipo')
    id_estado_equipo = models.ForeignKey(EstadoEquipo, models.DO_NOTHING, db_column='id_estado_equipo', blank=True, null=True)
    id_empleado = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)
    id_proveedor = models.ForeignKey(Proveedor, models.DO_NOTHING, db_column='id_proveedor', blank=True, null=True)
    etiqueta = models.CharField(max_length=150, unique=True)
    qr_code = models.ImageField(upload_to='qrcodes/', max_length=1000, blank=True, null=True)
     # >>> NUEVOS CAMPOS <<<
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='empresa_id', blank=True, null=True)
    id_departamento = models.ForeignKey(Departamento, models.DO_NOTHING, db_column='departamento_id', blank=True, null=True)


    def save(self, *args, **kwargs):
        from .utils import generar_qr

        # Autorellenar empresa/depto desde el empleado si faltan
        if self.id_empleado:
            if self.id_empresa is None:
                self.id_empresa = getattr(self.id_empleado, "id_empresa", None)
            if self.id_departamento is None:
                self.id_departamento = getattr(self.id_empleado, "id_departamento", None)

        is_new = self._state.adding
        super().save(*args, **kwargs)  # guarda primero para tener ID

        if is_new and self.etiqueta and not self.qr_code:
            generar_qr(self)
            super().save(update_fields=["qr_code"])




    class Meta:
        managed = False
        db_table = 'equipo'

    def __str__(self):
        # Nombre + marca + tipo para que sea fácil identificarlo
        return f"{self.nombre_equipo} - {self.id_marca} / {self.id_tipo_equipo}"


class AtributosEquipo(models.Model):
    id_atributo_equipo = models.AutoField(primary_key=True)
    id_tipo_equipo = models.ForeignKey(TipoEquipo, models.DO_NOTHING, db_column='id_tipo_equipo')
    atributo = models.CharField(max_length=100)
    valor = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'atributos_equipo'
        unique_together = (('id_tipo_equipo', 'atributo'),)

    def __str__(self):
        # Ej: "Notebook · RAM = 16GB"
        v = f" = {self.valor}" if self.valor else ""
        return f"{self.id_tipo_equipo} · {self.atributo}{v}"
    ##
    ##
    ## Nueva clase atributos por tipo de equipos

class AgregacionAtributosPorEquipo(models.Model):
    id = models.AutoField(primary_key=True)
    equipo = models.ForeignKey(Equipo, models.DO_NOTHING, db_column='id_equipo')
    atributo = models.ForeignKey(AtributosEquipo, models.DO_NOTHING, db_column='id_atributo_equipo')
    valor = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        managed = False  # tabla creada en BD
        db_table = 'inventario"."agregacion_atributos_por_equipo'
        unique_together = (('equipo', 'atributo'),)
        verbose_name = "Valor de atributo por equipo"
        verbose_name_plural = "Valores de atributos por equipo"

    def __str__(self):
        nombre_attr = getattr(self.atributo, "atributo", "Atributo")
        return f"{self.equipo_id} · {nombre_attr} = {self.valor or '—'}"



class EstadoMantencion(models.Model):
    id_estado_mantencion = models.AutoField(primary_key=True)
    tipo = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_mantencion'

    def __str__(self):
        return self.tipo
    
class TipoMantencion(models.Model):
    id_tipo_mantencion = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = "tipo_mantencion"
        verbose_name = "Tipo de mantención"
        verbose_name_plural = "Tipos de mantención"


    def __str__(self):
        return self.nombre


class PrioridadMantencion(models.Model):
    id_prioridad = models.AutoField(primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = "prioridad_mantencion"
        verbose_name = "Prioridad de mantención"
        verbose_name_plural = "Prioridades de mantención"

    def __str__(self):
        return self.nombre



class Mantencion(models.Model):
    id_mantencion = models.AutoField(primary_key=True)
    id_equipo = models.ForeignKey(Equipo, models.DO_NOTHING, db_column='id_equipo')
    id_estado_mantencion = models.ForeignKey(EstadoMantencion, models.DO_NOTHING, db_column='id_estado_mantencion')
    # NUEVAS FK que existen en tu tabla:
    id_tipo_mantencion = models.ForeignKey(TipoMantencion, models.DO_NOTHING, db_column='id_tipo_mantencion', null=True, blank=True)
    id_prioridad = models.ForeignKey(PrioridadMantencion, models.DO_NOTHING, db_column='id_prioridad', null=True, blank=True)
    fecha = models.DateField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    # NUEVOS (coinciden con SQL)
    responsable = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='responsable_id',
                                    null=True, blank=True, related_name='mantenciones_responsable')
    solicitante_user = models.ForeignKey("auth.User", models.DO_NOTHING, db_column='solicitante_user_id',
                                         null=True, blank=True, related_name='mantenciones_solicitadas')

    class Meta:
        managed = False
        db_table = 'mantencion'
        verbose_name = "Mantención"
        verbose_name_plural = "Mantenciones"

    def __str__(self):
        f = self.fecha.isoformat() if self.fecha else "s/f"
        return f"Mantención {self.id_mantencion} · {self.id_equipo} · {self.id_estado_mantencion} · {f}"


class Factura(models.Model):
    id_factura = models.AutoField(primary_key=True)
    id_proveedor = models.ForeignKey(Proveedor, models.DO_NOTHING, db_column='id_proveedor', blank=True, null=True)
    fecha_emision = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'factura'

    def __str__(self):
        prov = self.id_proveedor or "Proveedor s/i"
        f = self.fecha_emision.isoformat() if self.fecha_emision else "s/f"
        return f"Factura {self.id_factura} · {prov} · {f}"


class DetalleFactura(models.Model):
    id_detalle_factura = models.AutoField(primary_key=True)
    id_factura = models.ForeignKey(Factura, models.DO_NOTHING, db_column='id_factura')
    id_equipo = models.ForeignKey(Equipo, models.DO_NOTHING, db_column='id_equipo', blank=True, null=True)
    nombre_equipo = models.CharField(max_length=150, blank=True, null=True)
    cantidad = models.IntegerField()
    valor_unitario = models.IntegerField()
    valor_neto = models.IntegerField(blank=True, null=True)
    iva = models.IntegerField(blank=True, null=True)
    valor_total = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'detalle_factura'

    def __str__(self):
        item = self.nombre_equipo or (self.id_equipo and str(self.id_equipo)) or "Item s/i"
        return f"Detalle {self.id_detalle_factura} · Factura {self.id_factura_id} · {item}"
    

class HistorialEquipos(models.Model):
    id = models.AutoField(primary_key=True)
    equipo = models.ForeignKey(Equipo, models.DO_NOTHING, db_column='equipo_id')
    etiqueta = models.CharField(max_length=150, blank=True, null=True)
    nombre_equipo = models.CharField(max_length=150, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    tipo_equipo = models.ForeignKey(TipoEquipo, models.DO_NOTHING, db_column='tipo_equipo_id', blank=True, null=True)
    accion = models.CharField(max_length=50)  # "agregado", "asignado", "bodega", "dañado", "perdido", etc.
    usuario = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='usuario_id', blank=True, null=True)
    fecha = models.DateTimeField(default=timezone.now)
    empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='empresa_id', blank=True, null=True)
    departamento = models.ForeignKey(Departamento, models.DO_NOTHING, db_column='departamento_id', blank=True, null=True)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    estado_anterior = models.ForeignKey(EstadoEquipo, models.DO_NOTHING, db_column='estado_anterior_id', blank=True, null=True, related_name='estado_anterior')
    estado_nuevo = models.ForeignKey(EstadoEquipo, models.DO_NOTHING, db_column='estado_nuevo_id', blank=True, null=True, related_name='estado_nuevo')
    responsable_actual = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='responsable_actual_id', blank=True, null=True, related_name='responsable_actual')
    comentario = models.TextField(blank=True, null=True)

    # >>> NUEVO CAMPO (persistido) <<<
    responsable_anterior_fk = models.ForeignKey(
        "Empleado",
        null=True, blank=True,
        db_column="responsable_anterior_id",   # enlaza con la columna creada en PostgreSQL
        on_delete=models.SET_NULL,
        related_name="historial_responsable_anterior",
    )

    @property
    def responsable_anterior(self):
        """
        Devuelve el Empleado 'responsable anterior' si quedó guardado en comentario
        con el formato: RESP_ANT=<id>. Si no existe, retorna None.
        (Se mantiene por compatibilidad con tu UI actual.)
        """
        if getattr(self, "responsable_anterior_fk_id", None):
            return self.responsable_anterior_fk
        from .models_inventario import Empleado  # import local para evitar ciclos
        if not self.comentario:
            return None

        marker = "RESP_ANT="
        idx = str(self.comentario).find(marker)
        if idx == -1:
            return None
        try:
            tail = self.comentario[idx + len(marker):].strip()
            id_txt = ""
            for ch in tail:
                if ch.isdigit():
                    id_txt += ch
                else:
                    break
            if not id_txt:
                return None
            emp_id = int(id_txt)
            return Empleado.objects.filter(pk=emp_id).first()
        except Exception:
            return None

    class Meta:
        managed = False
        db_table = 'historial_equipos'
        ordering = ['-fecha']

    def __str__(self):
        eq = getattr(self, "equipo", None)
        return f"Historial #{self.pk} · {eq or '—'} · {self.fecha}"


# --- Nuevo:Historial de Mantenciones ---
# --- Historial de Mantenciones (VIEW) ---

class HistorialMantenciones(models.Model):
    id_historial = models.IntegerField(primary_key=True)
    id_mantencion = models.IntegerField()
    fecha_evento = models.DateTimeField()
    accion = models.CharField(max_length=50)
    detalle = models.TextField(null=True, blank=True)
    usuario_app_username = models.CharField(max_length=150, null=True, blank=True)

    # Datos enriquecidos que expone la VIEW
    id_equipo = models.IntegerField(null=True, blank=True)
    etiqueta = models.CharField(max_length=150, null=True, blank=True)
    equipo_nombre = models.CharField(max_length=150, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)

    tipo_mantencion = models.CharField(max_length=50, null=True, blank=True)
    prioridad = models.CharField(max_length=50, null=True, blank=True)
    estado_actual = models.CharField(max_length=50, null=True, blank=True)

    responsable_nombre = models.CharField(max_length=255, null=True, blank=True)
    solicitante_nombre = models.CharField(max_length=255, null=True, blank=True)

    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)

    @property
    def asignado_a(self) -> str:
        # Mostrar responsable si viene en la vista; si no, vacío
        return (self.responsable_nombre or "").strip()

    class Meta:
        managed = False
        db_table = "vw_historial_mantenciones"   # usa la VIEW, no crees tabla
        verbose_name = "Historial de Mantenciones"
        verbose_name_plural = "Historial de Mantenciones"
        default_permissions = ("view",)

    def __str__(self):
        return f"[{self.id_mantencion}] {self.accion} @ {self.fecha_evento:%Y-%m-%d %H:%M}"
####################################################################################################
#nueva clase para mantenimiento

class HistorialMantencionesLog(models.Model):
    id_evento = models.BigAutoField(primary_key=True)
    id_mantencion = models.IntegerField()
    fecha_evento = models.DateTimeField()
    accion = models.CharField(max_length=30)
    detalle = models.TextField(blank=True, default="")
    usuario_app_username = models.CharField(max_length=150, null=True, blank=True)

    # snapshot
    id_equipo = models.IntegerField(null=True, blank=True)
    etiqueta = models.CharField(max_length=150, null=True, blank=True)
    equipo_nombre = models.CharField(max_length=150, null=True, blank=True)

    tipo_mantencion = models.CharField(max_length=50, null=True, blank=True)
    prioridad = models.CharField(max_length=50, null=True, blank=True)
    estado_actual = models.CharField(max_length=50, null=True, blank=True)

    responsable_nombre = models.TextField(null=True, blank=True)
    solicitante_nombre = models.TextField(null=True, blank=True)

    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        managed = False  # la tabla ya existe en la BD
        db_table = 'inventario"."historial_mantenciones_log'
        verbose_name = "Historial de mantenciones (log)"
        verbose_name_plural = "Historial de mantenciones (log)"

    def __str__(self):
        return f"[{self.fecha_evento:%Y-%m-%d %H:%M}] M#{self.id_mantencion} · {self.accion}"

    @property
    def asignado_a(self) -> str:
        return (self.responsable_nombre or self.solicitante_nombre or "").strip()