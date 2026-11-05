"""/api/v1/usuarios (PB-02). Solo el administrador (PB-11)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, StrictBool
from sqlalchemy.orm import Session

from . import dependencias, servicio_usuarios
from .db_deps import get_session
from .errores import ErrorApi
from .models import Usuario
from .rutas_auth import usuario_publico

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

solo_admin = dependencias.requiere("administrador")
solo_admin_escribe = dependencias.requiere("administrador", escritura=True)


class UsuarioNuevo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str
    email: str
    password: str
    rol: str


class UsuarioCambio(BaseModel):
    # extra="forbid": no se admite cambiar la contraseña en esta fase.
    model_config = ConfigDict(extra="forbid")
    nombre: Optional[str] = None
    email: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[StrictBool] = None
    motivo: Optional[str] = None  # obligatorio si se cambia 'activo' (RNF07)   ← nuevo


@router.get("")
def listar(search: str = Query("", max_length=100), page: int = Query(1, ge=1),
           page_size: int = Query(20, ge=1, le=100),
           _ctx=Depends(solo_admin), db: Session = Depends(get_session)):
    r = servicio_usuarios.listar_usuarios(db, search, page, page_size)
    return {**r, "items": [usuario_publico(u) for u in r["items"]]}


@router.get("/{usuario_id}")
def obtener(usuario_id: int, _ctx=Depends(solo_admin), db: Session = Depends(get_session)):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise ErrorApi(404, "NO_ENCONTRADO", "El usuario no existe.")
    return usuario_publico(usuario)


@router.post("", status_code=201)
def crear(datos: UsuarioNuevo, ctx=Depends(solo_admin_escribe), db: Session = Depends(get_session)):
    usuario = servicio_usuarios.crear_usuario(
        db, ctx.usuario, nombre=datos.nombre, email=datos.email, password=datos.password, rol=datos.rol)
    return usuario_publico(usuario)


@router.patch("/{usuario_id}")
def actualizar(usuario_id: int, datos: UsuarioCambio, ctx=Depends(solo_admin_escribe),
               db: Session = Depends(get_session)):
    cambios = {k: getattr(datos, k) for k in datos.model_fields_set if k != "motivo"}
    if not cambios or any(v is None for v in cambios.values()):
        raise ErrorApi(422, "VALIDACION", "Indica al menos un campo válido para actualizar.",
                       {"cuerpo": "Envía nombre, email, rol o activo con un valor."})
    return usuario_publico(servicio_usuarios.actualizar_usuario(
        db, ctx.usuario, usuario_id, cambios, datos.motivo))
