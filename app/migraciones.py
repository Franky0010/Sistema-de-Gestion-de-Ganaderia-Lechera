"""Migración del esquema de SQLite (S1-PB-03-BE).

`Base.metadata.create_all` solo crea tablas que NO existen: nunca modifica una tabla vieja.
migrar() cubre ese hueco para `animal`: si la tabla existe pero no tiene todas las columnas o
restricciones del modelo actual, la reconstruye (receta oficial de SQLite: crear tabla nueva,
copiar filas, borrar la vieja y renombrar) conservando los datos y las referencias de `ordeno`.

- Es idempotente: sobre una base al día o sin tabla `animal` no hace nada.
- Se ejecuta sola al arrancar la API y en crear_admin; también a mano:
      python -m app.migraciones
- Las tablas nuevas (estado_animal) las crea create_all justo después.
"""
import sys

from sqlalchemy import inspect
from sqlalchemy.engine import Engine
from sqlalchemy.schema import CreateTable

from .models import Animal

# La restricción más reciente de `animal`: si no está en la tabla, hay que reconstruirla.
_MARCA = "ck_animal_arete_normalizado"


def _animal_al_dia(engine: Engine) -> bool:
    columnas = {c["name"] for c in inspect(engine).get_columns("animal")}
    if not {c.name for c in Animal.__table__.columns} <= columnas:
        return False
    with engine.connect() as con:
        sql = con.exec_driver_sql("SELECT sql FROM sqlite_master WHERE type='table' AND name='animal'").scalar()
    return _MARCA in (sql or "")


def migrar(engine: Engine) -> bool:
    """Devuelve True si reconstruyó la tabla `animal`."""
    if "animal" not in inspect(engine).get_table_names() or _animal_al_dia(engine):
        return False

    viejas = {c["name"] for c in inspect(engine).get_columns("animal")}
    comunes = ", ".join(c.name for c in Animal.__table__.columns if c.name in viejas)
    ddl = str(CreateTable(Animal.__table__).compile(dialect=engine.dialect))
    ddl = ddl.replace("CREATE TABLE animal (", "CREATE TABLE animal_nuevo (", 1)

    con = engine.raw_connection()
    try:
        con.execute("PRAGMA foreign_keys=OFF")  # debe ir fuera de la transacción
        con.execute("BEGIN")
        con.execute("DROP TABLE IF EXISTS animal_nuevo")
        con.execute(ddl)
        con.execute(f"INSERT INTO animal_nuevo ({comunes}) SELECT {comunes} FROM animal")
        con.execute("DROP TABLE animal")
        con.execute("ALTER TABLE animal_nuevo RENAME TO animal")
        if con.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("La migración dejaría referencias rotas; no se aplicó.")
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.execute("PRAGMA foreign_keys=ON")  # esta conexión vuelve al pool
        con.close()
    return True


if __name__ == "__main__":
    from .db_deps import engine

    print("Tabla animal migrada." if migrar(engine) else "La base ya estaba al día.")
    sys.exit(0)