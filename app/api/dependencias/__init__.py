"""Dependencias de FastAPI: sesión, CSRF/origen y autorización por rol (PB-11).
La autorización se aplica en el servidor en cada operación; ocultar botones no cuenta.

- verificacion_csrf.py: origen de la solicitud y token CSRF.
- autorizacion.py:      sesión requerida y control de acceso por rol.
- unidad_de_trabajo.py: construye la unidad de trabajo (persistencia) de cada petición.
"""
from .autorizacion import requiere, sesion_requerida
from .unidad_de_trabajo import get_uow
from .verificacion_csrf import verificar_csrf, verificar_origen, vinculo_actual

__all__ = ["get_uow", "requiere", "sesion_requerida", "verificar_csrf", "verificar_origen", "vinculo_actual"]
