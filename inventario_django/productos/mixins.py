# productos/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied, FieldDoesNotExist
from django.shortcuts import redirect
from django.db.models import ForeignKey, OneToOneField
from .models_inventario import Empleado
from django.contrib import messages
from .models_inventario import Activo, Ubicacion, Bodega, PermisoBodega
from django.core.exceptions import FieldError  # 👈 añade esto


# ==================== Roles / helpers de rol ====================

# Tomamos las constantes desde el modelo Empleado para no duplicar strings
ROL_ADMIN      = Empleado.ROL_ADMIN
ROL_JEFE       = Empleado.ROL_JEFE
ROL_USUARIO    = Empleado.ROL_USUARIO
ROL_INVITADO   = Empleado.ROL_INVITADO
ROL_TRABAJADOR = Empleado.ROL_TRABAJADOR


def rol_de_usuario(user):
    """
    Devuelve uno de: 'admin', 'jefe', 'usuario', 'empleado' o None.
    NO cambia nada en la BD, solo mira lo que ya existe.
    """
    if not user.is_authenticated:
        return ROL_TRABAJADOR

    # Súperusuario de Django => admin del sistema
    if user.is_superuser:
        return ROL_ADMIN

    empleado = getattr(user, "empleado", None)
    if not empleado:
        # Usuario sin registro de Empleado → lo tratamos como "usuario"
        return ROL_TRABAJADOR

    raw = (empleado.rol or "").lower()

    if raw in (ROL_ADMIN, ROL_JEFE, ROL_USUARIO, ROL_INVITADO):
        return raw

    return ROL_TRABAJADOR

# ==================== Permisos / login ====================

class ModelPermsMixin(LoginRequiredMixin):
    """
    Exige que el usuario esté autenticado y que tenga los permisos necesarios 
    para realizar acciones sobre un modelo en particular. Los permisos son definidos
    con la propiedad `action_perm` que se mapea a un permiso `<app_label>.<action_perm>_<model_name>`.
    
    El valor de `action_perm` puede ser 'view', 'add', 'change', o 'delete'.
    """
    ###################################### 09/12 #########################################
    # Modelos en los que NO queremos chequear permisos Django
    # (solo se aplican los roles / CompanyRequiredMixin)
    public_models = {"bodega"}  # 👈 aquí puedes agregar más si quieres

    def dispatch(self, request, *args, **kwargs):
        # Si la vista marca action_perm=None, no pedimos permisos extra
        action_perm = getattr(self, "action_perm", None)
        model = getattr(self, "model", None)

        # Si no hay modelo definido, o no queremos revisar permisos aquí, dejamos pasar
        if action_perm is None or model is None:
            return super().dispatch(request, *args, **kwargs)

        model_name = model._meta.model_name.lower()

        # 👉 Para Bodega, dejamos pasar sin chequear has_perm
        if model_name in self.public_models:
            return super().dispatch(request, *args, **kwargs)

        app = model._meta.app_label
        perm_codename = f"{app}.{action_perm}_{model_name}"

        if not request.user.has_perm(perm_codename):
            return HttpResponseForbidden("403 Forbidden")

        return super().dispatch(request, *args, **kwargs)
    ###################################### 09/12 #########################################

class CompanyRequiredMixin(LoginRequiredMixin):
    """
    Exige que el usuario esté autenticado **y** tenga una empresa seleccionada
    en la sesión. Si no hay empresa, redirige al selector de empresa.
    Además, bloquea a los trabajadores sin acceso.
    """
    def dispatch(self, request, *args, **kwargs):
        # Primero forzamos login (LoginRequiredMixin)
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Luego revisamos empresa
        if not request.session.get("empresa_id"):
            return redirect("productos:company_select")
        
        # 🚫 BLOQUEO: rol sin acceso (empleado)
        from .mixins import rol_de_usuario, ROL_TRABAJADOR  # si estás en el mismo archivo NO hace falta reimportar
        if rol_de_usuario(request.user) == ROL_TRABAJADOR:
            return HttpResponseForbidden("No tienes acceso a la aplicación de inventario.")

        return super().dispatch(request, *args, **kwargs)

