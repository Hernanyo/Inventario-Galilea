from django import forms
from .models_inventario import Mantencion

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
        ]
        widgets = {
            # Calendario nativo del navegador
            "fecha": forms.DateInput(attrs={"type": "date", "class": "input input-bordered"}),
            "descripcion": forms.Textarea(attrs={"rows": 6, "class": "textarea textarea-bordered"}),
        }
        labels = {
            "id_equipo": "Equipo",
            "id_estado_mantencion": "Estado",
            "id_tipo_mantencion": "Tipo de mantención",
            "id_prioridad": "Prioridad",
            "fecha": "Fecha",
            "descripcion": "Descripción",
        }
