# productos/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count
from .crud import get_crud_configs
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, render, redirect
from django.forms import inlineformset_factory
from django.contrib import messages
from .models_inventario import TipoEquipo, AtributosEquipo
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
from django.http import JsonResponse
from .models_inventario import AtributosEquipo
from .mixins import CompanyRequiredMixin

# modelos opcionales (según tu app)
try:
    from .models_inventario import (
        Equipo, TipoEquipo, Mantencion
    )
except Exception:
    Equipo = TipoEquipo = Mantencion = None


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "overview/home_sidebar.html"
    login_url = reverse_lazy("productos:company_select")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Empresa actual
        emp_id = self.request.session.get("empresa_id")

        # ===== Menú lateral (filtrado por empresa cuando aplique) =====
        menu = []
        for cfg in get_crud_configs():
            try:
                names = {f.name for f in cfg.model._meta.get_fields()}
                if emp_id:
                    if "id_empresa" in names:
                        count = cfg.model.objects.filter(id_empresa=emp_id).count()
                    elif "empresa" in names:
                        count = cfg.model.objects.filter(empresa_id=emp_id).count()
                    elif "id_equipo" in names:
                        count = cfg.model.objects.filter(id_equipo__id_empresa=emp_id).count()
                    else:
                        count = cfg.model.objects.count()
                else:
                    count = cfg.model.objects.count()
            except Exception:
                count = 0

            menu.append({
                "name": cfg.verbose_name_plural,
                "slug": cfg.slug,
                "count": count,
                "icon": getattr(cfg, "icon", "bi-folder2"),
            })
        ctx["menu"] = menu

        # ===== KPIs, listas y gráficos (todo filtrado por empresa) =====
        # Equipos
        qs_equipos = Equipo.objects.all()
        if emp_id:
            qs_equipos = qs_equipos.filter(id_empresa=emp_id)

        total_equipos = qs_equipos.count()
        disponibles   = qs_equipos.filter(id_empleado__isnull=True).count()
        en_uso        = qs_equipos.filter(id_empleado__isnull=False).count()

        # Mantenciones (con fallback si el modelo no tiene id_empresa)
        Mant = Mantencion  # ya importado arriba
        qs_mant = Mant.objects.all() if Mant else None
        if Mant and emp_id:
            mant_fields = {f.name for f in Mant._meta.get_fields()}
            if "id_empresa" in mant_fields:
                qs_mant = qs_mant.filter(id_empresa=emp_id)
            elif "id_equipo" in mant_fields:
                qs_mant = qs_mant.filter(id_equipo__id_empresa=emp_id)

        mant_pend = 0
        ult_mant = []
        chart_mant_labels = []
        chart_mant_values = []
        if Mant and qs_mant is not None:
            mant_pend = qs_mant.exclude(
                id_estado_mantencion__tipo__in=["Cerrada", "Completada", "Cancelada"]
            ).count()
            ult_mant = (
                qs_mant.select_related("id_equipo", "id_estado_mantencion")
                      .order_by("-id_mantencion")[:6]
            )
            datos_mant = (
                qs_mant.values("id_estado_mantencion__tipo")
                      .annotate(n=Count("id_mantencion"))
                      .order_by("id_estado_mantencion__tipo")
            )
            chart_mant_labels = [d["id_estado_mantencion__tipo"] or "Sin estado" for d in datos_mant]
            chart_mant_values = [d["n"] for d in datos_mant]

        # Contexto final
        ctx.update({
            "total_equipos": total_equipos,
            "disponibles": disponibles,
            "en_uso": en_uso,
            "mantenciones_pendientes": mant_pend,
            "ultimos_equipos": qs_equipos.order_by("-id_equipo")[:15],
            "ultimas_mantenciones": ult_mant,
        })

        # Gráfico de equipos por tipo (ya con qs_equipos filtrado)
        datos_tipos = (
            qs_equipos.values("id_tipo_equipo__tipo_equipo")
                      .annotate(n=Count("id_equipo"))
                      .order_by("id_tipo_equipo__tipo_equipo")
        )
        ctx["chart_tipos_labels"] = [d["id_tipo_equipo__tipo_equipo"] or "Sin tipo" for d in datos_tipos]
        ctx["chart_tipos_values"] = [d["n"] for d in datos_tipos]

        # Gráfico de mantenciones por estado (si corresponde)
        ctx["chart_mant_labels"] = chart_mant_labels
        ctx["chart_mant_values"] = chart_mant_values

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