############################## 04/12 ######################################
# ==================== Roles requeridos ====================
class RoleRequiredMixin(CompanyRequiredMixin):
    """
    Mixin para exigir uno o varios roles de Empleado.

    Uso:
        class MiVista(RoleRequiredMixin, TemplateView):
            required_roles = [ROL_ADMIN, ROL_JEFE]

    Hereda de CompanyRequiredMixin, así que:
      - exige login,
      - exige empresa en sesión,
      - y además revisa el rol.
    """

    # Lista/tupla de roles permitidos. Ej:
    #   [ROL_ADMIN, ROL_JEFE]
    required_roles = None

    def dispatch(self, request, *args, **kwargs):
        # 1) Aseguramos login primero
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # 2) Obtenemos el rol lógico del usuario
        rol = rol_de_usuario(request.user)

        # 3) Si hay lista de roles y el usuario NO está dentro, bloqueamos
        if self.required_roles and rol not in self.required_roles:
            messages.error(request, "No tienes permisos para acceder a esta sección.")
            return redirect("productos:home")
            # o, si prefieres 403:
            # raise PermissionDenied("No tienes permisos para acceder a esta sección.")

        # 4) Si pasa el filtro de rol, dejamos que CompanyRequiredMixin
        #    haga su trabajo (empresa_id en sesión, etc.)
        return super().dispatch(request, *args, **kwargs)

class AdminJefeRequiredMixin(RoleRequiredMixin):
    required_roles = [ROL_ADMIN, ROL_JEFE]


class SoloAdminRequiredMixin(RoleRequiredMixin):
    required_roles = [ROL_ADMIN]

############################## 04/12 ######################################



# ==================== Scoping por empresa ====================

# productos/mixins.py
from django.db.models import ForeignKey, OneToOneField

def scope_qs_by_empresa(request, qs):
    """
    Aplica un filtro de empresa a las consultas, asegurando que los resultados
    solo incluyan los objetos de la empresa activa en la sesión.
    
    :param request: La solicitud HTTP, que debe contener la empresa activa en la sesión.
    :param qs: La queryset a filtrar por `id_empresa`.
    :return: La queryset filtrada por empresa.
    """
    if qs is None:
        return qs
    emp_id = request.session.get("empresa_id")
    if not emp_id:
        return qs

    m = qs.model
    fields = {f.name: f for f in m._meta.get_fields() if hasattr(f, "name")}

    # 1) Campo directo id_empresa (entero o FK)
    f = fields.get("id_empresa")
    if f:
        # si es FK usamos id_empresa_id; si es entero, id_empresa
        return qs.filter(id_empresa_id=emp_id) if getattr(f, "is_relation", False) else qs.filter(id_empresa=emp_id)

    # 2) FK llamada 'empresa'
    f = fields.get("empresa")
    if f and getattr(f, "is_relation", False):
        return qs.filter(empresa_id=emp_id)

    # 3) Cualquier FK cuyo modelo relacionado tenga id_empresa
    for f in m._meta.get_fields():
        if getattr(f, "is_relation", False) and getattr(f, "concrete", False):
            rel = getattr(f, "related_model", None)
            if not rel:
                continue
            rel_field_names = {rf.name for rf in rel._meta.get_fields() if hasattr(rf, "name")}
            if "id_empresa" in rel_field_names:
                # filtra a través de la relación detectada (ej: tipo_activo__id_empresa)
                return qs.filter(**{f"{f.name}__id_empresa": emp_id}).distinct()

    return qs

class EmpresaScopeMixin(LoginRequiredMixin):
    """
    Mixin para aplicar el filtro de empresa en las vistas basadas en clases (CBVs).
    Asegura que las consultas (`querysets`) solo devuelvan resultados de la empresa activa.
    """
    def scope_queryset(self, qs):
        return scope_qs_by_empresa(self.request, qs)


class SaveEmpresaMixin(LoginRequiredMixin):
    """
    Mixin que se asegura de que al guardar una instancia de modelo que tenga un campo `id_empresa`, 
    este campo se complete automáticamente con el `empresa_id` de la sesión si no está presente.
    """
    def form_valid(self, form):
        emp_id = self.request.session.get("empresa_id")
        if emp_id:
            if hasattr(form.instance, "id_empresa_id") and not form.instance.id_empresa_id:
                form.instance.id_empresa_id = emp_id
            elif hasattr(form.instance, "id_empresa") and not getattr(form.instance, "id_empresa", None):
                form.instance.id_empresa = emp_id
        return super().form_valid(form)


#####################################>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>10/11
# mixins.py
from django.core.exceptions import ValidationError

