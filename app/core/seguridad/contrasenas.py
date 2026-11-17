"""Contraseñas: hash adaptativo scrypt con sal propia; los parámetros viajan en el hash,
así se pueden endurecer después sin invalidar las cuentas existentes."""
import base64
import hashlib
import hmac
import os
import secrets


_N, _R, _P = 2**14, 8, 1
_MAXMEM = 64 * 1024 * 1024


def _b64(datos: bytes) -> str:
    return base64.b64encode(datos).decode("ascii")


def hashear_password(password: str) -> str:
    sal = os.urandom(16)
    derivada = hashlib.scrypt(
        password.encode("utf-8"), salt=sal, n=_N, r=_R, p=_P, maxmem=_MAXMEM, dklen=32
    )
    return "$".join(["scrypt", str(_N), str(_R), str(_P), _b64(sal), _b64(derivada)])


def verificar_password(password: str, almacenado: str) -> bool:
    try:
        algoritmo, n, r, p, sal, esperado = almacenado.split("$")
        if algoritmo != "scrypt":
            return False
        esperado_bytes = base64.b64decode(esperado)
        derivada = hashlib.scrypt(
            password.encode("utf-8"), salt=base64.b64decode(sal),
            n=int(n), r=int(r), p=int(p), maxmem=_MAXMEM, dklen=len(esperado_bytes),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derivada, esperado_bytes)


_hash_ficticio = None


def verificar_contra_ficticio(password: str) -> None:
    """Gasta el mismo tiempo que una verificación real cuando el correo no existe,
    para que el tiempo de respuesta no revele si la cuenta existe."""
    global _hash_ficticio
    if _hash_ficticio is None:
        _hash_ficticio = hashear_password(secrets.token_hex(16))
    verificar_password(password, _hash_ficticio)
