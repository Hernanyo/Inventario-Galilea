# productos/forms.py
from django import forms
from .models import Activo  # o desde models_inventario

class ActivoForm(forms.ModelForm):
    class Meta:
        model = Activo
        fields = "__all__"  # rápido como el admin; si quieres, lista campos específicos
