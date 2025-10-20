# productos/views.py
#from productos.models_inventario import CategoriaActivo
#from django.views.generic.edit import CreateView
from django.views.generic import ListView, DetailView
from django.views.generic import ListView, DetailView
from .crud import ActivoForm
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Factura
from .forms import FacturaAdjuntoForm  # Formulario para adjuntar el archivo
from django.shortcuts import render
from .models_inventario import Departamento, EstadoMantencion, TipoMantencion, PrioridadMantencion
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from django.contrib import messages
from .models_inventario import Factura
# imports necesarios (verifica que estén)
from django.views import View
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import transaction
from django.utils import timezone
from .mixins import CompanyRequiredMixin, ModelPermsMixin   # ← IMPORTA AMBOS
from .models_inventario import Activo, EstadoActivo, Empleado, HistorialActivos
from django.shortcuts import render
from .crud import ActivoForm
from .models_inventario import Modelo

from .models_inventario import (
    Activo, EstadoActivo, Empleado, HistorialActivos
)
from django.views import View
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db import transaction
from productos.models_inventario import EstadoActivo
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count
from .crud import get_crud_configs
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, render, redirect
from django.forms import inlineformset_factory
from django.contrib import messages
from .models_inventario import TipoActivo, AtributosActivo
from django.views.generic import ListView
from .models_inventario import Activo
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.shortcuts import redirect
from .models_inventario import Activo, Empleado, EstadoActivo, HistorialActivos
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import MantencionForm
from .models_inventario import Mantencion, HistorialMantencionesLog
from django.http import JsonResponse
from .models_inventario import AtributosActivo
from .mixins import CompanyRequiredMixin
from django.db.models import Q
from django.http import Http404
from .models_inventario import Activo, Mantencion
from django.db import connection
from .crud import GenericList, view_class
from django.http import JsonResponse
# productos/views.py
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from .models_inventario import (
    AtributosActivo,
    AgregacionAtributosPorActivo,
    AtributoOpcionPorTipoActivo,   # 👈 importa el nuevo modelo
)

# modelos opcionales (según tu app)
try:
    from .models_inventario import (
        Activo, TipoActivo, Mantencion
    )
except Exception:
    Activo = TipoActivo = Mantencion = None

class CompanySelectView(TemplateView):
    """Vista para seleccionar la empresa activa.

    - Permite al usuario seleccionar entre las empresas disponibles.
    - Si se selecciona una empresa, se guarda en la sesión.
    - Si no se selecciona, se muestra un formulario con las empresas disponibles.
    """
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
    """Desasigna la empresa seleccionada en la sesión.

    - Elimina la empresa activa de la sesión actual.
    - Muestra un mensaje informando que la empresa fue deseleccionada.
    """
    # Elimina selección actual
    request.session.pop("empresa_id", None)
    request.session.pop("empresa_nombre", None)
    messages.info(request, "Empresa deseleccionada.")
    return redirect(reverse_lazy("productos:company_select"))

class HomeView(CompanyRequiredMixin, TemplateView):
    """Vista principal de la aplicación, con estadísticas y menú filtrado por empresa.

    - Muestra estadísticas de activos y mantenciones filtradas por empresa.
    - Permite ver el menú de opciones basado en la empresa activa.
    """
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
                    elif "id_activo" in names:
                        count = cfg.model.objects.filter(id_activo__id_empresa=emp_id).count()
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
        # Activos
        qs_activos = Activo.objects.all()
        if emp_id:
            qs_activos = qs_activos.filter(id_empresa_id=emp_id)

        total_activos = qs_activos.count()
        disponibles   = qs_activos.filter(id_empleado__isnull=True).count()
        en_uso        = qs_activos.filter(id_empleado__isnull=False).count()


        # Activos criticos
        criticos = qs_activos.filter(activo_critico=True).count()
        ctx.update({
            # ...
            "activos_criticos": criticos,
        })

        # Mantenciones (con fallback si el modelo no tiene id_empresa)
        Mant = Mantencion  # ya importado arriba
        qs_mant = Mant.objects.all() if Mant else None
        if Mant and emp_id:
            mant_fields = {f.name for f in Mant._meta.get_fields()}
            if "id_empresa" in mant_fields:
                qs_mant = qs_mant.filter(id_empresa=emp_id)
            elif "id_activo" in mant_fields:
                qs_mant = qs_mant.filter(id_activo__id_empresa=emp_id)

        mant_pend = 0
        ult_mant = []
        chart_mant_labels = []
        chart_mant_values = []
        if Mant and qs_mant is not None:
            mant_pend = qs_mant.exclude(
                id_estado_mantencion__tipo__in=["Cerrada", "Completada", "Cancelada"]
            ).count()

            # Mantenciones completadas
            mant_comp = 0
            if Mant and qs_mant is not None:
                # ... (lo que ya tienes)

                # ✅ NUEVO: total de mantenciones completadas
                mant_comp = qs_mant.filter(
                    id_estado_mantencion__tipo__iexact="Completada"
                ).count()



            ult_mant = (
                qs_mant.select_related("id_activo", "id_estado_mantencion")
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
            "total_activos": total_activos,
            "disponibles": disponibles,
            "en_uso": en_uso,
            "mantenciones_pendientes": mant_pend,
            "mantenciones_completadas": mant_comp,   # ✅ NUEVO
            "ultimos_activos": qs_activos.order_by("-id_activo")[:15],
            "ultimas_mantenciones": ult_mant,
        })

        # Gráfico de activos por tipo (ya con qs_activos filtrado)
        datos_tipos = (
            qs_activos.values("id_tipo_activo__tipo_activo")
                      .annotate(n=Count("id_activo"))
                      .order_by("id_tipo_activo__tipo_activo")
        )
        ctx["chart_tipos_labels"] = [d["id_tipo_activo__tipo_activo"] or "Sin tipo" for d in datos_tipos]
        ctx["chart_tipos_values"] = [d["n"] for d in datos_tipos]

        # Gráfico de mantenciones por estado (si corresponde)
        ctx["chart_mant_labels"] = chart_mant_labels
        ctx["chart_mant_values"] = chart_mant_values

        return ctx

