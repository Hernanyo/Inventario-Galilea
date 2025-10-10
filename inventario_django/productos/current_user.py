# productos/current_user.py
import threading
_local = threading.local()

def set_current_user(user):
    """
    Establece el usuario actual en el contexto del hilo.

    Asocia un objeto `user` al hilo actual utilizando almacenamiento local del hilo (`threading.local`).

    """
    _local.user = user

def get_current_user():
    """
    Obtiene el usuario actual del contexto del hilo.

    Recupera el usuario asociado al hilo actual desde el almacenamiento local del hilo (`threading.local`).
    """
    return getattr(_local, "user", None)
