"""Persistencia del historial de estados de los animales con SQLAlchemy."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import EstadoAnimal
from app.repositories.traduccion_errores import traducir_errores
from app.services.puertos import RepositorioEstados


class RepositorioEstadosSQL(RepositorioEstados):
    def __init__(self, db: Session) -> None:
        self._db = db

    @traducir_errores
    def agregar(self, estado: EstadoAnimal) -> None:
        self._db.add(estado)

    @traducir_errores
    def vigente_en(self, animal_id: int, fecha: date) -> EstadoAnimal | None:
        return self._db.scalars(
            select(EstadoAnimal)
            .where(EstadoAnimal.animal_id == animal_id, EstadoAnimal.fecha_desde <= fecha)
            .order_by(EstadoAnimal.fecha_desde.desc(), EstadoAnimal.id.desc()).limit(1)
        ).first()

    @traducir_errores
    def siguiente_a(self, animal_id: int, fecha: date) -> EstadoAnimal | None:
        return self._db.scalars(
            select(EstadoAnimal)
            .where(EstadoAnimal.animal_id == animal_id, EstadoAnimal.fecha_desde > fecha)
            .order_by(EstadoAnimal.fecha_desde, EstadoAnimal.id).limit(1)
        ).first()

    @traducir_errores
    def listar(self, animal_id: int, page: int, page_size: int):
        donde = EstadoAnimal.animal_id == animal_id
        total = self._db.scalar(select(func.count()).select_from(EstadoAnimal).where(donde))
        filas = self._db.scalars(
            select(EstadoAnimal).where(donde)
            .order_by(EstadoAnimal.fecha_desde, EstadoAnimal.id)
            .offset((page - 1) * page_size).limit(page_size)
        ).all()
        return filas, total

    @traducir_errores
    def tiene_estado(self, animal_id: int, estado: str) -> bool:
        return bool(self._db.scalar(
            select(func.count()).select_from(EstadoAnimal)
            .where(EstadoAnimal.animal_id == animal_id, EstadoAnimal.estado == estado)
        ))

    @traducir_errores
    def existe_cambio_en(self, animal_id: int, fecha: date) -> bool:
        return bool(self._db.scalar(
            select(EstadoAnimal.id).where(EstadoAnimal.animal_id == animal_id,
                                          EstadoAnimal.fecha_desde == fecha)
        ))
