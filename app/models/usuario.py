"""Cuentas de usuario."""
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, _ahora_utc


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint("rol IN ('administrador', 'operario', 'propietario')", name="ck_usuario_rol"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    # Correo normalizado (trim + minúsculas); único también para cuentas inactivas.
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    hash_clave: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    activo: Mapped[bool] = mapped_column(default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=_ahora_utc, nullable=False)
    actualizado_en: Mapped[datetime] = mapped_column(DateTime, default=_ahora_utc, nullable=False)
