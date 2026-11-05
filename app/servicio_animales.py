"""Reglas de negocio de animales y estados (PB-03, base de HT-02).

Cada operación de escritura es UNA transacción: animal/estado + versión + auditoría se
confirman juntos o se revierten juntos. Todo lo que puede fallar por reglas se valida antes
de escribir; lo que depende de la concurrencia (arete único, un cambio por día, versión) lo
decide la base de datos dentro de la transacción.
"""
from datetime import date, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import auditoria, seguridad
from .errores import ErrorApi
from .models import ESTADOS_ANIMAL, Animal, EstadoAnimal, Ordeno, Usuario

ESTADOS_ALTA = ("en_produccion", "seco", "no_productivo")
MOTIVO_ALTA = "Estado inicial al registrar el animal"
MENSAJE_ESTADOS = "Usa en_produccion, seco, no_productivo o fuera_del_hato."
_BOGOTA = timezone(timedelta(hours=-5))  # Colombia no usa horario de verano


def hoy() -> date:
    """Fecha de negocio (America/Bogota). Usa seguridad.ahora() para que las pruebas la muevan."""
    return seguridad.ahora().replace(tzinfo=timezone.utc).astimezone(_BOGOTA).date()


def _iso(valor):
    return valor.isoformat() if valor is not None else None


def _validar_alta(c: dict) -> dict:
    errores, v = {}, {}

    def texto(campo, maximo, obligatorio=True):
        valor = (c.get(campo) or "").strip()
        if not valor:
            if obligatorio:
                errores[campo] = "Este campo es obligatorio."
            v[campo] = None
        elif len(valor) > maximo:
            errores[campo] = f"Máximo {maximo} caracteres."
        else:
            v[campo] = valor

    texto("arete", 40)
    texto("raza", 80)
    texto("procedencia", 160)
    texto("nombre", 100, obligatorio=False)
    if v.get("arete"):
        v["arete"] = v["arete"].upper()  # trim + mayúsculas: no distingue mayúsculas

    limite = hoy()
    ingreso, nacimiento, edad = c.get("fecha_ingreso"), c.get("fecha_nacimiento"), c.get("edad_estimada_meses")
    if ingreso is None:
        errores["fecha_ingreso"] = "Este campo es obligatorio."
    elif ingreso > limite:
        errores["fecha_ingreso"] = "No puede ser una fecha futura."
    if (nacimiento is None) == (edad is None):
        mensaje = "Envía la fecha de nacimiento o la edad estimada, pero no ambas ni ninguna."
        errores["fecha_nacimiento"] = errores["edad_estimada_meses"] = mensaje
    elif nacimiento is not None:
        if nacimiento > limite:
            errores["fecha_nacimiento"] = "No puede ser una fecha futura."
        elif ingreso is not None and nacimiento > ingreso:
            errores["fecha_nacimiento"] = "No puede ser posterior a la fecha de ingreso."
    elif edad < 0:
        errores["edad_estimada_meses"] = "Debe ser 0 o mayor."
    if c.get("estado_inicial") not in ESTADOS_ALTA:
        errores["estado_inicial"] = "Usa en_produccion, seco o no_productivo."
    if errores:
        raise ErrorApi(422, "VALIDACION", "Revisa los campos indicados.", errores)
    v.update(fecha_ingreso=ingreso, fecha_nacimiento=nacimiento, edad_estimada_meses=edad,
             estado_inicial=c["estado_inicial"])
    return v


def snapshot(a: Animal, estado: str | None = None) -> dict:
    datos = {"arete": a.arete, "nombre": a.nombre, "raza": a.raza, "procedencia": a.procedencia,
             "fecha_ingreso": _iso(a.fecha_ingreso), "fecha_nacimiento": _iso(a.fecha_nacimiento),
             "edad_estimada_meses": a.edad_estimada_meses, "version": a.version}
    if estado:
        datos["estado"] = estado
    return datos


def estado_en(db: Session, animal_id: int, fecha: date) -> EstadoAnimal | None:
    return db.scalars(
        select(EstadoAnimal)
        .where(EstadoAnimal.animal_id == animal_id, EstadoAnimal.fecha_desde <= fecha)
        .order_by(EstadoAnimal.fecha_desde.desc(), EstadoAnimal.id.desc()).limit(1)
    ).first()


def animal_publico(db: Session, a: Animal) -> dict:
    actual = estado_en(db, a.id, hoy())
    return {
        "id": a.id, "arete": a.arete, "nombre": a.nombre, "raza": a.raza, "procedencia": a.procedencia,
        "fecha_ingreso": _iso(a.fecha_ingreso), "fecha_nacimiento": _iso(a.fecha_nacimiento),
        "edad_estimada_meses": a.edad_estimada_meses,
        "estado_actual": actual.estado if actual else None,
        "estado_desde": _iso(actual.fecha_desde) if actual else None,
        "version": a.version,
    }


def estado_publico(e: EstadoAnimal) -> dict:
    return {"id": e.id, "animal_id": e.animal_id, "estado": e.estado,
            "fecha_desde": _iso(e.fecha_desde), "motivo": e.motivo, "responsable_id": e.responsable_id}

def _siguiente_estado(db: Session, animal_id: int, fecha: date) -> EstadoAnimal | None:
    return db.scalars(
        select(EstadoAnimal).where(EstadoAnimal.animal_id == animal_id, EstadoAnimal.fecha_desde > fecha)
        .order_by(EstadoAnimal.fecha_desde, EstadoAnimal.id).limit(1)
    ).first()