class EmpresaBoundMixin:
    """
    Mixin para: 
    - fijar id_empresa desde la sesión,
    - autocompletarlo en initial,
    - deshabilitar el campo en el form,
    - validar que no cambie en updates.
    """
    empresa_field_name = "id_empresa"          # nombre del campo FK
    empresa_field_id_name = "id_empresa_id"    # nombre interno *_id

    def get_empresa_id(self):
        return self.request.session.get("empresa_id")

    # (2) Mejor UX: initial con la empresa de sesión
    def get_initial(self):
        initial = super().get_initial()
        emp_id = self.get_empresa_id()
        if emp_id and hasattr(self.model, self.empresa_field_name):
            initial.setdefault(self.empresa_field_name, emp_id)
        return initial

    # (3) Opcional: deshabilitar el campo para que no lo cambien
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.empresa_field_name in form.fields:
            form.fields[self.empresa_field_name].disabled = True
        return form

    # (1) Servidor manda: antes de guardar, fuerza la empresa de sesión
    def form_valid(self, form):
        emp_id = self.get_empresa_id()
        if emp_id and hasattr(form.instance, self.empresa_field_id_name):
            # En Create: setea siempre
            if self.__class__.__name__.lower().startswith("genericcreate"):
                setattr(form.instance, self.empresa_field_id_name, emp_id)
            # En Update: no permitir cambiar empresa
            else:
                # Si existe inconsistencia, la corriges o levantas error
                if getattr(form.instance, self.empresa_field_id_name, None) != emp_id:
                    # Opción A (corrige silenciosamente):
                    setattr(form.instance, self.empresa_field_id_name, emp_id)
                    # Opción B (más estricta):
                    # raise ValidationError("La empresa del registro no coincide con la empresa activa.")
        return super().form_valid(form)
    
############################################## 09/12 #####################################
# ================== NUEVO: filtro por permisos de bodegas ==================

def filtrar_activos_por_bodegas_permitidas(qs, empleado):
    """
    Restringe un queryset de Activo según las bodegas permitidas del empleado.

    Regla:
      - Si empleado es Admin o Jefe → devuelve qs tal cual.
      - Si empleado es Usuario → sólo activos en:
          * Ubicación física de las bodegas que tiene autorizadas
          * Ubicaciones cuya bodega_retorno sea una de esas bodegas
      - Si empleado no tiene permisos → qs.none()
      - Si request.user no tiene empleado asociado → no filtra (qs tal cual)
    """
    if empleado is None:
        # superusers de Django sin empleado → dejamos pasar
        return qs

    # Admin / Jefe → sin filtro adicional
    try:
        if empleado.es_supervisor():
            return qs
    except Exception:
        return qs

    bodega_ids = empleado.bodegas_autorizadas_ids()

    # Si devuelve None, lo interpretamos como “sin restricción” (por si en el futuro cambias la lógica)
    if bodega_ids is None:
        return qs

    # Si no tiene ninguna bodega asignada → no ve nada
    if not bodega_ids:
        return qs.none()

    # 1) Ubicación física de cada bodega
    ubic_bodega_ids = list(
        Bodega.objects.filter(
            id_bodega__in=bodega_ids,
            eliminado=False,
        ).values_list("id_ubicacion_id", flat=True)
    )

    # 2) Ubicaciones “de campo” cuya bodega_retorno sea una de esas bodegas
    ubic_retorno_ids = list(
        Ubicacion.objects.filter(
            id_bodega_retorno__in=bodega_ids,
            eliminado=False,
        ).values_list("id_ubicacion", flat=True)
    )

    ubic_ids = set(ubic_bodega_ids) | set(ubic_retorno_ids)

    if not ubic_ids:
        return qs.none()

    return qs.filter(id_ubicacion_id__in=ubic_ids)

def filtrar_empleados_por_bodegas_permitidas(qs, empleado):
    """
    Restringe un queryset de Empleado según las bodegas permitidas del empleado
    que ejecuta la acción.

    Regla:
      - Si empleado es Admin/Jefe (es_supervisor=True) → devuelve qs tal cual.
      - Si tiene bodegas autorizadas → solo empleados cuya ubicacion esté:
          * en la ubicación física de esas bodegas
          * o en ubicaciones cuya bodega_retorno sea una de esas bodegas
      - Si no tiene bodegas asignadas → qs.none()
      - Si no hay empleado (superuser sin empleado) → no filtra (qs tal cual)
    """
    if empleado is None:
        # superusers de Django sin empleado → dejamos pasar
        return qs

    # Admin / Jefe → sin filtro adicional
    try:
        if empleado.es_supervisor():
            return qs
    except Exception:
        return qs

    bodega_ids = empleado.bodegas_autorizadas_ids()

    # Si devuelve None, lo interpretamos como “sin restricción”
    if bodega_ids is None:
        return qs

    # Si no tiene ninguna bodega asignada → no ve a nadie
    if not bodega_ids:
        return qs.none()

    # 1) Ubicación física de cada bodega
    ubic_bodega_ids = list(
        Bodega.objects.filter(
            id_bodega__in=bodega_ids,
            eliminado=False,
        ).values_list("id_ubicacion_id", flat=True)
    )

    # 2) Ubicaciones “de campo” cuya bodega_retorno sea una de esas bodegas
    ubic_retorno_ids = list(
        Ubicacion.objects.filter(
            id_bodega_retorno__in=bodega_ids,
            eliminado=False,
        ).values_list("id_ubicacion", flat=True)
    )

    ubic_ids = set(ubic_bodega_ids) | set(ubic_retorno_ids)

    if not ubic_ids:
        return qs.none()

    # OJO: en Empleado el campo es `ubicacion`, por eso usamos `ubicacion_id`
    return qs.filter(ubicacion_id__in=ubic_ids)

