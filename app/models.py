"""Modelo de datos mínimo de la PoC (subconjunto del ERD del documento de diseño)."""
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import (
    CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

ESTADOS_ANIMAL = ("en_produccion", "seco", "no_productivo", "fuera_del_hato")

class Base(DeclarativeBase):
    pass


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


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


class Sesion(Base):
    __tablename__ = "sesion"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    hash_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    creada_en: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ultimo_uso: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    revocada_en: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Animal(Base):
    __tablename__ = "animal"
    __table_args__ = (
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
