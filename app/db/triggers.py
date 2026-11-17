"""Triggers de SQLite que garantizan la inmutabilidad de la auditoría y del historial.

Ambas funciones son idempotentes: se pueden llamar en cada arranque, también sobre una BD
ya existente. Se invocan después de create_all, porque las tablas deben existir.
"""
from sqlalchemy.engine import Engine


_TRIGGERS = (
    """CREATE TRIGGER IF NOT EXISTS auditoria_sin_update BEFORE UPDATE ON auditoria
       BEGIN SELECT RAISE(ABORT, 'La auditoría no se puede modificar'); END""",
    """CREATE TRIGGER IF NOT EXISTS auditoria_sin_delete BEFORE DELETE ON auditoria
       BEGIN SELECT RAISE(ABORT, 'La auditoría no se puede borrar'); END""",
)


def proteger_auditoria(engine: Engine) -> None:
    """Idempotente: se puede llamar en cada arranque, también sobre una BD ya existente."""
    with engine.begin() as conexion:
        for sentencia in _TRIGGERS:
            conexion.exec_driver_sql(sentencia)


_TRIGGERS_HISTORIAL = (
    """CREATE TRIGGER IF NOT EXISTS estado_animal_sin_update BEFORE UPDATE ON estado_animal
       BEGIN SELECT RAISE(ABORT, 'El historial de estados no se puede modificar'); END""",
    """CREATE TRIGGER IF NOT EXISTS estado_animal_sin_delete BEFORE DELETE ON estado_animal
       BEGIN SELECT RAISE(ABORT, 'El historial de estados no se puede borrar'); END""",
)


def proteger_historial(engine: Engine) -> None:
    """El historial de estados solo crece: la base impide UPDATE y DELETE (PB-04). Idempotente;
    se llama después de create_all, porque la tabla debe existir."""
    with engine.begin() as conexion:
        for sentencia in _TRIGGERS_HISTORIAL:
            conexion.exec_driver_sql(sentencia)
