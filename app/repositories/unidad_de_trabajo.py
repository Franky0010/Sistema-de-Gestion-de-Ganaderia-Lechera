"""Unidad de trabajo sobre una Session de SQLAlchemy."""
from sqlalchemy.orm import Session

from app.repositories.animales import RepositorioAnimalesSQL
from app.repositories.auditoria import RepositorioAuditoriaSQL
from app.repositories.estados import RepositorioEstadosSQL
from app.repositories.ordenos import RepositorioOrdenosSQL
from app.repositories.sesiones import RepositorioSesionesSQL
from app.repositories.traduccion_errores import traducir_errores
from app.repositories.usuarios import RepositorioUsuariosSQL
from app.services.puertos import UnidadDeTrabajo


class UnidadDeTrabajoSQL(UnidadDeTrabajo):
    """Envuelve una Session: todos los repositorios comparten la misma transacción."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self.usuarios = RepositorioUsuariosSQL(db)
        self.sesiones = RepositorioSesionesSQL(db)
        self.animales = RepositorioAnimalesSQL(db)
        self.estados = RepositorioEstadosSQL(db)
        self.ordenos = RepositorioOrdenosSQL(db)
        self.auditoria = RepositorioAuditoriaSQL(db)

    @traducir_errores
    def flush(self) -> None:
        self._db.flush()

    @traducir_errores
    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()

    @traducir_errores
    def refrescar(self, entidad: object) -> None:
        self._db.refresh(entidad)
