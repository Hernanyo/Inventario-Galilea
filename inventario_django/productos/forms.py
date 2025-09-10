from datetime import date
from django import forms
from .models_inventario import Mantencion, Empleado   # asegúrate de tener Empleado importado
from django.core.exceptions import ValidationError
from django.utils import timezone

class MantencionForm(forms.ModelForm):
    class Meta:
        model = Mantencion
        fields = [
            "id_equipo",
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
            "id_equipo": "Equipo",
            "id_estado_mantencion": "Estado",
            "id_tipo_mantencion": "Tipo de mantención",
            "id_prioridad": "Prioridad",
            "fecha": "Fecha",
            "descripcion": "Descripción",
            "responsable": "Responsable",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # estiliza selects
        for f in ['id_equipo','id_estado_mantencion','id_tipo_mantencion','id_prioridad','responsable']:
            if f in self.fields:
                self.fields[f].widget.attrs.update({'class': 'form-select'})
        # filtra empleados activos
        if 'responsable' in self.fields:
            self.fields['responsable'].queryset = Empleado.objects.filter(activo=True).order_by('nombre')
        # calendario con mínimo hoy
        if 'fecha' in self.fields:
            self.fields['fecha'].widget.attrs['min'] = date.today().isoformat()
            self.fields['fecha'].initial = date.today()

    def clean_fecha(self):
        f = self.cleaned_data.get("fecha")
        if f and f < date.today():
            raise forms.ValidationError("La fecha no puede ser anterior a hoy.")
        return f

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        # Ocultamos el OneToOne con auth_user para que no se edite desde aquí
        exclude = ["user"]
        # (opcional) widgets básicos para look & feel
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido_paterno": forms.TextInput(attrs={"class": "form-control"}),
            "apellido_materno": forms.TextInput(attrs={"class": "form-control"}),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "cargo": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "id_empresa": forms.Select(attrs={"class": "form-select"}),
            "id_departamento": forms.Select(attrs={"class": "form-select"}),
            "rol": forms.TextInput(attrs={"class": "form-control"}),
        }

def clean_fecha(self):
    f = self.cleaned_data.get("fecha")
    if f and f < timezone.localdate():
        raise ValidationError("La fecha no puede ser anterior a hoy.")
    return f