"""Persistencia de animales con SQLAlchemy."""
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Animal
from app.repositories.traduccion_errores import traducir_errores
from app.services.puertos import RepositorioAnimales


class RepositorioAnimalesSQL(RepositorioAnimales):
    def __init__(self, db: Session) -> None:
        self._db = db

    @traducir_errores
    def obtener(self, animal_id: int) -> Animal | None:
        return self._db.get(Animal, animal_id)

    @traducir_errores
    def agregar(self, animal: Animal) -> None:
        self._db.add(animal)

    @traducir_errores
    def incrementar_version(self, animal_id: int, version_esperada: int) -> bool:
        # Compara y actualiza en UNA sentencia: si dos peticiones llegan con la misma versión,
        # solo una ve rowcount == 1.
        resultado = self._db.execute(
            update(Animal).where(Animal.id == animal_id, Animal.version == version_esperada)
            .values(version=Animal.version + 1).execution_options(synchronize_session=False)
        )
        return resultado.rowcount == 1
