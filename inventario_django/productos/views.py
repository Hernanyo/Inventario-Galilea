# productos/views.py
### parte 1
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
from .models_inventario import Activo, DocumentoActivo, TipoDocumentoActivo
from django.http import HttpResponseBadRequest
from .models_inventario import ActivoNota
from datetime import datetime, timedelta

from .models_inventario import (
    MantencionEjecucion, MantencionEjecucionTarea, PlanMantencionTarea
)

# arriba del archivo
from datetime import datetime, timedelta
from django.utils import timezone
from django.http import HttpResponseBadRequest
# ...


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

# --- Acciones rápidas sobre Planes y PMA ---

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponseForbidden

from .models_inventario import PlanMantencion, PlanMantencionActivo
from .models_inventario import MantencionEjecucion, MantencionEjecucionTarea, PlanMantencionTarea
from .models_inventario import (
    PreparacionAsignacion,
    AccionPreparacion,
    ReglaCriticidad,   # para reutilizar la lógica de criticidad al asignar
)
from .models_inventario import CondicionDetalle, CondicionActivo
from django.contrib import messages as dj_messages
from .forms import DetalleFacturaInlineForm
from .models_inventario import Factura, DetalleFactura, Activo, TipoActivo
from .models_inventario import Ubicacion
from django.contrib.auth.views import LoginView
from .mixins import rol_de_usuario, ROL_ADMIN, ROL_JEFE, ROL_USUARIO, ROL_TRABAJADOR
# arriba en views.py, asegúrate de tener:
from .models_inventario import Ubicacion, Bodega
from .mixins import (
    CompanyRequiredMixin,
    filtrar_activos_por_bodegas_permitidas, filtrar_empleados_por_bodegas_permitidas,
)





# modelos opcionales (según tu app)
try:
    from .models_inventario import (
        Activo, TipoActivo, Mantencion
    )
except Exception:
    Activo = TipoActivo = Mantencion = None
############################### 04/12 #################################################
def empresas_para_usuario(user):
    """
    Devuelve un queryset de Empresa que el usuario puede ver/seleccionar,
    respetando rol:
      - Admin (superuser o permiso especial) → todas las empresas.
      - Jefe (grupo 'Jefes' / 'Jefes de Área'...) → por ahora, su propia empresa.
      - Usuario normal → solo su empresa.
    """
    from .models_inventario import Empresa, Empleado

    if not user.is_authenticated:
        return Empresa.objects.none()
    
    rol = rol_de_usuario(user)
    qs_base = Empresa.objects.all().order_by("nombre_empresa")

    # 1) Admin total -> todas las empresas
    if rol == ROL_ADMIN:
        return qs_base


    # 1) Admin total
    if user.is_superuser or user.has_perm("productos.ver_todas_empresas"):
        return qs_base

    # 2) Para jefe / usuario / lo que venga: usar su id_empresa
    empleado = getattr(user, "empleado", None)
    emp_id = getattr(empleado, "id_empresa_id", None)

    if not empleado or not emp_id:
        # Usuario sin empresa asociada → no puede elegir nada
        return Empresa.objects.none()

    # Por ahora, tanto jefe como usuario normal ven solo SU empresa.
    # Si después creas un M2M tipo empleado.empresas_visibles, se ajusta aquí.
    return qs_base.filter(id_empresa=emp_id)

############################### 04/12 - Login + empresa por usuario ########################
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.contrib import messages

from .models_inventario import Empleado


class MiLoginView(LoginView):
    """
    Login que:
      - Bloquea empleados con rol TRABAJADOR (no entran al sistema).
      - Después de autenticarse, decide la empresa:
          * 0 empresas -> mensaje + selector vacío
          * 1 empresa  -> la setea en sesión y va a Home
          * >1 empresa -> va al selector de empresas
    """
    template_name = "accounts/login.html"

    def form_valid(self, form):
        # Usuario que se acaba de autenticar (todavía no se ha hecho login en la sesión)
        user = form.get_user()

        # 1) Bloqueo por rol TRABAJADOR usando la constante del modelo
        try:
            empleado = Empleado.objects.get(user=user)
        except Empleado.DoesNotExist:
            empleado = None

        if empleado and empleado.rol == Empleado.ROL_TRABAJADOR:
            # NO hacemos login, solo mostramos error en el mismo formulario
            form.add_error(None, "No tienes acceso al sistema de inventario.")
            return self.form_invalid(form)

        # 2) Si no es TRABAJADOR, continuamos con el login normal
        return super().form_valid(form)

    def get_success_url(self):
        """
        Decide adónde ir después del login y setea empresa en sesión.
        """
        user = self.request.user

        # Empresas permitidas según tu función centralizada
        empresas_qs = empresas_para_usuario(user)
        total_empresas = empresas_qs.count()

        # Limpiar selección previa de empresa
        for k in ("empresa_id", "empresa_nombre", "empresa_slug"):
            self.request.session.pop(k, None)

        # 0 empresas -> mensaje y selector
        if total_empresas == 0:
            messages.error(
                self.request,
                "Tu usuario no tiene ninguna empresa asignada. "
                "Por favor contacta al área de soporte."
            )
            return reverse("productos:company_select")

        # 1 empresa -> setear en sesión y mandar a Home
        if total_empresas == 1:
            emp = empresas_qs.first()
            self.request.session["empresa_id"] = emp.id_empresa
            self.request.session["empresa_nombre"] = getattr(emp, "nombre_empresa", str(emp))
            if getattr(emp, "slug", None):
                self.request.session["empresa_slug"] = emp.slug
            return reverse("productos:home")

        # Varias empresas -> que elija una
        return reverse("productos:company_select")

############################### 04/12 - Login + empresa por usuario ########################
############################### 04/12 #################################################

class CompanySelectView(LoginRequiredMixin, TemplateView):
    """
    Vista para seleccionar la empresa activa UNA VEZ logueado.

    Usa `empresas_para_usuario` para mostrar solo las empresas
    a las que el usuario tiene acceso.
    """
    template_name = "accounts/company_select.html"
    login_url = reverse_lazy("productos:login")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        empresas = empresas_para_usuario(self.request.user)
        ctx["empresas"] = empresas
        ctx["empresa_id"] = self.request.session.get("empresa_id")
        ctx["empresa_nombre"] = self.request.session.get("empresa_nombre")
        return ctx

    def post(self, request, *args, **kwargs):
        emp_id = request.POST.get("empresa_id")

        # Validar emp_id
        try:
            emp_id_int = int(emp_id)
        except (TypeError, ValueError):
            messages.error(request, "Empresa inválida.")
            return redirect(request.path)

        # La empresa elegida debe estar dentro de las permitidas
        empresas = empresas_para_usuario(request.user).filter(id_empresa=emp_id_int)
        emp = empresas.first()
        if not emp:
            messages.error(request, "No tienes permisos para acceder a esa empresa.")
            return redirect(request.path)

        request.session["empresa_id"] = emp.id_empresa
        request.session["empresa_nombre"] = getattr(emp, "nombre_empresa", str(emp))

        # Si usas slug para logos en el login
        if hasattr(emp, "slug") and emp.slug:
            request.session["empresa_slug"] = emp.slug

        messages.success(request, f"Empresa seleccionada: {request.session['empresa_nombre']}")
        return redirect("productos:home")

    
