# utils.py
from io import BytesIO
import qrcode
from django.core.files import File
# en productos/urls.py (o mejor en un utils.py), añade:
from django.db import connection


def generar_qr(obj):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(obj.etiqueta)  # usar la etiqueta como contenido del QR
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar en un buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    filename = f"qr_{obj.pk}.png"

    # Guardar la imagen en el campo qr_code
    obj.qr_code.save(filename, File(buffer), save=False)

def log_mantencion_event(user, m, accion: str, detalle: str = ""):
    username = getattr(user, "username", None) or None
    # valores “congelados”
    etiqueta = getattr(getattr(m, "id_equipo", None), "etiqueta", None)
    equipo_nombre = getattr(getattr(m, "id_equipo", None), "nombre_equipo", None)

    # intenta leer strings de tipo/prioridad/estado si tus FKs existen;
    # si tus modelos tienen otros nombres de campo, ajusta aquí.
    tipo_txt = getattr(getattr(m, "id_tipo_mantencion", None), "tipo", None)
    prioridad_txt = getattr(getattr(m, "id_prioridad", None), "tipo", None)
    estado_txt = getattr(getattr(m, "id_estado_mantencion", None), "tipo", None)

    # responsables (si los tienes en la tabla)
    def nombre_emp(emp):
        if not emp:
            return None
        partes = [emp.nombre, emp.apellido_paterno, emp.apellido_materno or ""]
        return " ".join(p for p in partes if p)

    responsable_txt = nombre_emp(getattr(m, "id_empleado_responsable", None))
    solicitante_txt = nombre_emp(getattr(m, "id_empleado_solicitante", None))

    with connection.cursor() as c:
        c.execute("""
            INSERT INTO inventario.historial_mantenciones_log
            (id_mantencion, accion, detalle, usuario_app_username,
             id_equipo, etiqueta, equipo_nombre,
             tipo_mantencion, prioridad, estado_actual,
             responsable_nombre, solicitante_nombre, descripcion)
            VALUES (%s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s)
        """, [
            m.id_mantencion, accion, detalle, username,
            getattr(getattr(m, "id_equipo", None), "id_equipo", None),
            etiqueta, equipo_nombre,
            tipo_txt, prioridad_txt, estado_txt,
            responsable_txt, solicitante_txt,
            getattr(m, "descripcion", None),
        ])