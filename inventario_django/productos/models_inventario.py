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
from django.db import models
from django.contrib.auth.models import User
import json
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import RegexValidator
# imports útiles al inicio del archivo
import os
from uuid import uuid4
from django.utils.text import slugify
# --- Planes de Mantención ----------------------------------------------------
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe





class Empresa(models.Model):
    """Empresa de la organización.

    - PK: `id_empresa`
    - Único: `rut_empresa`
    - Borrado lógico: `eliminado`
    - Tabla: `empresa` (managed=True)

    Devuelve `nombre_empresa` en `__str__`.
    """
    #id_empresa = models.AutoField(primary_key=True) ####################################2609
    id_empresa = models.AutoField(primary_key=True, db_column="id_empresa")
    rut_empresa = models.CharField(unique=True, max_length=20)
    nombre_empresa = models.CharField(max_length=200)
    direccion_empresa = models.CharField(max_length=250, blank=True, null=True)
    giro = models.CharField(max_length=100, blank=True, null=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True ############################################################2609
        db_table = 'empresa'

    def __str__(self):
        return self.nombre_empresa


class Departamento(models.Model):
    """Departamento interno de una empresa.

    - PK: `id_departamento`
    - FK: `id_empresa → Empresa`
    - Único por empresa: (`id_empresa`, `nombre_departamento`)
    - Borrado lógico: `eliminado`
    - Tabla: `departamento`

    `__str__` muestra "nombre (empresa)".
    """
    #id_departamento = models.AutoField(primary_key=True)
    id_departamento = models.AutoField(primary_key=True, db_column="id_departamento")
    nombre_departamento = models.CharField(max_length=150)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'departamento'
        unique_together = (('id_empresa', 'nombre_departamento'),)

    def __str__(self):
        # Muestra el nombre y la empresa entre paréntesis
        return f"{self.nombre_departamento} ({self.id_empresa})"
    
# Define primero la clase Ubicacion
class Ubicacion(models.Model):
    """Tabla de ubicaciones asociadas a empleados."""
    id_ubicacion = models.AutoField(primary_key=True, db_column="id_ubicacion")
    id_empresa = models.ForeignKey('Empresa', on_delete=models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    nombre_ubicacion = models.CharField(max_length=255, verbose_name="Nombre de la Ubicación")
    direccion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'ubicacion'
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"  # Cambiar el nombre plural aquí

    def __str__(self):
        return self.nombre_ubicacion

class Cargo(models.Model):
    id_cargo = models.AutoField(primary_key=True, db_column="id_cargo")
    id_empresa = models.ForeignKey('Empresa', on_delete=models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    nombre_cargo = models.CharField(max_length=255, verbose_name="Nombre del Cargo")
    descripcion = models.TextField(blank=True, null=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'cargo'
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ["nombre_cargo"]
        unique_together = (('id_empresa', 'nombre_cargo'),)

    def __str__(self):
        return self.nombre_cargo



class Empleado(models.Model):
    """Empleado de la empresa, con rol, ubicación y vínculo opcional a usuario de Django.

    - PK: `id_empleado`
    - Único: `rut`, `correo` (opcional)
    - FKs: `id_empresa → Empresa`, `id_departamento → Departamento`
    - OneToOne: `user → auth.User` (opcional)
    - Campo de rol: `rol` (p.ej., admin/usuario/invitado)
    - Borrado lógico: `eliminado`
    - Tabla: `empleado`

    `__str__` devuelve nombre completo legible.
    """
    #id_empleado = models.AutoField(primary_key=True)
    id_empleado = models.AutoField(primary_key=True, db_column="id_empleado")

    rut = models.CharField(unique=True, max_length=20)
    nombre = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100, blank=True, null=True)
    estado_activo = models.BooleanField()
    cargo = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa')
    id_departamento = models.ForeignKey(Departamento, models.DO_NOTHING, db_column='id_departamento')
    # Campo nuevo para roles
    rol = models.CharField(max_length=20, default='usuario')  # admin, usuario, invitado
    user = models.OneToOneField("auth.User",models.DO_NOTHING, db_column="user_id", blank=True, null=True, related_name="empleado",)
    correo = models.CharField(max_length=255, unique=True, blank=True, null=True)  # <-- NUEVO
    eliminado = models.BooleanField(default=False)
    ubicacion = models.ForeignKey('Ubicacion', on_delete=models.SET_NULL, null=True, blank=True)  # Relación con Ubicación



    class Meta:
        managed = True
        db_table = 'empleado'

    def __str__(self):
        ap_m = self.apellido_materno or ""
        return f"{self.nombre} {self.apellido_paterno} {ap_m}".strip()


class Marca(models.Model):
    """Catálogo de marcas de activos.

    - PK: `id_marca`
    - FK: `id_empresa → Empresa` (opcional)
    - Único por empresa: (`id_empresa`, `nombre_marca`)
    - Borrado lógico: `eliminado`
    - Tabla: `marca`
    """
    #id_marca = models.AutoField(primary_key=True)
    id_marca = models.AutoField(primary_key=True, db_column="id_marca")
    nombre_marca = models.CharField(max_length=100)
    id_empresa = models.ForeignKey('Empresa', models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'marca'
        unique_together = (('id_empresa', 'nombre_marca'),)

    def __str__(self):
        return self.nombre_marca


class EstadoActivo(models.Model):
    """Estado de un activo (p.ej., operativo, en reparación, dado de baja).

    - PK: `id_estado_activo`
    - FK: `id_empresa → Empresa` (opcional)
    - Único por empresa: (`id_empresa`, `descripcion`)
    - Borrado lógico: `eliminado`
    - Tabla: `estado_activo`
    - Verbose: "Estado(s) de activo"

    `__str__` devuelve `descripcion`.
    """
    #id_estado_activo = models.AutoField(primary_key=True)
    id_estado_activo = models.AutoField(primary_key=True, db_column="id_estado_activo")
    descripcion = models.CharField(max_length=100)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'estado_activo'
        unique_together = (('id_empresa', 'descripcion'),)
        verbose_name = "Estado de activo"
        verbose_name_plural = "Estados de activo"

    def __str__(self):
        return self.descripcion


class CondicionActivo(models.Model):
    """
    Condición física/lógica del activo (Nuevo, Defectuoso, Perdido, etc.)
    - PK: id_condicion_activo
    - Único por empresa: (id_empresa, descripcion)
    """
    id_condicion_activo = models.AutoField(primary_key=True, db_column="id_condicion_activo")
    descripcion = models.CharField(max_length=100)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'condicion_activo'
        unique_together = (('id_empresa', 'descripcion'),)
        verbose_name = "Condición de activo"
        verbose_name_plural = "Condiciones de activo"

    def __str__(self):
        return self.descripcion




class Proveedor(models.Model):
    """Proveedor asociado a compras/facturación.

    - PK: `id_proveedor`
    - FK: `id_empresa → Empresa` (opcional)
    - Único por empresa: (`id_empresa`, `rut_proveedor`)
    - Borrado lógico: `eliminado`
    - Tabla: `proveedor`

    `__str__` devuelve `nombre_proveedor`.
    """
    #id_proveedor = models.AutoField(primary_key=True)
    id_proveedor = models.AutoField(primary_key=True, db_column="id_proveedor")
    nombre_proveedor = models.CharField(max_length=200)
    rut_proveedor = models.CharField(max_length=20, blank=True, null=True)
    id_empresa = models.ForeignKey('Empresa', models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'proveedor'
        unique_together = (('id_empresa', 'rut_proveedor'),)
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

    def __str__(self):
        return self.nombre_proveedor


class TipoActivo(models.Model):
    """Tipo o familia del activo (notebook, impresora, información, etc.).

    - PK: `id_tipo_activo`
    - FK: `id_empresa → Empresa` (opcional)
    - Único por empresa: (`id_empresa`, `tipo_activo`)
    - Borrado lógico: `eliminado`
    - Tabla: `tipo_activo`

    `__str__` devuelve `tipo_activo`.
    """
    #id_tipo_activo = models.AutoField(primary_key=True)
    id_tipo_activo = models.AutoField(primary_key=True, db_column="id_tipo_activo")
    tipo_activo = models.CharField(max_length=100)
    estructura_etiqueta = models.CharField(max_length=10, verbose_name="Prefijo de etiqueta", help_text="Abreviación para etiquetas (ej: NBK, IMP, MON).", blank=True, null=True, validators=[RegexValidator(r'^[A-Za-z0-9]+$', 'Solo letras y números.')])
    id_empresa = models.ForeignKey('Empresa', models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'tipo_activo'
        unique_together = (('id_empresa', 'tipo_activo'), ('id_empresa', 'estructura_etiqueta'), )
        verbose_name = "Tipo de activo"
        verbose_name_plural = "Tipos de activo"
    
    def save(self, *args, **kwargs):
        if self.estructura_etiqueta:
            self.estructura_etiqueta = self.estructura_etiqueta.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tipo_activo

class Modelo(models.Model):
    """Catálogo de modelos de activos disponibles para inventariar."""
    id_modelo = models.AutoField(primary_key=True, db_column="id_modelo")
    nombre_modelo = models.CharField(max_length=100)
    id_empresa = models.ForeignKey('Empresa', models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    id_tipo_activo = models.ForeignKey('TipoActivo', models.DO_NOTHING, db_column='id_tipo_activo', null=True, blank=True)
    id_marca = models.ForeignKey('Marca', models.DO_NOTHING, db_column='id_marca', null=True, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'modelo'
        unique_together = (('id_empresa', 'id_tipo_activo', 'nombre_modelo'),)

    def __str__(self):
        return self.nombre_modelo

class Activo(models.Model):
    """Activo inventariable con asignación, estado, QR y clasificación de seguridad.

    - PK: `id_activo`
    - FKs: `id_marca`, `id_tipo_activo`, `id_estado_activo` (opcional),
            `id_empleado` (responsable opcional), `id_proveedor` (opcional),
            `id_empresa` (opcional), `id_departamento` (opcional)
    - Identificación: `etiqueta` (única)
    - QR: `qr_code` (se genera automáticamente en alta si hay `etiqueta`)
    - Seguridad/criticidad: `activo_critico`, `clasificacion`,
            `confidencialidad`, `integridad`, `disponibilidad` (1..4)
    - Borrado lógico: `eliminado`
    - Tabla: `activo`
    - Propiedad de compatibilidad: `empresa` (alias de `id_empresa`)

    Lógica en `save()`:
    - Autocompleta `id_empresa`/`id_departamento` desde `id_empleado` si faltan.
    - Genera QR con `utils.generar_qr()` en creación cuando aplique.

    `__str__` muestra "nombre - marca / tipo".
    """
    #id_activo = models.AutoField(primary_key=True)
    id_activo = models.AutoField(primary_key=True, db_column="id_activo")
    nombre_activo = models.CharField(max_length=150)
    id_marca = models.ForeignKey(Marca, models.DO_NOTHING, db_column='id_marca')
    id_tipo_activo = models.ForeignKey(TipoActivo, models.DO_NOTHING, db_column='id_tipo_activo')
    id_estado_activo = models.ForeignKey(EstadoActivo, models.DO_NOTHING, db_column='id_estado_activo', blank=True, null=True)
    id_empleado = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='id_empleado', blank=True, null=True)
    id_proveedor = models.ForeignKey(Proveedor, models.DO_NOTHING, db_column='id_proveedor', blank=True, null=True)
    etiqueta = models.CharField(max_length=150, unique=True)
    qr_code = models.ImageField(upload_to='qrcodes/', max_length=1000, blank=True, null=True)
     # >>> NUEVOS CAMPOS <<<
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', blank=True, null=True)
    id_departamento = models.ForeignKey(Departamento, models.DO_NOTHING, db_column='departamento_id', blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    # Nuevos campos
    activo_critico = models.BooleanField(default=False)
    confidencialidad = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(4)])
    integridad = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(4)])
    disponibilidad = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(4)])
    clasificacion = models.CharField(max_length=20, choices=[('confidencial', 'Confidencial'),('uso_interno', 'Uso Interno'), ('publico', 'Público'),],blank=True, null=True,)
    eliminado = models.BooleanField(default=False)
    numero_serie = models.CharField(max_length=120, blank=True, null=True, db_index=True, help_text="Número de serie del activo (si aplica).")

    id_condicion_activo = models.ForeignKey(CondicionActivo, models.DO_NOTHING, db_column='id_condicion_activo', blank=True, null=True, verbose_name="Condición")
    id_factura = models.ForeignKey('Factura', models.DO_NOTHING, db_column='id_factura', blank=True, null=True, verbose_name='Factura (folio)')
    id_ubicacion = models.ForeignKey("Ubicacion", on_delete=models.SET_NULL, null=True, blank=True, db_column="id_ubicacion", related_name="activos")


    # Alias de compatibilidad para no romper plantillas/list_display que usan h.empresa
    @property
    def empresa(self):
        return self.id_empresa


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



    # models_inventario.py (dentro de class Activo)
    def estado_planes(self):
        mapa = {"ok": 0, "warning": 1, "overdue": 2}
        estados = [p.estado_calculado() for p in self.planes.filter(eliminado=False)]
        if not estados:
            return "—"
        return max(estados, key=lambda s: mapa.get(s, -1))

    #def estado_planes_badge(self):
    #    st = self.estado_planes()
    #    badges = {
    #        "ok": '<span class="badge bg-success">OK</span>',
    #        "warning": '<span class="badge bg-warning text-dark">Pronto</span>',
    #        "overdue": '<span class="badge bg-danger">Vencido</span>',
    #        "—": '<span class="text-muted">—</span>',
    #    }
    #    return mark_safe(badges.get(st, st))
    #estado_planes_badge.short_description = "Mantención"

    def estado_planes_badge(self):
        st = self.estado_planes()  # ok / warning / overdue / —
        # Colores (Bootstrap-ish)
        color = {
            "ok":      "#198754",  # verde
            "warning": "#FFC107",  # amarillo
            "overdue": "#DC3545",  # rojo
            "—":       "#ADB5BD",  # gris
        }.get(st, "#ADB5BD")

        html = (
            f'<span title="{st}" aria-label="{st}" '
            'style="display:inline-block; width:10px; height:10px; '
            'border-radius:50%; vertical-align:middle; '
            f'background:{color}; box-shadow:0 0 6px {color};"></span>'
        )
        return mark_safe(html)



    class Meta:
        managed = True
        db_table = 'activo'
        verbose_name="Activo"
        verbose_name_plural="Activos"


    def __str__(self):
        return f"{self.etiqueta or '—'} · ID: {self.id_activo} [{self.nombre_activo}]"


class AtributosActivo(models.Model):
    """Definición de atributo dinámico por tipo de activo.

    - PK: `id_atributo_activo`
    - FK: `id_tipo_activo → TipoActivo`
    - Datos: `atributo`, `valor` (opcional por defecto)
    - FK empresa opcional: `id_empresa`
    - Único: (`id_tipo_activo`, `atributo`)
    - Borrado lógico: `eliminado`
    - Tabla: `atributos_activo`

    Útil para construir formularios dinámicos y metadatos por tipo.
    """
    #id_atributo_activo = models.AutoField(primary_key=True)
    id_atributo_activo = models.AutoField(primary_key=True, db_column="id_atributo_activo")
    id_tipo_activo = models.ForeignKey(TipoActivo, models.DO_NOTHING, db_column='id_tipo_activo')
    atributo = models.CharField(max_length=100)
    valor = models.CharField(max_length=250, blank=True, null=True)
    id_empresa = models.ForeignKey('Empresa', models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'atributos_activo'
        unique_together = (('id_tipo_activo', 'atributo'),)
        verbose_name = "Atributo de activo"
        verbose_name_plural = "Atributos de activo"

    def __str__(self):
        # Ej: "Notebook · RAM = 16GB"
        v = f" = {self.valor}" if self.valor else ""
        return f"{self.id_tipo_activo} · {self.atributo}{v}"
    ##
    ##
    ## Nueva clase atributos por tipo de activos

class AtributoOpcionPorTipoActivo(models.Model):
    id_opcion = models.AutoField(primary_key=True, db_column="id_opcion")

    atributo_definicion = models.ForeignKey(
        AtributosActivo,
        on_delete=models.CASCADE,
        db_column="id_atributo_activo",
        related_name="opciones",
    )
    etiqueta_opcion = models.CharField(max_length=150)
    orden = models.PositiveIntegerField(default=0)
    habilitada = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = "atributo_opcion_por_tipo_activo"
        unique_together = (("atributo_definicion", "etiqueta_opcion"),)
        ordering = ["orden", "etiqueta_opcion"]

    def __str__(self):
        return self.etiqueta_opcion


class AgregacionAtributosPorActivo(models.Model):
    """Valor concreto de un atributo dinámico para un activo.

    - PK: `id`
    - FKs: `activo → Activo`, `atributo → AtributosActivo`
    - Datos: `valor`
    - Único: (`activo`, `atributo`)
    - Tabla: `agregacion_atributos_por_activo`
    """
    #id = models.AutoField(primary_key=True)
    id = models.AutoField(primary_key=True, db_column="id")
    activo = models.ForeignKey(Activo, models.DO_NOTHING, db_column='id_activo')
    atributo = models.ForeignKey(AtributosActivo, models.DO_NOTHING, db_column='id_atributo_activo')
    valor = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'agregacion_atributos_por_activo'
        unique_together = (('activo', 'atributo'),)
        verbose_name = "Valor de atributo por activo"
        verbose_name_plural = "Valores de atributos por activos"

    def __str__(self):
        nombre_attr = getattr(self.atributo, "atributo", "Atributo")
        return f"{self.activo_id} · {nombre_attr} = {self.valor or '—'}"
    


class EstadoMantencion(models.Model):
    """Estado del flujo de una mantención.

    - PK: `id_estado_mantencion`
    - FK: `id_empresa → Empresa` (opcional)
    - Único por empresa: (`id_empresa`, `tipo`)
    - Borrado lógico: `eliminado`
    - Tabla: `estado_mantencion`

    `__str__` devuelve `tipo`.
    """
    #id_estado_mantencion = models.AutoField(primary_key=True)
    id_estado_mantencion = models.AutoField(primary_key=True, db_column="id_estado_mantencion")
    tipo = models.CharField(max_length=50)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'estado_mantencion'
        unique_together = (('id_empresa', 'tipo'),)

    def __str__(self):
        return self.tipo
    
class TipoMantencion(models.Model):
    """Clasificación de la mantención (correctiva, preventiva, etc.).

    - PK: `id_tipo_mantencion`
    - FK: `id_empresa → Empresa` (opcional)
    - Único por empresa: (`id_empresa`, `nombre`)
    - Borrado lógico: `eliminado`
    - Tabla: `tipo_mantencion`
    - Verbose: "Tipo(s) de mantención"

    `__str__` devuelve `nombre`.
    """
    #id_tipo_mantencion = models.AutoField(primary_key=True)
    id_tipo_mantencion = models.AutoField(primary_key=True, db_column="id_tipo_mantencion")
    nombre = models.CharField(max_length=50)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'tipo_mantencion'
        unique_together = (('id_empresa', 'nombre'),)
        verbose_name = "Tipo de mantención"
        verbose_name_plural = "Tipos de mantención"


    def __str__(self):
        return self.nombre


class PrioridadMantencion(models.Model):
    """Prioridad de la mantención (alta, media, baja).

    - PK: `id_prioridad`
    - FK: `id_empresa → Empresa` (opcional)
    - Único por empresa: (`id_empresa`, `nombre`)
    - Borrado lógico: `eliminado`
    - Tabla: `prioridad_mantencion`

    `__str__` devuelve `nombre`.
    """
    #id_prioridad = models.AutoField(primary_key=True)
    id_prioridad = models.AutoField(primary_key=True, db_column="id_prioridad")
    nombre = models.CharField(max_length=50)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', blank=True, null=True)
    eliminado = models.BooleanField(default=False)
    

    class Meta:
        managed = True
        db_table = 'prioridad_mantencion'
        unique_together = (('id_empresa', 'nombre'),)
        verbose_name = "Prioridad de mantención"
        verbose_name_plural = "Prioridades de mantención"

    def __str__(self):
        return self.nombre



class Mantencion(models.Model):
    """Mantención de un activo con estado, tipo, prioridad y asignaciones.

    - PK: `id_mantencion`
    - FKs: `id_activo → Activo`, `id_estado_mantencion → EstadoMantencion`,
           `id_tipo_mantencion → TipoMantencion` (opcional),
           `id_prioridad → PrioridadMantencion` (opcional),
           `id_empresa → Empresa` (opcional),
           `responsable → Empleado` (opcional),
           `solicitante_user → auth.User` (opcional)
    - Datos: `fecha`, `descripcion`
    - Borrado lógico: `eliminado`
    - Tabla: `mantencion`

    Helpers:
    - `responsable_nombre`, `asignado_a`, `asignado_a_id`,
      `solicitante`/`solicitante_id`, `solicitante_nombre`.

    `__str__` incluye id, activo, estado y fecha.
    """
    #id_mantencion = models.AutoField(primary_key=True)
    id_mantencion = models.AutoField(primary_key=True, db_column="id_mantencion")
    id_activo = models.ForeignKey(Activo, models.DO_NOTHING, db_column='id_activo')
    id_estado_mantencion = models.ForeignKey(EstadoMantencion, models.DO_NOTHING, db_column='id_estado_mantencion')
    # NUEVAS FK que existen en tu tabla:
    id_tipo_mantencion = models.ForeignKey(TipoMantencion, models.DO_NOTHING, db_column='id_tipo_mantencion', null=True, blank=True)
    id_prioridad = models.ForeignKey(PrioridadMantencion, models.DO_NOTHING, db_column='id_prioridad', null=True, blank=True)
    fecha = models.DateField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    asignado = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='asignado_id', null=True, blank=True, related_name='mantenciones_asignado')

 # 👇 NUEVO: mapea la columna existente en BD
    id_empresa = models.ForeignKey('Empresa', models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)

    # NUEVOS (coinciden con SQL)
    responsable = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='responsable_id', null=True, blank=True, related_name='mantenciones_responsable')
    solicitante_user = models.ForeignKey("auth.User", models.DO_NOTHING, db_column='solicitante_user_id', null=True, blank=True, related_name='mantenciones_solicitadas')
    eliminado = models.BooleanField(default=False)
    

    class Meta:
        managed = True
        db_table = 'mantencion'
        verbose_name = "Mantención"
        verbose_name_plural = "Mantenciones"

    def __str__(self):
        f = self.fecha.isoformat() if self.fecha else "s/f"
        return f"Mantención {self.id_mantencion} · {self.id_activo} · {self.id_estado_mantencion} · {f}"

    @property
    def responsable_nombre(self):
        return str(self.responsable) if self.responsable_id else ""

    @property
    def asignado_a(self):
        return self.responsable

    @property
    def asignado_a_id(self):
        return getattr(self.responsable, "pk", None)
    
    
@property
def solicitante(self):
    # compat: por si algún código espera 'solicitante' en vez de 'solicitante_user'
    return self.solicitante_user

@property
def solicitante_id(self):
    return getattr(self.solicitante_user, "pk", None)

@property
def solicitante_nombre(self):
    u = getattr(self, "solicitante_user", None)
    if not u:
        return ""
    full = (u.get_full_name() or "").strip()
    return full or u.get_username() or str(u)

class Factura(models.Model):
    """Factura asociada a proveedor y empresa, con soporte de archivo adjunto.

    - PK: `id_factura`
    - FKs: `id_proveedor → Proveedor` (opcional), `id_empresa → Empresa` (opcional)
    - Datos: `fecha_emision`, `folio`, `observacion`
    - Archivo: `archivo_adjunto` (sube a `media/facturas/`)
    - Borrado lógico: `eliminado`
    - Tabla: `factura`

    Métodos:
    - `proveedor_rut()` devuelve el RUT legible del proveedor si existe.
    """
    #id_factura = models.AutoField(primary_key=True)
    id_factura = models.AutoField(primary_key=True, db_column="id_factura")
    id_proveedor = models.ForeignKey(Proveedor, models.DO_NOTHING, db_column='id_proveedor', blank=True, null=True)
    fecha_emision = models.DateField(blank=True, null=True)
    # EXISTENTE EN BD: solo lo reflejamos en el modelo
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', blank=True, null=True, related_name='facturas')
    # NUEVOS CAMPOS
    folio = models.CharField(max_length=50, blank=True, null=True, db_column="folio")
    observacion = models.TextField(blank=True, null=True, db_column="observacion")

    archivo_adjunto = models.FileField(upload_to='facturas/', null=True, blank=True)  # Aquí se agrega el campo de archivo
    eliminado = models.BooleanField(default=False)


    class Meta:
        managed = True
        db_table = 'factura'



    def __str__(self):
        # Si hay folio, lo mostramos; si no, queda vacío
        folio_txt = f" · Folio {self.folio.strip()}" if self.folio and self.folio.strip() else ""

        # Nombre legible del proveedor (intenta campos comunes)
        prov = (
            getattr(self.id_proveedor, "nombre", None)
            or getattr(self.id_proveedor, "nombre_proveedor", None)
            or (str(self.id_proveedor) if self.id_proveedor else "Proveedor s/i")
        )

        # Fecha legible
        f = self.fecha_emision.strftime("%d-%m-%Y") if self.fecha_emision else "s/f"

        return f"Factura {self.id_factura}{folio_txt} · {prov} · {f}"
    
    def proveedor_rut(self):
        """Muestra 'Proveedor (RUT)' en la lista."""
        p = getattr(self, "id_proveedor", None)
        if not p:
            return "—"
        # intenta varios nombres posibles de campo RUT
        for attr in ("rut", "rut_proveedor", "rut_empresa"):
            rut = getattr(p, attr, None)
            if rut:
                return rut
        return "—"

    proveedor_rut.short_description = "Proveedor"  # etiqueta de columna

class DetalleFactura(models.Model):
    """Detalle (ítem) de una factura.

    - PK: `id_detalle_factura`
    - FKs: `id_factura → Factura`, `id_activo → Activo` (opcional),
           `id_empresa → Empresa` (opcional)
    - Datos: `nombre_activo`, `cantidad`, `valor_unitario`,
             `valor_neto`, `iva`, `valor_total`
    - Borrado lógico: `eliminado`
    - Tabla: `detalle_factura`
    """
    #id_detalle_factura = models.AutoField(primary_key=True)
    id_detalle_factura = models.AutoField(primary_key=True, db_column="id_detalle_factura")
    id_factura = models.ForeignKey(Factura, models.DO_NOTHING, db_column='id_factura')
    id_activo = models.ForeignKey(Activo, models.DO_NOTHING, db_column='id_activo', blank=True, null=True)
    nombre_activo = models.CharField(max_length=150, blank=True, null=True)
    cantidad = models.IntegerField()
    valor_unitario = models.IntegerField()
    valor_neto = models.IntegerField(blank=True, null=True)
    iva = models.IntegerField(blank=True, null=True)
    valor_total = models.IntegerField(blank=True, null=True)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', blank=True, null=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        managed = True
        db_table = 'detalle_factura'

    def __str__(self):
        item = self.nombre_activo or (self.id_activo and str(self.id_activo)) or "Item s/i"
        return f"Detalle {self.id_detalle_factura} · Factura {self.id_factura_id} · {item}"
    

class HistorialActivos(models.Model):
    """Snapshot de cambios de un activo (estado, responsable, ubicación, etc.).

    - PK: `id` (autonumérico)
    - FKs: `activo → Activo`, `tipo_activo → TipoActivo` (opcional),
           `usuario → Empleado` (opcional), `id_empresa → Empresa` (opcional),
           `departamento → Departamento` (opcional),
           `estado_anterior/estado_nuevo → EstadoActivo` (opcionales),
           `responsable_actual → Empleado` (opcional)
    - Datos: `etiqueta`, `nombre_activo`, `modelo`, `ubicacion`, `comentario`,
             `fecha` (default `timezone.now`)
    - Compat: property `empresa` (alias de `id_empresa`)
    - Extra: `responsable_anterior_fk` persistido y property `responsable_anterior`
             que intenta resolver desde FK o el patrón `RESP_ANT=<id>` en `comentario`.
    - Tabla: `historial_activos`
    - `ordering`: más reciente primero
    """
    #id = models.AutoField(primary_key=True)
    id = models.AutoField(primary_key=True, db_column="id")
    activo = models.ForeignKey(Activo, models.DO_NOTHING, db_column='activo_id')
    etiqueta = models.CharField(max_length=150, blank=True, null=True)
    nombre_activo = models.CharField(max_length=150, blank=True, null=True)
    modelo = models.CharField(max_length=100, blank=True, null=True)
    tipo_activo = models.ForeignKey(TipoActivo, models.DO_NOTHING, db_column='tipo_activo_id', blank=True, null=True)
    accion = models.CharField(max_length=50)  # "agregado", "asignado", "bodega", "dañado", "perdido", etc.
    usuario = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='usuario_id', blank=True, null=True)
    fecha = models.DateTimeField(default=timezone.now)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', blank=True, null=True)
    departamento = models.ForeignKey(Departamento, models.DO_NOTHING, db_column='departamento_id', blank=True, null=True)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    estado_anterior = models.ForeignKey(EstadoActivo, models.DO_NOTHING, db_column='estado_anterior_id', blank=True, null=True, related_name='estado_anterior')
    estado_nuevo = models.ForeignKey(EstadoActivo, models.DO_NOTHING, db_column='estado_nuevo_id', blank=True, null=True, related_name='estado_nuevo')
    responsable_actual = models.ForeignKey(Empleado, models.DO_NOTHING, db_column='responsable_actual_id', blank=True, null=True, related_name='responsable_actual')
    comentario = models.TextField(blank=True, null=True)
 

    # --- Alias de compatibilidad: mantener .empresa para lecturas/escrituras viejas ---
    @property
    def empresa(self):
        return self.id_empresa

    @empresa.setter
    def empresa(self, value):
        self.id_empresa = value

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
        managed = True
        db_table = 'historial_activos'
        ordering = ['-fecha']
        verbose_name = "Historial de activos"
        verbose_name_plural = "Historial de activos"

    def __str__(self):
        eq = getattr(self, "activo", None)
        return f"Historial #{self.pk} · {eq or '—'} · {self.fecha}"


