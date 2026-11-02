"""POST/GET /api/v1/auth/* (PB-01). Ver docs/contrato-api-sprint1.md."""
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from . import dependencias, seguridad, servicio_auth, servicio_usuarios
from .db_deps import get_session
from .errores import ErrorApi
from .models import Usuario

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    password: str


def usuario_publico(u: Usuario) -> dict:
    return {"id": u.id, "nombre": u.nombre, "email": u.email, "rol": u.rol, "activo": u.activo}


@router.get("/csrf")
def obtener_csrf(request: Request, response: Response, db: Session = Depends(get_session)):
    response.headers["Cache-Control"] = "no-store"
    # tocar=False: pedir un token no prolonga la sesión (no hay "mantener viva" artificial).
    ctx = servicio_auth.obtener_contexto(db, request.cookies.get(seguridad.COOKIE_SESION), tocar=False)
    if ctx is not None:
        return {"csrf_token": seguridad.crear_csrf(ctx.hash_token)}
    anonimo = request.cookies.get(seguridad.COOKIE_CSRF_ANONIMO)
    if not anonimo:
        anonimo = seguridad.generar_token()
        servicio_auth.poner_cookie(response, request, seguridad.COOKIE_CSRF_ANONIMO, anonimo)
    return {"csrf_token": seguridad.crear_csrf(anonimo)}


@router.get("/session")
def sesion_actual(response: Response, ctx=Depends(dependencias.sesion_requerida)):
    response.headers["Cache-Control"] = "no-store"
    return {"usuario": usuario_publico(ctx.usuario)}


@router.post("/login")
def login(datos: LoginIn, request: Request, response: Response, db: Session = Depends(get_session)):
    response.headers["Cache-Control"] = "no-store"
    dependencias.verificar_origen(request)
    ctx_previo, vinculo = dependencias.vinculo_actual(request, db)
    dependencias.verificar_csrf(request, vinculo)

    email = servicio_usuarios.normalizar_email(datos.email)
    ip = request.client.host if request.client else "desconocida"
    clave_limite = f"{ip}|{email}"
    espera = seguridad.limitador_login.segundos_de_espera(clave_limite, seguridad.ahora())
    if espera:
        raise ErrorApi(429, "LIMITE_SOLICITUDES", "Demasiados intentos. Espera antes de volver a intentar.",
                       headers={"Retry-After": str(espera)})

    usuario = servicio_auth.autenticar_credenciales(db, email, datos.password)
    if usuario is None:
        seguridad.limitador_login.registrar_fallo(clave_limite, seguridad.ahora())
        raise ErrorApi(401, "CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos.")
    seguridad.limitador_login.limpiar(clave_limite)
    if not usuario.activo:  # solo se revela tras verificar la contraseña
        raise ErrorApi(403, "CUENTA_INACTIVA", "Tu cuenta está desactivada. Contacta al administrador.")

    token = servicio_auth.abrir_sesion(db, usuario, reemplaza=ctx_previo)
    servicio_auth.poner_cookie(response, request, seguridad.COOKIE_SESION, token)
    servicio_auth.borrar_cookie(response, request, seguridad.COOKIE_CSRF_ANONIMO)
    return {"usuario": usuario_publico(usuario),
            "csrf_token": seguridad.crear_csrf(seguridad.hash_token(token))}


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_session)):
    dependencias.verificar_origen(request)
    ctx, vinculo = dependencias.vinculo_actual(request, db)
    dependencias.verificar_csrf(request, vinculo)
    if ctx is not None:
        servicio_auth.revocar(db, ctx.sesion)
    respuesta = Response(status_code=204, headers={"Cache-Control": "no-store"})
    servicio_auth.borrar_cookie(respuesta, request, seguridad.COOKIE_SESION)
    return respuesta
