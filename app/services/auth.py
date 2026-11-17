"""Lógica de sesiones: abrir, validar (con expiración por inactividad) y revocar."""
from dataclasses import dataclass

from app.core import seguridad
from app.models import Sesion, Usuario
from app.services.puertos import RepositorioUsuarios, UnidadDeTrabajo


@dataclass
class ContextoSesion:
    usuario: Usuario
    sesion: Sesion
    hash_token: str  # vínculo del token CSRF


def autenticar_credenciales(usuarios: RepositorioUsuarios, email: str, password: str) -> Usuario | None:
    """Devuelve el usuario si la contraseña es correcta (esté activo o no); si no, None.
    Con correo inexistente verifica contra un hash ficticio para igualar tiempos."""
    usuario = usuarios.obtener_por_email(email)
    if usuario is None:
        seguridad.verificar_contra_ficticio(password)
        return None
    return usuario if seguridad.verificar_password(password, usuario.hash_clave) else None


def abrir_sesion(uow: UnidadDeTrabajo, usuario: Usuario, reemplaza: ContextoSesion | None = None) -> str:
    """Crea una sesión nueva (ID rotado) y revoca la anterior si el navegador ya tenía una."""
    instante = seguridad.ahora()
    if reemplaza is not None:
        reemplaza.sesion.revocada_en = instante
    token = seguridad.generar_token()
    uow.sesiones.agregar(Sesion(usuario_id=usuario.id, hash_token=seguridad.hash_token(token),
                                creada_en=instante, ultimo_uso=instante))
    uow.commit()
    return token


def obtener_contexto(uow: UnidadDeTrabajo, token: str | None, *, tocar: bool) -> ContextoSesion | None:
    """Sesión vigente o None. Revoca la sesión si venció o si la cuenta se desactivó.
    Con tocar=True cuenta como actividad (renueva el último uso)."""
    if not token:
        return None
    hash_ = seguridad.hash_token(token)
    fila = uow.sesiones.obtener_con_usuario(hash_)
    if fila is None:
        return None
    sesion, usuario = fila
    if sesion.revocada_en is not None:
        return None
    instante = seguridad.ahora()
    if not usuario.activo or instante - sesion.ultimo_uso > seguridad.TIMEOUT_INACTIVIDAD:
        sesion.revocada_en = instante
        uow.commit()
        return None
    if tocar and instante - sesion.ultimo_uso >= seguridad.REFRESCO_ULTIMO_USO:
        sesion.ultimo_uso = instante
        uow.commit()
    return ContextoSesion(usuario=usuario, sesion=sesion, hash_token=hash_)


def revocar(uow: UnidadDeTrabajo, sesion: Sesion) -> None:
    sesion.revocada_en = seguridad.ahora()
    uow.commit()
