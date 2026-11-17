"""Lógica de negocio del registro de ordeños.

Aquí está lo que la PoC pone a prueba: el ordeño y su auditoría se guardan en UNA
transacción, y los duplicados los detiene la restricción única de la base de datos
(no una consulta previa, que fallaría bajo concurrencia).
"""
import json
from decimal import Decimal, DecimalException, localcontext

from app.core.excepciones import BaseDeDatosOcupada, ErrorIntegridad
from app.models import Auditoria, Ordeno
from app.services.puertos import UnidadDeTrabajo


TURNOS = ("mañana", "tarde")
# Límite técnico del INTEGER de SQLite (64 bits con signo), expresado en litros.
MAX_LITROS = Decimal("92233720368547758.07")


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
    if litros > MAX_LITROS:
        raise ErrorDeValidacion(f"{campo} supera el límite de almacenamiento")
    try:
        with localcontext() as contexto:
            contexto.prec = 28
            if litros != litros.quantize(Decimal("0.01")):
                raise ErrorDeValidacion(f"{campo} admite máximo dos decimales")
            return int(litros * 100)
    except DecimalException as exc:
        raise ErrorDeValidacion(f"{campo} no puede representarse en centilitros") from exc


def _insertar_auditoria(uow: UnidadDeTrabajo, ordeno: Ordeno, usuario: str) -> None:
    uow.auditoria.agregar(
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
    uow: UnidadDeTrabajo,
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
        if uow.animales.obtener(animal_id) is None:
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
        uow.ordenos.agregar(ordeno)
        uow.flush()  # aquí salta la restricción única si hay duplicado
        _insertar_auditoria(uow, ordeno, usuario)
        uow.commit()
        return ordeno
    except ErrorIntegridad as exc:
        uow.rollback()
        if "UNIQUE" in exc.detalle.upper():
            raise DuplicadoError("ya existe un ordeño para ese animal, fecha y turno") from exc
        raise
    except BaseDeDatosOcupada as exc:
        uow.rollback()
        raise BloqueoTransitorio("base de datos ocupada, intente de nuevo") from exc
    except Exception:
        uow.rollback()  # cualquier fallo antes del commit deja cero registros nuevos
        raise
