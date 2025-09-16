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
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from .models_inventario import Equipo, Mantencion
from django.db import connection
from .crud import GenericList, view_class

# modelos opcionales (según tu app)
try:
    from .models_inventario import (
        Equipo, TipoEquipo, Mantencion
    )
except Exception:
    Equipo = TipoEquipo = Mantencion = None

class CompanySelectView(TemplateView):
    template_name = "empresa/select_company.html"

    def get_context_data(self, **kwargs):
        from .models_inventario import Empresa
        ctx = super().get_context_data(**kwargs)
        ctx["empresas"] = Empresa.objects.order_by("nombre_empresa")
        ctx["empresa_id"] = self.request.session.get("empresa_id")
        ctx["empresa_nombre"] = self.request.session.get("empresa_nombre")
        return ctx

    def post(self, request, *args, **kwargs):
        from .models_inventario import Empresa
        emp_id = request.POST.get("empresa_id")
        try:
            emp = Empresa.objects.get(pk=emp_id)
        except Empresa.DoesNotExist:
            messages.error(request, "Empresa inválida.")
            return redirect(request.path)

        request.session["empresa_id"] = emp.id_empresa
        request.session["empresa_nombre"] = getattr(emp, "nombre_empresa", str(emp))
        messages.success(request, f"Empresa seleccionada: {request.session['empresa_nombre']}")
        return redirect("/")
    
@login_required
def company_clear(request):
    # Elimina selección actual
    request.session.pop("empresa_id", None)
    request.session.pop("empresa_nombre", None)
    messages.info(request, "Empresa deseleccionada.")
    return redirect(reverse_lazy("productos:company_select"))

