"""Esquemas de /api/v1/usuarios y representación pública de un usuario."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, StrictBool

from app.models import Usuario


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


def usuario_publico(u: Usuario) -> dict:
    return {"id": u.id, "nombre": u.nombre, "email": u.email, "rol": u.rol, "activo": u.activo}
