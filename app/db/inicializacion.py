"""Secuencia única de preparación de la base de datos.

La usan la API al arrancar (app/main.py) y el comando de crear administrador, para que ambos
dejen la base exactamente igual de preparada.
"""
from sqlalchemy.engine import Engine

from app.db import migraciones, triggers
from app.models import Base


def inicializar_base(engine: Engine) -> None:
    """Idempotente: se puede llamar en cada arranque, también sobre una BD ya existente."""
    migraciones.migrar(engine)  # lleva una base existente al esquema actual
    Base.metadata.create_all(engine)
    triggers.proteger_auditoria(engine)  # triggers: la auditoría no se edita ni se borra
    triggers.proteger_historial(engine)  # triggers: el historial de estados solo crece
