# productos/views.py
from datetime import date, timedelta
import calendar

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Sum
from django.shortcuts import render

from .models_inventario import (
    Equipo, TipoEquipo, EstadoEquipo, Marca, Empleado,
    Mantencion, EstadoMantencion, AtributosEquipo,
    Proveedor, Factura, DetalleFactura
)

# ---------------------------
# Lista de equipos
# ---------------------------
@method_decorator(login_required(login_url='login'), name='dispatch')
class EquiposListView(ListView):
    model = Equipo
    template_name = 'equipos/list.html'      # coincide con /templates/equipos/list.html
    context_object_name = 'equipos'
    paginate_by = 20

    def get_queryset(self):
        qs = (
            Equipo.objects
            .select_related('id_marca', 'id_tipo_equipo', 'id_estado_equipo', 'id_empleado')
            .order_by('nombre_equipo')
        )

        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(nombre_equipo__icontains=q) |
                Q(id_marca__nombre_marca__icontains=q) |
                Q(id_tipo_equipo__tipo_equipo__icontains=q) |
                Q(id_empleado__nombre__icontains=q) |
                Q(id_empleado__apellido_paterno__icontains=q) |
                Q(id_empleado__apellido_materno__icontains=q)
            )

        tipo = self.request.GET.get('tipo')
        if tipo:
            qs = qs.filter(id_tipo_equipo_id=tipo)

        estado = self.request.GET.get('estado')
        if estado:
            qs = qs.filter(id_estado_equipo_id=estado)

        marca = self.request.GET.get('marca')
        if marca:
            qs = qs.filter(id_marca_id=marca)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tipos'] = TipoEquipo.objects.all().order_by('tipo_equipo')
        ctx['estados'] = EstadoEquipo.objects.all().order_by('descripcion')
        ctx['marcas'] = Marca.objects.all().order_by('nombre_marca')
        # mantener selección del usuario
        ctx['q'] = self.request.GET.get('q', '')
        ctx['tipo_sel'] = self.request.GET.get('tipo', '')
        ctx['estado_sel'] = self.request.GET.get('estado', '')
        ctx['marca_sel'] = self.request.GET.get('marca', '')
        return ctx


