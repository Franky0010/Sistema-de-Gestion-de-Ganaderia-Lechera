"""Lecturas de cuentas de usuario."""
from app.core.excepciones import ErrorApi
from app.models import Usuario
from app.services.puertos import RepositorioUsuarios


def obtener_usuario(usuarios: RepositorioUsuarios, usuario_id: int) -> Usuario:
    """Usuario por id; responde 404 si no existe."""
    usuario = usuarios.obtener(usuario_id)
    if usuario is None:
        raise ErrorApi(404, "NO_ENCONTRADO", "El usuario no existe.")
    return usuario


def listar_usuarios(usuarios: RepositorioUsuarios, search: str, page: int, page_size: int) -> dict:
    items, total = usuarios.buscar(search, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}
