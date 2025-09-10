# productos/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count
from .crud import get_crud_configs


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import MantencionForm
from .models_inventario import Mantencion, HistorialMantencionesLog

# modelos opcionales (según tu app)
try:
    from .models_inventario import (
        Equipo, TipoEquipo, Mantencion
    )
except Exception:
    Equipo = TipoEquipo = Mantencion = None


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "overview/home_sidebar.html"
    login_url = "login"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Menú lateral
        menu = []
        for cfg in get_crud_configs():
            try:
                count = cfg.model.objects.count()
            except Exception:
                count = 0
            menu.append({
                "name": cfg.verbose_name_plural,
                "slug": cfg.slug,
                "count": count,
                "icon": getattr(cfg, "icon", "bi-folder2")  # fallback
            })
        ctx["menu"] = menu

        # KPIs
        total_equipos = Equipo.objects.count() if Equipo else 0
        disponibles = Equipo.objects.filter(
            id_estado_equipo__descripcion__iexact="Disponible"
        ).count() if Equipo else 0
        en_uso = Equipo.objects.filter(
            id_estado_equipo__descripcion__iexact="En uso"
        ).count() if Equipo else 0
        mant_pend = Mantencion.objects.filter(
            id_estado_mantencion__tipo__iexact="Pendiente"
        ).count() if Mantencion else 0

        ctx.update({
            "total_equipos": total_equipos,
            "disponibles": disponibles,
            "en_uso": en_uso,
            "mantenciones_pendientes": mant_pend,
        })

        # Listas recientes
        ctx["ultimos_equipos"] = (
            Equipo.objects.select_related("id_marca", "id_tipo_equipo")
            .order_by("-id_equipo")[:6]
        ) if Equipo else []

        ctx["ultimas_mantenciones"] = (
            Mantencion.objects.select_related("id_equipo", "id_estado_mantencion")
            .order_by("-id_mantencion")[:6]
        ) if Mantencion else []

        # Gráficos
        if Equipo and TipoEquipo:
            datos = (
                Equipo.objects.values("id_tipo_equipo__tipo_equipo")
                .annotate(n=Count("id_equipo"))
                .order_by("id_tipo_equipo__tipo_equipo")
            )
            ctx["chart_tipos_labels"] = [
                d["id_tipo_equipo__tipo_equipo"] or "Sin tipo" for d in datos
            ]
            ctx["chart_tipos_values"] = [d["n"] for d in datos]
        else:
            ctx["chart_tipos_labels"] = []
            ctx["chart_tipos_values"] = []

        if Mantencion:
            datos = (
                Mantencion.objects.values("id_estado_mantencion__tipo")
                .annotate(n=Count("id_mantencion"))
                .order_by("id_estado_mantencion__tipo")
            )
            ctx["chart_mant_labels"] = [
                d["id_estado_mantencion__tipo"] or "Sin estado" for d in datos
            ]
            ctx["chart_mant_values"] = [d["n"] for d in datos]
        else:
            ctx["chart_mant_labels"] = []
            ctx["chart_mant_values"] = []

        return ctx

def _log_mantencion_snapshot(mant: Mantencion, accion: str, user, detalle: str = ""):
    HistorialMantencionesLog.objects.create(
        id_mantencion=mant.id_mantencion,
        fecha_evento=timezone.now(),
        accion=accion,
        detalle=detalle or "",
        usuario_app_username=getattr(user, 'username', ''),

        id_equipo=mant.id_equipo_id,
        etiqueta=getattr(mant.id_equipo, 'etiqueta', None),
        equipo_nombre=str(mant.id_equipo)[:150] if mant.id_equipo else None,

        tipo_mantencion=str(mant.id_tipo_mantencion) if mant.id_tipo_mantencion else None,
        prioridad=str(mant.id_prioridad) if mant.id_prioridad else None,
        estado_actual=str(mant.id_estado_mantencion) if mant.id_estado_mantencion else None,

        responsable_nombre=str(mant.responsable) if mant.responsable else None,
        solicitante_nombre=str(mant.solicitante_user) if mant.solicitante_user else None,

        descripcion=mant.descripcion or "",
    )

@login_required
def mantencion_nueva(request):
    if request.method == 'POST':
        form = MantencionForm(request.POST, request=request)
        if form.is_valid():
            mant = form.save(commit=False)
            # solicitante = usuario logueado
            mant.solicitante_user = request.user
            # si asignado_a va vacío, el form ya lo igualó a responsable
            mant.save()
            _log_mantencion_snapshot(mant, 'ALTA', request.user, 'Alta de mantención')
            return redirect('mantenciones_list')
    else:
        form = MantencionForm(request=request)
    return render(request, 'mantenciones/nueva.html', {'form': form})

@login_required
def mantencion_editar(request, pk):
    mant = get_object_or_404(Mantencion, pk=pk)
    estado_ant = mant.id_estado_mantencion_id
    asignado_ant = mant.asignado_a_id
    if request.method == 'POST':
        form = MantencionForm(request.POST, instance=mant, request=request)
        if form.is_valid():
            mant = form.save()
            if mant.id_estado_mantencion_id != estado_ant:
                _log_mantencion_snapshot(mant, 'ESTADO', request.user, 'Cambio de estado')
            if mant.asignado_a_id != asignado_ant:
                _log_mantencion_snapshot(mant, 'ASIGN', request.user, 'Asignación/Reasignación')
            _log_mantencion_snapshot(mant, 'EDICION', request.user, 'Edición de mantención')
            return redirect('mantenciones_list')
    else:
        form = MantencionForm(instance=mant, request=request)
    return render(request, 'mantenciones/editar.html', {'form': form, 'mantencion': mant})