"""Fixtures del Sprint 1: BD temporal con un usuario por rol, reloj controlable y cliente HTTPS."""
from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app import seguridad, servicio_usuarios
from app.database import crear_engine, crear_session_factory
from app.main import app, get_session
from app.models import Auditoria, Base, Sesion, Usuario

CLAVE = "clave-segura-1"
USUARIOS = {
    "admin": ("Ana Admin", "admin@finca.co", "administrador"),
    "operario": ("Oscar Operario", "operario@finca.co", "operario"),
    "propietario": ("Paula Propietaria", "propietario@finca.co", "propietario"),
}


class Reloj:
    def __init__(self):
        self.actual = seguridad.ahora()

    def ahora(self):
        return self.actual

    def avanzar(self, **kwargs):
        self.actual += timedelta(**kwargs)


@pytest.fixture
def api(tmp_path, monkeypatch):
    engine = crear_engine(f"sqlite:///{tmp_path / 'sprint1.db'}")
    Base.metadata.create_all(engine)
    SessionLocal = crear_session_factory(engine)
    with SessionLocal() as db:
        for nombre, email, rol in USUARIOS.values():
            servicio_usuarios.crear_usuario(db, None, nombre=nombre, email=email, password=CLAVE, rol=rol)

    def _get_session():
        with SessionLocal() as db:
            yield db

    app.dependency_overrides[get_session] = _get_session
    reloj = Reloj()
    monkeypatch.setattr(seguridad, "ahora", reloj.ahora)
    seguridad.limitador_login.reiniciar()

    def contar(modelo, *condiciones):
        with SessionLocal() as db:
            return db.scalar(select(func.count()).select_from(modelo).where(*condiciones))

    def consultar(consulta):
        with SessionLocal() as db:
            return db.scalars(consulta).all()

    def filas(consulta):  # varias columnas -> lista de tuplas
        with SessionLocal() as db:
            return [tuple(fila) for fila in db.execute(consulta).all()]

    yield SimpleNamespace(
        reloj=reloj, contar=contar, consultar=consultar, filas=filas,
        nuevo_cliente=lambda: TestClient(app, base_url="https://testserver"),
    )
    app.dependency_overrides.clear()
    seguridad.limitador_login.reiniciar()
    engine.dispose()


def pedir_csrf(cliente):
    return cliente.get("/api/v1/auth/csrf").json()["csrf_token"]


def iniciar_sesion(cliente, email, password=CLAVE):
    return cliente.post("/api/v1/auth/login", json={"email": email, "password": password},
                        headers={"X-CSRF-Token": pedir_csrf(cliente)})


def escribir(cliente, metodo, ruta, json=None):
    return cliente.request(metodo, ruta, json=json, headers={"X-CSRF-Token": pedir_csrf(cliente)})


def cliente_con_sesion(api, rol):
    cliente = api.nuevo_cliente()
    r = iniciar_sesion(cliente, USUARIOS[rol][1])
    assert r.status_code == 200, r.text
    return cliente
