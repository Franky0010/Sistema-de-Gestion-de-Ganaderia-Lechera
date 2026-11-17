"""Animales del hato."""
from datetime import date
from typing import Optional

from sqlalchemy import CheckConstraint, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Animal(Base):
    __tablename__ = "animal"
    __table_args__ = (
        CheckConstraint("length(arete) > 0 AND arete = upper(trim(arete))",
                        name="ck_animal_arete_normalizado"),
        CheckConstraint("edad_estimada_meses IS NULL OR edad_estimada_meses >= 0",
                        name="ck_animal_edad_no_negativa"),
        # Nacimiento o edad estimada, nunca ambos (el servicio exige exactamente uno).
        CheckConstraint("NOT (fecha_nacimiento IS NOT NULL AND edad_estimada_meses IS NOT NULL)",
                        name="ck_animal_nacimiento_o_edad"),
        CheckConstraint("fecha_nacimiento IS NULL OR fecha_ingreso IS NULL OR fecha_nacimiento <= fecha_ingreso",
                        name="ck_animal_nacimiento_antes_ingreso"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Arete normalizado (sin espacios extremos, en mayúsculas). RN01 / RF02.
    arete: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[Optional[str]] = mapped_column(String(100))
    # Las columnas nuevas admiten NULL solo para no invalidar los animales del PoC;
    # el servicio (PB-03) las exige todas en el alta.
    raza: Mapped[Optional[str]] = mapped_column(String(80))
    procedencia: Mapped[Optional[str]] = mapped_column(String(160))
    fecha_ingreso: Mapped[Optional[date]] = mapped_column(Date)
    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(Date)
    edad_estimada_meses: Mapped[Optional[int]] = mapped_column(Integer)
    # Control de concurrencia optimista: sube en cada cambio de estado.
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