class EquiposDisponiblesView(CompanyRequiredMixin, TemplateView):
    template_name = "equipos/disponibles_asignar.html"

    def get_queryset_disponibles(self):
        emp_id = self.request.session.get("empresa_id")
        qs = (
            Equipo.objects
            .select_related("id_marca", "id_tipo_equipo", "id_estado_equipo")
            .filter(
                id_estado_equipo__descripcion__iexact="bodega",
                id_empleado__isnull=True,
            )
            .order_by("-id_equipo")
        )
        if emp_id:
            qs = qs.filter(id_empresa=emp_id)  # seguridad multiempresa
        return qs

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
        # IDs únicos (evita duplicados si el form manda repetidos)
        ids = request.POST.getlist("equipos")
        ids = list(dict.fromkeys(map(int, ids)))

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

        emp_id = request.session.get("empresa_id")
        qs = (
            Equipo.objects
            .select_for_update()
            .filter(
                id_equipo__in=ids,
                id_estado_equipo__descripcion__iexact="bodega",
                id_empleado__isnull=True,
            )
        )
        if emp_id:
            qs = qs.filter(id_empresa=emp_id)

        faltantes = set(ids) - set(qs.values_list("id_equipo", flat=True))
        if faltantes:
            messages.error(
                request,
                f"Algunos equipos ya no están disponibles (IDs: {', '.join(map(str, faltantes))})."
            )
            return redirect(request.path)

        try:
            estado_asignado = EstadoEquipo.objects.get(descripcion__iexact="asignado")
        except EstadoEquipo.DoesNotExist:
            messages.error(request, "No existe el estado 'asignado' en la tabla estado_equipo.")
            return redirect(request.path)

        ahora = timezone.now()
        usuario_empleado = getattr(request.user, "empleado", None)

        historiales = []
        equipos_a_actualizar = []
        for e in qs:
            prev_emp_id    = e.id_empleado_id
            prev_estado_id = e.id_estado_equipo_id

            new_emp_id    = empleado.id_empleado
            new_estado_id = estado_asignado.id_estado_equipo
            changed = (prev_emp_id != new_emp_id) or (prev_estado_id != new_estado_id)
            if not changed:
                continue  # evita doble log cuando nada cambia

            historiales.append(HistorialEquipos(
                equipo=e,
                etiqueta=e.etiqueta,
                nombre_equipo=e.nombre_equipo,
                fecha=ahora,
                responsable_anterior_fk_id=prev_emp_id,   # snapshot ANTERIOR
                estado_anterior_id=prev_estado_id,        # snapshot ANTERIOR
                estado_nuevo=estado_asignado,
                responsable_actual=empleado,
                id_empresa=getattr(empleado, "id_empresa", None),
                departamento=getattr(empleado, "id_departamento", None),
                usuario=usuario_empleado,
                accion="ASIGNACION MASIVA",
                tipo_equipo=getattr(e, "id_tipo_equipo", None),
            ))

            e.id_empleado = empleado
            e.id_estado_equipo = estado_asignado
            equipos_a_actualizar.append(e)

        if equipos_a_actualizar:
            Equipo.objects.bulk_update(equipos_a_actualizar, ["id_empleado", "id_estado_equipo"])
        if historiales:
            HistorialEquipos.objects.bulk_create(historiales, ignore_conflicts=True)

        messages.success(request, f"Se asignaron {len(equipos_a_actualizar)} equipo(s) a {empleado}.")
        return redirect(request.path)