# --- Nuevo:Historial de Mantenciones ---
# --- Historial de Mantenciones (VIEW) ---

#class HistorialMantenciones(models.Model):
#    """Vista de solo lectura con el timeline de eventos de mantención.
#
#    - **managed=False** (usa la VIEW `vw_historial_mantenciones`)
#    - PK: `id_historial` (proveniente de la vista)
#    - Datos enriquecidos: etiquetas/nombres del activo, tipo/prioridad/estado,
#      responsable/solicitante legibles, `old_values`/`new_values` (JSON)
#    - Prop: `asignado_a` devuelve `responsable_nombre` si está disponible.
#    """
#    id_historial = models.IntegerField(primary_key=True)
#
#    id_mantencion = models.IntegerField()
#    fecha_evento = models.DateTimeField()
#    accion = models.CharField(max_length=50)
#    detalle = models.TextField(null=True, blank=True)
#    usuario_app_username = models.CharField(max_length=150, null=True, blank=True)
#
#    # Datos enriquecidos que expone la VIEW
#    id_activo = models.IntegerField(null=True, blank=True)
#    etiqueta = models.CharField(max_length=150, null=True, blank=True)
#    activo_nombre = models.CharField(max_length=150, null=True, blank=True)
#    descripcion = models.TextField(null=True, blank=True)
#
#    tipo_mantencion = models.CharField(max_length=50, null=True, blank=True)
#    prioridad = models.CharField(max_length=50, null=True, blank=True)
#    estado_actual = models.CharField(max_length=50, null=True, blank=True)
#
#    responsable_nombre = models.CharField(max_length=255, null=True, blank=True)
#    solicitante_nombre = models.CharField(max_length=255, null=True, blank=True)
#
#    old_values = models.JSONField(null=True, blank=True)
#    new_values = models.JSONField(null=True, blank=True)
#
#    @property
#    def asignado_a(self) -> str:
#        # Mostrar responsable si viene en la vista; si no, vacío
#        return (self.responsable_nombre or "").strip()
#
#    class Meta:
#        managed = False
#        db_table = "vw_historial_mantenciones"   # usa la VIEW, no crees tabla
#        verbose_name = "Historial de Mantenciones"
#        verbose_name_plural = "Historial de Mantenciones"
#        default_permissions = ("view",)
#
#    def __str__(self):
#        return f"[{self.id_mantencion}] {self.accion} @ {self.fecha_evento:%Y-%m-%d %H:%M}"
####################################################################################################
#nueva clase para mantenimiento

