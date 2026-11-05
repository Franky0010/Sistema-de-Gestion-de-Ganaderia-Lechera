"""Formato de error compartido del contrato: {"error": {"code", "message", "fields"}}."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError


class ErrorApi(Exception):
    def __init__(self, status: int, code: str, message: str, fields=None, headers=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.fields = fields or {}
        self.headers = headers


def _respuesta(status, code, message, fields=None, headers=None):
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "fields": fields or {}}},
        headers=headers,
    )


def instalar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorApi)
    async def _error_api(_request: Request, exc: ErrorApi):
        return _respuesta(exc.status, exc.code, exc.message, exc.fields, exc.headers)

    @app.exception_handler(RequestValidationError)
    async def _validacion(_request: Request, exc: RequestValidationError):
        campos = {}
        for error in exc.errors():
            campo = str(error["loc"][-1]) if error.get("loc") else "cuerpo"
            campos[campo] = "Este campo es obligatorio." if error.get("type") == "missing" else "Valor no válido."
        return _respuesta(422, "VALIDACION", "Revisa los campos indicados.", campos)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_request: Request, exc: StarletteHTTPException):
        codigos = {404: "NO_ENCONTRADO", 405: "METODO_NO_PERMITIDO"}
        mensaje = exc.detail if isinstance(exc.detail, str) else "No se pudo completar la operación."
        return _respuesta(exc.status_code, codigos.get(exc.status_code, "HTTP_ERROR"), mensaje,
                          headers=getattr(exc, "headers", None))

    @app.exception_handler(IntegrityError)
    async def _integridad(_request: Request, exc: IntegrityError):
        """Red de seguridad: una violación de la BD que ningún servicio tradujo no debe ser un 500."""
        texto = str(exc.orig).upper()
        if "FOREIGN KEY" in texto:
            return _respuesta(422, "REFERENCIA_INVALIDA", "El registro al que se hace referencia no existe.")
        if "UNIQUE" in texto:
            return _respuesta(409, "DUPLICADO", "Ya existe un registro con esos datos.")
        if "CHECK" in texto:
            return _respuesta(422, "VALIDACION", "Los valores enviados no son coherentes.")
        return _respuesta(409, "CONFLICTO_DATOS", "No se pudo guardar por un conflicto con los datos existentes.")
