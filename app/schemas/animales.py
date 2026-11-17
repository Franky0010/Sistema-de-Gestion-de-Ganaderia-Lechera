"""Esquemas de /api/v1/animales."""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, StrictInt


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
