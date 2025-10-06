from datetime import date
from django import forms
from .models import Factura
from .models_inventario import Mantencion, Empleado   # asegúrate de tener Empleado importado
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models_inventario import Mantencion, Empleado, Activo  # 👈 añade Activo
from .models_inventario import (
    Mantencion, Activo, Empleado,
    EstadoMantencion, TipoMantencion, PrioridadMantencion
)
from django.contrib.auth.models import User
from .models import Empleado
import re
import unicodedata

def normalize_name(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)                # colapsa espacios
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # sin tildes
    return s.lower()

class MantencionForm(forms.ModelForm):
    class Meta:
        model = Mantencion
        exclude = ['eliminado']  # Excluir el campo 'eliminado' en el formulario
        fields = [
            "id_activo",
            "id_estado_mantencion",
            "id_tipo_mantencion",
            "id_prioridad",
            "fecha",
            "descripcion",
            "responsable",
        ]
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date", "class": "input input-bordered"}),
            "descripcion": forms.Textarea(attrs={"rows": 4, "class": "textarea textarea-bordered"}),
        }
        labels = {
            "id_activo": "Activo",
            "id_estado_mantencion": "Estado",
            "id_tipo_mantencion": "Tipo de mantención",
            "id_prioridad": "Prioridad",
            "fecha": "Fecha",
            "descripcion": "Descripción",
            "responsable": "Responsable",
        }

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)

        # clases para selects/inputs
        for name, field in self.fields.items():
            w = field.widget
            css = w.attrs.get("class", "")
            if w.__class__.__name__ in ("Select", "SelectMultiple"):
                w.attrs["class"] = (css + " form-select").strip()
            else:
                w.attrs["class"] = (css + " form-control").strip()

        emp_id = request.session.get("empresa_id") if request is not None else None

        # Filtrar todos los combos por empresa activa
        if emp_id:
            if "id_activo" in self.fields:
                self.fields["id_activo"].queryset = (
                    Activo.objects.filter(id_empresa_id=emp_id)
                    .order_by("nombre_activo")
                )
            if "id_estado_mantencion" in self.fields:
                self.fields["id_estado_mantencion"].queryset = (
                    EstadoMantencion.objects.filter(id_empresa_id=emp_id)
                    .order_by("tipo")
                )
            if "id_tipo_mantencion" in self.fields:
                self.fields["id_tipo_mantencion"].queryset = (
                    TipoMantencion.objects.filter(id_empresa_id=emp_id)
                    .order_by("nombre")
                )
            if "id_prioridad" in self.fields:
                self.fields["id_prioridad"].queryset = (
                    PrioridadMantencion.objects.filter(id_empresa_id=emp_id)
                    .order_by("nombre")
                )
            if "responsable" in self.fields:
                self.fields["responsable"].queryset = (
                    Empleado.objects.filter(id_empresa_id=emp_id, estado_activo=True)
                    .order_by("nombre", "apellido_paterno", "apellido_materno")
                )
        else:
            # fallback si no hay empresa en sesión
            if "responsable" in self.fields:
                self.fields["responsable"].queryset = (
                    Empleado.objects.filter(estado_activo=True).order_by("nombre")
                )

        # fecha mínima (= hoy) sólo en creación
        if "fecha" in self.fields and not getattr(self.instance, "pk", None):
            self.fields["fecha"].widget.attrs["min"] = date.today().isoformat()
            self.fields["fecha"].initial = date.today()

        self._request = request  # por si lo necesitas luego

    def clean_fecha(self):
        f = self.cleaned_data.get("fecha")
        if not getattr(self.instance, "pk", None) and f and f < date.today():
            raise ValidationError("La fecha no puede ser anterior a hoy.")
        return f

    def clean(self):
        cleaned = super().clean()
        activo = cleaned.get("id_activo")
        if activo is None:
            return cleaned

        emp_id = getattr(activo, "id_empresa_id", None)

        # Autocompletar empresa de la mantención si viene vacía
        if getattr(self.instance, "id_empresa_id", None) in (None, ""):
            self.instance.id_empresa_id = emp_id

        # Validar coherencia de empresa en catálogos seleccionados
        checks = (
            ("id_estado_mantencion", "Estado de mantención"),
            ("id_tipo_mantencion", "Tipo de mantención"),
            ("id_prioridad", "Prioridad"),
            ("responsable", "Responsable"),
        )
        for field_name, label in checks:
            obj = cleaned.get(field_name)
            if obj is not None and getattr(obj, "id_empresa_id", emp_id) != emp_id:
                raise ValidationError({field_name: f"{label} pertenece a otra empresa."})

        return cleaned
    
class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        # Ocultamos el OneToOne con auth_user para que no se edite desde aquí
        exclude = ['user','eliminado']

        # (opcional) widgets básicos para look & feel
        widgets = {
            "rut":forms.TextInput(attrs={"class": "form-control"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido_paterno": forms.TextInput(attrs={"class": "form-control"}),
            "apellido_materno": forms.TextInput(attrs={"class": "form-control"}),
            "estado_activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "cargo": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "id_empresa": forms.Select(attrs={"class": "form-select"}),
            "id_departamento": forms.Select(attrs={"class": "form-select"}),
            "rol": forms.TextInput(attrs={"class": "form-control"}),
            "correo": forms.EmailInput(attrs={"class": "form-control"}),
        }
################################################################################################################
################################################################################################################
    def save(self, commit=True):
        # Crear el usuario automáticamente si no se ha asignado un user_id
        instance = super().save(commit=False)
        
        # Si no existe un usuario asociado, lo creamos
        if not instance.user_id:
            user = User.objects.create_user(
                username=self.cleaned_data["correo"],  # Usamos el correo como username
                email=self.cleaned_data["correo"],  # Usamos el correo
                password='defaultpassword',  # Puedes asignar una contraseña predeterminada o generarla
            )
            instance.user_id = user.id  # Asigna el usuario recién creado al campo user_id

        if commit:
            instance.save()
        return instance
################################################################################################################
################################################################################################################

class FacturaAdjuntoForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['archivo_adjunto']

# productos/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models_inventario import Marca

class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ["nombre_marca", "id_empresa"]  # <-- no incluimos 'eliminado'
        widgets = {
            "nombre_marca": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre de la marca"}
            ),
            "id_empresa": forms.Select(attrs={"class": "form-select"}),
        }
    # opcional: guardar ya “limpio” (sin espacios extra)
    def clean_nombre_marca(self):
        from .forms import re  # si no estás ya en este archivo
        name = (self.cleaned_data.get("nombre_marca") or "").strip()
        name = re.sub(r"\s+", " ", name)
        return name

    def clean(self):
        cleaned = super().clean()
        empresa = cleaned.get("id_empresa")
        nombre  = cleaned.get("nombre_marca") or ""

        # normaliza el nombre que intenta guardar
        norm_in = normalize_name(nombre)

        # armar queryset dentro de la misma empresa
        qs = Marca.objects.all()
        if empresa:
            # empresa puede ser objeto o id
            emp_id = getattr(empresa, "id_empresa", empresa)
            qs = qs.filter(id_empresa_id=emp_id)

        # al editar, excluirse a sí mismo
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        # comparar normalizados contra lo que ya existe
        for existente in qs.values_list("nombre_marca", flat=True):
            if normalize_name(existente) == norm_in:
                raise ValidationError({
                    "nombre_marca": "Ya existe una marca con ese nombre (ignorando mayúsculas, tildes y espacios) para esta empresa."
                })

        return cleaned
