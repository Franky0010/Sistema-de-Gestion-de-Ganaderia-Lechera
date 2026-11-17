"""/api/v1/animales (PB-03 y cambios de estado). Escribe solo el administrador; leen los tres roles."""
from fastapi import APIRouter, Depends, Query

from app.api import dependencias
from app.schemas.animales import AnimalNuevo, CambioEstado
from app.services import animales as servicio_animales
from app.services.puertos import UnidadDeTrabajo


router = APIRouter(prefix="/animales", tags=["animales"])
todos_los_roles = dependencias.requiere("administrador", "operario", "propietario")
solo_admin_escribe = dependencias.requiere("administrador", escritura=True)


@router.post("", status_code=201)
def crear(datos: AnimalNuevo, ctx=Depends(solo_admin_escribe), uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    animal = servicio_animales.crear_animal(uow, ctx.usuario, datos.model_dump())
    return servicio_animales.animal_publico(uow.estados, animal)


@router.get("/{animal_id}")
def detalle(animal_id: int, _ctx=Depends(todos_los_roles), uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    return servicio_animales.animal_publico(uow.estados, servicio_animales.obtener_animal(uow.animales, animal_id))


@router.get("/{animal_id}/estados")
def historial(animal_id: int, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
              _ctx=Depends(todos_los_roles), uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    animal = servicio_animales.obtener_animal(uow.animales, animal_id)
    return servicio_animales.listar_estados(uow.estados, animal, page=page, page_size=page_size)


@router.post("/{animal_id}/estados", status_code=201)
def cambiar_estado(animal_id: int, datos: CambioEstado, ctx=Depends(solo_admin_escribe),
                   uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    estado, animal = servicio_animales.cambiar_estado(
        uow, ctx.usuario, animal_id, estado=datos.estado, fecha_desde=datos.fecha_desde,
        motivo=datos.motivo, version=datos.version)
    return {"estado": servicio_animales.estado_publico(estado),
            "animal": servicio_animales.animal_publico(uow.estados, animal)}
