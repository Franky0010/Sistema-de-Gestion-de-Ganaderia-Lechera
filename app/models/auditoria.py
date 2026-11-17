"""Registro de auditoría."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, _ahora_utc


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    entidad: Mapped[str] = mapped_column(String(50), nullable=False)
    entidad_id: Mapped[int] = mapped_column(Integer, nullable=False)
    accion: Mapped[str] = mapped_column(String(30), nullable=False)
    usuario: Mapped[str] = mapped_column(String(100), nullable=False)
    momento: Mapped[datetime] = mapped_column(DateTime, default=_ahora_utc, nullable=False)
    despues: Mapped[Optional[str]] = mapped_column(Text)  # JSON con los valores nuevos
    antes: Mapped[Optional[str]] = mapped_column(Text)  # JSON con los valores anteriores
    motivo: Mapped[Optional[str]] = mapped_column(Text)
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuario.id"))
