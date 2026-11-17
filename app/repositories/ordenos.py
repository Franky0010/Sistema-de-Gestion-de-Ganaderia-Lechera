"""Persistencia de ordeños con SQLAlchemy."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ordeno
from app.repositories.traduccion_errores import traducir_errores
from app.services.puertos import RepositorioOrdenos


class RepositorioOrdenosSQL(RepositorioOrdenos):
    def __init__(self, db: Session) -> None:
        self._db = db

    @traducir_errores
    def agregar(self, ordeno: Ordeno) -> None:
        self._db.add(ordeno)

    @traducir_errores
    def hay_vigentes(self, animal_id: int, desde: date, hasta: date | None = None) -> bool:
        consulta = select(Ordeno.id).where(Ordeno.animal_id == animal_id, Ordeno.anulado.is_(False),
                                           Ordeno.fecha >= desde)
        if hasta is not None:
            consulta = consulta.where(Ordeno.fecha < hasta)
        return bool(self._db.scalar(consulta.limit(1)))
