"""Historial de estados de cada animal."""
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, _ahora_utc


ESTADOS_ANIMAL = ("en_produccion", "seco", "no_productivo", "fuera_del_hato")


class EstadoAnimal(Base):
    """Historial de estados: nunca se borra ni se edita; el vigente es el último por fecha."""
    __tablename__ = "estado_animal"
    __table_args__ = (
        # Un cambio por animal y día, incluido el estado inicial.
        UniqueConstraint("animal_id", "fecha_desde", name="uq_estado_animal_dia"),
        CheckConstraint("estado IN ('en_produccion', 'seco', 'no_productivo', 'fuera_del_hato')",
                        name="ck_estado_valido"),
        CheckConstraint("length(trim(motivo)) > 0", name="ck_estado_motivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animal.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_desde: Mapped[date] = mapped_column(Date, nullable=False)
    motivo: Mapped[str] = mapped_column(String(500), nullable=False)
    responsable_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=_ahora_utc, nullable=False)
