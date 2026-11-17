"""Sesión requerida y autorización por rol."""
from fastapi import Depends, Request

from app.api.dependencias.unidad_de_trabajo import get_uow
from app.api.dependencias.verificacion_csrf import verificar_csrf, verificar_origen
from app.core import seguridad
from app.core.excepciones import ErrorApi
from app.services import auth as servicio_auth
from app.services.auth import ContextoSesion
from app.services.puertos import UnidadDeTrabajo


def sesion_requerida(request: Request, uow: UnidadDeTrabajo = Depends(get_uow)) -> ContextoSesion:
    ctx = servicio_auth.obtener_contexto(uow, request.cookies.get(seguridad.COOKIE_SESION), tocar=True)
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
