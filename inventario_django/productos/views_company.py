# inventario_django/productos/views_company.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from .models_inventario import Empresa

def company_select(request):
    """
    Vista que permite seleccionar la empresa de trabajo.
    
    Muestra una lista de empresas disponibles para que el usuario pueda seleccionar 
    la empresa con la que desea trabajar. Se presenta en un template donde se muestran 
    todas las empresas ordenadas alfabéticamente.
    
    Si el usuario no ha seleccionado una empresa previamente, esta vista le permite 
    elegir una para continuar con el proceso.
    """
    empresas = Empresa.objects.order_by("nombre_empresa")
    return render(request, "accounts/company_select.html", {"empresas": empresas})

def set_company(request, empresa_id):
    """
    Vista que guarda la empresa seleccionada en la sesión del usuario.
    
    Recibe un `empresa_id` a través del POST, busca la empresa correspondiente en la base de datos,
    y guarda la información de la empresa seleccionada en la sesión del usuario. Luego redirige 
    al dashboard de productos.
    
    Si la solicitud no es un POST, redirige al selector de empresas.
    """
    if request.method != "POST":
        return redirect("company_select")

    empresa_id = request.POST.get("empresa_id")
    emp = get_object_or_404(Empresa, pk=empresa_id)
    request.session["empresa_nombre"] = emp.nombre_empresa  # 👈 nuevo

    request.session["empresa_id"] = emp.id_empresa
    emp = Empresa.objects.get(pk=empresa_id)
    request.session["empresa_nombre"] = emp.nombre_empresa
    request.session["empresa_slug"] = slugify(emp.nombre_empresa or "")
    #return redirect("productos:dashboard")
    return redirect("productos:activos_list")

def company_change(request):
    """
    Vista para cambiar la empresa seleccionada o eliminarla de la sesión.
    
    Esta vista limpia la información de la empresa en la sesión del usuario, permitiéndole 
    seleccionar una nueva empresa en el futuro. Luego, redirige al selector de empresas para 
    que el usuario elija una empresa nueva.
    """
    request.session.pop("empresa_id", None)
    request.session.pop("empresa_nombre", None)
    request.session.pop("empresa_slug", None)
    return redirect("company_select")