def _log_mantencion_snapshot(mant: Mantencion, accion: str, user, detalle: str = ""):
    """Crea un registro de historial de mantención con un snapshot de los cambios.

    - Crea un historial detallado de la acción realizada sobre la mantención.
    - Guarda datos legibles como nombre de responsable y estado del activo.
    """
    # Nombre visible: full_name → nombre del Empleado → username
    emp = getattr(user, "empleado", None)
    visible_name = (user.get_full_name() or (str(emp) if emp else "") or user.username)

    HistorialMantencionesLog.objects.create(
        id_mantencion=mant.id_mantencion,
        fecha_evento=timezone.now(),
        accion=accion,
        detalle=detalle or "",
        usuario_app_username=visible_name,   # <<--- aquí

        id_activo=mant.id_activo_id,
        etiqueta=getattr(mant.id_activo, 'etiqueta', None),
        activo_nombre=str(mant.id_activo)[:150] if mant.id_activo else None,

        tipo_mantencion=str(mant.id_tipo_mantencion) if mant.id_tipo_mantencion else None,
        prioridad=str(mant.id_prioridad) if mant.id_prioridad else None,
        estado_actual=str(mant.id_estado_mantencion) if mant.id_estado_mantencion else None,

        responsable_nombre=str(mant.responsable) if mant.responsable else None,
        solicitante_nombre=str(mant.solicitante_user) if mant.solicitante_user else None,

        descripcion=mant.descripcion or "",
    )

@login_required
def mantencion_nueva(request):
    """Vista para crear una nueva mantención.

    - Permite registrar una nueva mantención y asociar un usuario como solicitante.
    - Guarda el registro de la mantención y genera un historial.
    """
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
    """Vista para editar una mantención existente.

    - Permite modificar una mantención existente.
    - Guarda el historial de cambios, incluyendo cambios de estado o asignación.
    """
    mant = get_object_or_404(Mantencion, pk=pk)

    emp_id = request.session.get("empresa_id")
    if not emp_id or (mant.id_activo and mant.id_activo.id_empresa_id != emp_id):
        raise Http404("Mantención no pertenece a la empresa actual.")

    estado_ant = mant.id_estado_mantencion_id
    asignado_ant = mant.asignado_id

    if request.method == 'POST':
        form = MantencionForm(request.POST, instance=mant, request=request)
        if form.is_valid():
            mant = form.save()
            if mant.id_estado_mantencion_id != estado_ant:
                _log_mantencion_snapshot(mant, 'ESTADO', request.user, 'Cambio de estado')
            if mant.asignado_id != asignado_ant:
                _log_mantencion_snapshot(mant, 'ASIGN', request.user, 'Asignación/Reasignación')
            _log_mantencion_snapshot(mant, 'EDICION', request.user, 'Edición de mantención')
            return redirect('productos:mantencions_list')  # ver nota (d) abajo
    else:
        form = MantencionForm(instance=mant, request=request)

    return render(request, 'mantenciones/editar.html', {'form': form, 'mantencion': mant})