class HistorialMantencionesLog(models.Model):
    """Tabla persistente de eventos de mantención (log con “foto” legible).

    - PK: `id_evento`
    - Claves de negocio: `id_mantencion`, `fecha_evento`, `accion`, `detalle`
    - Snapshot: `id_activo`, `etiqueta`, `activo_nombre`,
                `tipo_mantencion`, `prioridad`, `estado_actual`,
                `responsable_nombre`, `solicitante_nombre`, `descripcion`
    - FK empresa: `id_empresa → Empresa` (opcional)
    - Tabla: `historial_mantenciones_log`

    `__str__` muestra timestamp, id de mantención y acción.
    """
    #id_evento = models.BigAutoField(primary_key=True)
    id_evento = models.AutoField(primary_key=True, db_column="id_evento")
    id_mantencion = models.IntegerField()
    fecha_evento = models.DateTimeField()
    accion = models.CharField(max_length=30)
    detalle = models.TextField(blank=True, default="")
    usuario_app_username = models.CharField(max_length=150, null=True, blank=True)

    # snapshot
    id_activo = models.IntegerField(null=True, blank=True)
    etiqueta = models.CharField(max_length=150, null=True, blank=True)
    activo_nombre = models.CharField(max_length=150, null=True, blank=True)

    tipo_mantencion = models.CharField(max_length=50, null=True, blank=True)
    prioridad = models.CharField(max_length=50, null=True, blank=True)
    estado_actual = models.CharField(max_length=50, null=True, blank=True)

    responsable_nombre = models.TextField(null=True, blank=True)
    solicitante_nombre = models.TextField(null=True, blank=True)

    descripcion = models.TextField(null=True, blank=True)
    id_empresa = models.ForeignKey('Empresa', models.DO_NOTHING, db_column='id_empresa', null=True, blank=True)


    class Meta:
        managed = True  # la tabla ya existe en la BD
        db_table = 'historial_mantenciones_log'
        verbose_name = "Historial de mantenciones (log)"
        verbose_name_plural = "Historial de mantenciones (log)"

    def __str__(self):
        return f"[{self.fecha_evento:%Y-%m-%d %H:%M}] M#{self.id_mantencion} · {self.accion}"

    @property
    def asignado_a(self) -> str:
        return (self.responsable_nombre or self.solicitante_nombre or "").strip()
    
