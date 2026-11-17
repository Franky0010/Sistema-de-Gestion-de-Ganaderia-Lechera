"""Fecha de negocio de la finca."""
from datetime import date, timedelta, timezone

from app.core import seguridad


_BOGOTA = timezone(timedelta(hours=-5))  # Colombia no usa horario de verano


def hoy() -> date:
    """Fecha de negocio (America/Bogota). Usa seguridad.ahora() para que las pruebas la muevan."""
    return seguridad.ahora().replace(tzinfo=timezone.utc).astimezone(_BOGOTA).date()
