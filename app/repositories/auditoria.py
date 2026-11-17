"""Persistencia de la auditoría con SQLAlchemy (solo inserción y lectura)."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Auditoria
from app.repositories.traduccion_errores import traducir_errores
from app.services.puertos import RepositorioAuditoria


class RepositorioAuditoriaSQL(RepositorioAuditoria):
    def __init__(self, db: Session) -> None:
        self._db = db

    @traducir_errores
    def agregar(self, registro: Auditoria) -> None:
        self._db.add(registro)

    @traducir_errores
    def buscar(self, *, entidad, entidad_id, accion, usuario_id, page: int, page_size: int):
        filtros = []
        if entidad:
            filtros.append(Auditoria.entidad == entidad)
        if entidad_id is not None:
            filtros.append(Auditoria.entidad_id == entidad_id)
        if accion:
            filtros.append(Auditoria.accion == accion)
        if usuario_id is not None:
            filtros.append(Auditoria.usuario_id == usuario_id)
        consulta, conteo = select(Auditoria), select(func.count(Auditoria.id))
        for f in filtros:
            consulta, conteo = consulta.where(f), conteo.where(f)
        filas = self._db.scalars(
            consulta.order_by(Auditoria.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return filas, self._db.scalar(conteo)
