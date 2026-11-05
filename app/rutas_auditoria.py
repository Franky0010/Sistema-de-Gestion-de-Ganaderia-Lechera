"""GET /api/v1/auditoria (RNF07). Solo lectura y solo administrador.
No hay POST/PATCH/DELETE: la API no ofrece ninguna forma de alterar la auditoría."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from . import auditoria, dependencias
from .db_deps import get_session

router = APIRouter(prefix="/auditoria", tags=["auditoria"])
solo_admin = dependencias.requiere("administrador")


@router.get("")
def consultar(
    entidad: Optional[str] = Query(None, max_length=50),
    entidad_id: Optional[int] = Query(None, ge=1),
    accion: Optional[str] = Query(None, max_length=30),
    usuario_id: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _ctx=Depends(solo_admin),
    db: Session = Depends(get_session),
):
    return auditoria.listar(db, entidad=entidad, entidad_id=entidad_id, accion=accion,
                            usuario_id=usuario_id, page=page, page_size=page_size)