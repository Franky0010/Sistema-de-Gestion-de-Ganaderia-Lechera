"""Persistencia de usuarios con SQLAlchemy."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Usuario
from app.repositories.traduccion_errores import traducir_errores
from app.services.puertos import RepositorioUsuarios


def _escapar_like(texto: str) -> str:
    """Escapa los comodines de LIKE para que el texto buscado se tome literal."""
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class RepositorioUsuariosSQL(RepositorioUsuarios):
    def __init__(self, db: Session) -> None:
        self._db = db

    @traducir_errores
    def obtener(self, usuario_id: int) -> Usuario | None:
        return self._db.get(Usuario, usuario_id)

    @traducir_errores
    def obtener_por_email(self, email: str) -> Usuario | None:
        return self._db.scalar(select(Usuario).where(Usuario.email == email))

    @traducir_errores
    def agregar(self, usuario: Usuario) -> None:
        self._db.add(usuario)

    @traducir_errores
    def buscar(self, texto: str, page: int, page_size: int):
        texto = texto.strip()
        filtro = None
        if texto:
            patron = f"%{_escapar_like(texto)}%"
            filtro = Usuario.nombre.ilike(patron, escape="\\") | Usuario.email.ilike(patron, escape="\\")
        consulta, conteo = select(Usuario), select(func.count(Usuario.id))
        if filtro is not None:  # filtrar antes de paginar: total e items deben coincidir
            consulta, conteo = consulta.where(filtro), conteo.where(filtro)
        items = self._db.scalars(consulta.order_by(Usuario.id).offset((page - 1) * page_size).limit(page_size)).all()
        return items, self._db.scalar(conteo)

    @traducir_errores
    def contar_administradores_activos(self) -> int:
        return self._db.scalar(select(func.count()).select_from(Usuario)
                               .where(Usuario.rol == "administrador", Usuario.activo.is_(True)))
