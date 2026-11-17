"""Registro y consulta de auditoría (HT-02 / RNF07).

- registrar() solo inserta dentro de la transacción de quien la llama: si esa transacción
  se revierte, la auditoría también.
- Nunca guarda contraseñas, hashes ni tokens: se rechazan por nombre de campo.
- Exige motivo en las acciones que lo requieren (RNF07).
- Los triggers que impiden UPDATE y DELETE sobre la tabla están en app/db/triggers.py.
"""
import json
from typing import Optional

from app.core.excepciones import ErrorApi
from app.models import Auditoria, Usuario
from app.services.puertos import RepositorioAuditoria


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
    repo: RepositorioAuditoria, *, entidad: str, entidad_id: int, accion: str,
    actor: Usuario | None, antes: dict | None = None, despues: dict | None = None,
    motivo: str | None = None,
) -> None:
    if accion in ACCIONES_CON_MOTIVO and not (motivo or "").strip():
        raise ValueError(f"La acción '{accion}' exige motivo.")
    antes, despues = _sin_secretos(antes), _sin_secretos(despues)
    repo.agregar(
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


def listar(repo: RepositorioAuditoria, *, entidad=None, entidad_id=None, accion=None, usuario_id=None,
           page: int = 1, page_size: int = 20) -> dict:
    filas, total = repo.buscar(entidad=entidad, entidad_id=entidad_id, accion=accion,
                               usuario_id=usuario_id, page=page, page_size=page_size)
    return {"items": [_publica(a) for a in filas], "total": total,
            "page": page, "page_size": page_size}
