"""Validación y normalización de los datos de una cuenta."""
import re

from app.core.excepciones import ErrorApi


ROLES = ("administrador", "operario", "propietario")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalizar_email(valor: str) -> str:
    return valor.strip().lower()


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
