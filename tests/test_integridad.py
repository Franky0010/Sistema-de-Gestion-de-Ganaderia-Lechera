"""HT-02: motivo obligatorio, auditoría inmutable y consultable, errores de BD y respaldo."""
import json
import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app import auditoria, respaldo
from app.database import crear_engine
from app.errores import instalar_manejadores
from app.models import Auditoria, Base, Usuario

from .conftest import cliente_con_sesion, escribir


def test_desactivar_sin_motivo_se_rechaza_y_no_escribe_nada(api):
    admin = cliente_con_sesion(api, "admin")
    antes = api.contar(Auditoria)
    for cuerpo in [{"activo": False}, {"activo": False, "motivo": "   "}]:
        r = escribir(admin, "PATCH", "/api/v1/usuarios/2", cuerpo)
        assert (r.status_code, r.json()["error"]["fields"]) == (422, {"motivo": "El motivo es obligatorio para este cambio."})
    assert api.contar(Auditoria) == antes
    assert api.filas(select(Usuario.activo).where(Usuario.id == 2)) == [(True,)]


def test_desactivar_y_reactivar_guardan_el_motivo(api):
    admin = cliente_con_sesion(api, "admin")
    assert escribir(admin, "PATCH", "/api/v1/usuarios/2", {"activo": False, "motivo": "Renunció"}).status_code == 200
    assert escribir(admin, "PATCH", "/api/v1/usuarios/2", {"activo": True, "motivo": "Regresó"}).status_code == 200
    filas = api.filas(select(Auditoria.accion, Auditoria.motivo).where(Auditoria.entidad_id == 2, Auditoria.motivo.is_not(None)))
    assert filas == [("desactivar", "Renunció"), ("reactivar", "Regresó")]


def test_cambiar_nombre_no_exige_motivo(api):
    admin = cliente_con_sesion(api, "admin")
    assert escribir(admin, "PATCH", "/api/v1/usuarios/2", {"nombre": "Otro Nombre"}).status_code == 200


def test_el_administrador_consulta_la_auditoria_con_filtros(api):
    admin = cliente_con_sesion(api, "admin")
    escribir(admin, "PATCH", "/api/v1/usuarios/2", {"activo": False, "motivo": "Prueba"})
    r = admin.get("/api/v1/auditoria?entidad=usuario&entidad_id=2&accion=desactivar").json()
    assert r["total"] == 1
    fila = r["items"][0]
    assert (fila["usuario"], fila["motivo"], fila["despues"]["activo"], fila["antes"]["activo"]) == ("admin@finca.co", "Prueba", False, True)
    assert fila["momento"].endswith("Z")
    assert "hash" not in json.dumps(r) and "scrypt" not in json.dumps(r)


def test_solo_el_administrador_consulta_y_nadie_puede_alterarla_por_la_api(api):
    operario = cliente_con_sesion(api, "operario")
    assert operario.get("/api/v1/auditoria").status_code == 403
    admin = cliente_con_sesion(api, "admin")
    for metodo in ("POST", "PUT", "PATCH", "DELETE"):
        assert escribir(admin, metodo, "/api/v1/auditoria/1", {}).status_code in (404, 405)
        assert escribir(admin, metodo, "/api/v1/auditoria", {}).status_code == 405


def test_la_bd_impide_update_y_delete_sobre_la_auditoria(tmp_path):
    engine = crear_engine(f"sqlite:///{tmp_path / 'a.db'}")
    Base.metadata.create_all(engine)
    auditoria.proteger_auditoria(engine)
    auditoria.proteger_auditoria(engine)  # idempotente
    with engine.begin() as con:
        con.execute(text("INSERT INTO auditoria (entidad, entidad_id, accion, usuario, momento) VALUES ('x', 1, 'crear', 'u', '2026-11-04')"))
    for sentencia in ("UPDATE auditoria SET usuario = 'otro'", "DELETE FROM auditoria"):
        with pytest.raises(DBAPIError):
            with engine.begin() as con:
                con.execute(text(sentencia))
    engine.dispose()


def test_la_auditoria_rechaza_secretos_y_exige_motivo():
    with pytest.raises(ValueError):
        auditoria.registrar(None, entidad="usuario", entidad_id=1, accion="crear", actor=None, despues={"password": "x"})
    with pytest.raises(ValueError):
        auditoria.registrar(None, entidad="usuario", entidad_id=1, accion="desactivar", actor=None, motivo=" ")


def test_clave_foranea_invalida_es_422_y_no_500(tmp_path):
    engine = crear_engine(f"sqlite:///{tmp_path / 'fk.db'}")
    Base.metadata.create_all(engine)
    mini = FastAPI()
    instalar_manejadores(mini)

    @mini.get("/falla")
    def falla():
        with engine.begin() as con:  # usuario_id 999 no existe
            con.execute(text("INSERT INTO auditoria (entidad, entidad_id, accion, usuario, momento, usuario_id) VALUES ('x', 1, 'crear', 'u', '2026-11-04', 999)"))

    r = TestClient(mini).get("/falla")
    assert (r.status_code, r.json()["error"]["code"]) == (422, "REFERENCIA_INVALIDA")
    engine.dispose()


def test_respaldo_y_restauracion(tmp_path):
    base = tmp_path / "poc.db"
    engine = crear_engine(f"sqlite:///{base}")
    Base.metadata.create_all(engine)
    with engine.begin() as con:
        con.execute(text("INSERT INTO animal (arete, nombre) VALUES ('A1', 'Luna')"))
    copia = respaldo.crear_respaldo(base, tmp_path / "respaldos")
    with engine.begin() as con:
        con.execute(text("DELETE FROM animal"))  # "desastre"
    engine.dispose()
    segundos = respaldo.restaurar(copia, base)
    assert segundos < 30 * 60
    con = sqlite3.connect(base)
    assert con.execute("SELECT arete FROM animal").fetchall() == [("A1",)]
    con.close()
    assert (tmp_path / "poc.db.previo").exists()


def test_respaldo_rota_los_antiguos(tmp_path):
    base = tmp_path / "poc.db"
    engine = crear_engine(f"sqlite:///{base}")
    Base.metadata.create_all(engine)
    carpeta = tmp_path / "r"
    carpeta.mkdir()
    for dia in range(1, 6):
        (carpeta / f"poc-2026010{dia}-000000.db").write_bytes(b"x")
    respaldo.crear_respaldo(base, carpeta, conservar=3)
    assert len(list(carpeta.glob("poc-*.db"))) == 3
    engine.dispose()