"""Registro de auditoría (HT-02 / RNF07). Solo inserta dentro de la transacción de quien
la llama: si esa transacción se revierte, la auditoría también. Nunca recibe contraseñas,
hashes ni tokens (los llamadores pasan solo instantáneas de campos públicos)."""
import json

from sqlalchemy.orm import Session

from .models import Auditoria, Usuario


def registrar(
    db: Session, *, entidad: str, entidad_id: int, accion: str,
    actor: Usuario | None, antes: dict | None = None, despues: dict | None = None,
    motivo: str | None = None,
) -> None:
    db.add(
        Auditoria(
            entidad=entidad,
            entidad_id=entidad_id,
            accion=accion,
            usuario=actor.email if actor else "sistema",
            usuario_id=actor.id if actor else None,
            antes=json.dumps(antes, ensure_ascii=False) if antes is not None else None,
            despues=json.dumps(despues, ensure_ascii=False) if despues is not None else None,
            motivo=motivo,
        )
    )
