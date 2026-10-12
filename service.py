"""Lógica de negocio del registro de ordeños.

Aquí está lo que la PoC pone a prueba: el ordeño y su auditoría se guardan en UNA
transacción, y los duplicados los detiene la restricción única de la base de datos
(no una consulta previa, que fallaría bajo concurrencia).
"""
import json
from decimal import Decimal

from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from .models import Animal, Auditoria, Ordeno

TURNOS = ("mañana", "tarde")


class ErrorDeValidacion(Exception):
    """Dato inválido (HTTP 422)."""


class AnimalNoExiste(Exception):
    """Animal inexistente (HTTP 404)."""


class DuplicadoError(Exception):
    """Ya existe un ordeño para ese animal, fecha y turno (HTTP 409)."""


class BloqueoTransitorio(Exception):
    """SQLite siguió bloqueada tras la espera acotada; el cliente puede reintentar (HTTP 503)."""


def a_centilitros(litros: Decimal, campo: str) -> int:
    """Convierte litros a centilitros enteros validando RN02 / RF05."""
    if not litros.is_finite():
        raise ErrorDeValidacion(f"{campo} debe ser un número finito")
    if litros < 0:
        raise ErrorDeValidacion(f"{campo} no puede ser negativo")
    if litros != litros.quantize(Decimal("0.01")):
        raise ErrorDeValidacion(f"{campo} admite máximo dos decimales")
    return int(litros * 100)


def _insertar_auditoria(session: Session, ordeno: Ordeno, usuario: str) -> None:
    session.add(
        Auditoria(
            entidad="ordeno",
            entidad_id=ordeno.id,
            accion="crear",
            usuario=usuario,
            despues=json.dumps(
                {
                    "animal_id": ordeno.animal_id,
                    "fecha": ordeno.fecha.isoformat(),
                    "turno": ordeno.turno,
                    "centilitros_producidos": ordeno.centilitros_producidos,
                    "centilitros_descartados": ordeno.centilitros_descartados,
                }
            ),
        )
    )


def registrar_ordeno(
    session: Session,
    *,
    animal_id: int,
    fecha,
    turno: str,
    litros_producidos: Decimal,
    litros_descartados: Decimal,
    usuario: str,
    observaciones: str | None = None,
) -> Ordeno:
    # 1) Validaciones que no requieren base de datos.
    if turno not in TURNOS:
        raise ErrorDeValidacion("turno debe ser 'mañana' o 'tarde'")
    producido = a_centilitros(litros_producidos, "litros_producidos")
    descartado = a_centilitros(litros_descartados, "litros_descartados")
    if descartado > producido:
        raise ErrorDeValidacion("el descarte no puede superar la producción")

    # 2) Todo lo que escribe va en una sola transacción.
    try:
        if session.get(Animal, animal_id) is None:
            raise AnimalNoExiste(f"el animal {animal_id} no existe")

        ordeno = Ordeno(
            animal_id=animal_id,
            fecha=fecha,
            turno=turno,
            centilitros_producidos=producido,
            centilitros_descartados=descartado,
            observaciones=observaciones,
            creado_por=usuario,
        )
        session.add(ordeno)
        session.flush()  # aquí salta la restricción única si hay duplicado
        _insertar_auditoria(session, ordeno, usuario)
        session.commit()
        return ordeno
    except IntegrityError as exc:
        session.rollback()
        if "UNIQUE" in str(exc.orig).upper():
            raise DuplicadoError("ya existe un ordeño para ese animal, fecha y turno") from exc
        raise
    except OperationalError as exc:
        session.rollback()
        if "locked" in str(exc.orig).lower():
            raise BloqueoTransitorio("base de datos ocupada, intente de nuevo") from exc
        raise
    except Exception:
        session.rollback()  # cualquier fallo antes del commit deja cero registros nuevos
        raise
