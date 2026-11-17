"""Alta de animales de las rutas antiguas del PoC (POST /animales)."""
from app.core.excepciones import ErrorIntegridad
from app.models import Animal
from app.services.puertos import UnidadDeTrabajo


class AreteDuplicado(Exception):
    """Ya existe un animal con ese arete."""


def crear_animal_poc(uow: UnidadDeTrabajo, arete: str, nombre: str | None) -> Animal:
    """Inserta el animal y confirma; cualquier restricción violada se informa como arete duplicado."""
    animal = Animal(arete=arete, nombre=nombre)
    uow.animales.agregar(animal)
    try:
        uow.commit()
    except ErrorIntegridad as exc:
        uow.rollback()
        raise AreteDuplicado("el arete ya existe") from exc
    return animal
