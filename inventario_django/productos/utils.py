# utils.py
from io import BytesIO
import qrcode
from django.core.files import File

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