class HomeView(CompanyRequiredMixin, TemplateView):
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
            qs_equipos = qs_equipos.filter(id_empresa_id=emp_id)

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
    # Nombre visible: full_name → nombre del Empleado → username
    emp = getattr(user, "empleado", None)
    visible_name = (user.get_full_name() or (str(emp) if emp else "") or user.username)

    HistorialMantencionesLog.objects.create(
        id_mantencion=mant.id_mantencion,
        fecha_evento=timezone.now(),
        accion=accion,
        detalle=detalle or "",
        usuario_app_username=visible_name,   # <<--- aquí

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
            return redirect('productos:mantencions_list')
    else:
        form = MantencionForm(request=request)
    return render(request, 'mantenciones/nueva.html', {'form': form})

@login_required
def mantencion_editar(request, pk):
    mant = get_object_or_404(Mantencion, pk=pk)

    emp_id = request.session.get("empresa_id")
    if not emp_id or (mant.id_equipo and mant.id_equipo.id_empresa_id != emp_id):
        raise Http404("Mantención no pertenece a la empresa actual.")

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
            return redirect('productos:mantencions_list')  # ver nota (d) abajo
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
                id_empleado__isnull=True,
                id_estado_equipo__descripcion__iexact="bodega",  # case-insensitive
            )
            .order_by("-id_equipo")
        )
        if emp_id:
            # si quisieras incluir equipos antiguos sin empresa, usa Q(...) | Q(id_empresa__isnull=True)
            qs = qs.filter(id_empresa_id=emp_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset_disponibles()
        ctx["equipos"] = qs
        ctx["total"] = qs.count()

        # ⬇️ Empleados SOLO de la empresa actual
        emp_id = self.request.session.get("empresa_id")
        empleados_qs = Empleado.objects.filter(activo=True)
        if emp_id:
            empleados_qs = empleados_qs.filter(id_empresa_id=emp_id)
        ctx["empleados"] = empleados_qs.order_by("nombre", "apellido_paterno", "apellido_materno")

        return ctx
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist("equipos")
        ids = list(dict.fromkeys(map(int, ids)))
        empleado_id = request.POST.get("empleado_id")

        if not ids:
            messages.warning(request, "Selecciona al menos un equipo.")
            return redirect(request.path)
        if not empleado_id:
            messages.warning(request, "Selecciona un empleado destino.")
            return redirect(request.path)

        emp_id = request.session.get("empresa_id")

        # ⬇️ seguridad: el empleado debe pertenecer a la empresa logueada
        try:
            empleado = Empleado.objects.get(
                pk=empleado_id, activo=True, id_empresa_id=emp_id
            )
        except Empleado.DoesNotExist:
            messages.error(request, "El empleado no existe, está inactivo o no pertenece a la empresa actual.")
            return redirect(request.path)

        qs = (
            Equipo.objects
            .select_for_update()
            .filter(
                id_equipo__in=ids,
                id_empleado__isnull=True,
                id_estado_equipo__descripcion__iexact="bodega",
            )
        )
        if emp_id:
            qs = qs.filter(id_empresa_id=emp_id)

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

        historiales, equipos_a_actualizar = [], []
        for e in qs:
            prev_emp_id    = e.id_empleado_id
            prev_estado_id = e.id_estado_equipo_id
            changed = (prev_emp_id != empleado.id_empleado) or (prev_estado_id != estado_asignado.id_estado_equipo)
            if not changed:
                continue

            historiales.append(HistorialEquipos(
                equipo=e,
                etiqueta=e.etiqueta,
                nombre_equipo=e.nombre_equipo,
                fecha=ahora,
                responsable_anterior_fk_id=prev_emp_id,
                estado_anterior_id=prev_estado_id,
                estado_nuevo=estado_asignado,
                responsable_actual=empleado,
                id_empresa=empleado.id_empresa,                 # snapshot
                departamento=empleado.id_departamento,           # snapshot
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
@login_required
def historial_mantenciones_equipo(request, equipo_id: int):
    emp_id = request.session.get("empresa_id")
    equipo = get_object_or_404(Equipo, pk=equipo_id)

    # Seguridad multiempresa: ese equipo debe pertenecer a la empresa activa
    if emp_id and getattr(equipo, "id_empresa_id", None) != emp_id:
        raise Http404("Equipo fuera de la empresa actual.")

    # Solo las mantenciones de ESTE equipo
    mantenciones = (
        Mantencion.objects
        .select_related("id_estado_mantencion", "id_tipo_mantencion", "id_prioridad")
        .filter(id_equipo_id=equipo_id)
        .order_by("-id_mantencion")
    )

    ctx = {
        "equipo": equipo,
        "mantenciones": mantenciones,
    }
    return render(request, "mantenciones/historial_por_equipo.html", ctx)


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
            qs = qs.filter(id_empresa_id=emp_id)  # seguridad multiempresa
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

# Config base del historial (si ya la tienes, reutilízala)
hist_mant_cfg = type("Cfg", (), {
    "model": HistorialMantencionesLog,
    "slug": "historial_mantenciones",
    "verbose_name": "Historial de mantenciones",
    "verbose_name_plural": "Historial de mantenciones",
    "list_display": [
        "id_equipo", "etiqueta", "equipo_nombre",
        "fecha_evento", "tipo_mantencion", "prioridad",
        "estado_actual", "asignado_a", "descripcion", "detalle",
        "usuario_app_username",
    ],
    "ordering": ["-fecha_evento"],
    "can_create": False, "can_update": False, "can_delete": False,
})()


class HistorialMantencionIndividual(view_class(HistorialMantencionesLog, hist_mant_cfg, GenericList)):
    """Listado filtrado al id de mantención (pk)."""
    def get_queryset(self):
        return (
            HistorialMantencionesLog.objects
            .filter(id_mantencion=self.kwargs["pk"])
            .order_by("-fecha_evento")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # título/subtítulo bonito
        try:
            mant = Mantencion.objects.select_related("id_equipo").get(pk=self.kwargs["pk"])
            ctx["subtitle"] = f"Mantención {mant.id_mantencion} · {mant.id_equipo}"
        except Mantencion.DoesNotExist:
            ctx["subtitle"] = f"Mantención {self.kwargs['pk']}"
        # sin botón “Nuevo”
        self.crud_config.can_create = False
        ctx["can_create"] = False
        return ctx