############################### 04/12 #################################################

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
    - Esta vista se encarga de poblar las tarjetas y numeros de barra de navegación
    """
    template_name = "overview/home_sidebar.html"
############################### 04/12 #################################################
    login_url = reverse_lazy("productos:login")
############################### 04/12 #################################################
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Importamos aquí para evitar líos de imports circulares
        from .mixins import (
            filtrar_activos_por_bodegas_permitidas,
            filtrar_empleados_por_bodegas_permitidas,
        )

        # Empresa actual y ejecutor (empleado logueado)
        emp_id = self.request.session.get("empresa_id")
        ejecutor = getattr(self.request.user, "empleado", None)

        # ===== Menú lateral (empresa + bodegas cuando aplique) =====
        menu = []
        for cfg in get_crud_configs():
            try:
                names = {f.name for f in cfg.model._meta.get_fields()}
                qs_count = cfg.model.objects.all()

                # Borrado lógico
                if "eliminado" in names:
                    qs_count = qs_count.filter(eliminado=False)

                # Filtro por empresa
                if emp_id:
                    if "id_empresa" in names:
                        qs_count = qs_count.filter(id_empresa=emp_id)
                    elif "empresa" in names:  # campo FK llamado "empresa"
                        qs_count = qs_count.filter(empresa_id=emp_id)
                    elif "id_activo" in names:  # modelos que cuelgan de Activo
                        qs_count = qs_count.filter(id_activo__id_empresa=emp_id)

                # Filtro por bodegas PERMITIDAS solo en modelos clave
                model_name = cfg.model.__name__
                if model_name == "Activo":
                    qs_count = filtrar_activos_por_bodegas_permitidas(qs_count, ejecutor)
                elif model_name == "Empleado":
                    qs_count = filtrar_empleados_por_bodegas_permitidas(qs_count, ejecutor)

                count = qs_count.count()
            except Exception:
                count = 0

            menu.append({
                "name": cfg.verbose_name_plural,
                "slug": cfg.slug,
                "count": count,
                "icon": getattr(cfg, "icon", "bi-folder2"),
            })
        ctx["menu"] = menu

        # ===== KPIs, listas y gráficos (empresa + bodegas) =====
        # Base de activos
        qs_activos = Activo.objects.filter(eliminado=False)
        if emp_id:
            qs_activos = qs_activos.filter(id_empresa_id=emp_id)

        # 🔒 Permisos por bodegas del ejecutor
        qs_activos = filtrar_activos_por_bodegas_permitidas(qs_activos, ejecutor)

        total_activos = qs_activos.count()
        disponibles   = qs_activos.filter(id_empleado__isnull=True).count()
        en_uso        = qs_activos.filter(id_empleado__isnull=False).count()
        criticos      = qs_activos.filter(activo_critico=True).count()

################################# 10/12 #################################################
        # === Cobertura de planes de mantención (nuevo módulo) ===
        # Planes vigentes asociados SOLO a los activos que el usuario puede ver
        try:
            qs_pma = PlanMantencionActivo.objects.filter(
                eliminado=False,
                es_vigente=True,
                id_activo__in=qs_activos,  # respeta empresa + bodegas permitidas
            )

            # Activos con al menos un plan vigente
            activos_con_plan = (
                qs_pma.values("id_activo")
                      .distinct()
                      .count()
            )
        except Exception:
            activos_con_plan = 0

        # Activos sin plan = total visibles - con plan (nunca negativo por si acaso)
        activos_sin_plan = max(total_activos - activos_con_plan, 0)

################################# 10/12 #################################################


        # Mantenciones (se filtran por empresa; si más adelante quieres
        # también por bodega, hacemos un helper similar en mixins)
        Mant = Mantencion
        qs_mant = Mant.objects.all() if Mant else None
        if Mant and emp_id:
            mant_fields = {f.name for f in Mant._meta.get_fields()}
            if "id_empresa" in mant_fields:
                qs_mant = qs_mant.filter(id_empresa=emp_id)
            elif "id_activo" in mant_fields:
                qs_mant = qs_mant.filter(id_activo__id_empresa=emp_id)

        mant_pend = 0
        mant_comp = 0
        ult_mant = []
        chart_mant_labels = []
        chart_mant_values = []

        if Mant and qs_mant is not None:
            mant_pend = qs_mant.exclude(
                id_estado_mantencion__tipo__in=["Cerrada", "Completada", "Cancelada"]
            ).count()

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
            chart_mant_labels = [
                d["id_estado_mantencion__tipo"] or "Sin estado"
                for d in datos_mant
            ]
            chart_mant_values = [d["n"] for d in datos_mant]

        # Contexto final
        ctx.update({
            "total_activos": total_activos,
            "disponibles": disponibles,
            "en_uso": en_uso,
            "activos_criticos": criticos,

##################################### 10/12 ########################################
            # ➜ NUEVAS MÉTRICAS PARA LAS TARJETAS
            "activos_con_plan": activos_con_plan,
            "activos_sin_plan": activos_sin_plan,
##################################### 10/12 ########################################


            "mantenciones_pendientes": mant_pend,
            "mantenciones_completadas": mant_comp,
            "ultimos_activos": qs_activos.order_by("-id_activo")[:15],
            "ultimas_mantenciones": ult_mant,
        })

        # Gráfico de activos por tipo (ya con empresa + bodegas aplicadas)
        datos_tipos = (
            qs_activos.values("id_tipo_activo__tipo_activo")
                      .annotate(n=Count("id_activo"))
                      .order_by("id_tipo_activo__tipo_activo")
        )
        ctx["chart_tipos_labels"] = [
            d["id_tipo_activo__tipo_activo"] or "Sin tipo"
            for d in datos_tipos
        ]
        ctx["chart_tipos_values"] = [d["n"] for d in datos_tipos]

        # Gráfico de mantenciones por estado
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

#############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><07/11
def _activar_plan_vigente_y_recalcular(pma, ahora):
    """
    Marca un PMA como vigente y recalcula vencimientos según su tipo de medición.
    Tolera 'intervalo_dias' = None y tipos por kilómetros.
    """
    pma.es_vigente = True
    pma.base_fecha = ahora.date()  # siempre dejamos “base” consistente para planes por tiempo
    pma.base_valor = None

    plan = pma.id_plan
    tipo = getattr(plan, "tipo_medicion", None)

    # Default: sin fecha calculable
    pma.proximo_vencimiento_fecha = None
    pma.proximo_vencimiento_valor = None

    # Si es por tiempo (Días) y el intervalo es válido
    if getattr(tipo, "es_tiempo", False) or (getattr(tipo, "codigo", "") in ("Día", "Dia", "Dias", "Días")):
        dias = getattr(plan, "intervalo_dias", None)
        if isinstance(dias, int) and dias > 0:
            pma.proximo_vencimiento_fecha = pma.base_fecha + timedelta(days=dias)

    # Si es por kilómetros
    if getattr(tipo, "codigo", "").lower() in ("km", "kilometros", "kilómetros"):
        # No inventamos fecha; solo dejamos ready el valor. Si necesitas regla, ajusta aquí.
        ultimo = pma.ultima_medicion_valor or 0
        pma.proximo_vencimiento_valor = ultimo + (plan.intervalo_valor or 0)

    pma.save()

def _registrar_ejecucion_pma(request, pma, tareas_ids=None, obs_map=None):
    """
    Registra una ejecución de mantención: cabecera + snapshot de tareas (marcadas y no marcadas).
    No rompe el flujo si algo falla.
    """
    from .models_inventario import MantencionEjecucion, MantencionEjecucionTarea, PlanMantencionTarea
    try:
        obs_map = obs_map or {}  # { id_tarea:int -> "texto" }
        activo = pma.id_activo
        user   = request.user
        emp_id = getattr(pma, "id_empresa_id", None) or getattr(activo, "id_empresa_id", None)

        # normaliza ids marcadas
        tareas_ids = tareas_ids or []
        marcadas = set(int(x) for x in tareas_ids if str(x).isdigit())

        # snapshot de tareas del plan
        tareas_plan = list(
            PlanMantencionTarea.objects
            .filter(id_plan=pma.id_plan, eliminado=False)
            .values("id_tarea", "descripcion", "obligatorio")
            .order_by("orden", "id_tarea")
        )
        labels_ok = [t["descripcion"] for t in tareas_plan if t["id_tarea"] in marcadas]
        resumen = (f"{len(labels_ok)} tarea(s): " + "; ".join(labels_ok[:5]) + ("…" if len(labels_ok) > 5 else "")) if labels_ok else None

        # crear cabecera de ejecución
        asign = getattr(activo, "id_empleado", None)
        ejec = MantencionEjecucion.objects.create(
            id_empresa_id=emp_id,
            pma=pma,
            id_activo=activo,
            activo_etiqueta=getattr(activo, "etiqueta", None),
            activo_nombre=getattr(activo, "nombre_activo", None),
            id_tipo_activo=getattr(activo, "id_tipo_activo", None),
            empleado_asignado_fk=asign if getattr(asign, "pk", None) else None,
            empleado_asignado_nombre=str(asign) if asign else None,
            usuario_fk=user if getattr(user, "pk", None) else None,
            usuario_app_username=(getattr(user, "get_full_name", lambda: "")() or getattr(user, "username", "") or None),
            notas=(request.POST.get("notas") or None),
            medicion_valor=(request.POST.get("medicion_valor") or None),
            medicion_fecha=(request.POST.get("medicion_fecha") or None),
            proximo_vencimiento_fecha=getattr(pma, "proximo_vencimiento_fecha", None),
            proximo_vencimiento_valor=getattr(pma, "proximo_vencimiento_valor", None),
            resumen_tareas=resumen[:500] if resumen else None,
            datos_extra={"tareas_marcadas": sorted(list(marcadas))} if marcadas else {},
        )

        # detalle por tarea
        bulk = []
        for t in tareas_plan:
            tid = t["id_tarea"]
            bulk.append(MantencionEjecucionTarea(
                ejecucion=ejec,
                id_tarea_plan_id=tid,
                descripcion=(t["descripcion"] or "")[:300],
                obligatorio=bool(t["obligatorio"]),
                marcada=(tid in marcadas),                 # ← lo que ves como “Realizada”
                observacion=(obs_map.get(tid) or None),    # ← comentario por tarea
            ))
        if bulk:
            MantencionEjecucionTarea.objects.bulk_create(bulk, batch_size=100)
    except Exception:
        pass
################################## 16 de Noviembre 16:57 ##################################
# Si ya tienes algo parecido para criticidad, reutiliza esa función
def _normaliza_cadena(txt: str) -> str:
    txt = (txt or "").strip()
    # colapsar espacios múltiples
    return " ".join(txt.split())


def construir_preparaciones_para_activos(activos, empleado):
    """
    Dado un iterable de activos y un empleado, devuelve un dict:
        { id_activo: {
              "activo": <Activo>,
              "acciones": [AccionPreparacion...],
          }, ... }

    Si un activo no tiene preparación configurada, su lista 'acciones' será [].
    """
    resultado = {}
    if not empleado:
        return resultado

    from .models_inventario import PreparacionAsignacion  # si no lo tienes ya importado
    cargo_norm = _normaliza_cadena(getattr(empleado, "cargo", "") or "")

    for a in activos:
        # Usamos el classmethod del modelo para centralizar la lógica
        reglas = list(PreparacionAsignacion.reglas_para(a, cargo_norm))

        if not reglas:
            resultado[a.id_activo] = {"activo": a, "acciones": []}
            continue

        prep = reglas[0]  # normalmente será solo una
        acciones = list(
            prep.acciones.filter(eliminado=False).order_by("orden", "id_accion_preparacion")
        )

        resultado[a.id_activo] = {"activo": a, "acciones": acciones}

    return resultado

################################## 16/11 16:57 ##################################

#############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><07/11

class ActivosDisponiblesView(CompanyRequiredMixin, TemplateView):
    """Vista para mostrar activos disponibles para asignación.

    - Filtra los activos por estado "disponible" y muestra solo los activos sin asignar.
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
                id_estado_activo__descripcion__iexact="disponible",  # case-insensitive
                eliminado=False,  # 👈 NO mostrar activos borrados lógicamente
            )
##################################### 22/11 #################################################################
            # 👇 No mostrar activos con condición NO DISPONIBLE o EN REPARACIÓN
            .exclude(
                id_condicion_activo__descripcion__in=["No Disponible", "En Reparación"]
            )
##################################### 22/11 #################################################################

            .order_by("-id_activo")  # Primero ordenar antes de hacer el slice
        )
        if emp_id:
            # Si quisieras incluir activos antiguos sin empresa, usa Q(...) | Q(id_empresa__isnull=True)
            qs = qs.filter(id_empresa_id=emp_id)

##################################### 09/12 ########################################################### 
        # 🔹 NUEVO: aplicar filtro de permisos por bodegas
        usuario_empleado = getattr(self.request.user, "empleado", None)
        qs = filtrar_activos_por_bodegas_permitidas(qs, usuario_empleado)
##################################### 09/12 ########################################################### 

        # Limitar a los últimos 15 activos después de ordenar
        return qs  # Limitar después de ordenar

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # base de disponibles (disponible + sin empleado) ya filtrada por empresa
        base = self.get_queryset_disponibles()

############################## 11/12 ##########################
        # === NUEVO: texto de búsqueda ===
        q = (self.request.GET.get("q") or "").strip()
############################## 11/12 ##########################

        # lee el ?tipo=<id> y filtra solo los activos mostrados
        tipo_id = self.request.GET.get("tipo")
        if tipo_id:
            activos = base.filter(id_tipo_activo_id=tipo_id)
        else:
            activos = base
############################## 11/12 ##########################
        # === NUEVO: aplicar filtro de búsqueda ===
        if q:
            filtros = (
                Q(etiqueta__icontains=q) |
                Q(nombre_activo__icontains=q) |
                Q(id_marca__nombre_marca__icontains=q) |              # ← Marca (Apple, HP, etc.)
                Q(id_tipo_activo__tipo_activo__icontains=q)    # ← Tipo (Notebook, Monitor...)
            )

            # si q es un número, también buscamos por id_activo
            try:
                q_id = int(q)
            except ValueError:
                q_id = None
            if q_id is not None:
                filtros |= Q(id_activo=q_id)

            activos = activos.filter(filtros)
############################## 11/12 ##########################

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

##################################### 09/12 ############################################################
        # 🔹 NUEVO: filtrar empleados por bodegas/ubicaciones permitidas del usuario que ejecuta
        ejecutor = getattr(self.request.user, "empleado", None)
        empleados_qs = filtrar_empleados_por_bodegas_permitidas(empleados_qs, ejecutor)
