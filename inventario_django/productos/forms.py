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
#from .models import Empleado
import re
import unicodedata

def normalize_name(s: str) -> str:
    """
    Normaliza un nombre eliminando tildes y espacios extra.

    Este método se utiliza para comparar nombres de forma insensible a tildes y mayúsculas.

    Parameters:
    s (str): El nombre a normalizar.

    Returns:
    str: El nombre normalizado, en minúsculas y sin tildes.
    """
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)                # colapsa espacios
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")  # sin tildes
    return s.lower()

class MantencionForm(forms.ModelForm):
    """
    Formulario para la creación y edición de mantenimientos.

    Este formulario permite gestionar las mantenciones, asignando los activos,
    estados, tipos y prioridades, así como la fecha y descripción.

    Attributes:
        model (Mantencion): El modelo asociado con este formulario.
        exclude (list): Campos a excluir del formulario.
        widgets (dict): Widgets de entrada de los campos.
        labels (dict): Etiquetas personalizadas para los campos.
    """
    class Meta:
        model = Mantencion
        exclude = ['eliminado']  # Excluir el campo 'eliminado' en el formulario
        fields = [
            "id_activo",
            "asignado",
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
        """
        Inicializa el formulario, añadiendo filtros y configuraciones adicionales.

        Esta función también asigna filtros específicos por empresa activa para
        los campos de selección (activos, estados, tipos, etc.).

        Parameters:
        request (HttpRequest): La solicitud actual, para obtener la empresa activa.

        """
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

            if "asignado" in self.fields:
                self.fields["asignado"].queryset = (
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


        # ---------- PREFILL ASIGNADO desde el ACTIVO ----------
        # ---------- PREFILL (id_activo y asignado) ----------
        # 1) Levanta el id del activo desde varios nombres de parámetro posibles
        activo_id_from_qs = None
        if request is not None:
            for key in ("activo", "id_activo", "aid", "pk", "id"):
                val = request.GET.get(key)
                if val:
                    try:
                        activo_id_from_qs = int(val)
                        break
                    except (TypeError, ValueError):
                        pass

        # 2) Determina el activo actual (por instancia o querystring)
        activo_obj = None
        if getattr(self.instance, "id_activo_id", None):
            activo_obj = self.instance.id_activo
        elif activo_id_from_qs:
            activo_obj = Activo.objects.filter(pk=activo_id_from_qs).first()
            if activo_obj and "id_activo" in self.fields and not self.is_bound:
                # Usa self.initial para asegurar que el widget lo respete
                self.initial["id_activo"] = activo_obj.pk

        # 3) Si el activo tiene empleado asignado, prellenar "asignado"
        if activo_obj and getattr(activo_obj, "id_empleado_id", None) and "asignado" in self.fields:
            empleado_id = activo_obj.id_empleado_id

            # Asegura que el empleado esté en el queryset (por si filtros lo excluyen)
            qs = self.fields["asignado"].queryset or Empleado.objects.all()
            if not qs.filter(pk=empleado_id).exists():
                self.fields["asignado"].queryset = qs | Empleado.objects.filter(pk=empleado_id)

            if not self.is_bound:
                self.initial["asignado"] = empleado_id

        self._request = request  # por si lo necesitas luego

    def clean_fecha(self):
        """
        Valida la fecha ingresada en el formulario.

        La fecha no puede ser anterior a hoy, excepto si ya existe un registro
        con la fecha pasada.

        Parameters:
        None

        Returns:
        date: La fecha validada.
        """
        f = self.cleaned_data.get("fecha")
        if not getattr(self.instance, "pk", None) and f and f < date.today():
            raise ValidationError("La fecha no puede ser anterior a hoy.")
        return f

    def clean(self):
        """
        Realiza validaciones adicionales para asegurar que los campos seleccionados
        pertenezcan a la empresa activa.

        También autocompleta la empresa de la mantención si no se encuentra asignada.

        Parameters:
        None

        Returns:
        dict: Los datos del formulario validados.
        """
        cleaned = super().clean()
        activo = cleaned.get("id_activo")
        if activo is None:
            return cleaned

        # Si no se envió "asignado" pero el activo tiene responsable, lo completamos
        if not cleaned.get("asignado") and getattr(activo, "id_empleado_id", None):
            cleaned["asignado"] = activo.id_empleado

        # Rellenar el campo visual 'asignado' ignorando el POST (por estar disabled)
        self.cleaned_data["asignado"] = activo.id_empleado

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
    """
    Formulario para la creación y edición de empleados.

    Este formulario permite gestionar la información de los empleados, como
    el nombre, rut, cargo, teléfono, y la asignación a un departamento y empresa.

    Attributes:
        model (Empleado): El modelo asociado con este formulario.
        exclude (list): Campos a excluir del formulario (en este caso, 'user' y 'eliminado').
        widgets (dict): Widgets de entrada de los campos.
    """
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
        """
        Guarda el formulario creando un usuario asociado si no existe.

        Si el empleado no tiene un usuario asociado, se crea un nuevo usuario
        en el sistema con el correo como nombre de usuario y una contraseña
        predeterminada.

        Parameters:
        commit (bool): Si se debe guardar o no el objeto en la base de datos.

        Returns:
        Empleado: El empleado guardado.
        """
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
    """
    Formulario para adjuntar un archivo a una factura.

    Este formulario permite agregar un archivo adjunto a una factura existente.

    Attributes:
        model (Factura): El modelo asociado con este formulario.
        fields (list): Los campos del formulario, en este caso solo 'archivo_adjunto'.
    """
    class Meta:
        model = Factura
        fields = ['archivo_adjunto']

# productos/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models_inventario import Marca

class MarcaForm(forms.ModelForm):
    """
    Formulario para la creación y edición de marcas.

    Este formulario permite gestionar las marcas asociadas a los productos
    en la empresa.

    Attributes:
        model (Marca): El modelo asociado con este formulario.
        fields (list): Los campos del formulario, en este caso 'nombre_marca' y 'id_empresa'.
        widgets (dict): Widgets de entrada de los campos.
    """
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
        """
        Normaliza el nombre de la marca para eliminar espacios y mayúsculas innecesarias.

        Este método asegura que el nombre de la marca se guarde de manera uniforme
        al comparar con otras marcas.

        Parameters:
        None

        Returns:
        str: El nombre de la marca sin espacios extra.
        """
        from .forms import re  # si no estás ya en este archivo
        name = (self.cleaned_data.get("nombre_marca") or "").strip()
        name = re.sub(r"\s+", " ", name)
        return name

    def clean(self):
        """
        Realiza validaciones adicionales para asegurarse de que el nombre de la marca
        no se repita dentro de la empresa.

        Parameters:
        None

        Returns:
        dict: Los datos del formulario validados.
        """
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
