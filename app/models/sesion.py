"""Sesiones de acceso (solo se guarda el hash del token)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Sesion(Base):
    __tablename__ = "sesion"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    hash_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    creada_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ultimo_uso: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revocada_en: Mapped[Optional[datetime]] = mapped_column(DateTime)
