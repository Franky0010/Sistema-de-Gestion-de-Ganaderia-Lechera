"""Escrituras de animales: alta y cambio de estado, cada una en UNA transacción."""
from datetime import date

from app.core.excepciones import ErrorApi, ErrorIntegridad
from app.models import ESTADOS_ANIMAL, Animal, EstadoAnimal, Usuario
from app.services import auditoria
from app.services.animales.consultas import obtener_animal
from app.services.animales.fechas import hoy
from app.services.animales.serializadores import snapshot
from app.services.animales.validaciones import _validar_alta
from app.services.puertos import UnidadDeTrabajo


MOTIVO_ALTA = "Estado inicial al registrar el animal"
MENSAJE_ESTADOS = "Usa en_produccion, seco, no_productivo o fuera_del_hato."


def _arete_duplicado() -> ErrorApi:
    return ErrorApi(409, "ARETE_DUPLICADO", "Ya existe un animal con ese arete.",
                    {"arete": "Usa un identificador diferente."})


def _cambio_diario_duplicado() -> ErrorApi:
    return ErrorApi(409, "CAMBIO_DIARIO_DUPLICADO", "El animal ya tiene un cambio de estado ese día.",
                    {"fecha_desde": "Elige otra fecha."})


def crear_animal(uow: UnidadDeTrabajo, actor: Usuario, campos: dict) -> Animal:
    d = _validar_alta(campos)
    animal = Animal(arete=d["arete"], nombre=d["nombre"], raza=d["raza"], procedencia=d["procedencia"],
                    fecha_ingreso=d["fecha_ingreso"], fecha_nacimiento=d["fecha_nacimiento"],
                    edad_estimada_meses=d["edad_estimada_meses"], version=1)
    try:
        uow.animales.agregar(animal)
        uow.flush()  # aquí salta la restricción única del arete
        uow.estados.agregar(EstadoAnimal(animal_id=animal.id, estado=d["estado_inicial"],
                                         fecha_desde=d["fecha_ingreso"], motivo=MOTIVO_ALTA,
                                         responsable_id=actor.id))
        uow.flush()
        auditoria.registrar(uow.auditoria, entidad="animal", entidad_id=animal.id, accion="crear",
                            actor=actor, despues=snapshot(animal, d["estado_inicial"]))
        uow.commit()
    except ErrorIntegridad as exc:
        uow.rollback()
        if "ANIMAL.ARETE" in exc.detalle.upper():
            raise _arete_duplicado() from exc
        raise
    except Exception:
        uow.rollback()
        raise
    return animal


def cambiar_estado(uow: UnidadDeTrabajo, actor: Usuario, animal_id: int, *, estado: str, fecha_desde: date,
                   motivo: str | None, version: int) -> tuple[EstadoAnimal, Animal]:
    animal = obtener_animal(uow.animales, animal_id)
    errores = {}
    if estado not in ESTADOS_ANIMAL:
        errores["estado"] = MENSAJE_ESTADOS
    if animal.fecha_ingreso is not None and fecha_desde < animal.fecha_ingreso:
        errores["fecha_desde"] = "No puede ser anterior a la fecha de ingreso."
    elif fecha_desde > hoy():
        errores["fecha_desde"] = "No puede ser una fecha futura."
    if errores:
        raise ErrorApi(422, "VALIDACION", "Revisa los campos indicados.", errores)
    motivo = auditoria.validar_motivo(motivo, obligatorio=True)

    if version != animal.version:
        raise ErrorApi(409, "VERSION_OBSOLETA", "El animal cambió desde que lo consultaste. Recarga e intenta de nuevo.")
    if uow.estados.tiene_estado(animal.id, "fuera_del_hato"):
        raise ErrorApi(409, "ESTADO_INCOMPATIBLE", "El animal ya salió del hato.")
    if uow.estados.existe_cambio_en(animal.id, fecha_desde):
        raise _cambio_diario_duplicado()
    vigente = uow.estados.vigente_en(animal.id, fecha_desde)
    if vigente is not None and vigente.estado == estado:
        raise ErrorApi(422, "VALIDACION", "Revisa los campos indicados.",
                       {"estado": "El animal ya está en ese estado en esa fecha."})

    siguiente = uow.estados.siguiente_a(animal.id, fecha_desde)
    if estado == "fuera_del_hato" and siguiente is not None:
        raise ErrorApi(409, "ESTADO_INCOMPATIBLE", "La salida del hato debe ser el último cambio del animal.",
                       {"fecha_desde": "Hay cambios de estado posteriores a esa fecha."})
    if estado != "en_produccion":
        # El nuevo estado rige desde fecha_desde hasta el siguiente cambio (si existe): solo los
        # ordeños vigentes (no anulados) de ese tramo lo contradicen.
        hasta = siguiente.fecha_desde if siguiente is not None else None
        if uow.ordenos.hay_vigentes(animal.id, fecha_desde, hasta):
            raise ErrorApi(409, "ESTADO_INCOMPATIBLE",
                           "Hay ordeños vigentes en ese período; el animal no puede quedar en ese estado.",
                           {"estado": "Anula o corrige los ordeños antes de cambiar el estado."})

    antes = {"estado": vigente.estado if vigente else None, "version": animal.version}
    despues = {"estado": estado, "fecha_desde": fecha_desde.isoformat(), "version": animal.version + 1}
    try:
        # Compara y actualiza la versión en una sola operación: si otro la cambió antes, no toca ninguna fila.
        if not uow.animales.incrementar_version(animal.id, version):
            raise ErrorApi(409, "VERSION_OBSOLETA", "El animal cambió desde que lo consultaste. Recarga e intenta de nuevo.")
        nuevo = EstadoAnimal(animal_id=animal.id, estado=estado, fecha_desde=fecha_desde, motivo=motivo,
                             responsable_id=actor.id)
        uow.estados.agregar(nuevo)
        uow.flush()
        auditoria.registrar(uow.auditoria, entidad="animal", entidad_id=animal.id, accion="cambiar_estado",
                            actor=actor, antes=antes, despues=despues, motivo=motivo)
        uow.commit()
    except ErrorIntegridad as exc:
        uow.rollback()
        if "UNIQUE" in exc.detalle.upper():
            raise _cambio_diario_duplicado() from exc
        raise
    except Exception:
        uow.rollback()
        raise
    uow.refrescar(animal)
    return nuevo, animal
