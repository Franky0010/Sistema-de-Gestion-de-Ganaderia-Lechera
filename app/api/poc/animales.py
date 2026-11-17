"""POST /animales del PoC."""
from fastapi import APIRouter, Depends, HTTPException

from app.api import dependencias
from app.schemas.poc import AnimalIn
from app.services import animales_poc
from app.services.puertos import UnidadDeTrabajo

router = APIRouter()


@router.post("/animales", status_code=201)
def crear_animal(datos: AnimalIn, uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    arete = datos.arete  # normalizado y validado por AnimalIn
    try:
        animal = animales_poc.crear_animal_poc(uow, arete, datos.nombre)
    except animales_poc.AreteDuplicado as exc:
        raise HTTPException(409, str(exc))
    return {"id": animal.id, "arete": animal.arete}
