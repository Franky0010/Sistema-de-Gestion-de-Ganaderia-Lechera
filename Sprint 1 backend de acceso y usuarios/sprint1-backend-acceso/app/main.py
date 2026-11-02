"""API: rutas versionadas /api/v1 (sesión y usuarios, Sprint 1) y las rutas del PoC
(/animales, /ordenos), que siguen usando X-Usuario como sustituto de la sesión hasta el Sprint 2."""
from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import rutas_auth, rutas_usuarios, service
from .db_deps import SessionLocal, engine, get_session  # noqa: F401  (get_session se reexporta)
from .errores import instalar_manejadores
from .models import Animal, Base


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="PoC - Registro de ordeños sin duplicados", lifespan=lifespan)
instalar_manejadores(app)
app.include_router(rutas_auth.router, prefix="/api/v1")
app.include_router(rutas_usuarios.router, prefix="/api/v1")


class AnimalIn(BaseModel):
    arete: str = Field(min_length=1)
    nombre: Optional[str] = None

    @field_validator("arete")
    @classmethod
    def normalizar_arete(cls, valor: str) -> str:
        valor = valor.strip().upper()
        if not valor:
            raise ValueError("el arete no puede estar vacío")
        return valor


class OrdenoIn(BaseModel):
    animal_id: int
    fecha: date
    turno: Literal["mañana", "tarde"]
    litros_producidos: Decimal = Field(allow_inf_nan=False)
    litros_descartados: Decimal = Field(allow_inf_nan=False)
    observaciones: Optional[str] = None


@app.post("/animales", status_code=201)
def crear_animal(datos: AnimalIn, session: Session = Depends(get_session)):
    arete = datos.arete  # normalizado y validado por AnimalIn
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
