"""S1-PB-03-BE: migración de una base creada antes de ampliar la tabla `animal`."""
import sqlite3

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app import migraciones
from app.database import crear_engine
from app.models import Base

ESQUEMA_VIEJO = """
CREATE TABLE animal (id INTEGER NOT NULL PRIMARY KEY, arete VARCHAR(50) NOT NULL UNIQUE, nombre VARCHAR(100));
CREATE TABLE ordeno (id INTEGER NOT NULL PRIMARY KEY, animal_id INTEGER NOT NULL REFERENCES animal (id), fecha DATE);
INSERT INTO animal (id, arete, nombre) VALUES (1, 'V-001', 'Luna'), (2, 'V-002', NULL);
INSERT INTO ordeno (id, animal_id, fecha) VALUES (1, 1, '2026-01-01');
"""


@pytest.fixture
def base_vieja(tmp_path):
    ruta = tmp_path / "vieja.db"
    con = sqlite3.connect(ruta)
    con.executescript(ESQUEMA_VIEJO)
    con.close()
    engine = crear_engine(f"sqlite:///{ruta}")
    yield engine
    engine.dispose()


def test_migra_la_tabla_vieja_conservando_datos_y_referencias(base_vieja):
    assert migraciones.migrar(base_vieja) is True
    Base.metadata.create_all(base_vieja)  # crea estado_animal, como al arrancar
    columnas = {c["name"] for c in inspect(base_vieja).get_columns("animal")}
    assert {"raza", "procedencia", "fecha_ingreso", "fecha_nacimiento", "edad_estimada_meses", "version"} <= columnas
    with base_vieja.connect() as con:
        assert con.execute(text("SELECT id, arete, nombre, version, raza FROM animal ORDER BY id")).all() == [
            (1, "V-001", "Luna", 1, None), (2, "V-002", None, 1, None)]
        assert con.execute(text("SELECT count(*) FROM ordeno")).scalar() == 1
        assert con.exec_driver_sql("PRAGMA foreign_key_check").fetchall() == []
        assert con.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1  # la conexión quedó con FK activas


def test_despues_de_migrar_la_base_aplica_las_restricciones(base_vieja):
    migraciones.migrar(base_vieja)
    for sql in ["INSERT INTO animal (arete) VALUES ('v-003')",                       # minúsculas
                "INSERT INTO animal (arete) VALUES ('  V-004  ')",                    # espacios extremos
                "INSERT INTO animal (arete) VALUES ('')",                              # vacío
                "INSERT INTO animal (arete) VALUES ('V-001')",                         # reutilizado
                "INSERT INTO animal (arete, edad_estimada_meses) VALUES ('V-005', -1)",
                "INSERT INTO animal (arete, fecha_nacimiento, edad_estimada_meses) VALUES ('V-006', '2020-01-01', 5)",
                "INSERT INTO ordeno (animal_id, fecha) VALUES (99, '2026-01-01')"]:   # la FK de ordeno sigue viva
        with pytest.raises(IntegrityError):
            with base_vieja.begin() as con:
                con.execute(text(sql))


def test_es_idempotente_y_no_toca_una_base_nueva_o_sin_animal(base_vieja, tmp_path):
    assert migraciones.migrar(base_vieja) is True
    assert migraciones.migrar(base_vieja) is False
    nueva = crear_engine(f"sqlite:///{tmp_path / 'nueva.db'}")
    assert migraciones.migrar(nueva) is False  # sin tabla animal
    Base.metadata.create_all(nueva)
    assert migraciones.migrar(nueva) is False  # ya creada con el esquema actual
    nueva.dispose()


def test_repara_una_tabla_con_columnas_agregadas_a_mano_pero_sin_restricciones(base_vieja):
    with base_vieja.begin() as con:  # lo que haría un ALTER TABLE ADD COLUMN manual
        for sql in ("ALTER TABLE animal ADD COLUMN raza VARCHAR(80)", "ALTER TABLE animal ADD COLUMN procedencia VARCHAR(160)",
                    "ALTER TABLE animal ADD COLUMN fecha_ingreso DATE", "ALTER TABLE animal ADD COLUMN fecha_nacimiento DATE",
                    "ALTER TABLE animal ADD COLUMN edad_estimada_meses INTEGER",
                    "ALTER TABLE animal ADD COLUMN version INTEGER NOT NULL DEFAULT 1"):
            con.execute(text(sql))
    assert migraciones.migrar(base_vieja) is True
    with pytest.raises(IntegrityError):
        with base_vieja.begin() as con:
            con.execute(text("INSERT INTO animal (arete, edad_estimada_meses) VALUES ('V-009', -5)"))