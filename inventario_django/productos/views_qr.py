# productos/views_qr.py
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from productos.models_inventario import Equipo
from .utils import generar_qr
import qrcode
import base64
from io import BytesIO
from django.urls import reverse_lazy

@login_required
def qr_print_view(request, pk):
    from .models_inventario import Equipo
    obj = get_object_or_404(Equipo, pk=pk)

    # --- Depuración ---
    print("Etiqueta del equipo:", obj.etiqueta)  # <--- aquí
    # ------------------

    # Generar QR con solo el código de etiqueta
    qr_data = obj.etiqueta  # o obj.id, lo que quieras que se escanee
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # --- Depuración QR ---
    print("Largo del string base64 generado:", len(img_str))
    print("Primeros 100 caracteres:", img_str[:100])
    # ----------------------

    context = {
        "object": obj,
        "qr_img": img_str,
        "back_url": reverse_lazy("productos:equipos_list"),
    }
    return render(request, "equipos/qr_print.html", context)