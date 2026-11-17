"""Lecturas de animales y de su historial de estados."""
from app.core.excepciones import ErrorApi
from app.models import Animal
from app.services.animales.fechas import hoy
from app.services.animales.serializadores import _iso, estado_publico
from app.services.puertos import RepositorioAnimales, RepositorioEstados


def animal_publico(estados: RepositorioEstados, a: Animal) -> dict:
    actual = estados.vigente_en(a.id, hoy())
    return {
        "id": a.id, "arete": a.arete, "nombre": a.nombre, "raza": a.raza, "procedencia": a.procedencia,
        "fecha_ingreso": _iso(a.fecha_ingreso), "fecha_nacimiento": _iso(a.fecha_nacimiento),
        "edad_estimada_meses": a.edad_estimada_meses,
        "estado_actual": actual.estado if actual else None,
        "estado_desde": _iso(actual.fecha_desde) if actual else None,
        "version": a.version,
    }


def listar_estados(estados: RepositorioEstados, animal: Animal, *, page: int = 1, page_size: int = 20) -> dict:
    """Historial en orden cronológico (fecha efectiva, luego id). Nunca se edita ni se borra."""
    filas, total = estados.listar(animal.id, page, page_size)
    return {"items": [estado_publico(e) for e in filas], "total": total, "page": page, "page_size": page_size}


def obtener_animal(animales: RepositorioAnimales, animal_id: int) -> Animal:
    animal = animales.obtener(animal_id)
    if animal is None:
        raise ErrorApi(404, "NO_ENCONTRADO", "El animal no existe.")
    return animal
