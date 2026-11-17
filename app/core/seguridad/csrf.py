"""CSRF: token firmado con HMAC y ligado a la sesión (o a una cookie anónima antes del login)."""
import hashlib
import hmac
import os
import secrets


_clave = None


def _clave_secreta() -> bytes:
    """POC_SECRET_KEY debe venir del entorno (nunca del repositorio). Si falta se genera
    una clave aleatoria: los tokens CSRF dejan de valer al reiniciar y no sirve con
    varios procesos."""
    global _clave
    if _clave is None:
        valor = os.getenv("POC_SECRET_KEY")
        _clave = valor.encode("utf-8") if valor else secrets.token_bytes(32)
    return _clave


def _firmar(vinculo: str, nonce: str) -> str:
    return hmac.new(_clave_secreta(), f"{vinculo}|{nonce}".encode("utf-8"), hashlib.sha256).hexdigest()


def crear_csrf(vinculo: str) -> str:
    nonce = secrets.token_urlsafe(16)
    return f"{nonce}.{_firmar(vinculo, nonce)}"


def validar_csrf(token, vinculo) -> bool:
    if not token or not vinculo or "." not in token:
        return False
    nonce, _, firma = token.partition(".")
    return hmac.compare_digest(firma, _firmar(vinculo, nonce))