class ActivosDisponiblesView(CompanyRequiredMixin, TemplateView):
    """Vista para mostrar activos disponibles para asignación.

    - Filtra los activos por estado "bodega" y muestra solo los activos sin asignar.
    - Permite asignar activos a un empleado.
    """
    template_name = "activos/disponibles_asignar.html"

    def get_queryset_disponibles(self):
        emp_id = self.request.session.get("empresa_id")
        qs = (
            Activo.objects
            .select_related("id_marca", "id_tipo_activo", "id_estado_activo")
            .filter(
                id_empleado__isnull=True,
                id_estado_activo__descripcion__iexact="bodega",  # case-insensitive
            )
            .order_by("-id_activo")  # Primero ordenar antes de hacer el slice
        )
        if emp_id:
            # Si quisieras incluir activos antiguos sin empresa, usa Q(...) | Q(id_empresa__isnull=True)
            qs = qs.filter(id_empresa_id=emp_id)

        # Limitar a los últimos 15 activos después de ordenar
        return qs  # Limitar después de ordenar

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # base de disponibles (bodega + sin empleado) ya filtrada por empresa
        base = self.get_queryset_disponibles()

        # lee el ?tipo=<id> y filtra solo los activos mostrados
        tipo_id = self.request.GET.get("tipo")
        if tipo_id:
            activos = base.filter(id_tipo_activo_id=tipo_id)
        else:
            activos = base

        # tipos para el combo (conteo siempre sobre el base)
        tipos = (
            base.values("id_tipo_activo_id", "id_tipo_activo__tipo_activo")
                .annotate(n=Count("id_activo"))
                .order_by("id_tipo_activo__tipo_activo")
        )

        # empleados (igual que antes)
        emp_id = self.request.session.get("empresa_id")
        empleados_qs = Empleado.objects.filter(estado_activo=True)
        if emp_id:
            empleados_qs = empleados_qs.filter(id_empresa_id=emp_id)

        ctx.update({
            "activos": activos.order_by("-id_activo"),
            "total": base.count(),
            "tipos": tipos,
            "tipo_seleccionado": str(tipo_id or ""),
            "empleados": empleados_qs.order_by("nombre", "apellido_paterno", "apellido_materno"),
        })
        return ctx
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist("activos")
        ids = list(dict.fromkeys(map(int, ids)))
        empleado_id = request.POST.get("empleado_id")

        if not ids:
            messages.warning(request, "Selecciona al menos un activo.")
            return redirect(request.path)
        if not empleado_id:
            messages.warning(request, "Selecciona un empleado destino.")
            return redirect(request.path)

        emp_id = request.session.get("empresa_id")

        # El empleado debe pertenecer a la empresa en sesión
        try:
            empleado = Empleado.objects.get(
                pk=empleado_id, estado_activo=True, id_empresa_id=emp_id
            )
        except Empleado.DoesNotExist:
            messages.error(request, "El empleado no existe, está inactivo o no pertenece a la empresa actual.")
            return redirect(request.path)

        # Resolución segura de estados por empresa
        estado_bodega = (
            EstadoActivo.objects
            .filter(descripcion__iexact="bodega", id_empresa_id=emp_id)
            .order_by("id_estado_activo")
            .first()
            or EstadoActivo.objects
            .filter(descripcion__iexact="bodega", id_empresa__isnull=True)
            .order_by("id_estado_activo")
            .first()
        )
        estado_asignado = (
            EstadoActivo.objects
            .filter(descripcion__iexact="asignado", id_empresa_id=emp_id)
            .order_by("id_estado_activo")
            .first()
            or EstadoActivo.objects
            .filter(descripcion__iexact="asignado", id_empresa__isnull=True)
            .order_by("id_estado_activo")
            .first()
        )

        if not estado_bodega or not estado_asignado:
            messages.error(request, "Faltan estados 'Bodega' y/o 'Asignado' para esta empresa.")
            return redirect(request.path)

        ahora = timezone.now()
        usuario_empleado = getattr(request.user, "empleado", None)

        with transaction.atomic():
            qs = (
                Activo.objects
                .select_for_update()
                .filter(
                    id_activo__in=ids,
                    id_empleado__isnull=True,
                    id_estado_activo=estado_bodega,   # 👈 usamos el objeto, no la descripción
                )
            )
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)

            faltantes = set(ids) - set(qs.values_list("id_activo", flat=True))
            if faltantes:
                messages.error(
                    request,
                    f"Algunos activos ya no están disponibles (IDs: {', '.join(map(str, faltantes))})."
                )
                return redirect(request.path)

            historiales, activos_a_actualizar = [], []
            for e in qs:
                prev_emp_id    = e.id_empleado_id
                prev_estado_id = e.id_estado_activo_id
                changed = (
                    prev_emp_id != empleado.id_empleado
                    or prev_estado_id != estado_asignado.id_estado_activo
                )
                if not changed:
                    continue

                historiales.append(HistorialActivos(
                    activo=e,
                    etiqueta=e.etiqueta,
                    nombre_activo=e.nombre_activo,
                    fecha=ahora,
                    responsable_anterior_fk_id=prev_emp_id,
                    estado_anterior_id=prev_estado_id,
                    estado_nuevo=estado_asignado,
                    responsable_actual=empleado,
                    id_empresa=empleado.id_empresa,       # snapshot
                    departamento=empleado.id_departamento, # snapshot
                    usuario=usuario_empleado,
                    accion="ASIGNACION MASIVA",
                    tipo_activo=getattr(e, "id_tipo_activo", None),
                ))

                e.id_empleado = empleado
                e.id_estado_activo = estado_asignado
                activos_a_actualizar.append(e)

            if activos_a_actualizar:
                Activo.objects.bulk_update(
                    activos_a_actualizar, ["id_empleado", "id_estado_activo"]
                )
            if historiales:
                HistorialActivos.objects.bulk_create(historiales, ignore_conflicts=True)

        messages.success(request, f"Se asignaron {len(activos_a_actualizar)} activo(s) a {empleado}.")
        return redirect(request.path)
    

@login_required
def historial_mantenciones_activo(request, activo_id: int):
    """Vista para ver el historial de mantenciones de un activo específico.

    - Muestra todas las mantenciones relacionadas con un activo específico.
    - Filtra las mantenciones por empresa y activo.
    """
    emp_id = request.session.get("empresa_id")
    activo = get_object_or_404(Activo, pk=activo_id)

    # Seguridad multiempresa: ese activo debe pertenecer a la empresa activa
    if emp_id and getattr(activo, "id_empresa_id", None) != emp_id:
        raise Http404("Activo fuera de la empresa actual.")

    # Solo las mantenciones de ESTE activo
    mantenciones = (
        Mantencion.objects
        .select_related("id_estado_mantencion", "id_tipo_mantencion", "id_prioridad")
        .filter(id_activo_id=activo_id)
        .order_by("-id_mantencion")
    )

    ctx = {
        "activo": activo,
        "mantenciones": mantenciones,
    }
    return render(request, "mantenciones/historial_por_activo.html", ctx)


# --- Desasignación masiva (espejo de ActivosDisponiblesView) ---
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .models_inventario import Activo, Empleado, EstadoActivo, HistorialActivos
from .mixins import CompanyRequiredMixin
from django.http import HttpResponseForbidden
from django.db.models import Q


