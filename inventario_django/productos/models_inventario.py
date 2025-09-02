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
    etiqueta = models.CharField(max_length=50, blank=True, null=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # primero guarda para tener id
        from .utils import generar_qr
        if self.etiqueta and not self.qr_code:
            generar_qr(self)

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


class EstadoMantencion(models.Model):
    id_estado_mantencion = models.AutoField(primary_key=True)
    tipo = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'estado_mantencion'

    def __str__(self):
        return self.tipo


class Mantencion(models.Model):
    id_mantencion = models.AutoField(primary_key=True)
    id_equipo = models.ForeignKey(Equipo, models.DO_NOTHING, db_column='id_equipo')
    id_estado_mantencion = models.ForeignKey(EstadoMantencion, models.DO_NOTHING, db_column='id_estado_mantencion')
    fecha = models.DateField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mantencion'

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