# ---------------------------
# Detalle de un equipo
# ---------------------------
@method_decorator(login_required(login_url='login'), name='dispatch')
class EquipoDetailView(DetailView):
    model = Equipo
    pk_url_kwarg = 'equipo_id'
    template_name = 'equipos/detalle.html'   # <-- corregido (antes: 'equipos/detail.html')
    context_object_name = 'equipo'

    def get_queryset(self):
        return (
            Equipo.objects
            .select_related('id_marca', 'id_tipo_equipo', 'id_estado_equipo', 'id_empleado', 'id_proveedor')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        eq = self.object
        ctx['mantenciones'] = (
            Mantencion.objects
            .filter(id_equipo=eq)
            .select_related('id_estado_mantencion')
            .order_by('-fecha', '-id_mantencion')[:20]
        )
        ctx['atributos'] = (
            AtributosEquipo.objects
            .filter(id_tipo_equipo=eq.id_tipo_equipo)
            .order_by('atributo')
        )
        return ctx


# ---------------------------
# Dashboard (home)
# ---------------------------
@login_required(login_url='login')
def home(request):
    # --- TARJETAS PRINCIPALES ---
    total_equipos = Equipo.objects.count()

    # Ajusta estos textos según los valores reales de tu tabla estado_equipo
    disponibles = Equipo.objects.filter(id_estado_equipo__descripcion__iexact="Disponible").count()
    en_uso = Equipo.objects.filter(id_estado_equipo__descripcion__iexact="En uso").count()

    # Mantenciones (ajusta si tus estados son otros)
    mant_pendientes = Mantencion.objects.filter(
        id_estado_mantencion__tipo__iexact="Pendiente"
    ).count()

    # --- TABLAS (recientes) ---
    ultimos_equipos = (
        Equipo.objects
        .select_related('id_marca', 'id_tipo_equipo', 'id_estado_equipo', 'id_empleado')
        .order_by('-id_equipo')[:10]
    )

    ultimas_mantenciones = (
        Mantencion.objects
        .select_related('id_equipo', 'id_estado_mantencion')
        .order_by('-id_mantencion')[:10]
    )

    ultimas_facturas = (
        Factura.objects
        .select_related('id_proveedor')
        .order_by('-id_factura')[:10]
    )

    # --- GRÁFICOS ---
    # 1) Equipos por tipo
    equipos_por_tipo = (
        Equipo.objects
        .values('id_tipo_equipo__tipo_equipo')
        .annotate(total=Count('id_equipo'))
        .order_by('id_tipo_equipo__tipo_equipo')
    )
    chart_tipos_labels = [e['id_tipo_equipo__tipo_equipo'] or 'Sin tipo' for e in equipos_por_tipo]
    chart_tipos_values = [e['total'] for e in equipos_por_tipo]

    # 2) Equipos por marca (top 10)
    equipos_por_marca = (
        Equipo.objects
        .values('id_marca__nombre_marca')
        .annotate(total=Count('id_equipo'))
        .order_by('-total')[:10]
    )
    chart_marcas_labels = [e['id_marca__nombre_marca'] or 'Sin marca' for e in equipos_por_marca]
    chart_marcas_values = [e['total'] for e in equipos_por_marca]

    # 3) Mantenciones por estado (torta)
    mant_por_estado = (
        Mantencion.objects
        .values('id_estado_mantencion__tipo')
        .annotate(total=Count('id_mantencion'))
        .order_by('id_estado_mantencion__tipo')
    )
    chart_mant_labels = [m['id_estado_mantencion__tipo'] or 'Sin estado' for m in mant_por_estado]
    chart_mant_values = [m['total'] for m in mant_por_estado]

    # 4) Gasto mensual (últimos 6 meses)
    hoy = date.today()
    seis_meses_atras = (hoy.replace(day=1) - timedelta(days=180)).replace(day=1)

    gastos_por_mes = (
        DetalleFactura.objects
        .filter(id_factura__fecha_emision__gte=seis_meses_atras)
        .values('id_factura__fecha_emision__year', 'id_factura__fecha_emision__month')
        .annotate(gasto=Sum('valor_total'))
        .order_by('id_factura__fecha_emision__year', 'id_factura__fecha_emision__month')
    )

    # Normalizamos los meses faltantes
    labels_line = []
    cur = seis_meses_atras
    while cur <= hoy:
        labels_line.append((cur.year, cur.month))
        cur = date(cur.year + 1, 1, 1) if cur.month == 12 else date(cur.year, cur.month + 1, 1)

    dic_gastos = {
        (g['id_factura__fecha_emision__year'], g['id_factura__fecha_emision__month']): (g['gasto'] or 0)
        for g in gastos_por_mes
    }
    chart_gastos_labels = [f"{calendar.month_abbr[m]}-{y}" for (y, m) in labels_line]
    chart_gastos_values = [dic_gastos.get((y, m), 0) for (y, m) in labels_line]

    context = {
        # tarjetas
        "total_equipos": total_equipos,
        "disponibles": disponibles,
        "en_uso": en_uso,
        "mantenciones_pendientes": mant_pendientes,
        # tablas
        "ultimos_equipos": ultimos_equipos,
        "ultimas_mantenciones": ultimas_mantenciones,
        "ultimas_facturas": ultimas_facturas,
        # charts
        "chart_tipos_labels": chart_tipos_labels,
        "chart_tipos_values": chart_tipos_values,
        "chart_marcas_labels": chart_marcas_labels,
        "chart_marcas_values": chart_marcas_values,
        "chart_mant_labels": chart_mant_labels,
        "chart_mant_values": chart_mant_values,
        "chart_gastos_labels": chart_gastos_labels,
        "chart_gastos_values": chart_gastos_values,
    }

    # productos/views.py
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import HttpResponse
import csv

from .mixins import ModelPermsMixin
from .forms import EquipoForm
from .models import Equipo  # o desde models_inventario

class EquipoList(ModelPermsMixin, ListView):
    model = Equipo
    template_name = "equipos/list.html"
    context_object_name = "items"
    paginate_by = 25
    action_perm = "view"

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q", "").strip()
        o = self.request.GET.get("o", "")
        if q:
            # Ajusta campos a los que te convenga buscar
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(serie__icontains=q) |
                Q(modelo__icontains=q)
            )
        if o:
            qs = qs.order_by(o)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["o"] = self.request.GET.get("o", "")
        return ctx

class EquipoCreate(ModelPermsMixin, CreateView):
    model = Equipo
    form_class = EquipoForm
    template_name = "equipos/detalle.html"  # usas tu plantilla existente
    success_url = reverse_lazy("productos:equipos_list")
    action_perm = "add"

class EquipoUpdate(ModelPermsMixin, UpdateView):
    model = Equipo
    form_class = EquipoForm
    template_name = "equipos/detalle.html"
    success_url = reverse_lazy("productos:equipos_list")
    action_perm = "change"

class EquipoDelete(ModelPermsMixin, DeleteView):
    model = Equipo
    template_name = "equipos/confirm_delete.html"
    success_url = reverse_lazy("productos:equipos_list")
    action_perm = "delete"

def equipos_csv(request):
    """Exporta a CSV lo que estás viendo/filtrando en la lista."""
    from django.contrib.auth.decorators import permission_required
    # chequeo manual de permiso (mismo que la lista)
    if not request.user.has_perm(f"{Equipo._meta.app_label}.view_{Equipo._meta.model_name}"):
        return HttpResponse(status=403)

    q = request.GET.get("q", "").strip()
    rows = Equipo.objects.all()
    if q:
        rows = rows.filter(
            Q(nombre__icontains=q) |
            Q(serie__icontains=q) |
            Q(modelo__icontains=q)
        )

    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = 'attachment; filename="equipos.csv"'
    w = csv.writer(resp)
    w.writerow(["ID", "Nombre", "Serie", "Modelo", "Estado", "Ubicación"])
    for r in rows:
        w.writerow([r.id, getattr(r, "nombre", ""), getattr(r, "serie", ""),
                    getattr(r, "modelo", ""), getattr(r, "estado", ""),
                    getattr(r, "ubicacion", "")])
    return resp

    return render(request, "home.html", context)
