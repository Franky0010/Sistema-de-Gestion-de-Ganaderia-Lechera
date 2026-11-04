"""Primitivas de seguridad (HT-01). Solo usa la librería estándar.

- Contraseñas: hash adaptativo scrypt con sal propia; los parámetros viajan en el hash,
  así se pueden endurecer después sin invalidar las cuentas existentes.
- Tokens de sesión: aleatorios y opacos; en la base solo se guarda su SHA-256.
- CSRF: token firmado con HMAC y ligado a la sesión (o a una cookie anónima antes del login).
- Límite de intentos de login en memoria (un solo proceso; suficiente para el prototipo).
"""
import base64
import hashlib
import hmac
import os
import secrets
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

TIMEOUT_INACTIVIDAD = timedelta(minutes=30)  # PB-01 criterio 2
REFRESCO_ULTIMO_USO = timedelta(seconds=30)  # evita escribir en la BD en cada petición

COOKIE_SESION = "sesion"
COOKIE_CSRF_ANONIMO = "csrf_anonimo"


def ahora() -> datetime:
    """Instante actual en UTC, sin zona (SQLite guarda fechas sin zona).
    Siempre llamarla como seguridad.ahora() para que las pruebas puedan moverla."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# --- Contraseñas ------------------------------------------------------------
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


# --- Tokens -----------------------------------------------------------------
def generar_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# --- CSRF -------------------------------------------------------------------
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


# --- Límite de intentos -----------------------------------------------------
class LimitadorIntentos:
    def __init__(self, maximo: int = 5, ventana: timedelta = timedelta(minutes=15)):
        self.maximo = maximo
        self.ventana = ventana
        self._fallos = defaultdict(deque)
        self._lock = threading.Lock()

    def _purgar(self, clave, instante):
        fallos = self._fallos[clave]
        while fallos and instante - fallos[0] >= self.ventana:
            fallos.popleft()
        if not fallos:
            del self._fallos[clave]

    def segundos_de_espera(self, clave: str, instante: datetime) -> int:
        """0 si puede intentar; si no, segundos hasta que se libere un intento."""
        with self._lock:
            self._purgar(clave, instante)
            fallos = self._fallos.get(clave)
            if fallos and len(fallos) >= self.maximo:
                restante = fallos[0] + self.ventana - instante
                return max(1, int(restante.total_seconds()) + 1)
            return 0

    def registrar_fallo(self, clave: str, instante: datetime) -> None:
        with self._lock:
            self._fallos[clave].append(instante)

    def limpiar(self, clave: str) -> None:
        with self._lock:
            self._fallos.pop(clave, None)

    def reiniciar(self) -> None:
        with self._lock:
            self._fallos.clear()


limitador_login = LimitadorIntentos()
