"""Engine, fábrica de sesiones y dependencia get_session compartidos por las rutas."""
import os

from .database import crear_engine, crear_session_factory

engine = crear_engine(os.getenv("POC_DATABASE_URL", "sqlite:///poc.db"))
SessionLocal = crear_session_factory(engine)


def get_session():
    with SessionLocal() as session:
        yield session
