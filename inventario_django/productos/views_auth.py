# productos/views_auth.py
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.text import slugify
from .models_inventario import Empresa

def seleccionar_empresa(request):
    """
    Pantalla previa al login: elige empresa y guardamos en sesión.
    Luego redirige al login normal.
    """
    # <----- AÑADIR AQUÍ: lee el "next" entrante para preservarlo
    next_url = request.GET.get("next") or request.POST.get("next") or ""

    if request.method == "POST":
        empresa_id = request.POST.get("empresa_id")
        emp = Empresa.objects.filter(pk=empresa_id).first()
        if emp:
            request.session["empresa_id"] = emp.id_empresa
            request.session["empresa_nombre"] = emp.nombre_empresa
            request.session["empresa_slug"] = slugify(emp.nombre_empresa or "")

        login_url = reverse("login")
        # <----- AÑADIR AQUÍ: si venía ?next=, lo mantenemos
        if next_url:
            return redirect(f"{login_url}?next={next_url}")
        return redirect(login_url)

    empresas = Empresa.objects.all().order_by("nombre_empresa")
    return render(
        request,
        "auth/seleccionar_empresa.html",
        {"empresas": empresas, "next": next_url},  # <----- AÑADIR next al contexto
    )

# <----- AÑADIR ESTA VISTA NUEVA (para el link 'company_change' en tu login.html)
def cambiar_empresa(request):
    """
    Limpia la empresa de la sesión y vuelve al selector.
    Preserva ?next= si venía.
    """
    next_url = request.GET.get("next") or ""
    for key in ("empresa_id", "empresa_nombre", "empresa_slug"):
        request.session.pop(key, None)

    select_url = reverse("productos:company_select")
    if next_url:
        return redirect(f"{select_url}?next={next_url}")
    return redirect(select_url)