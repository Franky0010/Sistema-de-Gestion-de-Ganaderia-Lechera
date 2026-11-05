"""Registro y consulta de auditoría (HT-02 / RNF07).

- registrar() solo inserta dentro de la transacción de quien la llama: si esa transacción
  se revierte, la auditoría también.
- Nunca guarda contraseñas, hashes ni tokens: se rechazan por nombre de campo.
- Exige motivo en las acciones que lo requieren (RNF07).
- proteger_auditoria() crea triggers que impiden UPDATE y DELETE sobre la tabla.
"""
import json
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from .errores import ErrorApi
from .models import Auditoria, Usuario

# RNF07: motivo obligatorio en correcciones, anulaciones, reactivaciones y cambios de estado.
ACCIONES_CON_MOTIVO = {"corregir", "anular", "reactivar", "desactivar", "cambiar_estado"}
CAMPOS_PROHIBIDOS = {"password", "clave", "hash_clave", "hash_token", "token", "csrf_token"}
MAX_MOTIVO = 500


def validar_motivo(motivo: Optional[str], obligatorio: bool) -> Optional[str]:
    """Normaliza el motivo; si es obligatorio y falta, responde 422 ANTES de escribir nada."""
    limpio = (motivo or "").strip()
    if obligatorio and not limpio:
        raise ErrorApi(422, "VALIDACION", "Revisa los campos indicados.",
                       {"motivo": "El motivo es obligatorio para este cambio."})
    if len(limpio) > MAX_MOTIVO:
        raise ErrorApi(422, "VALIDACION", "Revisa los campos indicados.",
                       {"motivo": f"Máximo {MAX_MOTIVO} caracteres."})
    return limpio or None


def _sin_secretos(datos: Optional[dict]) -> Optional[dict]:
    if datos is not None and CAMPOS_PROHIBIDOS & {str(k).lower() for k in datos}:
        raise ValueError("La auditoría no puede contener contraseñas, hashes ni tokens.")
    return datos


def registrar(
    db: Session, *, entidad: str, entidad_id: int, accion: str,
    actor: Usuario | None, antes: dict | None = None, despues: dict | None = None,
    motivo: str | None = None,
) -> None:
    if accion in ACCIONES_CON_MOTIVO and not (motivo or "").strip():
        raise ValueError(f"La acción '{accion}' exige motivo.")
    antes, despues = _sin_secretos(antes), _sin_secretos(despues)
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


def _publica(a: Auditoria) -> dict:
    return {
        "id": a.id, "entidad": a.entidad, "entidad_id": a.entidad_id, "accion": a.accion,
        "usuario": a.usuario, "usuario_id": a.usuario_id,
        "momento": a.momento.isoformat() + "Z",  # se guarda en UTC sin zona
        "antes": json.loads(a.antes) if a.antes else None,
        "despues": json.loads(a.despues) if a.despues else None,
        "motivo": a.motivo,
    }


def listar(db: Session, *, entidad=None, entidad_id=None, accion=None, usuario_id=None,
           page: int = 1, page_size: int = 20) -> dict:
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
    filas = db.scalars(
        consulta.order_by(Auditoria.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": [_publica(a) for a in filas], "total": db.scalar(conteo),
            "page": page, "page_size": page_size}


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