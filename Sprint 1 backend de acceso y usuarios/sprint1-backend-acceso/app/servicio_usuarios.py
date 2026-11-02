"""Reglas de negocio de cuentas de usuario (PB-02, HT-02): validación, unicidad de correo,
desactivación lógica y auditoría en la misma transacción."""
import re

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import auditoria, seguridad
from .errores import ErrorApi
from .models import Sesion, Usuario

ROLES = ("administrador", "operario", "propietario")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalizar_email(valor: str) -> str:
    return valor.strip().lower()


def snapshot(u: Usuario) -> dict:
    """Solo campos públicos: nunca el hash ni la contraseña."""
    return {"nombre": u.nombre, "email": u.email, "rol": u.rol, "activo": u.activo}


def _validar(campos: dict) -> dict:
    """Valida los campos presentes; devuelve los valores normalizados o lanza 422."""
    errores, limpios = {}, {}
    if "nombre" in campos:
        nombre = campos["nombre"].strip()
        if not nombre:
            errores["nombre"] = "El nombre es obligatorio."
        elif len(nombre) > 120:
            errores["nombre"] = "Máximo 120 caracteres."
        else:
            limpios["nombre"] = nombre
    if "email" in campos:
        email = normalizar_email(campos["email"])
        if len(email) > 254 or not _EMAIL.match(email):
            errores["email"] = "Escribe un correo válido (máximo 254 caracteres)."
        else:
            limpios["email"] = email
    if "password" in campos:
        password = campos["password"]
        try:
            password.encode("utf-8")
            valida = 8 <= len(password) <= 128
        except UnicodeEncodeError:
            valida = False
        if not valida:
            errores["password"] = "La contraseña debe tener entre 8 y 128 caracteres."
        else:
            limpios["password"] = password
    if "rol" in campos:
        if campos["rol"] not in ROLES:
            errores["rol"] = "Rol no permitido."
        else:
            limpios["rol"] = campos["rol"]
    if "activo" in campos:
        limpios["activo"] = campos["activo"]
    if errores:
        raise ErrorApi(422, "VALIDACION", "Revisa los campos indicados.", errores)
    return limpios


def _email_duplicado() -> ErrorApi:
    return ErrorApi(409, "EMAIL_DUPLICADO", "Ya existe un usuario con ese correo.",
                    {"email": "Usa un correo diferente."})


def crear_usuario(db: Session, actor: Usuario | None, *, nombre: str, email: str,
                  password: str, rol: str) -> Usuario:
    datos = _validar({"nombre": nombre, "email": email, "password": password, "rol": rol})
    hash_clave = seguridad.hashear_password(datos["password"])  # costoso: fuera de la transacción
    usuario = Usuario(nombre=datos["nombre"], email=datos["email"], hash_clave=hash_clave,
                      rol=datos["rol"], activo=True)
    try:
        db.add(usuario)
        db.flush()  # aquí salta la restricción única del correo
        auditoria.registrar(db, entidad="usuario", entidad_id=usuario.id, accion="crear",
                            actor=actor, despues=snapshot(usuario))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if "UNIQUE" in str(exc.orig).upper():
            raise _email_duplicado() from exc
        raise
    except Exception:
        db.rollback()
        raise
    return usuario


def actualizar_usuario(db: Session, actor: Usuario, usuario_id: int, cambios: dict) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise ErrorApi(404, "NO_ENCONTRADO", "El usuario no existe.")
    nuevos = {k: v for k, v in _validar(cambios).items() if getattr(usuario, k) != v}
    if not nuevos:
        return usuario  # nada cambió: sin escritura ni auditoría

    antes = snapshot(usuario)
    era_admin_activo = antes["rol"] == "administrador" and antes["activo"]
    try:
        for campo, valor in nuevos.items():
            setattr(usuario, campo, valor)
        usuario.actualizado_en = seguridad.ahora()
        db.flush()
        if nuevos.get("activo") is False:  # desactivar revoca todas sus sesiones
            db.execute(update(Sesion).where(Sesion.usuario_id == usuario.id, Sesion.revocada_en.is_(None))
                       .values(revocada_en=seguridad.ahora()))
        if era_admin_activo and not (usuario.rol == "administrador" and usuario.activo):
            # Se comprueba tras escribir, con el bloqueo de escritura de SQLite ya tomado,
            # para que dos administradores no puedan quitarse el acceso a la vez.
            if db.scalar(select(func.count()).select_from(Usuario)
                         .where(Usuario.rol == "administrador", Usuario.activo.is_(True))) == 0:
                raise ErrorApi(409, "ULTIMO_ADMINISTRADOR",
                               "Debe quedar al menos un administrador activo.")
        accion = ("desactivar" if nuevos.get("activo") is False
                  else "reactivar" if nuevos.get("activo") is True else "actualizar")
        auditoria.registrar(db, entidad="usuario", entidad_id=usuario.id, accion=accion,
                            actor=actor, antes=antes, despues=snapshot(usuario))
        db.commit()
    except ErrorApi:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        if "UNIQUE" in str(exc.orig).upper():
            raise _email_duplicado() from exc
        raise
    except Exception:
        db.rollback()
        raise
    return usuario


def _escapar_like(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def listar_usuarios(db: Session, search: str, page: int, page_size: int) -> dict:
    filtro = None
    if search.strip():
        patron = f"%{_escapar_like(search.strip())}%"
        filtro = Usuario.nombre.ilike(patron, escape="\\") | Usuario.email.ilike(patron, escape="\\")
    consulta, conteo = select(Usuario), select(func.count(Usuario.id))
    if filtro is not None:  # filtrar antes de paginar
        consulta, conteo = consulta.where(filtro), conteo.where(filtro)
    items = db.scalars(consulta.order_by(Usuario.id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": items, "total": db.scalar(conteo), "page": page, "page_size": page_size}