def listar_estados(db: Session, animal: Animal, *, page: int = 1, page_size: int = 20) -> dict:
    """Historial en orden cronológico (fecha efectiva, luego id). Nunca se edita ni se borra."""
    donde = EstadoAnimal.animal_id == animal.id
    total = db.scalar(select(func.count()).select_from(EstadoAnimal).where(donde))
    filas = db.scalars(
        select(EstadoAnimal).where(donde).order_by(EstadoAnimal.fecha_desde, EstadoAnimal.id)
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {"items": [estado_publico(e) for e in filas], "total": total, "page": page, "page_size": page_size}

def obtener_animal(db: Session, animal_id: int) -> Animal:
    animal = db.get(Animal, animal_id)
    if animal is None:
        raise ErrorApi(404, "NO_ENCONTRADO", "El animal no existe.")
    return animal


def _arete_duplicado() -> ErrorApi:
    return ErrorApi(409, "ARETE_DUPLICADO", "Ya existe un animal con ese arete.",
                    {"arete": "Usa un identificador diferente."})


def _cambio_diario_duplicado() -> ErrorApi:
    return ErrorApi(409, "CAMBIO_DIARIO_DUPLICADO", "El animal ya tiene un cambio de estado ese día.",
                    {"fecha_desde": "Elige otra fecha."})


def crear_animal(db: Session, actor: Usuario, campos: dict) -> Animal:
    d = _validar_alta(campos)
    animal = Animal(arete=d["arete"], nombre=d["nombre"], raza=d["raza"], procedencia=d["procedencia"],
                    fecha_ingreso=d["fecha_ingreso"], fecha_nacimiento=d["fecha_nacimiento"],
                    edad_estimada_meses=d["edad_estimada_meses"], version=1)
    try:
        db.add(animal)
        db.flush()  # aquí salta la restricción única del arete
        db.add(EstadoAnimal(animal_id=animal.id, estado=d["estado_inicial"], fecha_desde=d["fecha_ingreso"],
                            motivo=MOTIVO_ALTA, responsable_id=actor.id))
        db.flush()
        auditoria.registrar(db, entidad="animal", entidad_id=animal.id, accion="crear", actor=actor,
                            despues=snapshot(animal, d["estado_inicial"]))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "ANIMAL.ARETE" in str(exc.orig).upper():
            raise _arete_duplicado() from exc
        raise
    except Exception:
        db.rollback()
        raise
    return animal


def cambiar_estado(db: Session, actor: Usuario, animal_id: int, *, estado: str, fecha_desde: date,
                   motivo: str | None, version: int) -> tuple[EstadoAnimal, Animal]:
    animal = obtener_animal(db, animal_id)
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
    if db.scalar(select(func.count()).select_from(EstadoAnimal)
                 .where(EstadoAnimal.animal_id == animal.id, EstadoAnimal.estado == "fuera_del_hato")):
        raise ErrorApi(409, "ESTADO_INCOMPATIBLE", "El animal ya salió del hato.")
    if db.scalar(select(EstadoAnimal.id).where(EstadoAnimal.animal_id == animal.id,
                                               EstadoAnimal.fecha_desde == fecha_desde)):
        raise _cambio_diario_duplicado()
    vigente = estado_en(db, animal.id, fecha_desde)
    if vigente is not None and vigente.estado == estado:
        raise ErrorApi(422, "VALIDACION", "Revisa los campos indicados.",
                       {"estado": "El animal ya está en ese estado en esa fecha."})

    siguiente = _siguiente_estado(db, animal.id, fecha_desde)
    if estado == "fuera_del_hato" and siguiente is not None:
        raise ErrorApi(409, "ESTADO_INCOMPATIBLE", "La salida del hato debe ser el último cambio del animal.",
                       {"fecha_desde": "Hay cambios de estado posteriores a esa fecha."})
    if estado != "en_produccion":
        # El nuevo estado rige desde fecha_desde hasta el siguiente cambio (si existe): solo los
        # ordeños vigentes (no anulados) de ese tramo lo contradicen.
        ordenos = select(Ordeno.id).where(Ordeno.animal_id == animal.id, Ordeno.anulado.is_(False),
                                          Ordeno.fecha >= fecha_desde)
        if siguiente is not None:
            ordenos = ordenos.where(Ordeno.fecha < siguiente.fecha_desde)
        if db.scalar(ordenos.limit(1)):
            raise ErrorApi(409, "ESTADO_INCOMPATIBLE",
                           "Hay ordeños vigentes en ese período; el animal no puede quedar en ese estado.",
                           {"estado": "Anula o corrige los ordeños antes de cambiar el estado."})

    antes = {"estado": vigente.estado if vigente else None, "version": animal.version}
    despues = {"estado": estado, "fecha_desde": fecha_desde.isoformat(), "version": animal.version + 1}
    try:
        # Compara y actualiza la versión en una sola sentencia: si otro la cambió antes, no toca ninguna fila.
        resultado = db.execute(
            update(Animal).where(Animal.id == animal.id, Animal.version == version)
            .values(version=Animal.version + 1).execution_options(synchronize_session=False)
        )
        if resultado.rowcount != 1:
            raise ErrorApi(409, "VERSION_OBSOLETA", "El animal cambió desde que lo consultaste. Recarga e intenta de nuevo.")
        nuevo = EstadoAnimal(animal_id=animal.id, estado=estado, fecha_desde=fecha_desde, motivo=motivo,
                             responsable_id=actor.id)
        db.add(nuevo)
        db.flush()
        auditoria.registrar(db, entidad="animal", entidad_id=animal.id, accion="cambiar_estado", actor=actor,
                            antes=antes, despues=despues, motivo=motivo)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "UNIQUE" in str(exc.orig).upper():
            raise _cambio_diario_duplicado() from exc
        raise
    except Exception:
        db.rollback()
        raise
    db.refresh(animal)
    return nuevo, animal