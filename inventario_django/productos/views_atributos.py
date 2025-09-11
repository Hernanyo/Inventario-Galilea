# productos/views_atributos.py
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelformset_factory
from django.db import transaction
from .models_inventario import TipoEquipo, AtributosEquipo
from django import forms


class AttrForm(forms.ModelForm):
    class Meta:
        model = AtributosEquipo
        fields = ("atributo", "valor")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control").strip()


def editar_atributos_por_tipo(request, tipo_id):
    tipo = get_object_or_404(TipoEquipo, pk=tipo_id)

    FormSet = modelformset_factory(
        AtributosEquipo,
        form=AttrForm,      # ← estilos aquí, sin add_class en template
        extra=0,           # una fila en blanco
        can_delete=True    # permitir borrar filas
    )

    qs = AtributosEquipo.objects.filter(id_tipo_equipo=tipo_id).order_by("atributo")

    if request.method == "POST":
        formset = FormSet(request.POST, queryset=qs, prefix="attrs")
        if formset.is_valid():
            with transaction.atomic():
                # guarda existentes / borrados
                objs = formset.save(commit=False)

                # asigna el tipo a los nuevos
                for obj in objs:
                    obj.id_tipo_equipo_id = tipo_id
                    obj.save()

                # procesar eliminados
                for obj in formset.deleted_objects:
                    obj.delete()

            return redirect("productos:editar_atributos_por_tipo", tipo_id=tipo_id)
    else:
        formset = FormSet(queryset=qs, prefix="attrs")

    return render(request, "atributos/editar_por_tipo.html", {
        "tipo": tipo,
        "formset": formset,
    })
# Vista “ver” (solo lectura) para mostrar muchos atributos en su propia página.
def ver_atributos_por_tipo(request, tipo_id):
    tipo = get_object_or_404(TipoEquipo, pk=tipo_id)
    attrs = AtributosEquipo.objects.filter(id_tipo_equipo=tipo_id).order_by("atributo")
    return render(request, "atributos/ver_por_tipo.html", {
        "tipo": tipo,
        "attrs": attrs,
    })