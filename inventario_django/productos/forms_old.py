# productos/forms.py
from django import forms
from .models import Equipo  # o desde models_inventario

class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = "__all__"  # rápido como el admin; si quieres, lista campos específicos
