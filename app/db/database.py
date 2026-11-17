"""Configuración de SQLite con SQLAlchemy.

Los PRAGMA se aplican en cada conexión nueva:
- foreign_keys=ON: SQLite no valida claves foráneas por defecto.
- journal_mode=WAL: permite lecturas mientras otra conexión escribe.
- busy_timeout: espera acotada ante un bloqueo transitorio (en vez de fallar al instante).
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


def crear_engine(url: str = "sqlite:///poc.db"):
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False, "timeout": 5},
    )

    @event.listens_for(engine, "connect")
    def _configurar_sqlite(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    return engine


def crear_session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)
