"""Verificación del origen de la solicitud y del token CSRF."""
import os
from urllib.parse import urlparse

from fastapi import Request

from app.core import seguridad
from app.core.excepciones import ErrorApi
from app.services import auth as servicio_auth
from app.services.puertos import UnidadDeTrabajo


def verificar_origen(request: Request) -> None:
    """Si el navegador envía Origin, debe ser el propio sitio o uno permitido por
    POC_ORIGENES_PERMITIDOS (lista separada por comas)."""
    origen = request.headers.get("origin")
    if not origen:
        return
    permitidos = {o.strip().rstrip("/") for o in os.getenv("POC_ORIGENES_PERMITIDOS", "").split(",") if o.strip()}
    if origen.rstrip("/") in permitidos:
        return
    netloc = urlparse(origen).netloc
    if netloc and netloc == request.headers.get("host", ""):
        return
    raise ErrorApi(403, "CSRF_INVALIDO", "Origen de la solicitud no permitido.")


def verificar_csrf(request: Request, vinculo: str | None) -> None:
    if not seguridad.validar_csrf(request.headers.get("x-csrf-token"), vinculo):
        raise ErrorApi(403, "CSRF_INVALIDO", "La solicitud no pudo verificarse. Recarga e intenta de nuevo.")


def vinculo_actual(request: Request, uow: UnidadDeTrabajo):
    """(contexto de sesión o None, vínculo CSRF). Sin sesión, el vínculo es la cookie anónima."""
    ctx = servicio_auth.obtener_contexto(uow, request.cookies.get(seguridad.COOKIE_SESION), tocar=False)
    if ctx is not None:
        return ctx, ctx.hash_token
    return None, request.cookies.get(seguridad.COOKIE_CSRF_ANONIMO)