# --- Desasignación masiva (espejo de EquiposDisponiblesView) ---
class EquiposDesasignarView(CompanyRequiredMixin, TemplateView):
    template_name = "equipos/en_uso_desasignar.html"

    def get_queryset_en_uso(self):
        emp_id = self.request.session.get("empresa_id")
        qs = (
            Equipo.objects
            .select_related("id_marca", "id_tipo_equipo", "id_estado_equipo", "id_empleado")
            .filter(id_empleado__isnull=False)
            .order_by("-id_equipo")
        )
        if emp_id:
            qs = qs.filter(id_empresa=emp_id)  # seguridad multiempresa
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset_en_uso()
        ctx["equipos"] = qs
        ctx["total"] = qs.count()
        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        emp_id = request.session.get("empresa_id")
        ids = request.POST.getlist("equipos")
        ids = list(dict.fromkeys(map(int, ids)))  # de-dupe

        if not ids:
            messages.warning(request, "Selecciona al menos un equipo.")
            return redirect(request.path)

        qs = (
            Equipo.objects
            .select_for_update()
            .filter(id_equipo__in=ids, id_empleado__isnull=False)
        )
        if emp_id:
            qs = qs.filter(id_empresa=emp_id)

        faltantes = set(ids) - set(qs.values_list("id_equipo", flat=True))
        if faltantes:
            messages.error(
                request,
                f"Algunos equipos ya no están en uso (IDs: {', '.join(map(str, faltantes))})."
            )
            return redirect(request.path)

        try:
            estado_bodega = EstadoEquipo.objects.get(descripcion__iexact="bodega")
        except EstadoEquipo.DoesNotExist:
            messages.error(request, "No existe el estado 'bodega' en la tabla estado_equipo.")
            return redirect(request.path)

        ahora = timezone.now()
        usuario_empleado = getattr(request.user, "empleado", None)

        historiales = []
        equipos_a_actualizar = []
        for e in qs:
            prev_emp_id    = e.id_empleado_id
            prev_estado_id = e.id_estado_equipo_id

            new_emp_id    = None
            new_estado_id = estado_bodega.id_estado_equipo
            changed = (prev_emp_id != new_emp_id) or (prev_estado_id != new_estado_id)
            if not changed:
                continue  # evita doble log cuando nada cambia

            historiales.append(HistorialEquipos(
                equipo=e,
                etiqueta=e.etiqueta,
                nombre_equipo=e.nombre_equipo,
                fecha=ahora,
                responsable_anterior_fk_id=prev_emp_id,  # snapshot ANTERIOR
                estado_anterior_id=prev_estado_id,       # snapshot ANTERIOR
                estado_nuevo=estado_bodega,
                responsable_actual=None,                 # vuelve a bodega
                id_empresa=e.id_empresa,
                departamento=None,
                usuario=usuario_empleado,
                accion="DESASIGNACION MASIVA",
                tipo_equipo=getattr(e, "id_tipo_equipo", None),
            ))

            e.id_empleado = None
            e.id_estado_equipo = estado_bodega
            equipos_a_actualizar.append(e)

        if equipos_a_actualizar:
            Equipo.objects.bulk_update(equipos_a_actualizar, ["id_empleado", "id_estado_equipo"])
        if historiales:
            HistorialEquipos.objects.bulk_create(historiales, ignore_conflicts=True)

        messages.success(request, f"Se desasignaron {len(equipos_a_actualizar)} equipo(s).")
        return redirect(request.path)
    
@login_required
def api_atributos_por_tipo(request):
    tipo_id = request.GET.get("tipo_id")
    if not tipo_id:
        return JsonResponse({"items": []})
    attrs = list(
        AtributosEquipo.objects
        .filter(id_tipo_equipo_id=tipo_id)
        .values("id_atributo_equipo", "atributo", "valor")  # valor = default si lo tuvieran
    )
    return JsonResponse({"items": attrs})