"""/api/v1/animales (PB-03 y cambios de estado). Escribe solo el administrador; leen los tres roles."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, StrictInt
from sqlalchemy.orm import Session

from . import dependencias, servicio_animales
from .db_deps import get_session

router = APIRouter(prefix="/animales", tags=["animales"])

todos_los_roles = dependencias.requiere("administrador", "operario", "propietario")
solo_admin_escribe = dependencias.requiere("administrador", escritura=True)


class AnimalNuevo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    arete: str
    nombre: Optional[str] = None
    raza: str
    procedencia: str
    fecha_ingreso: date
    fecha_nacimiento: Optional[date] = None
    edad_estimada_meses: Optional[StrictInt] = None
    estado_inicial: str


class CambioEstado(BaseModel):
    model_config = ConfigDict(extra="forbid")
    estado: str
    fecha_desde: date
    motivo: str
    version: StrictInt


@router.post("", status_code=201)
def crear(datos: AnimalNuevo, ctx=Depends(solo_admin_escribe), db: Session = Depends(get_session)):
    animal = servicio_animales.crear_animal(db, ctx.usuario, datos.model_dump())
    return servicio_animales.animal_publico(db, animal)


@router.get("/{animal_id}")
def detalle(animal_id: int, _ctx=Depends(todos_los_roles), db: Session = Depends(get_session)):
    return servicio_animales.animal_publico(db, servicio_animales.obtener_animal(db, animal_id))


@router.post("/{animal_id}/estados", status_code=201)
def cambiar_estado(animal_id: int, datos: CambioEstado, ctx=Depends(solo_admin_escribe),
                   db: Session = Depends(get_session)):
    estado, animal = servicio_animales.cambiar_estado(
        db, ctx.usuario, animal_id, estado=datos.estado, fecha_desde=datos.fecha_desde,
        motivo=datos.motivo, version=datos.version)
    return {"estado": servicio_animales.estado_publico(estado),
            "animal": servicio_animales.animal_publico(db, animal)}