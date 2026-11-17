"""Modelo de datos mínimo de la PoC (subconjunto del ERD del documento de diseño).

Cada entidad vive en su propio módulo. Este paquete las reexporta para que
`from app.models import Animal, Base, ...` siga funcionando y para que `Base.metadata`
conozca todas las tablas.
"""
from .base import Base
from .usuario import Usuario
from .sesion import Sesion
from .animal import Animal
from .estado_animal import ESTADOS_ANIMAL, EstadoAnimal
from .ordeno import Ordeno
from .auditoria import Auditoria

__all__ = [
    "Base", "Usuario", "Sesion", "Animal", "ESTADOS_ANIMAL", "EstadoAnimal", "Ordeno", "Auditoria",
]
