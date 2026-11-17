"""/api/v1/usuarios (PB-02). Solo el administrador (PB-11)."""
from fastapi import APIRouter, Depends, Query

from app.api import dependencias
from app.core.excepciones import ErrorApi
from app.schemas.usuarios import UsuarioCambio, UsuarioNuevo, usuario_publico
from app.services import usuarios as servicio_usuarios
from app.services.puertos import UnidadDeTrabajo


router = APIRouter(prefix="/usuarios", tags=["usuarios"])
solo_admin = dependencias.requiere("administrador")
solo_admin_escribe = dependencias.requiere("administrador", escritura=True)


@router.get("")
def listar(search: str = Query("", max_length=100), page: int = Query(1, ge=1),
           page_size: int = Query(20, ge=1, le=100),
           _ctx=Depends(solo_admin), uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    r = servicio_usuarios.listar_usuarios(uow.usuarios, search, page, page_size)
    return {**r, "items": [usuario_publico(u) for u in r["items"]]}


@router.get("/{usuario_id}")
def obtener(usuario_id: int, _ctx=Depends(solo_admin), uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    return usuario_publico(servicio_usuarios.obtener_usuario(uow.usuarios, usuario_id))


@router.post("", status_code=201)
def crear(datos: UsuarioNuevo, ctx=Depends(solo_admin_escribe), uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    usuario = servicio_usuarios.crear_usuario(
        uow, ctx.usuario, nombre=datos.nombre, email=datos.email, password=datos.password, rol=datos.rol)
    return usuario_publico(usuario)


@router.patch("/{usuario_id}")
def actualizar(usuario_id: int, datos: UsuarioCambio, ctx=Depends(solo_admin_escribe),
               uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    cambios = {k: getattr(datos, k) for k in datos.model_fields_set if k != "motivo"}
    if not cambios or any(v is None for v in cambios.values()):
        raise ErrorApi(422, "VALIDACION", "Indica al menos un campo válido para actualizar.",
                       {"cuerpo": "Envía nombre, email, rol o activo con un valor."})
    return usuario_publico(servicio_usuarios.actualizar_usuario(
        uow, ctx.usuario, usuario_id, cambios, datos.motivo))