from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models_inventario import Activo, EstadoActivo, HistorialActivos
from .mixins import CompanyRequiredMixin
from django.http import HttpResponseForbidden

class ActivosDesasignarView(CompanyRequiredMixin, TemplateView):
    """Vista para desasignar activos de empleados.

    - Permite desasignar múltiples activos de un empleado y asignarlos a un estado "bodega".
    - Registra un historial de la acción realizada.
    """
    template_name = "activos/en_uso_desasignar.html"

    def get_queryset_asignados(self):
        # Consulta los activos actualmente asignados
        emp_id = self.request.session.get("empresa_id")
        qs = (
            Activo.objects
            .select_related("id_marca", "id_tipo_activo", "id_estado_activo", "id_empleado")
            .filter(id_empleado__isnull=False)  # Solo activos con empleado asignado
            .order_by("-id_activo")
        )
        if emp_id:
            qs = qs.filter(id_empresa_id=emp_id)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset_asignados()
        ctx["activos"] = qs
        ctx["total"] = qs.count()

        # Empleados SOLO de la empresa actual (para mostrar en la vista)
        emp_id = self.request.session.get("empresa_id")
        empleados_qs = Empleado.objects.filter(estado_activo=True)
        if emp_id:
            empleados_qs = empleados_qs.filter(id_empresa_id=emp_id)
        ctx["empleados"] = empleados_qs.order_by("nombre", "apellido_paterno", "apellido_materno")

        return ctx

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist("activos")
        ids = list(dict.fromkeys(map(int, ids)))  # Eliminar duplicados
        if not ids:
            messages.warning(request, "Selecciona al menos un activo.")
            return redirect(request.path)

        emp_id = request.session.get("empresa_id")

        # Resolver el estado 'bodega' para desasignar los activos
        estado_bodega = (
            EstadoActivo.objects
            .filter(descripcion__iexact="bodega", id_empresa_id=emp_id)
            .order_by("id_estado_activo")
            .first()
            or EstadoActivo.objects
            .filter(descripcion__iexact="bodega", id_empresa__isnull=True)
            .order_by("id_estado_activo")
            .first()
        )

        if not estado_bodega:
            messages.error(request, "Falta configurar el estado 'Bodega'.")
            return redirect(request.path)

        ahora = timezone.now()
        usuario_empleado = getattr(request.user, "empleado", None)

        # Desasignar activos seleccionados
        with transaction.atomic():
            qs = (
                Activo.objects
                .select_for_update()
                .filter(id_activo__in=ids, id_empleado__isnull=False)
            )
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)

            faltantes = set(ids) - set(qs.values_list("id_activo", flat=True))
            if faltantes:
                messages.error(
                    request,
                    f"Algunos activos no están asignados o ya han sido desasignados "
                    f"(IDs: {', '.join(map(str, faltantes))})."
                )
                return redirect(request.path)

            historiales, activos_a_actualizar = [], []
            for e in qs:
                prev_emp_id = e.id_empleado_id
                prev_estado_id = e.id_estado_activo_id

                # Crear historial de desasignación
                historiales.append(HistorialActivos(
                    activo=e,
                    etiqueta=e.etiqueta,
                    nombre_activo=e.nombre_activo,
                    fecha=ahora,
                    responsable_anterior_fk_id=prev_emp_id,
                    estado_anterior_id=prev_estado_id,
                    estado_nuevo=estado_bodega,
                    responsable_actual=None,
                    id_empresa=e.id_empresa,  # snapshot desde el activo
                    departamento=None,
                    usuario=usuario_empleado,
                    accion="DESASIGNACION MASIVA",
                    tipo_activo=getattr(e, "id_tipo_activo", None),
                ))

                # Actualizar el estado y empleado del activo
                e.id_empleado = None
                e.id_estado_activo = estado_bodega
                activos_a_actualizar.append(e)

            if activos_a_actualizar:
                Activo.objects.bulk_update(
                    activos_a_actualizar, ["id_empleado", "id_estado_activo"]
                )
            if historiales:
                HistorialActivos.objects.bulk_create(historiales, ignore_conflicts=True)

        messages.success(request, f"Se desasignaron {len(activos_a_actualizar)} activo(s).")
        return redirect(request.path)

    
@login_required
def api_atributos_por_tipo(request):
    emp_id    = request.session.get("empresa_id")
    tipo_id   = request.GET.get("tipo_id")
    activo_id = request.GET.get("activo_id")

    # tipo_id válido
    try:
        tipo_id = int(tipo_id)
    except (TypeError, ValueError):
        return JsonResponse({"items": []})

    # 1) Atributos definidos para ese tipo (y empresa si aplica)
    qs = AtributosActivo.objects.filter(id_tipo_activo_id=tipo_id)
    if emp_id:
        qs = qs.filter(id_tipo_activo__id_empresa_id=emp_id)

    if not qs.exists():
        return JsonResponse({"items": []})

    # Incluyo 'valor' como posible default
    attrs = list(qs.values("id_atributo_activo", "atributo", "valor"))
    attr_ids = [a["id_atributo_activo"] for a in attrs]

    # 2) Valores existentes del activo (si estamos editando)
    valores = {}
    if activo_id:
        valores = dict(
            AgregacionAtributosPorActivo.objects
            .filter(activo_id=activo_id, atributo_id__in=attr_ids)
            .values_list("atributo_id", "valor")
        )

    # 3) Opciones permitidas (dropdown) para cada atributo
    opt_qs = (
        AtributoOpcionPorTipoActivo.objects
        .filter(atributo_definicion_id__in=attr_ids, habilitada=True)
        .order_by("orden", "etiqueta_opcion")
        .values("atributo_definicion_id", "etiqueta_opcion")
    )
    opciones_map = {}
    for r in opt_qs:
        opciones_map.setdefault(r["atributo_definicion_id"], []).append(r["etiqueta_opcion"])

    # 4) Respuesta final: usa valor guardado; si no, el default del atributo
    items = []
    for a in attrs:
        aid = a["id_atributo_activo"]
        default = a.get("valor") or ""
        current = valores.get(aid, default)
        items.append({
            "id_atributo_activo": aid,
            "atributo": a["atributo"],
            "valor": current,
            "opciones": opciones_map.get(aid, []),  # lista de strings
        })

    return JsonResponse({"items": items})

