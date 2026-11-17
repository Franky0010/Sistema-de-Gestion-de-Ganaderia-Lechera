"""Tokens de sesión: aleatorios y opacos; en la base solo se guarda su SHA-256."""
import hashlib
import secrets


def generar_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
