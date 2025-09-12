# inventario_django/productos/views_company.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from .models_inventario import Empresa

def company_select(request):
    empresas = Empresa.objects.order_by("nombre_empresa")
    return render(request, "accounts/company_select.html", {"empresas": empresas})

def set_company(request):
    if request.method != "POST":
        return redirect("company_select")

    empresa_id = request.POST.get("empresa_id")
    emp = get_object_or_404(Empresa, pk=empresa_id)

    request.session["empresa_id"] = emp.id_empresa
    request.session["empresa_nombre"] = emp.nombre_empresa
    request.session["empresa_slug"] = slugify(emp.nombre_empresa or "")

    return redirect("login")

def company_change(request):
    """Borra la empresa de la sesión y vuelve a la pantalla de selección."""
    request.session.pop("empresa_id", None)
    request.session.pop("empresa_nombre", None)
    request.session.pop("empresa_slug", None)
    return redirect("company_select")
