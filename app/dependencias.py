"""Dependencias de FastAPI: sesión, CSRF/origen y autorización por rol (PB-11).
La autorización se aplica en el servidor en cada operación; ocultar botones no cuenta."""
import os
from urllib.parse import urlparse

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from . import seguridad, servicio_auth
from .db_deps import get_session
from .errores import ErrorApi
from .servicio_auth import ContextoSesion


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


def vinculo_actual(request: Request, db: Session):
    """(contexto de sesión o None, vínculo CSRF). Sin sesión, el vínculo es la cookie anónima."""
    ctx = servicio_auth.obtener_contexto(db, request.cookies.get(seguridad.COOKIE_SESION), tocar=False)
    if ctx is not None:
        return ctx, ctx.hash_token
    return None, request.cookies.get(seguridad.COOKIE_CSRF_ANONIMO)


def sesion_requerida(request: Request, db: Session = Depends(get_session)) -> ContextoSesion:
    ctx = servicio_auth.obtener_contexto(db, request.cookies.get(seguridad.COOKIE_SESION), tocar=True)
    if ctx is None:
        raise ErrorApi(401, "SESION_EXPIRADA", "Inicia sesión para continuar.")
    return ctx


def requiere(*roles: str, escritura: bool = False):
    """Orden: sesión válida (401) -> origen y CSRF si escribe (403) -> rol (403)."""
    def dependencia(request: Request, ctx: ContextoSesion = Depends(sesion_requerida)) -> ContextoSesion:
        if escritura:
            verificar_origen(request)
            verificar_csrf(request, ctx.hash_token)
        if ctx.usuario.rol not in roles:
            raise ErrorApi(403, "SIN_PERMISO", "No tienes permiso para realizar esta acción.")
        return ctx
    return dependencia
