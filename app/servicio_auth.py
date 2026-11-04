"""Lógica de sesiones: abrir, validar (con expiración por inactividad) y revocar."""
import os
from dataclasses import dataclass

from fastapi import Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import seguridad
from .models import Sesion, Usuario


@dataclass
class ContextoSesion:
    usuario: Usuario
    sesion: Sesion
    hash_token: str  # vínculo del token CSRF


def cookie_segura(request: Request) -> bool:
    """Secure en HTTPS. Detrás de un proxy, arrancar uvicorn con --proxy-headers o
    definir POC_COOKIE_SECURE=1."""
    return request.url.scheme == "https" or os.getenv("POC_COOKIE_SECURE", "").lower() in {"1", "true"}


def poner_cookie(response: Response, request: Request, nombre: str, valor: str) -> None:
    response.set_cookie(nombre, valor, httponly=True, secure=cookie_segura(request), samesite="lax", path="/")


def borrar_cookie(response: Response, request: Request, nombre: str) -> None:
    response.delete_cookie(nombre, path="/", httponly=True, secure=cookie_segura(request), samesite="lax")


def autenticar_credenciales(db: Session, email: str, password: str) -> Usuario | None:
    """Devuelve el usuario si la contraseña es correcta (esté activo o no); si no, None.
    Con correo inexistente verifica contra un hash ficticio para igualar tiempos."""
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    if usuario is None:
        seguridad.verificar_contra_ficticio(password)
        return None
    return usuario if seguridad.verificar_password(password, usuario.hash_clave) else None


def abrir_sesion(db: Session, usuario: Usuario, reemplaza: ContextoSesion | None = None) -> str:
    """Crea una sesión nueva (ID rotado) y revoca la anterior si el navegador ya tenía una."""
    instante = seguridad.ahora()
    if reemplaza is not None:
        reemplaza.sesion.revocada_en = instante
    token = seguridad.generar_token()
    db.add(Sesion(usuario_id=usuario.id, hash_token=seguridad.hash_token(token),
                  creada_en=instante, ultimo_uso=instante))
    db.commit()
    return token


def obtener_contexto(db: Session, token: str | None, *, tocar: bool) -> ContextoSesion | None:
    """Sesión vigente o None. Revoca la sesión si venció o si la cuenta se desactivó.
    Con tocar=True cuenta como actividad (renueva el último uso)."""
    if not token:
        return None
    hash_ = seguridad.hash_token(token)
    fila = db.execute(
        select(Sesion, Usuario).join(Usuario, Usuario.id == Sesion.usuario_id).where(Sesion.hash_token == hash_)
    ).first()
    if fila is None:
        return None
    sesion, usuario = fila
    if sesion.revocada_en is not None:
        return None
    instante = seguridad.ahora()
    if not usuario.activo or instante - sesion.ultimo_uso > seguridad.TIMEOUT_INACTIVIDAD:
        sesion.revocada_en = instante
        db.commit()
        return None
    if tocar and instante - sesion.ultimo_uso >= seguridad.REFRESCO_ULTIMO_USO:
        sesion.ultimo_uso = instante
        db.commit()
    return ContextoSesion(usuario=usuario, sesion=sesion, hash_token=hash_)


def revocar(db: Session, sesion: Sesion) -> None:
    sesion.revocada_en = seguridad.ahora()
    db.commit()