## Config base del historial (si ya la tienes, reutilízala)
#hist_mant_cfg = type("Cfg", (), {
#    "model": HistorialMantencionesLog,
#    "slug": "historial_mantenciones",
#    "verbose_name": "Historial de mantenciones",
#    "verbose_name_plural": "Historial de mantenciones",
#    "list_display": [
#        "id_activo",
#        "etiqueta",
#        "activo_nombre",
#        "asignado_a",
#        "fecha_evento",
#        "tipo_mantencion", 
#        "prioridad",
#        "estado_actual",
#        "descripcion",
#        "detalle",
#        "usuario_app_username",
#    ],
#    "ordering": ["-fecha_evento"],
#    "can_create": False, "can_update": False, "can_delete": False,
#})()


#class HistorialMantencionIndividual(view_class(HistorialMantencionesLog, hist_mant_cfg, GenericList)):
#    """Listado filtrado al id de mantención (pk)."""
#    def get_queryset(self):
#        return (
#            HistorialMantencionesLog.objects
#            .filter(id_mantencion=self.kwargs["pk"])
#            .order_by("-fecha_evento")
#        )
#
#    def get_context_data(self, **kwargs):
#        ctx = super().get_context_data(**kwargs)
#        # título/subtítulo bonito
#        try:
#            mant = Mantencion.objects.select_related("id_activo").get(pk=self.kwargs["pk"])
#            ctx["subtitle"] = f"Mantención {mant.id_mantencion} · {mant.id_activo}"
#        except Mantencion.DoesNotExist:
#            ctx["subtitle"] = f"Mantención {self.kwargs['pk']}"
#        # sin botón “Nuevo”
#        self.crud_config.can_create = False
#        ctx["can_create"] = False
#        return ctx
    

@login_required
def nuevos_estados_mantencion(request):
    # Obtener todos los tipos de estado de mantención para la empresa actual
    estados = EstadoMantencion.objects.filter(id_empresa=request.session.get("empresa_id")).order_by('tipo')

    return render(request, 'nombre_del_template.html', {
        'side_items': estados  # Aquí pasamos los estados a side_items
    })

#class ActivoCreateView(CreateView):
#    model = Activo
#    form_class = ActivoForm
#    template_name = 'activo_form.html'
#
#    def form_valid(self, form):
#        # Verifica si el activo es crítico
#        if form.cleaned_data['activo_critico']:
#            # Aquí puedes guardar o hacer algo adicional si el activo es crítico
#            # Por ejemplo, guardar los datos de confidencialidad, integridad, disponibilidad.
#            pass
#
#        return super().form_valid(form)






from .models_inventario import Factura

class FacturaListView(LoginRequiredMixin, ListView):
    """Vista para listar las facturas.

    - Permite visualizar una lista paginada de las facturas asociadas a la empresa activa.
    - Soporta filtrado por proveedor y folio de factura.
    """
    model = Factura
    template_name = "productos/facturas_list.html"
    context_object_name = "facturas"
    paginate_by = 20

    def get_queryset(self):
        emp_id = self.request.session.get("empresa_id")
        qs = super().get_queryset().select_related("id_proveedor", "id_empresa").order_by("-fecha_emision", "-id_factura")
        if emp_id:
            qs = qs.filter(id_empresa_id=emp_id)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(id_proveedor__nombre_proveedor__icontains=q) | qs.filter(id_factura__icontains=q)
        return qs

class FacturaDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver los detalles de una factura específica.

    - Muestra información detallada de una factura específica.
    """
    model = Factura
    template_name = "productos/factura_detail.html"
    context_object_name = "factura"
    pk_url_kwarg = "id_factura"



from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from .models_inventario import Factura

def factura_attach_file(request, factura_id):
    """Vista para adjuntar un archivo a una factura existente.

    - Permite adjuntar un archivo a la factura y guarda el archivo en el sistema.
    - Muestra un mensaje de éxito o error según el resultado de la operación.
    """
    factura = get_object_or_404(Factura, id_factura=factura_id)

    if request.method == "POST" and request.FILES.get("archivo_adjunto"):
        factura.archivo_adjunto = request.FILES["archivo_adjunto"]
        factura.save(update_fields=["archivo_adjunto"])
        messages.success(request, "Factura guardada exitosamente.")
        return redirect("productos:facturas_list")

    return render(request, "productos/factura_adjuntar.html", {"factura": factura})

#########################################################################################################
#########################################################################################################0110
#@login_required
#@require_POST
#def factura_quitar_adjunto(request, factura_id: int):
#    factura = get_object_or_404(Factura, id_factura=factura_id)
#
#    # seguridad multiempresa
#    emp_id = request.session.get("empresa_id")
#    if emp_id and factura.id_empresa_id != emp_id:
#        raise Http404("Factura fuera de la empresa actual.")
#
#    if factura.archivo_adjunto:
#        # (opcional) borra el archivo del disco; quítalo si prefieres conservarlo
#        try:
#            factura.archivo_adjunto.delete(save=False)
#        except Exception:
#            pass
#
#        # fuerza el cambio del campo para que el signal lo registre
#        factura.archivo_adjunto = None
#        factura.save(update_fields=["archivo_adjunto"])
#
#        messages.success(request, "Se quitó el archivo adjunto.")
#    else:
#        messages.info(request, "La factura no tenía archivo adjunto.")
#
#    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
#    return redirect(next_url or "productos:facturas_list")
from django.views.generic import ListView
from .models import Registro

class RegistroListView(ListView):
    """Vista para listar los registros de acciones realizadas en el sistema.

    - Muestra un listado de registros filtrados por empresa activa.
    - Permite ver el historial de acciones de auditoría.
    """
    model = Registro
    template_name = "productos/registros_list.html"
    context_object_name = "registros"
    paginate_by = 25  # Puedes ajustar la paginación si es necesario

    def get_queryset(self):
        emp_id = self.request.session.get("empresa_id")
        qs = (Registro.objects
              .select_related("tipo_registro", "usuario", "id_empresa")
              .order_by("-fecha", "-id_registro"))
        return qs.filter(id_empresa_id=emp_id) if emp_id else qs


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from .models_inventario import Factura

@login_required
def factura_quitar_adjunto(request, factura_id):
    """Vista para quitar un archivo adjunto de una factura.

    - Permite quitar el archivo adjunto de una factura y eliminar el archivo físico.
    - Muestra un mensaje informando el estado de la operación.
    """
    factura = get_object_or_404(Factura, id_factura=factura_id)

    # (opcional) seguridad multi-empresa
    emp_id = request.session.get("empresa_id")
    if emp_id and factura.id_empresa_id != emp_id:
        from django.http import Http404
        raise Http404("Factura fuera de la empresa actual.")

    if request.method == "POST" and factura.archivo_adjunto:
        # elimina el archivo físico pero no el registro
        factura.archivo_adjunto.delete(save=False)
        factura.archivo_adjunto = None
        # esto dispara tu signal y registrará QUITAR_ADJUNTO
        factura.save(update_fields=["archivo_adjunto"])
        messages.success(request, "Se quitó el archivo adjunto.")

    next_url = request.POST.get("next") or reverse("productos:facturas_list")
    return redirect(next_url)

##################################################################################
######################################################################################
from django.http import HttpResponse
from django.utils import timezone
import csv

from .models_inventario import Activo, DetalleFactura
from .utils import get_attr_value_de_activo

def exportar_activos_criticos_excel(request):
    """
    Exporta SOLO los activos marcados como críticos en un CSV compatible con Excel,
    usando el encabezado de tu planilla (área, serie, nombre, descripción, etc.).

    Encabezado (exacto):
        Area, Numero de serie, Nombre del activo, Descripcion, Tipo, Nombre equipo,
        Clasificacion, Confid, Integ, Dispon, Total valor, Valor del activo

    - Delimitador: ';' (para Excel en Windows).
    - Codificación: UTF-8 con BOM (para que Excel detecte tildes).
    - Multiempresa: si el usuario tiene `empleado.id_empresa`, filtra por esa empresa.

    Args:
        request (django.http.HttpRequest): Petición web.

    Returns:
        django.http.HttpResponse: Respuesta con attachment CSV.
    """
    qs = (Activo.objects
          .filter(eliminado=False, activo_critico=True)
          .select_related(
              "id_empresa", "id_departamento", "id_tipo_activo",
              "id_marca", "id_estado_activo", "id_empleado"
          )
          .order_by("etiqueta"))

    # Filtro por empresa del usuario, si corresponde
    emp = getattr(getattr(request.user, "empleado", None), "id_empresa", None)
    if emp:
        qs = qs.filter(id_empresa=emp)

    # Prefetch pequeño de atributos dinámicos (para nº de serie, modelo, hostname)
    # (Opcional: si quieres súper óptimo, puedes añadir un Prefetch aquí)

    # Respuesta CSV con BOM
    now = timezone.localtime().strftime("%Y%m%d_%H%M")
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename=activos_criticos_{now}.csv'
    response.write("\ufeff")  # BOM para Excel

    writer = csv.writer(response, delimiter=";", lineterminator="\r\n")

    headers = [
        "Area",
        "Numero de serie",
        "Nombre del activo",
        "Descripcion",
        "Tipo",
        "Nombre equipo",
        "Clasificacion",
        "Confid",
        "Integ",
        "Dispon",
        "Total valor",
        "Valor del activo",
    ]
    writer.writerow(headers)

    # Helper para mapping de clasificación a rótulo "bonito"
    def clasif_label(cod: str) -> str:
        mapa = {
            "confidencial": "confidencial",
            "uso_interno": "uso interno",
            "publico": "público",
        }
        return mapa.get((cod or "").lower(), cod or "")

    for a in qs:
        # Atributos dinámicos buscados por nombres alternativos
        nro_serie = (a.numero_serie or get_attr_value_de_activo(
            a,
            ["número de serie", "numero de serie", "serial", "sn", "s/n", "service tag"]
        ) or "").strip()
        descripcion = get_attr_value_de_activo(
            a,
            ["modelo", "model", "descripcion", "descripción"]
        )
        nombre_equipo = a.etiqueta or ""

        # Área = departamento
        area = getattr(a.id_departamento, "nombre_departamento", "") or ""

        # Tipo
        tipo = getattr(a.id_tipo_activo, "tipo_activo", "") or ""

        # Clasificación
        clasif = clasif_label(a.clasificacion or "")

        # Criticidad (numéricos o vacío)
        confid = a.confidencialidad or 0
        integ = a.integridad or 0
        dispon = a.disponibilidad or 0
        total_valor= confid + integ + dispon

        # "Valor del activo" (unitario estimado: primero encontrado)
        unit = (DetalleFactura.objects
                .filter(id_activo=a, eliminado=False)
                .values_list("valor_unitario", flat=True)
                .first())
        valor_unitario = unit or ""

        writer.writerow([
            area,
            nro_serie,
            a.nombre_activo or "",
            descripcion,
            tipo,
            nombre_equipo,
            clasif,
            confid,
            integ,
            dispon,
            total_valor,
            valor_unitario,
        ])

    return response

# productos/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden
from .models_inventario import Activo, AgregacionAtributosPorActivo

# productos/views.py
@login_required
def activo_detail(request, pk: int):
    emp_id = request.session.get("empresa_id")
    activo = (
        Activo.objects
        .select_related(
            "id_marca", "id_tipo_activo", "id_estado_activo",
            "id_empleado", "id_proveedor", "id_departamento"
        )
        .get(pk=pk)
    )

    if emp_id and getattr(activo, "id_empresa_id", None) and activo.id_empresa_id != emp_id:
        return HttpResponseForbidden("No permitido")

    pares = (
        AgregacionAtributosPorActivo.objects
        .filter(activo_id=pk)
        .select_related("atributo")
        .order_by("atributo__atributo")
    )
    attrs = [{"nombre": p.atributo.atributo, "valor": p.valor} for p in pares]

    # etiqueta legible para la clasificación
    mapa_clasif = {"confidencial": "Confidencial", "uso_interno": "Uso interno", "publico": "Público"}
    clasif_legible = mapa_clasif.get((activo.clasificacion or "").lower(), activo.clasificacion or "")

    ctx = {"activo": activo, "attrs": attrs, "clasif_legible": clasif_legible}
    return render(request, "activos/detail.html", ctx)


# productos/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from .models_inventario import Empleado, Activo

@login_required
def empleado_detail(request, pk: int):
    emp_id = request.session.get("empresa_id")

    empleado = (
        Empleado.objects
        .select_related("id_empresa", "id_departamento", "user")
        .get(pk=pk)
    )

    # seguridad multiempresa (opcional)
    if emp_id and getattr(empleado, "id_empresa_id", None) and empleado.id_empresa_id != emp_id:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No permitido")

    # Activos asignados a este empleado
    activos = (
        Activo.objects
        .select_related("id_marca", "id_tipo_activo", "id_estado_activo")
        .filter(id_empleado_id=empleado.id_empleado)
        .order_by("-id_activo")
    )

    ctx = {"empleado": empleado, "activos": activos}
    return render(request, "empleados/detail.html", ctx)


# --- Listado de Activos críticos ---
# productos/views.py
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Prefetch
from .mixins import CompanyRequiredMixin
from .models_inventario import Activo, DetalleFactura

class ActivosCriticosList(CompanyRequiredMixin, TemplateView):
    template_name = "activos/criticos_list.html"

    def get_queryset_criticos(self):
        emp_id = self.request.session.get("empresa_id")
        qs = (
            Activo.objects
            .select_related("id_marca", "id_tipo_activo", "id_estado_activo", "id_empleado", "id_departamento")
            .filter(eliminado=False, activo_critico=True)
            .order_by("-id_activo")
        )
        if emp_id:
            qs = qs.filter(id_empresa_id=emp_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset_criticos()

        for a in qs:
            a.total_cid = (a.confidencialidad or 0) + (a.integridad or 0) + (a.disponibilidad or 0)


        # (opcional) prefetch de 1er valor unitario para mostrar en tabla
        precios = {
            a.id_activo: (DetalleFactura.objects
                          .filter(id_activo=a, eliminado=False)
                          .values_list("valor_unitario", flat=True)
                          .first())
            for a in qs
        }

        ctx["activos"] = qs
        ctx["total"]   = qs.count()
        ctx["precios"] = precios
        return ctx


    ####################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class DesasignarPorEmpleadoView(CompanyRequiredMixin, TemplateView):
    """
    Lista empleados que tienen activos asignados (>0) en la empresa activa.
    Al hacer click en 'Desasignar', se abre un modal con los activos de ese empleado.
    """
    template_name = "activos/desasignar_por_empleado.html"

    def get_queryset_empleados(self):
        emp_id = self.request.session.get("empresa_id")
        qs = (Empleado.objects
              .filter(estado_activo=True)
              .annotate(n_activos=Count("activo"))        # reverse lookup de Activo (book/book_set → activo)
              .filter(n_activos__gt=0)
              .order_by("nombre", "apellido_paterno", "apellido_materno"))
        if emp_id:
            qs = qs.filter(id_empresa_id=emp_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset_empleados()
        ctx["empleados"] = qs
        ctx["total"] = qs.count()
        return ctx


@login_required
def activos_de_empleado_json(request, empleado_id: int):
    """
    Devuelve en JSON los activos asignados a un empleado (para poblar el modal).
    Seguridad multiempresa incluida.
    """
    emp_id = request.session.get("empresa_id")
    empleado = get_object_or_404(Empleado, pk=empleado_id)

    if emp_id and getattr(empleado, "id_empresa_id", None) != emp_id:
        raise Http404("Empleado fuera de la empresa actual.")

    activos = (Activo.objects
               .select_related("id_marca", "id_tipo_activo", "id_estado_activo")
               .filter(id_empleado_id=empleado.id_empleado)
               .order_by("-id_activo"))

    items = []
    for a in activos:
        items.append({
            "id": a.id_activo,
            "etiqueta": a.etiqueta or "",
            "nombre": a.nombre_activo,
            "marca": str(a.id_marca) if a.id_marca_id else "",
            "tipo": str(a.id_tipo_activo) if a.id_tipo_activo_id else "",
            "estado": str(a.id_estado_activo) if a.id_estado_activo_id else "",
        })
    return JsonResponse({"empleado": str(empleado), "items": items})


@method_decorator(login_required, name="dispatch")
class DesasignarEmpleadoPostView(View):
    """
    Procesa el POST del modal: desasigna los activos seleccionados **de ese empleado**,
    moviéndolos a estado 'bodega' y registrando en HistorialActivos.
    """
    def post(self, request, empleado_id: int):
        emp_id = request.session.get("empresa_id")
        empleado = get_object_or_404(Empleado, pk=empleado_id)

        if emp_id and getattr(empleado, "id_empresa_id", None) != emp_id:
            raise Http404("Empleado fuera de la empresa actual.")

        ids = request.POST.getlist("activos")
        ids = list(dict.fromkeys(map(int, ids)))
        if not ids:
            messages.warning(request, "Selecciona al menos un activo.")
            return redirect('productos:activos_desasignar')

        # Buscar estado 'Bodega'
        estado_bodega = (
            EstadoActivo.objects
            .filter(descripcion__iexact="bodega", id_empresa_id=emp_id).order_by("id_estado_activo").first()
            or EstadoActivo.objects
            .filter(descripcion__iexact="bodega", id_empresa__isnull=True).order_by("id_estado_activo").first()
        )
        if not estado_bodega:
            messages.error(request, "Falta configurar el estado 'Bodega'.")
            return redirect('productos:activos_desasignar')

        ahora = timezone.now()
        usuario_empleado = getattr(request.user, "empleado", None)

        with transaction.atomic():
            # Solo activos que realmente pertenecen a ESTE empleado (seguridad)
            qs = (Activo.objects
                  .select_for_update()
                  .filter(id_activo__in=ids, id_empleado_id=empleado.id_empleado))
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)

            faltantes = set(ids) - set(qs.values_list("id_activo", flat=True))
            if faltantes:
                messages.error(
                    request,
                    f"Algunos activos no pertenecen a {empleado} o ya no están asignados "
                    f"(IDs: {', '.join(map(str, faltantes))})."
                )
                return redirect('productos:activos_desasignar')

            historiales, a_actualizar = [], []
            for e in qs:
                historiales.append(HistorialActivos(
                    activo=e,
                    etiqueta=e.etiqueta,
                    nombre_activo=e.nombre_activo,
                    fecha=ahora,
                    responsable_anterior_fk_id=e.id_empleado_id,
                    estado_anterior_id=e.id_estado_activo_id,
                    estado_nuevo=estado_bodega,
                    responsable_actual=None,
                    id_empresa=e.id_empresa,
                    departamento=None,
                    usuario=usuario_empleado,
                    accion="DESASIGNACION MASIVA",
                    tipo_activo=getattr(e, "id_tipo_activo", None),
                ))
                e.id_empleado = None
                e.id_estado_activo = estado_bodega
                a_actualizar.append(e)

            if a_actualizar:
                Activo.objects.bulk_update(a_actualizar, ["id_empleado", "id_estado_activo"])
            if historiales:
                HistorialActivos.objects.bulk_create(historiales, ignore_conflicts=True)

        messages.success(request, f"Se desasignaron {len(a_actualizar)} activo(s) de {empleado}.")
        return redirect('productos:activos_desasignar')

    #########################################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>

@login_required
def api_activos_disponibles(request):
    """
    Devuelve activos disponibles (estado 'bodega' y sin empleado) filtrados por tipo (opcional).
    JSON: [{id, etiqueta, nombre, marca, tipo, estado}]
    """
    emp_id  = request.session.get("empresa_id")
    tipo_id = request.GET.get("tipo")

    qs = (Activo.objects
          .select_related("id_marca", "id_tipo_activo", "id_estado_activo")
          .filter(id_empleado__isnull=True,
                  id_estado_activo__descripcion__iexact="bodega"))
    if emp_id:
        qs = qs.filter(id_empresa_id=emp_id)
    if tipo_id:
        qs = qs.filter(id_tipo_activo_id=tipo_id)

    items = [{
        "id": a.id_activo,
        "etiqueta": a.etiqueta or "",
        "nombre": a.nombre_activo,
        "marca": str(a.id_marca) if a.id_marca_id else "",
        "tipo": str(a.id_tipo_activo) if a.id_tipo_activo_id else "",
        "estado": str(a.id_estado_activo) if a.id_estado_activo_id else "",
    } for a in qs.order_by("-id_activo")]

    return JsonResponse({"items": items})

########################################################


def mi_vista(request):
    emp_id = request.session.get('empresa_id')  # Obtener el ID de la empresa desde la sesión
    if not emp_id:
        # Si no hay `emp_id` en la sesión, manejamos la lógica por defecto
        emp_id = 1  # O usa cualquier lógica que prefieras

    form = ActivoForm(request.POST or None, emp_id=emp_id)  # Pasa el emp_id al formulario
    return render(request, 'form.html', {'form': form})


