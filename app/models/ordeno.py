"""Ordeños (producción y descarte por animal, fecha y turno)."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, _ahora_utc


class Ordeno(Base):
    __tablename__ = "ordeno"
    __table_args__ = (
        # RF05: un solo ordeño por animal, fecha y turno (incluye anulados).
        UniqueConstraint("animal_id", "fecha", "turno", name="uq_ordeno_animal_fecha_turno"),
        CheckConstraint("turno IN ('mañana', 'tarde')", name="ck_turno"),
        CheckConstraint("centilitros_producidos >= 0", name="ck_produccion_no_negativa"),
        CheckConstraint("centilitros_descartados >= 0", name="ck_descarte_no_negativo"),
        CheckConstraint(
            "centilitros_descartados <= centilitros_producidos", name="ck_descarte_le_produccion"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animal.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    turno: Mapped[str] = mapped_column(String(10), nullable=False)
    # Los litros se guardan como centilitros enteros: 12,50 L -> 1250 cL (RF06).
    centilitros_producidos: Mapped[int] = mapped_column(Integer, nullable=False)
    centilitros_descartados: Mapped[int] = mapped_column(Integer, nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    anulado: Mapped[bool] = mapped_column(default=False, nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    creado_por: Mapped[str] = mapped_column(String(100), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=_ahora_utc, nullable=False)
