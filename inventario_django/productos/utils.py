import qrcode
from io import BytesIO
from django.core.files import File

def generar_qr(equipo):
    data = f"Equipo: {equipo.nombre_equipo}, Etiqueta: {equipo.etiqueta}"
    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    filename = f"qr_equipo_{equipo.id_equipo}.png"
    equipo.qr_code.save(filename, File(buffer), save=True)
