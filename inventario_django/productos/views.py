# productos/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count
from .crud import get_crud_configs

from django.views.generic import ListView
from .models_inventario import Equipo
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.shortcuts import redirect

from .models_inventario import Equipo, Empleado, EstadoEquipo, HistorialEquipos


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
            id_estado_equipo__descripcion__iexact="bodega",
            id_empleado__isnull=True
        ).count() if Equipo else 0


        en_uso = Equipo.objects.filter(
            id_empleado__isnull=False
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

class EquiposDisponiblesView(LoginRequiredMixin, TemplateView):
    template_name = "equipos/disponibles_asignar.html"

    def get_queryset_disponibles(self):
        return (
            Equipo.objects
            .select_related("id_marca", "id_tipo_equipo", "id_estado_equipo")
            .filter(
                id_estado_equipo__descripcion__iexact="bodega",
                id_empleado__isnull=True,
            )
            .order_by("-id_equipo")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset_disponibles()
        ctx["equipos"] = qs
        ctx["total"] = qs.count()
        ctx["empleados"] = (
            Empleado.objects
            .filter(activo=True)
            .order_by("nombre", "apellido_paterno")
        )
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # 1) Obtener selección
        ids = request.POST.getlist("equipos")
        empleado_id = request.POST.get("empleado_id")

        if not ids:
            messages.warning(request, "Selecciona al menos un equipo.")
            return redirect(request.path)

        if not empleado_id:
            messages.warning(request, "Selecciona un empleado destino.")
            return redirect(request.path)

        try:
            empleado = Empleado.objects.get(pk=empleado_id, activo=True)
        except Empleado.DoesNotExist:
            messages.error(request, "El empleado seleccionado no existe o está inactivo.")
            return redirect(request.path)

        # 2) Validar que TODOS sigan disponibles
        qs = (
            Equipo.objects
            .select_for_update()
            .filter(
                id_equipo__in=ids,
                id_estado_equipo__descripcion__iexact="bodega",
                id_empleado__isnull=True,
            )
        )

        faltantes = set(map(int, ids)) - set(qs.values_list("id_equipo", flat=True))
        if faltantes:
            messages.error(
                request,
                f"Algunos equipos ya no están disponibles (IDs: {', '.join(map(str, faltantes))})."
            )
            return redirect(request.path)

        # 3) Estado 'asignado'
        try:
            estado_asignado = EstadoEquipo.objects.get(descripcion__iexact="asignado")
        except EstadoEquipo.DoesNotExist:
            messages.error(request, "No existe el estado 'asignado' en la tabla estado_equipo.")
            return redirect(request.path)

        ahora = timezone.now()
        usuario_empleado = getattr(request.user, "empleado", None)

        # 4) Actualizar + historial
        historiales = []
        for e in qs:
            historiales.append(HistorialEquipos(
                equipo=e,
                etiqueta=e.etiqueta,
                nombre_equipo=e.nombre_equipo,
                fecha=ahora,
                    # ⬇️ CAMBIO: usar el campo verdadero, no la propiedad
                responsable_anterior_fk=e.id_empleado,   # None (bodega)
                estado_anterior=e.id_estado_equipo,      # bodega
                #responsable_anterior=e.id_empleado,   # None (bodega)
                #estado_anterior=e.id_estado_equipo,   # bodega
                estado_nuevo=estado_asignado,
                responsable_actual=empleado,
                empresa=getattr(empleado, "id_empresa", None),
                departamento=getattr(empleado, "id_departamento", None),
                usuario=usuario_empleado,
                accion="ASIGNACION MASIVA",
                tipo_equipo=getattr(e, "id_tipo_equipo", None),
            ))

            e.id_empleado = empleado
            e.id_estado_equipo = estado_asignado
            #e.fecha_modificacion = ahora  # si existe el campo en BD

        Equipo.objects.bulk_update(qs, ["id_empleado", "id_estado_equipo"])
        if historiales:
            HistorialEquipos.objects.bulk_create(historiales, ignore_conflicts=True)

        messages.success(
            request,
            f"Se asignaron {qs.count()} equipo(s) a {empleado.nombre} {empleado.apellido_paterno}."
        )
        return redirect(request.path)