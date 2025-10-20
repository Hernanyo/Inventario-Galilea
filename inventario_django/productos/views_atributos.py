# productos/views_atributos.py
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelformset_factory
from django.db import transaction
from .models_inventario import TipoActivo, AtributosActivo
from django import forms
from django.contrib import messages
from django.urls import reverse
from django.utils.http import urlencode 
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils.http import urlencode


class AttrForm(forms.ModelForm):
    """
    Formulario para editar atributos de un activo.
    Genera el formulario para el modelo AtributosActivo.
    """
    class Meta:
        model = AtributosActivo
        fields = ("atributo", "valor")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control").strip()
#1##################################################################################################24-09-2025
def atributosactivos_list(request):
    """
    Muestra el listado de tipos de activos disponibles en la empresa activa.
    Filtra los tipos de activos según la empresa activa.
    """
    emp_id = request.session.get("empresa_id")
    tipos = TipoActivo.objects.all()
    if emp_id:
        tipos = tipos.filter(id_empresa_id=emp_id).order_by("tipo_activo")

    return render(request, "atributos/list.html", {
        "tipos_activo": tipos,
        "crud_config": {
            "model_name": "atributosactivo",
            "verbose_name": "Atributo de activo",
            "verbose_name_plural": "Atributos de Activos",
            "slug": "atributosactivos",
            "can_create": True
        }
    })

#2##################################################################################################24-09-2025

@login_required
def editar_atributos_por_tipo(request, tipo_id):
    """
    Permite editar los atributos de un tipo de activo específico.
    Solo los atributos de ese tipo se pueden editar o eliminar.
    """
    tipo = get_object_or_404(TipoActivo, pk=tipo_id)

    emp_id = request.session.get("empresa_id")
    if emp_id and tipo.id_empresa_id != emp_id:
        raise Http404("Tipo no pertenece a la empresa actual.")

    FormSet = modelformset_factory(
        AtributosActivo,
        form=AttrForm,
        extra=0,
        can_delete=True
    )

    qs = AtributosActivo.objects.filter(id_tipo_activo=tipo_id).order_by("atributo")

    if request.method == "POST":
        formset = FormSet(request.POST, queryset=qs, prefix="attrs")
        if formset.is_valid():
            with transaction.atomic():
                objs = formset.save(commit=False)

                for obj in objs:
                    obj.id_tipo_activo_id = tipo_id
                    obj.id_empresa_id = tipo.id_empresa_id
                    obj.save()

                for obj in formset.deleted_objects:
                    obj.delete()

            messages.success(request, "Atributos actualizados correctamente.")

            # 👇 si apretaron "Guardar y seguir aquí", vuelve a esta misma vista
            if "save_stay" in request.POST:
                # preserva ?next=... si venía
                next_url = request.GET.get("next") or request.POST.get("next")
                url = reverse("productos:editar_atributos_por_tipo", kwargs={"tipo_id": tipo.pk})
                if next_url:
                    url = f"{url}?{urlencode({'next': next_url})}"
                return redirect(url)

            # Flujo normal: ir al listado
            return redirect("productos:atributosactivos_list")
    else:
        formset = FormSet(queryset=qs, prefix="attrs")

    return render(request, "atributos/editar_por_tipo.html", {
        "tipo": tipo,
        "formset": formset,
    })

# Vista “ver” (solo lectura) para mostrar muchos atributos en su propia página.
def ver_atributos_por_tipo(request, tipo_id):
    tipo = get_object_or_404(TipoActivo, pk=tipo_id)
    emp_id = request.session.get("empresa_id")
    if emp_id and tipo.id_empresa_id != emp_id:
        raise Http404("Tipo no pertenece a la empresa actual.")
    
    attrs = AtributosActivo.objects.filter(id_tipo_activo=tipo_id).order_by("atributo")
    return render(request, "atributos/ver_por_tipo.html", {
        "tipo": tipo,
        "attrs": attrs,
    })


def atributos_nuevo_wizard(request):
    """
    Paso previo a crear atributos: elige el Tipo de activo y
    redirigimos a la pantalla de 'Editar atributos' para ese tipo.
    Así el usuario puede añadir varias filas de una vez.
    """
    emp_id = request.session.get("empresa_id")
    print("Empresa ID en atributos_nuevo_wizard:", emp_id)  # Depuración
    tipos = TipoActivo.objects.all()
    if emp_id:
        tipos = tipos.filter(id_empresa_id=emp_id)


    if request.method == "POST":
        tipo_id = request.POST.get("tipo_id") or request.POST.get("id_tipo_activo")
        if tipo_id:
            tipo = get_object_or_404(TipoActivo, pk=tipo_id)
            if emp_id and tipo.id_empresa_id != emp_id:
                raise Http404("Tipo no pertenece a la empresa actual.")
            # Después de guardar, vuelve al listado de atributos (no a tipo activos)
            next_url = reverse("productos:atributosactivos_list")
            edit_url = reverse("productos:editar_atributos_por_tipo", kwargs={"tipo_id": tipo_id})
            return redirect(f"{edit_url}?next={next_url}")

    #tipos = TipoActivo.objects.order_by("tipo_activo")
    tipos = tipos.order_by("tipo_activo")
    return render(request, "atributos/nuevo_selector_tipo.html", {"tipos": tipos})