##################################### 09/12 ############################################################

        ctx.update({
            "activos": activos.order_by("-id_activo"),
            "total": base.count(),
            "tipos": tipos,
            "tipo_seleccionado": str(tipo_id or ""),
            "empleados": empleados_qs.order_by("nombre", "apellido_paterno", "apellido_materno"),
            "q": q,   # <<< importante para que el input recuerde el texto

        })

        # --- NUEVO 16/11: indicador de preparación pendiente en sesión ---
        # Indicador de preparaciones pendientes (pueden ser varias)
        prep_dict = self.request.session.get("prep_pendientes", {})
        if prep_dict:
            # Lo pasamos como lista para que el template pueda iterar
            ctx["prep_pendientes"] = list(prep_dict.values())
        # -----------------------------------------------------------------


        return ctx
    
################################ 25/11 ########################################

################################ 25/11 ########################################

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        POST de asignación de activos.

        Ahora soporta 3 flujos:
        - Asignar directamente (como antes).
        - Guardar temporalmente la preparación en sesión.
        - Reanudar una preparación pendiente desde la sesión.
        - Eliminar la preparación (nueva funcionalidad para borrar la preparación y restaurar estado).

        """
        ids = request.POST.getlist("activos")
        ids = list(dict.fromkeys(map(int, ids)))
        empleado_id = request.POST.get("empleado_id")


################################ 25/11 ########################################
        accion = request.POST.get("accion")  # "guardar", "confirmar", "borrar"

        # ======================================================================
        # ACCIÓN: BORRAR PREPARACIÓN → restaurar a "Nuevo / Sin preparar"
        # ======================================================================
        if accion == "borrar":
            emp_id = request.session.get("empresa_id")

            # 1) Recuperar la preparación guardada en sesión para este empleado
            prep_all = request.session.get("prep_pendientes", {}) or {}
            prep_emp = prep_all.get(str(empleado_id), {})

            activos_a_borrar = prep_emp.get("activos_ids", [])

            # Quitar el banner de preparación pendiente de este empleado
            if str(empleado_id) in prep_all:
                del prep_all[str(empleado_id)]
                if prep_all:
                    request.session["prep_pendientes"] = prep_all
                else:
                    request.session.pop("prep_pendientes", None)
                request.session.modified = True

            if not activos_a_borrar:
                messages.info(
                    request,
                    "No hay una preparación guardada para este empleado."
                )
                return redirect(request.path)

            if not emp_id:
                messages.error(
                    request,
                    "No hay empresa activa en la sesión."
                )
                return redirect(request.path)

            # 2) Buscar el detalle "Sin Preparar" asociado a la condición NUEVO
            detalle_sin_preparar = (
                CondicionDetalle.objects
                .filter(
                    eliminado=False,
                    id_empresa_id=emp_id,
                    descripcion__iexact="Sin Preparar",
                    condicion_activo__codigo_sistema__iexact="NUEVO",
                )
                .order_by("id_condicion_detalle")
                .first()
            )

            if not detalle_sin_preparar:
                messages.error(
                    request,
                    "No está configurada la condición 'Nuevo / Sin preparar' para esta empresa."
                )
                return redirect(request.path)

            # 3) Restaurar la condición de todos los activos de esa preparación
            (
                Activo.objects
                .filter(
                    id_activo__in=activos_a_borrar,
                    eliminado=False,
                    id_empresa_id=emp_id,
                )
                .update(
                    id_condicion_activo=detalle_sin_preparar.condicion_activo,
                    id_condicion_detalle=detalle_sin_preparar,
                )
            )

            messages.success(
                request,
                f"Se eliminó la preparación de {len(activos_a_borrar)} activo(s) y "
                "se restauraron como 'Nuevo / Sin preparar'."
            )
            return redirect(request.path)
        # ======================================================================
        # FIN ACCIÓN BORRAR
        # ======================================================================


################################ 25/11 ########################################
        

        # --- NUEVO 16/11: flujo de preparación paso a paso / reanudar ---
        accion_preparacion = request.POST.get("accion_preparacion")  # None | "guardar" | "confirmar"
        reanudar = request.POST.get("reanudar_preparacion") == "1"
        # -----------------------------------------------------------------
        prep_dict = request.session.get("prep_pendientes", {})

############################## 22/11 #################################17:39
        # ¿Este POST viene desde el checklist de preparación?
        desde_checklist = "confirmar_preparacion" in request.POST

        # Si vengo desde el checklist o vengo reanudando, debo permitir activos en "En Reparación"
        permitir_en_reparacion = reanudar or desde_checklist
############################## 22/11 #################################17:39


        # --- NUEVO 16/11: si es reanudar, sobreescribimos ids y empleado con lo guardado ---
        if reanudar:
            # Diccionario con TODAS las preparaciones pendientes (por empleado)
            prep_all = request.session.get("prep_pendientes", {}) or {}
            # Preparación específica de este empleado
            prep_emp = prep_all.get(str(empleado_id))

            if not prep_emp:
                messages.info(request, "No hay una preparación pendiente para este empleado.")
                return redirect(request.path)

            # Sobrescribimos los ids que venían del formulario
            ids = prep_emp.get("activos_ids", [])

        # -------------------------------------------------------------------------------


        
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
        estado_disponible = (
            EstadoActivo.objects
            .filter(descripcion__iexact="disponible", id_empresa_id=emp_id)
            .order_by("id_estado_activo")
            .first()
            or EstadoActivo.objects
            .filter(descripcion__iexact="disponible", id_empresa__isnull=True)
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

        if not estado_disponible or not estado_asignado:
            messages.error(request, "Faltan estados 'disponible' y/o 'Asignado' para esta empresa.")
            return redirect(request.path)

        ########################################################################
        # NUEVO 15/11: Paso intermedio de PREPARACIÓN antes de asignar
        ########################################################################

        # ==== Candidatos a asignar (sin lock todavía) ====
        candidatos = (
            Activo.objects
            .select_related("id_tipo_activo", "id_empresa")
            .filter(
                id_activo__in=ids,
                id_empleado__isnull=True,
############################ 22/11 ####################17:02
                id_estado_activo_id=estado_disponible.id_estado_activo,
                eliminado=False,  # 👈 no trabajar con activos borrados
############################ 22/11 ####################17:02
#            )
#            .exclude(
#                id_condicion_activo__descripcion__in=["No Disponible", "En Reparación"]
            )
        )

############################ 22/11 ####################17:02
############################## 22/11 ############################################### 17:41


        if emp_id:
            candidatos = candidatos.filter(id_empresa_id=emp_id)

############################## 09/12 ###################################
        # 🔹 NUEVO: restringir por permisos de bodegas del usuario que ejecuta
        usuario_empleado = getattr(request.user, "empleado", None)
        candidatos = filtrar_activos_por_bodegas_permitidas(candidatos, usuario_empleado)
############################## 09/12 ###################################


        # Si estoy reanudando o vengo del checklist, permito "En Reparación"
        if permitir_en_reparacion:
            candidatos = candidatos.exclude(
                id_condicion_activo__descripcion__iexact="No Disponible"
            )
        else:
            candidatos = candidatos.exclude(
                id_condicion_activo__descripcion__in=["No Disponible", "En Reparación"]
            )

############################## 22/11 ############################################### 17:41

        activos_lista = list(candidatos)
        if not activos_lista:
            messages.error(
                request,
                "Los activos seleccionados ya no están disponibles para asignación."
            )
            return redirect(request.path)

        # Construir reglas de preparación por activo
        preparaciones = construir_preparaciones_para_activos(activos_lista, empleado)

        # ¿Hay al menos una acción de preparación definida?
        hay_acciones = any(
            len(info["acciones"]) > 0
            for info in preparaciones.values()
        )

        # ============================
        # FASE 1: mostrar checklist
        # ============================
        if "confirmar_preparacion" not in request.POST and hay_acciones:
            # --- 2) Recuperar checks guardados SOLO para este empleado ---
            saved_by_activo = {}
            if reanudar:
                prep_all = request.session.get("prep_pendientes", {}) or {}
                prep_emp = prep_all.get(str(empleado.id_empleado), {})
                raw_checked_map = prep_emp.get("checked_map", {})

            # normalizamos: claves a int, valores a set(int)
                # normalizamos: claves a int, valores a set(int)
                for act_id_str, acc_list in raw_checked_map.items():
                    try:
                        act_id_int = int(act_id_str)
                    except (TypeError, ValueError):
                        continue
                    saved_by_activo[act_id_int] = {
                        int(v) for v in acc_list if str(v).isdigit()
                    }
            # ---------------------------------------------------------------------
            items = []
            for a in activos_lista:
                info = preparaciones.get(a.id_activo, {"acciones": []})
                items.append({
                    "activo": a,
                    "acciones": info["acciones"],
                    # ✅ si estoy reanudando y hay datos en sesión para este activo,
                    #    los uso; si no, lista vacía.
                    "checked_ids": list(saved_by_activo.get(a.id_activo, set())),
                })

            ctx = {
                "empleado": empleado,
                "cargo": empleado.cargo,
                "activos_ids": [a.id_activo for a in activos_lista],
                "items": items,
            }
            return render(request, "activos/preparacion_asignacion.html", ctx)

        # ============================
        # FASE 2: validar checklist
        # ============================
        checked_map = {}
        if "confirmar_preparacion" in request.POST and hay_acciones:
            # Recuperamos qué acciones marcó el usuario por activo
            for a in activos_lista:
                key = f"prep_{a.id_activo}"
                marcadas = request.POST.getlist(key)
                checked_map[a.id_activo] = {
                    int(v) for v in marcadas if str(v).isdigit()
                }
############################ 22/11 ####################17:02
            # --- NUEVO 16/11: si la acción es GUARDAR, no validamos obligatorios ---

            if accion_preparacion == "guardar":
                # 1) Buscar el detalle "No disponible temporalmente" (En Reparación)
                detalle_temporal = (
                    CondicionDetalle.objects
                    .filter(
                        eliminado=False,
                        id_empresa_id=emp_id,
                        condicion_activo__descripcion__iexact="en reparación",
                        descripcion__iexact="No disponible temporalmente",
                    )
                    .order_by("id_condicion_detalle")
                    .first()
                )

                if not detalle_temporal:
                    messages.error(
                        request,
                        "No está configurado el detalle de condición "
                        "'En Reparación / No disponible temporalmente' para esta empresa."
                    )
                    return redirect(request.path)
################################################# 25/11 #########################################################                
#                # Guardar las condiciones originales de los activos antes de marcarlos como "En Reparación"
#                for activo in activos_lista:
#                    activo.estado_original = activo.id_estado_activo  # Guardamos el estado original
#                    activo.condicion_original = activo.id_condicion_activo  # Guardamos la condición original
#                    activo.condicion_detalle_original = activo.id_condicion_detalle  # Guardamos el detalle de la condición original
#                    activo.save()
################################################# 25/11 #########################################################                

                # 2) Marcar los activos como "En Reparación / No disponible temporalmente"
                Activo.objects.filter(
                    id_activo__in=[a.id_activo for a in activos_lista],
                    id_empleado__isnull=True,
                    id_estado_activo_id=estado_disponible.id_estado_activo,
                    id_empresa_id=emp_id,
                ).update(
                    id_condicion_activo=detalle_temporal.condicion_activo,
                    id_condicion_detalle=detalle_temporal,
                )

                # 3) Guardar la preparación en sesión (igual que antes)
#                request.session["prep_pendiente"] = {
                # 3) Guardar / fusionar la preparación en sesión POR EMPLEADO
                prep_all = request.session.get("prep_pendientes", {}) or {}
                key = str(empleado.id_empleado)
                previo = prep_all.get(key, {})

                prev_ids = previo.get("activos_ids", [])
                nuevos_ids = [a.id_activo for a in activos_lista]
                merged_ids = sorted(set(prev_ids) | set(nuevos_ids))

                prev_checked = previo.get("checked_map", {})
                new_checked = {
                    str(a_id): list(ids_set)
                    for a_id, ids_set in checked_map.items()
                }
                merged_checked = {**prev_checked, **new_checked}

                prep_all[key] = {
                    "empleado_id": empleado.id_empleado,
                    "empleado_nombre": str(empleado),
                    "cargo": empleado.cargo,
                    "activos_ids": merged_ids,
                    "checked_map": merged_checked,
                    "timestamp": timezone.now().isoformat(),
                }

                request.session["prep_pendientes"] = prep_all
                request.session.modified = True
                messages.info(
                    request,
                    "Preparación guardada temporalmente. "
                    "El activo queda marcado como 'En reparación (No disponible temporalmente)'."
                )
                return redirect(request.path)
            # ---------------------------------------------------------------------
############################ 22/11 ####################17:02

            errores = []
            # Validar que TODAS las acciones obligatorias estén marcadas
            for a in activos_lista:
                info = preparaciones.get(a.id_activo, {"acciones": []})
                acciones = info["acciones"]
                if not acciones:
                    continue  # este activo no requiere preparación

                obligatorias = [
                    acc for acc in acciones
                    if getattr(acc, "obligatorio", True)
                ]
                if not obligatorias:
                    continue

                marcadas_ids = checked_map.get(a.id_activo, set())
                faltantes = [
                    acc.descripcion
                    for acc in obligatorias
                    if acc.id_accion_preparacion not in marcadas_ids
                ]
                if faltantes:
                    errores.append(
                        f"Activo {a.etiqueta or a.id_activo}: faltan por marcar → {', '.join(faltantes)}"
                    )

            if errores:
                messages.error(
                    request,
                    "Debes completar todas las acciones obligatorias de preparación antes de asignar."
                )
                # Volvemos a mostrar el formulario con los checks ya marcados
                items = []
                for a in activos_lista:
                    info = preparaciones.get(a.id_activo, {"acciones": []})
                    items.append({
                        "activo": a,
                        "acciones": info["acciones"],
                        "checked_ids": list(checked_map.get(a.id_activo, set())),
                    })
                ctx = {
                    "empleado": empleado,
                    "cargo": empleado.cargo,
                    "activos_ids": [a.id_activo for a in activos_lista],
                    "items": items,
                    "errores": errores,
                }
                return render(request, "activos/preparacion_asignacion.html", ctx)

            # --- NUEVO 16/11: si se confirma bien, limpiamos la preparación pendiente ---
            # --- 4) Si se confirma bien, limpiamos SOLO la preparación de este empleado ---
            prep_all = request.session.get("prep_pendientes", {}) or {}
            key = str(empleado.id_empleado)
            if key in prep_all:
                del prep_all[key]
                if prep_all:
                    request.session["prep_pendientes"] = prep_all
                else:
                    request.session.pop("prep_pendientes", None)
                request.session.modified = True
            # ---------------------------------------------------------------------------
        ########################################################################
        # FIN NUEVO 15/11 – si llegamos aquí:
        #   - no hay preparaciones, o
        #   - ya se validaron todas → seguimos con tu lógica de asignación
        ########################################################################



#################################### 22/11 #################################################
        # ============================================================
        # NUEVO 22/11: buscar el detalle OPERATIVO para esta empresa
        # Suponemos que solo hay UN detalle asociado a Operativo.
        # ============================================================
        detalle_operativo = (
            CondicionDetalle.objects
            .filter(
                eliminado=False,
                id_empresa_id=emp_id,
                condicion_activo__descripcion__iexact="operativo",
            )
            .order_by("id_condicion_detalle")
            .first()
        )

        if not detalle_operativo:
            messages.error(
                request,
                "No está configurado el detalle de condición OPERATIVO "
                "para esta empresa."
            )
            return redirect(request.path)
        # ============================================================
#################################### 22/11 #################################################

        ahora = timezone.now()
        usuario_empleado = getattr(request.user, "empleado", None)

#################################### 22/11 ################################################# 17:43
        with transaction.atomic():
            qs = (
                Activo.objects
                .select_for_update(of=("self",))
                .filter(
                    id_activo__in=ids,
                    id_empleado__isnull=True,
                    id_estado_activo=estado_disponible.id_estado_activo,
                    eliminado=False,  # 👈 idem
                )
            )
            if emp_id:
                qs = qs.filter(id_empresa_id=emp_id)

############################# 09/12 #######################################
            # 🔹 NUEVO: el usuario que *ejecuta* la desasignación solo puede tocar
            # activos en bodegas para las que tiene permiso
            ejecutor = getattr(request.user, "empleado", None)
            qs = filtrar_activos_por_bodegas_permitidas(qs, ejecutor)
############################# 09/12 #######################################

#            # Mismo criterio que en "candidatos": si vengo del checklist o reanudo,
#            # permito activos en "En Reparación"
#            if permitir_en_reparacion:
#                qs = qs.exclude(
#                    id_condicion_activo__descripcion__iexact="No Disponible"
#                )
#            else:
#                qs = qs.exclude(
#                    id_condicion_activo__descripcion__in=["No Disponible", "En Reparación"]
#                )
#################################### 22/11 ################################################# 17:43


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
####################################### 22/11 ########################################################
                prev_cond_det_id  = getattr(e, "id_condicion_detalle_id", None)
                prev_cond_act_id  = getattr(e, "id_condicion_activo_id", None)
####################################### 22/11 ########################################################

                changed = (
                    prev_emp_id != empleado.id_empleado
                    or prev_estado_id != estado_asignado.id_estado_activo
                )
                if not changed:
                    continue

    ############################################################################################>>>>>>>>>>>>04/11
                # Primero actualizamos los planes de mantenimiento asociados al activo
                # --- Actualizar PMAs del activo (sin reventar por intervalo_dias = None) ---
                planes = PlanMantencionActivo.objects.filter(id_activo=e, eliminado=False)

                # Apagar vigentes actuales
                planes.filter(es_vigente=True).update(es_vigente=False)

                # Elegir candidato a vigente
                plan_preventivo = planes.filter(id_plan__nombre__icontains="preventiva").first()
                pma_objetivo = plan_preventivo or planes.first()

                if pma_objetivo:
                    _activar_plan_vigente_y_recalcular(pma_objetivo, ahora)

    ############################################################################################>>>>>>>>>>>>15/11
                # --- Asignar empleado y estado ---
                e.id_empleado = empleado
                e.id_estado_activo = estado_asignado
####################################### 22/11 ########################################################
                e.id_condicion_detalle = detalle_operativo
                e.id_condicion_activo = detalle_operativo.condicion_activo
####################################### 22/11 ########################################################

####################################### 03/12 ########################################################
                # 🔹 NUEVO: mover activo a la misma ubicación del empleado (si tiene)
                if empleado.ubicacion_id:
                    e.id_ubicacion_id = empleado.ubicacion_id
####################################### 03/12 ########################################################

                # --- NUEVO: aplicar regla de criticidad según cargo + tipo + empresa ---
                aplicar_regla_criticidad(e)  # <<< esto rellena activo_critico + CID + clasificacion

    ############################################################################################>>>>>>>>>>>>15/11


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

                ##e.id_empleado = empleado
                ##e.id_estado_activo = estado_asignado
                activos_a_actualizar.append(e)

            if activos_a_actualizar:
                Activo.objects.bulk_update(
                    activos_a_actualizar,
                    [
                        "id_empleado",
                        "id_estado_activo",
####################################### 22/11 ########################################################
                        "id_condicion_activo",     # <<< NUEVO
                        "id_condicion_detalle",    # <<< NUEVO
####################################### 22/11 ########################################################
####################################### 03/12 ######################################################## 
                        "id_ubicacion",       # 🔹 NUEVO
####################################### 03/12 ######################################################## 
                        "activo_critico",
                        "clasificacion",
                        "confidencialidad",
                        "integridad",
                        "disponibilidad",
                    ],
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

    - Permite desasignar múltiples activos de un empleado y asignarlos a un estado "disponible".
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

        # Resolver el estado 'disponible' para desasignar los activos
        estado_disponible = (
            EstadoActivo.objects
            .filter(descripcion__iexact="disponible", id_empresa_id=emp_id)
            .order_by("id_estado_activo")
            .first()
            or EstadoActivo.objects
            .filter(descripcion__iexact="disponible", id_empresa__isnull=True)
            .order_by("id_estado_activo")
            .first()
        )

        if not estado_disponible:
            messages.error(request, "Falta configurar el estado 'disponible'.")
            return redirect(request.path)

        ahora = timezone.now()
        usuario_empleado = getattr(request.user, "empleado", None)

        # Desasignar activos seleccionados
        with transaction.atomic():
            qs = (
                Activo.objects
                .select_for_update()
################################# 03/12 ################################################## 03/12
                .select_related("id_ubicacion")              # 👈 añadimos esto
################################# 03/12 ################################################## 03/12
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
                    estado_nuevo=estado_disponible,
                    responsable_actual=None,
                    id_empresa=e.id_empresa,  # snapshot desde el activo
                    departamento=None,
                    usuario=usuario_empleado,
                    accion="DESASIGNACION MASIVA",
                    tipo_activo=getattr(e, "id_tipo_activo", None),
                ))
################################# 03/12 ################################################## 03/12
                # --- lógica nueva de ubicación ---
                ubic_actual = e.id_ubicacion
                nueva_ubicacion = ubicacion_bodega_para(ubic_actual)
                e.id_ubicacion = nueva_ubicacion
################################# 03/12 ################################################## 03/12

                # Actualizar el estado y empleado del activo
                e.id_empleado = None
                e.id_estado_activo = estado_disponible
                activos_a_actualizar.append(e)

            if activos_a_actualizar:
                Activo.objects.bulk_update(
                    activos_a_actualizar, ["id_empleado", "id_estado_activo", "id_ubicacion"]
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
    
### parte 2
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

        # === Planes de mantención de este activo (para la tabla del detalle) ===
    planes = (
        PlanMantencionActivo.objects
        .filter(id_activo=activo, eliminado=False)
        .select_related("id_plan")
        .order_by("-es_vigente", "pk")
    )

    ctx = {"activo": activo, "attrs": attrs, "clasif_legible": clasif_legible, "planes": planes,}
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
    moviéndolos a estado 'disponible' y registrando en HistorialActivos.
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

        # Buscar estado 'disponible'
        estado_disponible = (
            EstadoActivo.objects
            .filter(descripcion__iexact="disponible", id_empresa_id=emp_id).order_by("id_estado_activo").first()
            or EstadoActivo.objects
            .filter(descripcion__iexact="disponible", id_empresa__isnull=True).order_by("id_estado_activo").first()
        )
        if not estado_disponible:
            messages.error(request, "Falta configurar el estado 'disponible'.")
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
                    estado_nuevo=estado_disponible,
                    responsable_actual=None,
                    id_empresa=e.id_empresa,
                    departamento=None,
                    usuario=usuario_empleado,
                    accion="DESASIGNACION MASIVA",
                    tipo_activo=getattr(e, "id_tipo_activo", None),
                ))
################################# 03/12 ################################################## 03/12
                # --- lógica nueva de ubicación ---
                ubic_actual = e.id_ubicacion
                nueva_ubicacion = ubicacion_bodega_para(ubic_actual)
                e.id_ubicacion = nueva_ubicacion
################################# 03/12 ################################################## 03/12
                e.id_empleado = None
                e.id_estado_activo = estado_disponible
                a_actualizar.append(e)

            if a_actualizar:
                Activo.objects.bulk_update(a_actualizar, ["id_empleado", "id_estado_activo", "id_ubicacion"])
            if historiales:
                HistorialActivos.objects.bulk_create(historiales, ignore_conflicts=True)

        messages.success(request, f"Se desasignaron {len(a_actualizar)} activo(s) de {empleado}.")
        return redirect('productos:activos_desasignar')

    #########################################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>

@login_required
def api_activos_disponibles(request):
    """
    Devuelve activos disponibles (estado 'disponible' y sin empleado) filtrados por tipo (opcional).
    JSON: [{id, etiqueta, nombre, marca, tipo, estado}]
    """
    emp_id  = request.session.get("empresa_id")
    tipo_id = request.GET.get("tipo")

    qs = (Activo.objects
          .select_related("id_marca", "id_tipo_activo", "id_estado_activo")
          .filter(id_empleado__isnull=True,
                  id_estado_activo__descripcion__iexact="disponible"))
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
    ##################>>>>>>>>>>>>>>>>>>>>>>>>>>##########################

# productos/views.py

@login_required
def documentos_activo_upload(request, activo_id: int):
    activo = get_object_or_404(Activo, pk=activo_id)

    # scope empresa
    emp_id = request.session.get("empresa_id")
    if emp_id and activo.id_empresa_id != emp_id:
        return HttpResponseForbidden("No permitido para esta empresa.")

    # tipos disponibles (por empresa)
    tipos = TipoDocumentoActivo.objects.filter(
        id_empresa_id=emp_id or activo.id_empresa_id, eliminado=False
    ).order_by("nombre")

    # si no hay tipos, puedes crearlos con el CRUD o sembrar aquí 2 básicos
    if not tipos.exists():
        for name in ("Asignación de activo", "Venta de activo"):
            TipoDocumentoActivo.objects.create(id_empresa_id=emp_id or activo.id_empresa_id, nombre=name)
        tipos = TipoDocumentoActivo.objects.filter(
            id_empresa_id=emp_id or activo.id_empresa_id, eliminado=False
        ).order_by("nombre")

    if request.method == "POST":
        tipo_id = request.POST.get("tipo")
        files = request.FILES.getlist("archivos")  # ← múltiples
        if not tipo_id or not files:
            messages.error(request, "Selecciona un tipo y al menos un archivo.")
            return redirect(request.path)

        tipo = get_object_or_404(TipoDocumentoActivo, pk=tipo_id, eliminado=False)

        for f in files:
            DocumentoActivo.objects.create(
                id_empresa_id=emp_id or activo.id_empresa_id,
                id_activo=activo,
                tipo=tipo,
                archivo=f,
            )

        messages.success(request, f"Se subieron {len(files)} documento(s).")
        next_url = request.POST.get("next") or reverse("productos:activos_list")
        return redirect(next_url)

    # GET: muestra también los ya subidos
    docs = DocumentoActivo.objects.filter(
        id_activo=activo, eliminado=False
    ).select_related("tipo").order_by("-id_documento")

    next_url = request.GET.get("next") or reverse("productos:activos_list")
    ctx = {"activo": activo, "tipos": tipos, "docs": docs, "next_url": next_url}
    return render(request, "activos/documentos_upload.html", ctx)

@login_required
@require_POST
def pma_hacer_vigente(request, pma_id: int):
    """
    Marca un PlanMantencionActivo como 'vigente' y apaga los demás del mismo activo
    (la señal pre_save ya hace el apagado de los otros).
    """
    pma = get_object_or_404(PlanMantencionActivo, pk=pma_id, eliminado=False)

    emp_id = request.session.get("empresa_id")
    if emp_id and getattr(pma, "id_empresa_id", None) != emp_id:
        return HttpResponseForbidden("No permitido para esta empresa.")

    if not pma.es_vigente:
        pma.es_vigente = True
        pma.save(update_fields=["es_vigente"])
        messages.success(request, "Plan marcado como vigente para este activo.")
    else:
        messages.info(request, "Este plan ya está vigente para el activo.")

    return redirect(request.META.get("HTTP_REFERER", "/"))

@login_required
@require_POST
def plan_toggle_habilitado(request, plan_id: int):
    """
    Habilita/Deshabilita un PlanMantencion (no toca los PMA ya creados).
    Si está deshabilitado, no se aplicará a nuevos activos.
    """
    plan = get_object_or_404(PlanMantencion, pk=plan_id, eliminado=False)

    emp_id = request.session.get("empresa_id")
    if emp_id and getattr(plan, "id_empresa_id", None) != emp_id:
        return HttpResponseForbidden("No permitido para esta empresa.")

    plan.habilitado = not plan.habilitado
    plan.save(update_fields=["habilitado"])
    messages.success(request, "Plan habilitado." if plan.habilitado else "Plan deshabilitado.")
    return redirect(request.META.get("HTTP_REFERER", "/"))

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from .models_inventario import PlanMantencion, PlanMantencionActivo
@require_POST
@login_required
def planmantencion_toggle(request, pk):
    obj = get_object_or_404(PlanMantencion, pk=pk)
    obj.habilitado = not obj.habilitado
    obj.save(update_fields=["habilitado"])
    messages.success(
        request,
        f"Plan «{getattr(obj, 'nombre', obj.pk)}» "
        f"{'habilitado' if obj.habilitado else 'deshabilitado'}."
    )
    return redirect(request.POST.get("next") or request.META.get("HTTP_REFERER") or "/")


def _label_activo(activo):
    # usa etiqueta si existe; si no, usa id_activo; si no, el FK numérico
    return getattr(activo, 'etiqueta', None) or getattr(activo, 'id_activo', None) or activo.pk


@require_POST
@login_required
def planmantencionactivo_hacer_vigente(request, pk):
    pma = get_object_or_404(PlanMantencionActivo, pk=pk)
    # regla: 1 solo vigente por activo → apaga los demás del mismo activo
    (PlanMantencionActivo.objects
        .filter(id_activo=pma.id_activo, es_vigente=True)
        .exclude(pk=pma.pk)
        .update(es_vigente=False))
    pma.es_vigente = True
    pma.save(update_fields=['es_vigente'])
    label = _label_activo(pma.id_activo)
    messages.success(request, f"Plan marcado como vigente para el activo {label}.")
    return redirect(request.POST.get('next') or reverse('productos:planmantencionactivos_list'))

@require_POST
def planmantencionactivo_quitar_vigencia(request, pk):
    pma = get_object_or_404(PlanMantencionActivo, pk=pk)
    pma.es_vigente = False
    pma.save(update_fields=['es_vigente'])
    label = _label_activo(pma.id_activo)
    messages.info(request, f"Plan dejado como NO vigente para el activo {label}.")
    return redirect(request.POST.get('next') or reverse('productos:planmantencionactivos_list'))

    #########################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>04/11

from django.shortcuts import render, redirect
from django.http import Http404
from django.utils import timezone
from .models_inventario import PlanMantencionActivo, TipoMedicionActivo
from datetime import timedelta
from decimal import Decimal

def mantencion_realizada(request, pk):
    try:
        plan = PlanMantencionActivo.objects.get(pk=pk)
        tipo_medicion = plan.id_plan.tipo_medicion
        print(f"Recuperado plan {plan.id_plan.nombre} para el activo {plan.id_activo.nombre_activo} [{plan.id_activo.id_activo}]")
        
        if plan.id_plan.tipo_medicion.codigo == "Km":
            # Obtiene la última medición de kilómetros
            ultima_medicion_valor = plan.ultima_medicion_valor or Decimal(0)
            # Suma 10,000 kilómetros a la última medición
            nuevo_valor = ultima_medicion_valor + Decimal(10000)
            # Actualiza el valor de la última medición
            plan.ultima_medicion_valor = nuevo_valor
            # Calcula el próximo vencimiento (sumamos 10,000 km)
            plan.proximo_vencimiento_valor = nuevo_valor
            # Guardamos los cambios
            plan.save()

        # Verificar que tipo de medición sea Día
        if tipo_medicion.codigo == "Día":
            print("Aplicando plan por días")
            # Actualizar la base_fecha a la fecha actual
            plan.base_fecha = timezone.now().date()
            # Calcular el próximo vencimiento
            plan.proximo_vencimiento_fecha = plan.base_fecha + timedelta(days=plan.id_plan.intervalo_dias)
            # Guardar los cambios
            plan.save()

            print(f"Base fecha actualizada a {plan.base_fecha}")
            print(f"Próximo vencimiento actualizado a {plan.proximo_vencimiento_fecha}")

        plan.refresh_from_db()  # Recargar el plan desde la base de datos
        print(f"Valores después del save: Base Fecha: {plan.base_fecha}, Base Valor: {plan.base_valor}")


        # === NUEVO: leer checks y comentarios del POST ===
        tareas_ids = (
            request.POST.getlist("tareas[]") or
            request.POST.getlist("tareas") or
            request.POST.getlist("tareas_ids[]") or  # ← nombre que envía tu JS actual
            []
        )
        obs_map = {}
        for k, v in request.POST.items():
            if k.startswith("obs[") and k.endswith("]"):
                try:
                    tid = int(k[4:-1])
                    txt = (v or "").strip()
                    if txt:
                        obs_map[tid] = txt[:300]
                except ValueError:
                    pass

        # Guarda ejecución con checks + comentarios
        _registrar_ejecucion_pma(request, plan, tareas_ids=tareas_ids, obs_map=obs_map)

        return redirect('productos:planmantencionactivos_list')  # Ajusta esta URL según corresponda

    except PlanMantencionActivo.DoesNotExist:
        raise Http404("Plan no encontrado")

##############################################$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#################04/11
# views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models_inventario import (
    PlanMantencionActivo,
    PlanMantencionTarea,
)

@login_required
def tareas_plan(request, aplicacion_id: int):
    """Devuelve solo el fragmento HTML con las tareas del plan (sin layout)."""
    aplicacion = get_object_or_404(PlanMantencionActivo, pk=aplicacion_id)
    plan = aplicacion.id_plan
    tareas = (PlanMantencionTarea.objects
              .filter(id_plan=plan, eliminado=False)
              .order_by("orden", "id_tarea"))
    return render(request, "activos/tareas_plan.html", {
        "plan": plan,
        "tareas": tareas,
    })

############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>############>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>05/11
############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>############>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>05/11
############################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>############>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>05/11

# productos/views.py
# productos/views.py
from django.http import JsonResponse
from django.db.models import Count

from .models_inventario import Activo, TipoActivo, Ubicacion, Modelo   # usa el módulo correcto
from .mixins import scope_qs_by_empresa                     # si no existe, quita esta línea

########################################### 09/12 ##########################################
@login_required
def overview_data(request):
    """
    API JSON del panel principal (home_sidebar).

    Parte de un queryset base de activos (`qs_base`) ya filtrado por:
    - empresa seleccionada en la sesión (`scope_qs_by_empresa`)
    - borrado lógico (`eliminado = False`)
    - permisos de bodega del usuario (`filtrar_activos_por_bodegas_permitidas`)

    Sobre ese queryset base se aplican los filtros enviados por GET
    (`tipos`, `ubicaciones`, `cargos`, `condiciones`) y se construyen:

    - los datos de los filtros laterales (tipos, ubicaciones, cargos, condición)
    - los datos de los gráficos (marca, ubicación, condición)
    - el listado inferior de activos

    El resultado se devuelve como JSON y es consumido por el JS de `home_sidebar.html`.
    """

    # ==== QS base: empresa + borrado lógico + permisos de bodega ====
    ejecutor = getattr(request.user, "empleado", None)

    qs_base = Activo.objects.select_related(
        "id_tipo_activo",
        "id_ubicacion",
        "id_marca",
        "id_empleado",
        "id_condicion_activo",
    )

    # Filtrar por empresa (si tienes helper)
    try:
        qs_base = scope_qs_by_empresa(request, qs_base)
    except Exception:
        pass

    # Excluir borrados lógicos
    qs_base = qs_base.filter(eliminado=False)

    # 🔒 Permisos de bodega del usuario
    qs_base = filtrar_activos_por_bodegas_permitidas(qs_base, ejecutor)

    # A partir de aquí, trabajamos sobre qs (qs_base + filtros GET)
    qs = qs_base

    # ====== Filtros GET (?tipos=..&ubicaciones=..&cargos=..&condiciones=..) ======
    tipos = request.GET.getlist("tipos")
    ubic  = request.GET.getlist("ubicaciones")
    cargos = request.GET.getlist("cargos")
    condiciones = request.GET.getlist("condiciones")

    if tipos:
        qs = qs.filter(id_tipo_activo__in=[int(x) for x in tipos if x.isdigit()])
    if ubic:
        qs = qs.filter(id_ubicacion__in=[int(x) for x in ubic if x.isdigit()])
    if cargos:
        # cargo es texto, usamos los valores tal cual
        qs = qs.filter(id_empleado__cargo__in=cargos)
    if condiciones:
        qs = qs.filter(id_condicion_activo__in=[int(x) for x in condiciones if x.isdigit()])

    # ====== Filtros laterales ======

    # Tipos
    tipos_qs = (
        qs.values("id_tipo_activo", "id_tipo_activo__tipo_activo")
          .annotate(count=Count("id_activo"))
          .order_by("id_tipo_activo__tipo_activo")
    )
    tipos_data = [
        {
            "id": r["id_tipo_activo"],
            "nombre": r["id_tipo_activo__tipo_activo"],
            "count": r["count"],
        }
        for r in tipos_qs
    ]

    # Ubicaciones
    ubic_qs = (
        qs.values("id_ubicacion", "id_ubicacion__nombre_ubicacion")
          .annotate(count=Count("id_activo"))
          .order_by("id_ubicacion__nombre_ubicacion")
    )
    ubic_data = [
        {
            "id": r["id_ubicacion"],
            "nombre": r["id_ubicacion__nombre_ubicacion"],
            "count": r["count"],
        }
        for r in ubic_qs
    ]

    # Cargos
    cargos_qs = (
        qs.exclude(id_empleado__cargo__isnull=True)
          .exclude(id_empleado__cargo__exact="")
          .values("id_empleado__cargo")
          .annotate(count=Count("id_activo"))
          .order_by("id_empleado__cargo")
    )
    cargos_data = [
        {
            "id": r["id_empleado__cargo"],     # usamos el nombre del cargo como ID del filtro
            "nombre": r["id_empleado__cargo"],
            "count": r["count"],
        }
        for r in cargos_qs
    ]

    # Condiciones
    cond_qs = (
        qs.values("id_condicion_activo", "id_condicion_activo__descripcion")
          .annotate(count=Count("id_activo"))
          .order_by("id_condicion_activo__descripcion")
    )
    condiciones_data = [
        {
            "id": r["id_condicion_activo"],
            "nombre": r["id_condicion_activo__descripcion"] or "—",
            "count": r["count"],
        }
        for r in cond_qs
    ]

    # ====== Gráfico por condición ======
    cond_group = (
        qs.values("id_condicion_activo__descripcion")
          .annotate(c=Count("id_activo"))
          .order_by("-c", "id_condicion_activo__descripcion")
    )
    cond_chart = {
        "labels": [r["id_condicion_activo__descripcion"] or "—" for r in cond_group],
        "data":   [r["c"] for r in cond_group],
    }

    # ====== Gráfico por marca ======
    top = (
        qs.values("id_marca__nombre_marca")
          .annotate(c=Count("id_activo"))
          .order_by("-c")
    )
    modelos = {
        "labels": [r["id_marca__nombre_marca"] or "—" for r in top],
        "data":   [r["c"] for r in top],
    }

    # ====== Gráfico ubicación por tipo seleccionado ======
    qs_loc = qs
    if tipos:
        ids_tipos = [int(x) for x in tipos if x.isdigit()]
        qs_loc = qs.filter(id_tipo_activo__in=ids_tipos)

    loc = (
        qs_loc.values("id_ubicacion__nombre_ubicacion")
              .annotate(c=Count("id_activo"))
              .order_by("-c", "id_ubicacion__nombre_ubicacion")
    )
    tipo_ubic = {
        "labels": [r["id_ubicacion__nombre_ubicacion"] or "—" for r in loc],
        "data":   [r["c"] for r in loc],
    }

    # ====== Tabla inferior ======
    lista_qs = (
        qs.order_by("-id_activo")
          .values(
              "id_activo",
              "etiqueta",
              "nombre_activo",
              "id_tipo_activo__tipo_activo",
              "id_ubicacion__nombre_ubicacion",
              "id_empleado__nombre",
              "id_empleado__apellido_paterno",
              "id_empleado__apellido_materno",
              "id_condicion_activo__descripcion",
          )
    )

    lista = []
    for r in lista_qs:
        nom = r.pop("id_empleado__nombre", None)
        ap1 = r.pop("id_empleado__apellido_paterno", None)
        ap2 = r.pop("id_empleado__apellido_materno", None)
        empleado = " ".join([x for x in [nom, ap1, ap2] if x]) or None

        lista.append({
            "id_activo": r["id_activo"],
            "etiqueta": r["etiqueta"],
            "nombre_activo": r["nombre_activo"],
            "condicion": r["id_condicion_activo__descripcion"],
            "id_tipo_activo__tipo_activo": r["id_tipo_activo__tipo_activo"],
            "id_ubicacion__nombre_ubicacion": r["id_ubicacion__nombre_ubicacion"],
            "empleado": empleado,
        })

    return JsonResponse({
        "tipos": tipos_data,
        "ubicaciones": ubic_data,
        "cargos": cargos_data,
        "condiciones": condiciones_data,
        "modelos": modelos,
        "tipo_ubic": tipo_ubic,
        "lista": lista,
        "total": qs.count(),
        "cond_chart": cond_chart,
    })

########################################### 09/12 ##########################################


##################################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>06/11
# productos/views.py
# productos/views.py
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from .models_inventario import PlanMantencionActivo, PlanMantencionTarea, Registro, TipoRegistro
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType  # <--

@require_GET
@login_required
def pma_checklist(request, pma_id: int):
    pma = (PlanMantencionActivo.objects
           .select_related("id_plan", "id_activo")
           .filter(pk=pma_id, eliminado=False)
           .first())
    if not pma:
        return HttpResponseBadRequest("PMA no encontrado")
    tareas = (PlanMantencionTarea.objects
              .filter(id_plan=pma.id_plan, eliminado=False)
              .order_by("orden", "id_tarea")
              .values("id_tarea", "descripcion", "obligatorio"))
    return JsonResponse({
        "plan": pma.id_plan.nombre,
        "activo": str(pma.id_activo),
        "tareas": list(tareas),
    })

@require_POST
@login_required
def pma_ejecutar(request, pma_id: int):
    # 1) Cargar PMA
    pma = (PlanMantencionActivo.objects
           .select_related("id_plan", "id_activo")
           .filter(pk=pma_id, eliminado=False)
           .first())
    if not pma:
        return HttpResponseBadRequest("PMA no encontrado")

    # 2) Parsear entradas del form
    tareas_ids = request.POST.getlist("tareas[]") or request.POST.getlist("tareas") or []
    marcadas = set(int(x) for x in tareas_ids if str(x).isdigit())

    # Comentarios por tarea: obs[ID] => {ID: "texto"}
    obs_map = {}
    for k, v in request.POST.items():
        if k.startswith("obs[") and k.endswith("]"):
            try:
                tid = int(k[4:-1])
                txt = (v or "").strip()
                if txt:
                    obs_map[tid] = txt[:300]
            except ValueError:
                pass

    # 3) Si el plan es por tiempo, actualizar base y recalcular
    if getattr(pma.id_plan.tipo_medicion, "es_tiempo", False):
        pma.base_fecha = timezone.localdate()
        pma.base_valor = None
    pma.refrescar_estado_y_vencimiento(persist=True)

    # 4) Snapshot de tareas del plan
    tareas_plan = list(
        PlanMantencionTarea.objects
        .filter(id_plan=pma.id_plan, eliminado=False)
        .values("id_tarea", "descripcion", "obligatorio")
        .order_by("orden", "id_tarea")
    )
    labels_ok = [t["descripcion"] for t in tareas_plan if t["id_tarea"] in marcadas]
    resumen = ""
    if labels_ok:
        resumen = f"{len(labels_ok)} tarea(s): " + "; ".join(labels_ok[:5])
        if len(labels_ok) > 5:
            resumen += "…"

    medicion_valor = request.POST.get("medicion_valor") or None
    medicion_fecha = request.POST.get("medicion_fecha") or None

    # 5) Crear cabecera de ejecución
    activo = pma.id_activo
    asign  = getattr(activo, "id_empleado", None)
    ejec = MantencionEjecucion.objects.create(
        id_empresa_id=(getattr(pma, "id_empresa_id", None) or getattr(activo, "id_empresa_id", None)),
        pma=pma,
        id_activo=activo,
        activo_etiqueta=getattr(activo, "etiqueta", None),
        activo_nombre=getattr(activo, "nombre_activo", None),
        id_tipo_activo=getattr(activo, "id_tipo_activo", None),
        empleado_asignado_fk=asign if getattr(asign, "pk", None) else None,
        empleado_asignado_nombre=str(asign) if asign else None,
        usuario_fk=request.user if getattr(request.user, "pk", None) else None,
        usuario_app_username=(request.user.get_full_name() or request.user.username or None),
        notas=(request.POST.get("notas") or None),
        medicion_valor=(medicion_valor if medicion_valor not in ("", None) else None),
        medicion_fecha=(medicion_fecha if medicion_fecha not in ("", None) else None),
        proximo_vencimiento_fecha=getattr(pma, "proximo_vencimiento_fecha", None),
        proximo_vencimiento_valor=getattr(pma, "proximo_vencimiento_valor", None),
        resumen_tareas=(resumen[:500] if resumen else None),
        datos_extra={"tareas_marcadas": sorted(list(marcadas))} if marcadas else {},
    )

    # 6) Detalle por tarea (realizada + comentario)
    bulk = []
    for t in tareas_plan:
        tid = t["id_tarea"]
        bulk.append(MantencionEjecucionTarea(
            ejecucion=ejec,
            id_tarea_plan_id=tid,
            descripcion=(t["descripcion"] or "")[:300],
            obligatorio=bool(t["obligatorio"]),
            marcada=(tid in marcadas),                 # ← “Realizada”
            observacion=obs_map.get(tid),              # ← Comentario
        ))
    if bulk:
        MantencionEjecucionTarea.objects.bulk_create(bulk, batch_size=100)

    # 7) Auditoría (Registro)
    try:
        tipo = TipoRegistro.objects.get(nombre__iexact="Mantención realizada")
    except TipoRegistro.DoesNotExist:
        tipo = TipoRegistro.objects.create(nombre="Mantención realizada")

    ct = ContentType.objects.get_for_model(PlanMantencionActivo)
    Registro.objects.create(
        usuario=getattr(request.user, "empleado", None),
        tipo_registro=tipo,
        content_type=ct,
        object_id=pma.pk,
        descripcion=f"Mantención realizada en {pma.id_activo}",
        datos_nuevos={"tareas_marcadas": sorted(list(marcadas))},
        id_empresa=pma.id_empresa,
    )

    return JsonResponse({"ok": True})


#######################################################################>>>>>>>>>>>>>>>>>>>07/11
#######################################################################>>>>>>>>>>>>>>>>>>>07/11

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.db.models import Q
from .models_inventario import MantencionEjecucion

class PmaHistorialListView(LoginRequiredMixin, ListView):
    model = MantencionEjecucion
    template_name = "mantenciones/pma_historial_list.html"
    context_object_name = "items"
    paginate_by = 25

    def get_queryset(self):
        qs = (MantencionEjecucion.objects
              .select_related("id_activo", "pma", "id_empresa", "usuario_fk", "pma__id_plan", "pma__id_activo")
              .order_by("-fecha_ejecucion", "-id"))  # 👈 nuevo
        emp_id = self.request.session.get("empresa_id")
        if emp_id:
            qs = qs.filter(id_empresa_id=emp_id)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(activo_etiqueta__icontains=q) |
                Q(activo_nombre__icontains=q)   |
                Q(usuario_app_username__icontains=q) |
                Q(resumen_tareas__icontains=q) |
                Q(pma__id_plan__nombre__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["now"] = timezone.now()
        return ctx


#########################################################################################>>>>>>>>>>>>>>>07/11-20:05
# views.py (agrega junto a otros @login_required JSON)
from django.views.decorators.http import require_GET

@login_required
@require_GET
def ejecucion_tareas_json(request, ejec_id: int):
    """
    Devuelve las tareas registradas para una ejecución (log),
    con sus banderas (obligatorio, marcada) y observación.
    """
    ejec = get_object_or_404(MantencionEjecucion, pk=ejec_id)

    tareas = (
        MantencionEjecucionTarea.objects
        .filter(ejecucion=ejec)
        .order_by('id')
    )
    data = {
        "plan": getattr(ejec.pma.id_plan, "nombre", ""),
        "activo_etiqueta": ejec.activo_etiqueta or "",
        "activo_nombre": ejec.activo_nombre or "",
        "items": [{
            # CAMBIO: tus campos en el snapshot
            "descripcion": t.descripcion or "",
            "obligatorio": bool(t.obligatorio),
            # CAMBIO: API devuelve "realizada", mapeando tu campo "marcada"
            "realizada": bool(t.marcada),
            "observacion": t.observacion or "",
        } for t in tareas]
    }
    return JsonResponse(data)

    ######################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>11/11 16:30
    ###################################################################################>>>>>>>>>>>>>>>>>>>>>>>>13/11
    # productos/views.py
@login_required
@login_required
def panel_notas_activo(request, id_activo: int):
    activo = get_object_or_404(Activo, pk=id_activo, eliminado=False)
    grupos = activo.notas_grouped_por_dia()  # lista de grupos del modelo

    emp_id = request.session.get("empresa_id")
    if emp_id and getattr(activo, "id_empresa_id", None) != emp_id:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No permitido para esta empresa.")

    hoy  = timezone.localdate()
    ayer = hoy - timedelta(days=1)

    MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

    def normaliza(d):
        # d puede venir como date o datetime
        if hasattr(d, "tzinfo"):      # datetime
            d = timezone.localtime(d).date()
        label = f"{d.day} {MESES[d.month-1]} {d.year}"
        if d == hoy:
            label += " (hoy)"
        elif d == ayer:
            label += " (ayer)"
        return d, label

    grupos_fmt = []
    for g in grupos:
        # acepta "fecha" o "dia" según lo que devuelva tu helper
        base = g.get("fecha") or g.get("dia")
        f_local, label = normaliza(base)
        g2 = dict(g)
        g2["fecha"] = f_local
        g2["label"] = label
        grupos_fmt.append(g2)

    ctx = {
        "activo": activo,
        "grupos": grupos_fmt,  # ← IMPORTANTE: ahora sí mandamos los formateados
        "total_notas": sum(len(g["items"]) for g in grupos_fmt),
        "hoy": hoy,
        "ayer": ayer,
    }
    return render(request, "activos/_panel_notas.html", ctx)

@login_required
@require_POST
def crear_nota_activo_ajax(request, id_activo: int):
    """Crea la nota y devuelve el MISMO parcial ya actualizado."""
    activo = get_object_or_404(Activo, pk=id_activo, eliminado=False)
    texto = (request.POST.get("texto") or "").strip()
    foto  = request.FILES.get("foto")  # ⬅️ NUEVO

    if not texto and not foto:
        return HttpResponseBadRequest("Debes escribir una nota o adjuntar una foto.")
    
    emp_id = request.session.get("empresa_id")
    if emp_id and getattr(activo, "id_empresa_id", None) != emp_id:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No permitido para esta empresa.")

    emp = getattr(request.user, "empleado", None)
    ActivoNota.objects.create(
        id_activo=activo,
        id_autor=emp if emp else None,
        id_empresa=(emp.id_empresa if emp else getattr(activo, "id_empresa", None)),
        texto=texto,
        foto=foto,  # ⬅️ NUEVO
    )
    # devolvemos el panel ya refrescado
    return panel_notas_activo(request, id_activo)
    ###################################################################################>>>>>>>>>>>>>>>>>>>>>>>>13/11
    ###################################################################################>>>>>>>>>>>>>>>>>>>>>>>>13/11


#########################################################>>>>>>>>>>>>>>>>>>>>>>>>>>>15/11
def aplicar_regla_criticidad(activo):
    """
    Aplica la ReglaCriticidad al activo según:
      - empresa
      - tipo de activo
      - cargo del empleado

    NO guarda en BD, solo modifica el objeto en memoria.
    """
    # Empleado asociado
    empleado = getattr(activo, "id_empleado", None)
    if not empleado or not activo.id_tipo_activo_id:
        return

    # Cargo “limpio”
    cargo = (empleado.cargo or "").strip()
    if not cargo:
        return

    # Empresa: primero la del activo, si no, la del empleado
    empresa_id = getattr(activo, "id_empresa_id", None) or getattr(empleado, "id_empresa_id", None)
    if not empresa_id:
        return

    # Importa aquí para evitar problemas de import circular si tienes muchos modelos
    from .models_inventario import ReglaCriticidad

    regla = (
        ReglaCriticidad.objects
        .filter(
            eliminado=False,
            id_empresa_id=empresa_id,
            id_tipo_activo_id=activo.id_tipo_activo_id,
            cargo_nombre__iexact=cargo,
        )
        .order_by("id_regla")
        .first()
    )
    if not regla:
        return

    # Marcamos como crítico
    activo.activo_critico = True

    # Solo rellenamos si están vacíos / en None
    if not getattr(activo, "clasificacion", None):
        activo.clasificacion = getattr(regla, "clasificacion", None)
    if getattr(activo, "confidencialidad", None) is None:
        activo.confidencialidad = getattr(regla, "confidencialidad", None)
    if getattr(activo, "integridad", None) is None:
        activo.integridad = getattr(regla, "integridad", None)
    if getattr(activo, "disponibilidad", None) is None:
        activo.disponibilidad = getattr(regla, "disponibilidad", None)

#########################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>15/11
    ################################# 26/11 ########################################
@login_required
def factura_detalles_view(request, pk: int):
    """
    Editor de líneas de una factura usando inline formset.

    - Muestra todas las líneas de DetalleFactura de la factura.
    - Permite agregar varias líneas nuevas a la vez.
    - Permite marcar líneas para eliminar (borrado lógico si existe `eliminado`).
    """
    from .models_inventario import Factura, DetalleFactura

    emp_id = request.session.get("empresa_id")
    if not emp_id:
        raise Http404("Empresa no seleccionada.")

    factura = get_object_or_404(Factura, pk=pk)

    # seguridad multiempresa
    if getattr(factura, "id_empresa_id", None) != emp_id:
        return HttpResponseForbidden("No permitido para la empresa actual.")

    # Base para el formset: solo detalles de esta factura y empresa
    qs_detalles = DetalleFactura.objects.filter(
        id_factura=factura,
        id_empresa_id=emp_id,
    )
    # Si el modelo tiene borrado lógico, excluimos los eliminados
    if hasattr(DetalleFactura, "eliminado"):
        qs_detalles = qs_detalles.filter(eliminado=False)

    # Configuramos el formset
    DetalleFormSet = inlineformset_factory(
        Factura,
        DetalleFactura,
        form=DetalleFacturaInlineForm,
        fk_name="id_factura",
        extra=5,          # nº de filas nuevas vacías
        can_delete=True,  # checkbox para borrar líneas existentes
    )

    if request.method == "POST":
        formset = DetalleFormSet(
            request.POST,
            instance=factura,
            queryset=qs_detalles,
        )

        if formset.is_valid():
            # Guardamos sin commit para poder setear empresa, etc.
            detalles = formset.save(commit=False)

            # 1) Borrados: marcamos eliminado=True si existe el campo, si no, borramos
            for obj in formset.deleted_objects:
                if hasattr(obj, "eliminado"):
                    obj.eliminado = True
                    obj.save(update_fields=["eliminado"])
                else:
                    obj.delete()

            # 2) Nuevos y modificados
            for det in detalles:
                # Aseguramos la FK a factura
                det.id_factura = factura

                # Asignamos empresa si viene vacía
                if emp_id and hasattr(det, "id_empresa_id") and not det.id_empresa_id:
                    det.id_empresa_id = emp_id

                det.save()

            dj_messages.success(
                request,
                "Detalles de la factura guardados correctamente."
            )
            # Volvemos a la misma pantalla
            return redirect(request.path)

    else:
        formset = DetalleFormSet(
            instance=factura,
            queryset=qs_detalles,
        )

    # Totales con lo que hay actualmente en BD (sin eliminados)
    detalles_db = qs_detalles.order_by("id_detalle_factura")
    total_neto = sum(d.valor_neto or 0 for d in detalles_db)
    total_iva = sum(d.iva or 0 for d in detalles_db)
    total_total = sum(d.valor_total or 0 for d in detalles_db)

    ctx = {
        "factura": factura,
        "formset": formset,
        "detalles": detalles_db,  # por si quieres mostrar algo en modo lectura
        "total_neto": total_neto,
        "total_iva": total_iva,
        "total_total": total_total,
    }
    # 👇 Cambiamos el template a uno pensado para formset
    return render(request, "productos/factura_detalle_formset.html", ctx)



@login_required
def vincular_activos_factura(request, pk: int):
    """
    Vista para vincular Activos a los DetalleFactura de una Factura específica.

    - Restringe por empresa en sesión.
    - Muestra todos los detalles de la factura con:
        * cantidad total
        * cantidad ya vinculada
        * cantidad restante
    - Lista activos disponibles (sin id_detalle_factura) para vincularlos al detalle elegido.
    """
    from .models_inventario import (
        Factura,
        DetalleFactura,
        Activo,
        AtributosActivo,
        AgregacionAtributosPorActivo,
    )

    emp_id = request.session.get("empresa_id")
    if not emp_id:
        raise Http404("Empresa no seleccionada.")

    factura = get_object_or_404(Factura, pk=pk)

    # Seguridad: la factura debe pertenecer a la empresa en sesión
    if getattr(factura, "id_empresa_id", None) != emp_id:
        return HttpResponseForbidden("No permitido para la empresa actual.")

    # Obtener los activos ya vinculados a la factura
    activos_vinculados = Activo.objects.filter(id_factura=factura)

    # Agrupar los activos por detalle de factura
    detalles = DetalleFactura.objects.filter(id_factura=factura, eliminado=False)
    detalles_con_activos = {}
    
    for detalle in detalles:
        activos_por_detalle = activos_vinculados.filter(id_detalle_factura=detalle)
        detalles_con_activos[detalle] = {
            'activos': activos_por_detalle,
            'valor_unitario': detalle.valor_unitario  # Valor unitario de cada detalle
        }

    # --- BASE: activos de la empresa, no eliminados ---
    activos_base = Activo.objects.all()
    if getattr(Activo, "_meta", None) and hasattr(Activo._meta, "fields"):
        # por si usas helpers _model_has_empresa_fk / _has_field, puedes
        # reemplazar esta parte usando esos helpers
        activos_base = activos_base.filter(id_empresa_id=emp_id, eliminado=False)

    # --- DETALLES DE FACTURA CON CONTADORES ---
    detalles = list(
        DetalleFactura.objects.filter(
            id_factura=factura,
            id_empresa_id=emp_id,
            eliminado=False,
        ).order_by("id_detalle_factura")
    )


    # --- ACTIVOS DISPONIBLES: sin detalle asignado todavía ---
    activos_disponibles = activos_base.filter(
        id_empresa_id=emp_id,
        eliminado=False,
        id_detalle_factura__isnull=True,
    )

    # Tipos de activo que aparecen en los activos disponibles
    tipos_activo = (
        TipoActivo.objects.filter(
            id_empresa_id=emp_id,
            activo__in=activos_disponibles,   # FK inversa desde Activo
            eliminado=False                  # si tu modelo tiene este campo
        )
        .distinct()
        .order_by("tipo_activo")
    )

    if request.method == "POST":
        detalle_id = request.POST.get("detalle_id")
        activos_ids = request.POST.getlist("activos_ids")

        if not detalle_id or not activos_ids:
            dj_messages.error(
                request,
                "Debes seleccionar un detalle de factura y al menos un activo.",
            )
            return redirect(request.path)

        detalle = get_object_or_404(
            DetalleFactura,
            pk=detalle_id,
            id_factura=factura,
            id_empresa_id=emp_id,
        )

        vinculados = detalle.cantidad_vinculada
        total = detalle.cantidad or 0
        restantes = max(total - vinculados, 0)

        seleccion = activos_disponibles.filter(id_activo__in=activos_ids)

        # Si el detalle tiene cantidad, respetamos el tope
        if total and seleccion.count() > restantes:
            dj_messages.error(
                request,
                (
                    f"No es posible vincular {seleccion.count()} activos: "
                    f"solo quedan {restantes} unidades disponibles para ese detalle."
                ),
            )
            return redirect(request.path)

        # Buscar atributo dinámico "Valor en Factura" para este tipo de activo
        # (si existe, se rellenará al vuelo)
        def actualizar_valor_en_factura(activo, detalle):
            """
            Actualiza el atributo dinámico 'Valor en Factura' de un activo
            usando el valor_unitario del detalle.
            Si no existe el atributo, se ignora silenciosamente.
            """
            if detalle.valor_unitario is None:
                return

            try:
                attr = AtributosActivo.objects.filter(
                    atributo__iexact="Valor en Factura",
                    id_tipo_activo_id=activo.id_tipo_activo_id,
                    id_empresa_id=activo.id_empresa_id,
                    eliminado=False,
                ).first()
            except Exception:
                return

            if not attr:
                return

            try:
                AgregacionAtributosPorActivo.objects.update_or_create(
                    activo=activo,
                    atributo=attr,
                    defaults={"valor": str(detalle.valor_unitario)},
                )
            except Exception:
                # no queremos romper la vinculación por esto
                pass

        # Guardamos todo junto
        with transaction.atomic():
            for a in seleccion:
                # Vincular al detalle seleccionado
                a.id_detalle_factura = detalle

                # Asegurar que el activo quede asociado a ESTA factura
                if a.id_factura_id != factura.id_factura:
                    a.id_factura = factura

                # Actualizar proveedor del activo según la factura
                if factura.id_proveedor_id and a.id_proveedor_id != factura.id_proveedor_id:
                    a.id_proveedor_id = factura.id_proveedor_id

                # Guardamos solo los campos que realmente cambiaron
                a.save(update_fields=["id_detalle_factura", "id_factura", "id_proveedor"])

                # Actualizar atributo dinámico "Valor en Factura"
                actualizar_valor_en_factura(a, detalle)

        dj_messages.success(
            request,
            f"Se vincularon {seleccion.count()} activo(s) al detalle de la factura."
        )
        return redirect(request.path)

    ctx = {
        "factura": factura,
        "detalles": detalles,
        "activos_disponibles": activos_disponibles,
        "activos_vinculados": activos_vinculados,  # Incluir los activos vinculados en el contexto
        "detalles_con_activos": detalles_con_activos,  # Agrupamos activos por detalle
        "tipos_activo": tipos_activo, 

    }
    return render(request, "productos/vincular_activos.html", ctx)


# productos/views_facturas_multi.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models_inventario import Empresa, Factura, DetalleFactura
from .forms import DetalleFacturaFormSet

from django.urls import reverse


############################## 27/11 ########################################
def nuevo_detalle_factura_multiple(request):
    """
    Crea VARIAS líneas de DetalleFactura para una misma factura.
    """
    empresa_id = request.session.get("empresa_id")
    empresa = None
    if empresa_id:
        empresa = Empresa.objects.filter(pk=empresa_id, eliminado=False).first()

    # Factura seleccionada (GET ?factura=ID o POST)
    factura_id = request.GET.get("factura") or request.POST.get("factura")
    factura = None
    if factura_id:
        factura = get_object_or_404(
            Factura.objects.select_related("id_proveedor"),
            pk=factura_id,
            eliminado=False,
        )

    # Facturas para el combo
    facturas_qs = Factura.objects.filter(
        eliminado=False,
        id_empresa_id=empresa_id if empresa_id else None,
    ).order_by("-id_factura")

    if request.method == "POST":
        formset = DetalleFacturaFormSet(
            request.POST,
            queryset=DetalleFactura.objects.none(),  # siempre creo nuevos
            prefix="linea",
        )

        if not factura:
            # Error simple si no seleccionó factura
            formset.non_form_errors = lambda: ["Debes seleccionar una factura."]
        elif formset.is_valid():
            creados = []

            for form in formset:
                if not form.cleaned_data:
                    continue  # fila totalmente vacía

                nombre = form.cleaned_data.get("nombre_activo")
                cantidad = form.cleaned_data.get("cantidad")
                v_unit = form.cleaned_data.get("valor_unitario")

                # Si no tiene datos básicos, la considero vacía
                if not (nombre and cantidad and v_unit):
                    continue

                detalle = form.save(commit=False)
                detalle.id_factura = factura
                if empresa and detalle.id_empresa_id is None:
                    detalle.id_empresa = empresa

                detalle.save()  # aquí se recalcula neto/iva/total en el modelo
                creados.append(detalle)

            if creados:
                factura.recalcular_totales()

            # 🔹 Ahora vamos al listado de DetalleFacturas filtrado por factura
            return redirect(f"/detallefacturas/?factura={factura.id_factura}")
    else:
        # GET: una fila vacía
        formset = DetalleFacturaFormSet(
            queryset=DetalleFactura.objects.none(),
            prefix="linea",
        )

    contexto = {
        "empresa": empresa,
        "facturas": facturas_qs,
        "factura": factura,
        "formset": formset,
    }
    return render(request, "productos/detalle_factura_multiple_form.html", contexto)


    ################################# 27/11 ########################################
from django.shortcuts import get_object_or_404, redirect
from .models_inventario import Activo

@login_required
def desvincular_activo(request, activo_id):
    """
    Desvincula un activo de la factura y lo vuelve a poner en la lista de activos disponibles.
    """
    # Asegurarse de que el usuario tiene permisos
    activo = get_object_or_404(Activo, pk=activo_id)

    # Si el activo tiene vinculado un detalle de factura, lo desvinculamos
    if activo.id_detalle_factura:
        activo.id_detalle_factura = None
        activo.save()

        # Mensaje de éxito
        messages.success(request, f"Activo {activo.etiqueta} desvinculado exitosamente.")

    # Redirigir de vuelta a la página de vinculación de activos
    return redirect(request.META.get('HTTP_REFERER'))

####################################### 08/12 NUEVA VERSIÓN ######################
def ubicacion_bodega_para(ubic):
    from .models_inventario import Bodega, Ubicacion

    if ubic is None:
        return None

    # Si es Ubicacion y tiene bodega de retorno → devolvemos
    # la ubicación física de esa bodega
    if hasattr(ubic, "id_bodega_retorno") and ubic.id_bodega_retorno_id:
        bodega = ubic.id_bodega_retorno
        return bodega.id_ubicacion  # también es Ubicacion

    # Si ya está en una ubicación que es bodega o no tiene mapeo
    return ubic
####################################### 08/12 NUEVA VERSIÓN ######################

