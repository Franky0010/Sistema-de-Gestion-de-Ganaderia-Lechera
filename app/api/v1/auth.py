"""POST/GET /api/v1/auth/* (PB-01). Ver docs/contrato-api-sprint1.md."""
from fastapi import APIRouter, Depends, Request, Response

from app.api import cookies, dependencias
from app.core import seguridad
from app.core.excepciones import ErrorApi
from app.schemas.auth import LoginIn
from app.schemas.usuarios import usuario_publico
from app.services import auth as servicio_auth
from app.services import usuarios as servicio_usuarios
from app.services.puertos import UnidadDeTrabajo


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/csrf")
def obtener_csrf(request: Request, response: Response, uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    response.headers["Cache-Control"] = "no-store"
    # tocar=False: pedir un token no prolonga la sesión (no hay "mantener viva" artificial).
    ctx = servicio_auth.obtener_contexto(uow, request.cookies.get(seguridad.COOKIE_SESION), tocar=False)
    if ctx is not None:
        return {"csrf_token": seguridad.crear_csrf(ctx.hash_token)}
    anonimo = request.cookies.get(seguridad.COOKIE_CSRF_ANONIMO)
    if not anonimo:
        anonimo = seguridad.generar_token()
        cookies.poner_cookie(response, request, seguridad.COOKIE_CSRF_ANONIMO, anonimo)
    return {"csrf_token": seguridad.crear_csrf(anonimo)}


@router.get("/session")
def sesion_actual(response: Response, ctx=Depends(dependencias.sesion_requerida)):
    response.headers["Cache-Control"] = "no-store"
    return {"usuario": usuario_publico(ctx.usuario)}


@router.post("/login")
def login(datos: LoginIn, request: Request, response: Response, uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    response.headers["Cache-Control"] = "no-store"
    dependencias.verificar_origen(request)
    ctx_previo, vinculo = dependencias.vinculo_actual(request, uow)
    dependencias.verificar_csrf(request, vinculo)

    email = servicio_usuarios.normalizar_email(datos.email)
    ip = request.client.host if request.client else "desconocida"
    clave_limite = f"{ip}|{email}"
    espera = seguridad.limitador_login.segundos_de_espera(clave_limite, seguridad.ahora())
    if espera:
        raise ErrorApi(429, "LIMITE_SOLICITUDES", "Demasiados intentos. Espera antes de volver a intentar.",
                       headers={"Retry-After": str(espera)})

    usuario = servicio_auth.autenticar_credenciales(uow.usuarios, email, datos.password)
    if usuario is None:
        seguridad.limitador_login.registrar_fallo(clave_limite, seguridad.ahora())
        raise ErrorApi(401, "CREDENCIALES_INVALIDAS", "Correo o contraseña incorrectos.")
    seguridad.limitador_login.limpiar(clave_limite)
    if not usuario.activo:  # solo se revela tras verificar la contraseña
        raise ErrorApi(403, "CUENTA_INACTIVA", "Tu cuenta está desactivada. Contacta al administrador.")

    token = servicio_auth.abrir_sesion(uow, usuario, reemplaza=ctx_previo)
    cookies.poner_cookie(response, request, seguridad.COOKIE_SESION, token)
    cookies.borrar_cookie(response, request, seguridad.COOKIE_CSRF_ANONIMO)
    return {"usuario": usuario_publico(usuario),
            "csrf_token": seguridad.crear_csrf(seguridad.hash_token(token))}


@router.post("/logout")
def logout(request: Request, uow: UnidadDeTrabajo = Depends(dependencias.get_uow)):
    dependencias.verificar_origen(request)
    ctx, vinculo = dependencias.vinculo_actual(request, uow)
    dependencias.verificar_csrf(request, vinculo)
    if ctx is not None:
        servicio_auth.revocar(uow, ctx.sesion)
    respuesta = Response(status_code=204, headers={"Cache-Control": "no-store"})
    cookies.borrar_cookie(respuesta, request, seguridad.COOKIE_SESION)
    return respuesta