def filtrar_qs_por_permiso_bodega_sobre_activo(qs, empleado, fk_name="id_activo"):
    """
    Aplica el filtro de permisos de bodega a un queryset cuyo modelo
    tiene un FK hacia `Activo`.

    - `qs`       : queryset de, por ejemplo, PlanMantencionActivo o MantencionEjecucion.
    - `empleado`: empleado que ejecuta la acción (request.user.empleado).
    - `fk_name` : nombre del campo FK hacia Activo (por defecto 'id_activo').

    La lógica replica la de `filtrar_activos_por_bodegas_permitidas`, pero
    filtrando a través del FK indicado.
    """
    if empleado is None:
        # superusers sin empleado → no filtramos nada extra
        return qs

    # Admin / Jefe → sin filtro adicional
    try:
        if empleado.es_supervisor():
            return qs
    except Exception:
        return qs

    bodega_ids = empleado.bodegas_autorizadas_ids()

    # Si devuelve None, lo interpretamos como “sin restricción”
    if bodega_ids is None:
        return qs

    # Si no tiene bodegas → no ve nada
    if not bodega_ids:
        return qs.none()

    # 1) Ubicación física de cada bodega
    ubic_bodega_ids = list(
        Bodega.objects.filter(
            id_bodega__in=bodega_ids,
            eliminado=False,
        ).values_list("id_ubicacion_id", flat=True)
    )

    # 2) Ubicaciones de campo cuya bodega_retorno es una de esas bodegas
    ubic_retorno_ids = list(
        Ubicacion.objects.filter(
            id_bodega_retorno__in=bodega_ids,
            eliminado=False,
        ).values_list("id_ubicacion", flat=True)
    )

    ubic_ids = set(ubic_bodega_ids) | set(ubic_retorno_ids)
    if not ubic_ids:
        return qs.none()

    # Filtramos pasando por el FK hacia Activo
    filtro = {f"{fk_name}__id_ubicacion_id__in": list(ubic_ids)}
    return qs.filter(**filtro)

############################################## 09/12 #####################################
######################################## 10/12 ###########################################
def filtrar_ubicaciones_por_bodegas_permitidas(qs_ubicaciones, usuario_empleado):
    """
    Restringe un queryset de Ubicacion a las ubicaciones que el empleado
    logueado puede administrar según sus PermisoBodega.

    - Admin / Jefes → ven todas las ubicaciones.
    - Solo restringimos a rol USUARIO (bodegueros).
    """
    if not usuario_empleado:
        # Usuario sin empleado asociado → no restringimos
        return qs_ubicaciones

    rol_emp = (usuario_empleado.rol or "").strip().lower()
    if (ROL_USUARIO or "").strip().lower() != rol_emp:
        # Solo aplicamos filtro a los USUARIO; el resto ve todo
        return qs_ubicaciones

    # Import local para evitar ciclos
    from .models_inventario import PermisoBodega, Bodega

    # Permisos de bodega de este empleado
    permisos = PermisoBodega.objects.filter(id_empleado=usuario_empleado)
    try:
        # Si el modelo tiene campo eliminado, lo usamos, si no, no pasa nada
        permisos = permisos.filter(eliminado=False)
    except FieldError:
        pass

    bodega_ids = list(permisos.values_list("id_bodega_id", flat=True))
    if not bodega_ids:
        # No tiene bodegas asociadas → no puede asignar ubicaciones
        return qs_ubicaciones.none()

    bodegas_qs = Bodega.objects.filter(id_bodega__in=bodega_ids)
    try:
        bodegas_qs = bodegas_qs.filter(eliminado=False)
    except FieldError:
        pass

    ubicacion_ids = bodegas_qs.values_list("id_ubicacion_id", flat=True).distinct()
    if not ubicacion_ids:
        return qs_ubicaciones.none()

    # Ubicacion.pk es id_ubicacion, así que pk__in funciona perfecto
    return qs_ubicaciones.filter(pk__in=ubicacion_ids)
######################################## 10/12 ###########################################
