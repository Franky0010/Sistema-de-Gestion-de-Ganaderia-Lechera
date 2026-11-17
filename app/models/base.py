"""Base declarativa y utilidades compartidas por todos los modelos."""
from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)
