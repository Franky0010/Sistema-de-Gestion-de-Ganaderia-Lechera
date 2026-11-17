"""POST /ordenos del PoC."""
from fastapi import APIRouter, Depends, Header, HTTPException

from app.api import dependencias
from app.schemas.poc import OrdenoIn
from app.services import ordenos as service
from app.services.puertos import UnidadDeTrabajo

router = APIRouter()


@router.post("/ordenos", status_code=201)
def crear_ordeno(
    datos: OrdenoIn,
    x_usuario: str = Header(...),
    uow: UnidadDeTrabajo = Depends(dependencias.get_uow),
):
    try:
        o = service.registrar_ordeno(
            uow,
            animal_id=datos.animal_id,
            fecha=datos.fecha,
            turno=datos.turno,
            litros_producidos=datos.litros_producidos,
            litros_descartados=datos.litros_descartados,
            observaciones=datos.observaciones,
            usuario=x_usuario,
        )
    except service.ErrorDeValidacion as e:
        raise HTTPException(422, str(e))
    except service.AnimalNoExiste as e:
        raise HTTPException(404, str(e))
    except service.DuplicadoError as e:
        raise HTTPException(409, str(e))
    except service.BloqueoTransitorio as e:
        raise HTTPException(503, str(e))

    producido = o.centilitros_producidos / 100
    descartado = o.centilitros_descartados / 100
    return {
        "id": o.id,
        "animal_id": o.animal_id,
        "fecha": o.fecha.isoformat(),
        "turno": o.turno,
        "litros_producidos": producido,
        "litros_descartados": descartado,
        "litros_disponibles": round(producido - descartado, 2),
        "responsable": o.creado_por,
    }
