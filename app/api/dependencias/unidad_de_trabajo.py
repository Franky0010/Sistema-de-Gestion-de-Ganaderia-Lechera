"""Raíz de composición: aquí (y solo aquí) se elige la implementación concreta de persistencia."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories import UnidadDeTrabajoSQL
from app.services.puertos import UnidadDeTrabajo


def get_uow(db: Session = Depends(get_session)) -> UnidadDeTrabajo:
    """Unidad de trabajo de la petición, sobre la misma sesión de BD que get_session.

    FastAPI cachea la dependencia por petición: la sesión, la cadena de autorización y el
    endpoint reciben la MISMA unidad de trabajo."""
    return UnidadDeTrabajoSQL(db)
