"""Escrituras de cuentas de usuario: cada operación es una transacción con su auditoría."""
from app.core import seguridad
from app.core.excepciones import ErrorApi, ErrorIntegridad
from app.models import Usuario
from app.services import auditoria
from app.services.puertos import UnidadDeTrabajo
from app.services.usuarios.validaciones import _validar


def snapshot(u: Usuario) -> dict:
    """Solo campos públicos: nunca el hash ni la contraseña."""
    return {"nombre": u.nombre, "email": u.email, "rol": u.rol, "activo": u.activo}


def _email_duplicado() -> ErrorApi:
    return ErrorApi(409, "EMAIL_DUPLICADO", "Ya existe un usuario con ese correo.",
                    {"email": "Usa un correo diferente."})


def _viola_correo_unico(exc: ErrorIntegridad) -> bool:
    """True solo si la restricción violada es la del correo (p. ej. "UNIQUE constraint failed:
    usuario.email"). Cualquier otro UNIQUE (sesión, auditoría...) NO es un correo repetido."""
    texto = exc.detalle.upper()
    return "UNIQUE" in texto and "USUARIO.EMAIL" in texto


def crear_usuario(uow: UnidadDeTrabajo, actor: Usuario | None, *, nombre: str, email: str,
                  password: str, rol: str) -> Usuario:
    datos = _validar({"nombre": nombre, "email": email, "password": password, "rol": rol})
    hash_clave = seguridad.hashear_password(datos["password"])  # costoso: fuera de la transacción
    usuario = Usuario(nombre=datos["nombre"], email=datos["email"], hash_clave=hash_clave,
                      rol=datos["rol"], activo=True)
    try:
        uow.usuarios.agregar(usuario)
        uow.flush()  # aquí salta la restricción única del correo
        auditoria.registrar(uow.auditoria, entidad="usuario", entidad_id=usuario.id, accion="crear",
                            actor=actor, despues=snapshot(usuario))
        uow.commit()
    except ErrorIntegridad as exc:
        uow.rollback()
        if _viola_correo_unico(exc):
            raise _email_duplicado() from exc
        raise
    except Exception:
        uow.rollback()
        raise
    return usuario


def actualizar_usuario(uow: UnidadDeTrabajo, actor: Usuario, usuario_id: int, cambios: dict,
                       motivo: str | None = None) -> Usuario:
    usuario = uow.usuarios.obtener(usuario_id)
    if usuario is None:
        raise ErrorApi(404, "NO_ENCONTRADO", "El usuario no existe.")
    nuevos = {k: v for k, v in _validar(cambios).items() if getattr(usuario, k) != v}
    if not nuevos:
        return usuario  # nada cambió: sin escritura ni auditoría
    motivo = auditoria.validar_motivo(motivo, obligatorio="activo" in nuevos)

    if "email" in nuevos:
        # Solo es duplicado si el correo lo tiene OTRA cuenta (activa o inactiva); el propio
        # usuario conservando su correo nunca cuenta como duplicado.
        otro = uow.usuarios.obtener_por_email(nuevos["email"])
        if otro is not None and otro.id != usuario.id:
            raise _email_duplicado()

    antes = snapshot(usuario)
    era_admin_activo = antes["rol"] == "administrador" and antes["activo"]
    try:
        for campo, valor in nuevos.items():
            setattr(usuario, campo, valor)
        usuario.actualizado_en = seguridad.ahora()
        uow.flush()
        if nuevos.get("activo") is False:  # desactivar revoca todas sus sesiones
            uow.sesiones.revocar_activas_de(usuario.id, seguridad.ahora())
        if era_admin_activo and not (usuario.rol == "administrador" and usuario.activo):
            # Se comprueba tras escribir, con el bloqueo de escritura de SQLite ya tomado,
            # para que dos administradores no puedan quitarse el acceso a la vez.
            if uow.usuarios.contar_administradores_activos() == 0:
                raise ErrorApi(409, "ULTIMO_ADMINISTRADOR",
                               "Debe quedar al menos un administrador activo.")
        accion = ("desactivar" if nuevos.get("activo") is False
                  else "reactivar" if nuevos.get("activo") is True else "actualizar")
        auditoria.registrar(uow.auditoria, entidad="usuario", entidad_id=usuario.id, accion=accion,
                            actor=actor, antes=antes, despues=snapshot(usuario),
                            motivo=motivo)
        uow.commit()
    except ErrorApi:
        uow.rollback()
        raise
    except ErrorIntegridad as exc:
        uow.rollback()
        if _viola_correo_unico(exc):
            raise _email_duplicado() from exc
        raise
    except Exception:
        uow.rollback()
        raise
    return usuario