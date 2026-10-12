"""API mínima de la PoC. No incluye autenticación real: el responsable llega en la
cabecera X-Usuario como sustituto de la sesión (queda fuera de lo que valida la PoC)."""
import os
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import service
from .database import crear_engine, crear_session_factory
from .models import Animal, Base

engine = crear_engine(os.getenv("POC_DATABASE_URL", "sqlite:///poc.db"))
SessionLocal = crear_session_factory(engine)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="PoC - Registro de ordeños sin duplicados", lifespan=lifespan)


def get_session():
    with SessionLocal() as session:
        yield session


class AnimalIn(BaseModel):
    arete: str = Field(min_length=1)
    nombre: Optional[str] = None


class OrdenoIn(BaseModel):
    animal_id: int
    fecha: date
    turno: Literal["mañana", "tarde"]
    litros_producidos: Decimal = Field(allow_inf_nan=False)
    litros_descartados: Decimal = Field(allow_inf_nan=False)
    observaciones: Optional[str] = None


@app.post("/animales", status_code=201)
def crear_animal(datos: AnimalIn, session: Session = Depends(get_session)):
    arete = datos.arete.strip().upper()  # normalización de RF02
    animal = Animal(arete=arete, nombre=datos.nombre)
    session.add(animal)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "el arete ya existe")
    return {"id": animal.id, "arete": animal.arete}


@app.post("/ordenos", status_code=201)
def crear_ordeno(
    datos: OrdenoIn,
    x_usuario: str = Header(...),
    session: Session = Depends(get_session),
):
    try:
        o = service.registrar_ordeno(
            session,
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