##############################################################################################################
##############################################################################################################0110
# --- AUDITORÍA / REGISTRO MAESTRO ---
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
import json
from django.db.models.functions import Lower  # <-- importa esto arriba


# Tipo de registro: indica qué tipo de acción se realizó
class TipoRegistro(models.Model):
    """Catálogo global de tipos de registro para auditoría.

    - PK: `id_tipo_registro`
    - Único global: `nombre`
    - Datos: `descripcion`
    - FK empresa: `id_empresa` (opcional)
    - Borrado lógico: `eliminado`
    - Tabla: `tipo_registro`
    - `ordering`: por `nombre`
    """
    id_tipo_registro = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)  # único GLOBAL
    descripcion = models.TextField(blank=True, null=True)
    eliminado = models.BooleanField(default=False)
        # Relación con la empresa
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', blank=True, null=True)

    class Meta:
        db_table = "tipo_registro"
        verbose_name = "Tipo de registro"
        verbose_name_plural = "Tipos de registro"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# Registro maestro de acciones, para almacenar todas las acciones que suceden en la aplicación
class Registro(models.Model):
    """Registro maestro de acciones/auditoría sobre cualquier modelo.

    - PK: `id_registro`
    - FK usuario: `usuario → Empleado` (opcional)
    - FK tipo: `tipo_registro → TipoRegistro`
    - Target genérico: `content_type` + `object_id` + `objeto (GenericForeignKey)`
    - Datos: `descripcion`, `datos_anteriores` (JSON), `datos_nuevos` (JSON),
             `comentario`, `fecha` (auto_now_add)
    - FK empresa: `id_empresa → Empresa` (opcional)
    - Borrado lógico: `eliminado`

    Lógica en `save()`:
    - Normaliza `datetime` a ISO-8601 (propio y dentro de JSON anidado).

    `ordering`: `-fecha`, `-id_registro` (recientes primero).
    """
    id_registro = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, db_column='usuario_id')
    tipo_registro = models.ForeignKey(TipoRegistro, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    objeto = GenericForeignKey("content_type", "object_id")
    descripcion = models.TextField()
    datos_anteriores = models.JSONField(null=True, blank=True)  
    datos_nuevos = models.JSONField(null=True, blank=True) 
    comentario = models.TextField(null=True, blank=True)
    eliminado = models.BooleanField(default=False)
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='id_empresa', blank=True, null=True)

    def __str__(self):
        return f"{self.tipo_registro.nombre} - {self.objeto} - {self.fecha}"
    

    def save(self, *args, **kwargs):
        # Asegúrate de convertir `fecha` a formato string ISO 8601 antes de guardar
        if isinstance(self.fecha, timezone.datetime):
            self.fecha = self.fecha.isoformat()

        # Convertir cualquier campo datetime dentro de los JSONField (datos_anteriores y datos_nuevos)
        if self.datos_anteriores:
            self.datos_anteriores = self.convert_datetime_in_dict(self.datos_anteriores)
        if self.datos_nuevos:
            self.datos_nuevos = self.convert_datetime_in_dict(self.datos_nuevos)

        super().save(*args, **kwargs)

    def convert_datetime_in_dict(self, data):
        """
        Convierte cualquier campo datetime dentro de un diccionario a formato string ISO 8601.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, timezone.datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, dict):
                    # Recursivamente convertir los valores en subdiccionarios
                    data[key] = self.convert_datetime_in_dict(value)
        return data


    class Meta:
        verbose_name = "Registro de acción"
        verbose_name_plural = "Registros de acciones"
        ordering = ["-fecha", "-id_registro"]  # Asegura que los registros más recientes estén primero



#    class Meta:
#        db_table = "registro"
#        verbose_name = "Registro"
#        verbose_name_plural = "Registros"
#        ordering = ["-fecha", "-id_registro"]
#
#    def __str__(self):
#        modelo = self.content_type.model if self.content_type_id else "obj"
#        return f"[{self.fecha:%Y-%m-%d %H:%M}] {self.tipo} · {modelo}#{self.object_id}"


# --- Documentos por Activo ----------------------------------------------------

from django.db import models

class TipoDocumentoActivo(models.Model):
    id_tipo_documento = models.AutoField(primary_key=True)
    id_empresa = models.ForeignKey(
        'Empresa', on_delete=models.CASCADE, db_column='id_empresa',
        null=True, blank=True
    )
    nombre = models.CharField(max_length=120)
    eliminado = models.BooleanField(default=False)

    class Meta:
        db_table = 'inventario.tipo_documento_activo'
        verbose_name = 'Tipo de documento de activo'
        verbose_name_plural = 'Tipos de documento de activo'
        unique_together = (('id_empresa', 'nombre'),)

    def __str__(self):
        return self.nombre


def documento_activo_upload_to(instance, filename: str) -> str:
    # /media/activos/<id>/docs/<archivo>
    return f"activos/{instance.id_activo_id}/docs/{filename}"


class DocumentoActivo(models.Model):
    id_documento = models.AutoField(primary_key=True)
    id_empresa = models.ForeignKey(
        'Empresa', on_delete=models.CASCADE, db_column='id_empresa',
        null=True, blank=True
    )
    id_activo = models.ForeignKey(
        'Activo', on_delete=models.CASCADE, db_column='id_activo',
        related_name='documentos'
    )
    tipo = models.ForeignKey(
        'TipoDocumentoActivo', on_delete=models.PROTECT,
        db_column='id_tipo_documento'
    )
    archivo = models.FileField(upload_to=documento_activo_upload_to)
    creado_en = models.DateTimeField(auto_now_add=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        db_table = 'inventario.documento_activo'
        verbose_name = 'Documento de activo'
        verbose_name_plural = 'Documentos de activo'
        indexes = [
            models.Index(fields=['id_activo', 'eliminado']),
        ]

    def __str__(self):
        return f"{self.tipo} · {self.archivo.name if self.archivo else '(sin archivo)'}"



    #############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><
class TipoMedicionActivo(models.Model):
    id_tipo_medicion = models.AutoField(primary_key=True, db_column="id_tipo_medicion")
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column="id_empresa", null=True, blank=True)
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=30, help_text="ej: dias, km, horas")
    unidad = models.CharField(max_length=30, help_text="ej: días, km, h")
    es_tiempo = models.BooleanField(default=False)
    eliminado = models.BooleanField(default=False)

    class Meta:
        db_table = "tipo_medicion_activo"
        verbose_name = "Tipo de medición"
        verbose_name_plural = "Tipos de medición"
        constraints = [
            models.UniqueConstraint(
                fields=["id_empresa", "codigo"], name="uq_tipomedicion_empresa_codigo"
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.unidad})"


class MedicionActivo(models.Model):
    id_medicion = models.AutoField(primary_key=True, db_column="id_medicion")
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column="id_empresa", null=True, blank=True)
    id_activo = models.ForeignKey("Activo", models.DO_NOTHING, db_column="id_activo", related_name="mediciones")
    tipo_medicion = models.ForeignKey(TipoMedicionActivo, models.DO_NOTHING, db_column="id_tipo_medicion")
    # uno de estos dos se usa:
    valor_numerico = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    valor_fecha = models.DateField(null=True, blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    observacion = models.CharField(max_length=250, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        db_table = "medicion_activo"
        verbose_name = "Medición"
        verbose_name_plural = "Mediciones"
        ordering = ["-fecha_registro"]

    def __str__(self):
        v = self.valor_numerico if self.valor_numerico is not None else self.valor_fecha
        return f"{self.id_activo} · {self.tipo_medicion.codigo} = {v}"
    
    def clean(self):
        if self.tipo_medicion and self.tipo_medicion.es_tiempo:
            if not self.valor_fecha:
                raise ValidationError("Para mediciones de tiempo debes completar 'valor_fecha'.")
            # Normaliza
            self.valor_numerico = None
        else:
            if self.valor_numerico is None:
                raise ValidationError("Debes completar 'valor_numerico' (km, horas, etc.).")
            self.valor_fecha = None


class PlanMantencion(models.Model):
    id_plan = models.AutoField(primary_key=True, db_column="id_plan")
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column="id_empresa", null=True, blank=True)
    nombre = models.CharField(max_length=150)
    id_tipo_activo = models.ForeignKey("TipoActivo", models.DO_NOTHING, db_column="id_tipo_activo")
    tipo_medicion = models.ForeignKey(TipoMedicionActivo, models.DO_NOTHING, db_column="id_tipo_medicion")
    # intervalo: usa UNO de los dos según es_tiempo
    intervalo_dias = models.PositiveIntegerField(null=True, blank=True)
    intervalo_valor = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    prealerta_pct = models.PositiveIntegerField(default=10)  # 10% del intervalo
    descripcion = models.TextField(blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        db_table = "plan_mantencion"
        verbose_name = "Plan de mantención"
        verbose_name_plural = "Planes de mantención"
        constraints = [
            models.UniqueConstraint(
                fields=["id_empresa", "id_tipo_activo", "nombre"],
                name="uq_plan_empresa_tipo_nombre"
            )
        ]

    def __str__(self):
        return f"{self.nombre} · {self.id_tipo_activo}"

    # Helpers mínimos
    def intervalo(self) -> Decimal | int:
        return self.intervalo_dias if self.tipo_medicion.es_tiempo else self.intervalo_valor or Decimal("0")

    def umbral_prealerta(self) -> Decimal:
        """Devuelve el valor en unidades del punto de prealerta (p.ej., 9000km si intervalo=10000 y 10%)."""
        i = Decimal(self.intervalo() or 0)
        return i * (Decimal("1.0") - Decimal(self.prealerta_pct) / Decimal("100.0"))
    
    def clean(self):
        # solo uno de los dos intervalos, según el tipo de medición
        if self.tipo_medicion and self.tipo_medicion.es_tiempo:
            if not self.intervalo_dias:
                raise ValidationError("Debes indicar 'intervalo_dias' para planes por tiempo.")
            self.intervalo_valor = None
        else:
            if not self.intervalo_valor:
                raise ValidationError("Debes indicar 'intervalo_valor' para planes por medición numérica (km, horas, etc.).")
            self.intervalo_dias = None


class PlanMantencionTarea(models.Model):
    id_tarea = models.AutoField(primary_key=True, db_column="id_tarea")
    id_plan = models.ForeignKey(PlanMantencion, models.DO_NOTHING, db_column="id_plan", related_name="tareas")
    orden = models.PositiveIntegerField(default=1)
    descripcion = models.CharField(max_length=300)
    obligatorio = models.BooleanField(default=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        db_table = "plan_mantencion_tarea"
        verbose_name = "Tarea de plan"
        verbose_name_plural = "Tareas del plan"
        ordering = ["orden", "id_tarea"]

    def __str__(self):
        return f"[{self.id_plan.nombre}] {self.descripcion}"


class PlanMantencionActivo(models.Model):
    id_plan_mantencion_activo = models.AutoField(primary_key=True, db_column="id_plan_mantencion_activo")
    id_empresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column="id_empresa", null=True, blank=True)
    id_plan = models.ForeignKey(PlanMantencion, models.DO_NOTHING, db_column="id_plan", related_name="aplicaciones")
    id_activo = models.ForeignKey("Activo", models.DO_NOTHING, db_column="id_activo", related_name="planes")

    # Base del ciclo actual (cuándo/desde qué valor empezamos a contar)
    base_fecha = models.DateField(null=True, blank=True)
    base_valor = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    # Última medición conocida (denormalizado para cálculo rápido)
    ultima_medicion_fecha = models.DateField(null=True, blank=True)
    ultima_medicion_valor = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    # Próximo vencimiento (opcionalmente pre-calculado)
    proximo_vencimiento_fecha = models.DateField(null=True, blank=True)
    proximo_vencimiento_valor = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    # Estado simple: ok / warning / overdue (puedes calcularlo on the fly)
    estado = models.CharField(max_length=12, blank=True, choices=[("ok", "Ok"), ("warning", "Advertencia"), ("overdue", "Vencido")], default="ok")

    fecha_inicio = models.DateField(default=date.today)
    observacion = models.CharField(max_length=250, blank=True)
    eliminado = models.BooleanField(default=False)

    class Meta:
        db_table = "plan_mantencion_activo"
        verbose_name = "Plan aplicado a Activo"
        verbose_name_plural = "Planes aplicados a Activos"
        constraints = [
            models.UniqueConstraint(
                fields=["id_plan", "id_activo"],
                name="uq_plan_activo_unico"
            )
        ]

    def __str__(self):
        return f"{self.id_plan.nombre} → {self.id_activo}"
    

    def estado_planes(self):
        mapa = {"ok": 0, "warning": 1, "overdue": 2}
        
        # Obtiene los planes asociados al activo de este plan
        planes = PlanMantencionActivo.objects.filter(id_activo=self.id_activo, eliminado=False)
        
        estados = [p.estado_calculado() for p in planes]
        
        if not estados:
            return "—"
        
        return max(estados, key=lambda s: mapa.get(s, -1))

    def estado_planes_badge(self):
        st = self.estado_planes()  # ok / warning / overdue / —
        # Colores (Bootstrap-ish)
        color = {
            "ok":      "#198754",  # verde
            "warning": "#FFC107",  # amarillo
            "overdue": "#DC3545",  # rojo
            "—":       "#ADB5BD",  # gris
        }.get(st, "#ADB5BD")

        html = (
            f'<span title="{st}" aria-label="{st}" '
            'style="display:inline-block; width:10px; height:10px; '
            'border-radius:50%; vertical-align:middle; '
            f'background:{color}; box-shadow:0 0 6px {color};"></span>'
        )
        return mark_safe(html)

    # ---------------- Cálculo “on the fly” ----------------
    def _base(self):
        """Devuelve (base_fecha, base_valor) usando base_* o fecha_inicio/0 como fallback."""
        bf = self.base_fecha or self.fecha_inicio
        bv = self.base_valor or Decimal("0")
        return bf, bv

    def _actual(self):
        """Devuelve la lectura actual: para tiempo = hoy; para numérico = última medición."""
        if self.id_plan.tipo_medicion.es_tiempo:
            return date.today()
        # numérico
        if self.ultima_medicion_valor is not None:
            return Decimal(self.ultima_medicion_valor)
        # si no tenemos denormalizado, intentamos buscar la última medición
        m = (self.id_activo.mediciones
             .filter(eliminado=False, tipo_medicion=self.id_plan.tipo_medicion)
             .order_by("-fecha_registro")
             .first())
        return Decimal(m.valor_numerico) if m and m.valor_numerico is not None else None

    def progreso_ratio(self) -> Decimal:
        """
        0.0 = recién comienza el ciclo; 1.0 = alcanzó el intervalo; >1.0 = vencido.
        """
        intervalo = Decimal(self.id_plan.intervalo() or 0)
        if intervalo <= 0:
            return Decimal("0")

        if self.id_plan.tipo_medicion.es_tiempo:
            base_fecha, _ = self._base()
            dias = Decimal((date.today() - base_fecha).days)
            return dias / Decimal(int(intervalo))
        else:
            _, base_valor = self._base()
            actual = self._actual()
            if actual is None:
                return Decimal("0")
            return (Decimal(actual) - Decimal(base_valor)) / Decimal(intervalo)

    def estado_calculado(self) -> str:
        """Devuelve ok / warning / overdue según progreso y prealerta."""
        r = self.progreso_ratio()
        if r >= Decimal("1"):
            return "overdue"
        # prealerta
        pre = Decimal("1") - (Decimal(self.id_plan.prealerta_pct) / Decimal("100"))
        return "warning" if r >= pre else "ok"

    def proximo_vencimiento(self):
        """
        Calcula la fecha/valor de vencimiento teórico del ciclo actual.
        (No persiste; lo puedes guardar en los campos *_vencimiento si quieres).
        """
        intervalo = self.id_plan.intervalo()
        if self.id_plan.tipo_medicion.es_tiempo:
            base_fecha, _ = self._base()
            return (base_fecha + timedelta(days=int(intervalo))), None
        else:
            _, base_valor = self._base()
            return None, (Decimal(base_valor) + Decimal(intervalo))

    # Helpers útiles para refrescar campos denormalizados (puedes llamar desde signals o tareas)
    def refrescar_estado_y_vencimiento(self, persist=True):
        est = self.estado_calculado()
        prox_fech, prox_val = self.proximo_vencimiento()
        self.estado = est
        self.proximo_vencimiento_fecha = prox_fech
        self.proximo_vencimiento_valor = prox_val
        if persist:
            self.save(update_fields=["estado", "proximo_vencimiento_fecha", "proximo_vencimiento_valor"])
        return est
    
    @property
    def vencimiento_estimado(self):
        """Compat alias (código viejo): devuelve el próximo vencimiento."""
        # Si el plan es de tiempo, vendrá por fecha; si es numerico (km/horas), por valor.
        return self.proximo_vencimiento_fecha or self.proximo_vencimiento_valor