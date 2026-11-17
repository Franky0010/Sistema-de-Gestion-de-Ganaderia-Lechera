"""Reloj de la aplicación."""
from datetime import datetime, timezone


def ahora() -> datetime:
    """Instante actual en UTC, sin zona (SQLite guarda fechas sin zona).
    Siempre llamarla como seguridad.ahora() para que las pruebas puedan moverla."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
