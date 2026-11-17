"""Primitivas de seguridad (HT-01). Solo usa la librería estándar.

- Contraseñas: hash adaptativo scrypt con sal propia (contrasenas.py).
- Tokens de sesión: aleatorios y opacos; en la base solo se guarda su SHA-256 (tokens.py).
- CSRF: token firmado con HMAC y ligado a la sesión (csrf.py).
- Límite de intentos de login en memoria (limitador.py).

Este paquete expone todo en un solo punto: el resto del código usa `seguridad.<nombre>`.
`ahora` se reexporta aquí a propósito: siempre hay que llamarla como `seguridad.ahora()`
para que las pruebas puedan moverla (monkeypatch sobre este paquete).
"""
from app.core.reloj import ahora

from .constantes import COOKIE_CSRF_ANONIMO, COOKIE_SESION, REFRESCO_ULTIMO_USO, TIMEOUT_INACTIVIDAD
from .contrasenas import hashear_password, verificar_contra_ficticio, verificar_password
from .csrf import crear_csrf, validar_csrf
from .limitador import LimitadorIntentos, limitador_login
from .tokens import generar_token, hash_token

__all__ = [
    "ahora",
    "COOKIE_CSRF_ANONIMO", "COOKIE_SESION", "REFRESCO_ULTIMO_USO", "TIMEOUT_INACTIVIDAD",
    "hashear_password", "verificar_contra_ficticio", "verificar_password",
    "crear_csrf", "validar_csrf",
    "LimitadorIntentos", "limitador_login",
    "generar_token", "hash_token",
]
