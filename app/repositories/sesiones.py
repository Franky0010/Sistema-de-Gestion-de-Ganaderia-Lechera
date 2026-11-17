"""Persistencia de sesiones con SQLAlchemy."""
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Sesion, Usuario
from app.repositories.traduccion_errores import traducir_errores
from app.services.puertos import RepositorioSesiones


class RepositorioSesionesSQL(RepositorioSesiones):
    def __init__(self, db: Session) -> None:
        self._db = db

    @traducir_errores
    def agregar(self, sesion: Sesion) -> None:
        self._db.add(sesion)

    @traducir_errores
    def obtener_con_usuario(self, hash_token: str):
        return self._db.execute(
            select(Sesion, Usuario).join(Usuario, Usuario.id == Sesion.usuario_id)
            .where(Sesion.hash_token == hash_token)
        ).first()

    @traducir_errores
    def revocar_activas_de(self, usuario_id: int, instante: datetime) -> None:
        self._db.execute(update(Sesion).where(Sesion.usuario_id == usuario_id, Sesion.revocada_en.is_(None))
                         .values(revocada_en=instante))
