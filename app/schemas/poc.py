"""Esquemas de las rutas antiguas del PoC (/animales y /ordenos)."""
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


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
