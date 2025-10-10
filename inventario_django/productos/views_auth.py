# productos/views_auth.py
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.text import slugify
from .models_inventario import Empresa
from django.shortcuts import redirect
from django.contrib import messages


def seleccionar_empresa(request):
    """
    Vista para seleccionar la empresa antes de iniciar sesión.
    
    Permite al usuario elegir una empresa desde una lista y guarda esa empresa en la sesión 
    para que se mantenga disponible durante el proceso de login. Si hay una URL de redirección 
    pendiente (almacenada en el parámetro "next"), la vista asegura que el usuario sea redirigido 
    a dicha URL después de seleccionar la empresa.
    
    Si el usuario hace un POST, la empresa seleccionada se guarda en la sesión y se redirige 
    al login. Si la URL contiene un parámetro "next", este se preserva para ser utilizado 
    después del login. En caso contrario, se redirige directamente al login.
    
    Si la solicitud es GET, muestra un formulario para elegir la empresa disponible y redirige 
    a la vista correspondiente.
    """
    # <----- AÑADIR AQUÍ: lee el "next" entrante para preservarlo
    next_url = request.GET.get("next") or request.POST.get("next") or ""

    if request.method == "POST":
        empresa_id = request.POST.get("empresa_id")
        print(f"empresa_id recibido: {empresa_id}")  # Depuración: Verifica el valor de empresa_id
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
    Vista para cambiar la empresa seleccionada en la sesión.

    Limpia los datos de la empresa de la sesión y redirige al selector de empresas. Si se proporciona
    un parámetro "next" en la URL, se preserva para redirigir al usuario después de seleccionar la nueva empresa.
    """
    next_url = request.GET.get("next") or ""
    for key in ("empresa_id", "empresa_nombre", "empresa_slug"):
        request.session.pop(key, None)

    select_url = reverse("productos:company_select")
    if next_url:
        return redirect(f"{select_url}?next={next_url}")
    return redirect(select_url)