# productos/views_atributos.py
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelformset_factory
from django.db import transaction
from .models_inventario import TipoEquipo, AtributosEquipo
from django import forms
from django.contrib import messages
from django.urls import reverse


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
    # 👇 IMPORTANTE: definir aquí, fuera del if POST/GET
    FormSet = modelformset_factory(
        AtributosEquipo,
        form=AttrForm,
        extra=0,          # sin filas extra (las añades con el botón "+")
        can_delete=True   # checkbox "Eliminar" en filas existentes
    )

    qs = AtributosEquipo.objects.filter(id_tipo_equipo=tipo_id).order_by("atributo")
    

    if request.method == "POST":
        formset = FormSet(request.POST, queryset=qs, prefix="attrs")
        if formset.is_valid():
            with transaction.atomic():
                objs = formset.save(commit=False)

                # asigna el tipo a los nuevos/actualizados
                for obj in objs:
                    obj.id_tipo_equipo_id = tipo_id
                    obj.save()

                # elimina marcados
                for obj in formset.deleted_objects:
                    obj.delete()

            messages.success(request, "Atributos actualizados correctamente.")  # ✅ feedback
            return redirect("productos:atributosquipos_list")

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


def atributos_nuevo_wizard(request):
    """
    Paso previo a crear atributos: elige el Tipo de equipo y
    redirigimos a la pantalla de 'Editar atributos' para ese tipo.
    Así el usuario puede añadir varias filas de una vez.
    """
    if request.method == "POST":
        tipo_id = request.POST.get("tipo_id") or request.POST.get("id_tipo_equipo")
        if tipo_id:
            # Después de guardar, vuelve al listado de atributos (no a tipo equipos)
            next_url = reverse("productos:atributosequipos_list")
            edit_url = reverse("productos:editar_atributos_por_tipo", kwargs={"tipo_id": tipo_id})
            return redirect(f"{edit_url}?next={next_url}")

    tipos = TipoEquipo.objects.order_by("tipo_equipo")
    return render(request, "atributos/nuevo_selector_tipo.html", {"tipos": tipos})