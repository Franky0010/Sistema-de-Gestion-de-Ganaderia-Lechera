"""Política de sesión y nombres de cookies."""
from datetime import timedelta


TIMEOUT_INACTIVIDAD = timedelta(minutes=30)  # PB-01 criterio 2
REFRESCO_ULTIMO_USO = timedelta(seconds=30)  # evita escribir en la BD en cada petición
COOKIE_SESION = "sesion"
COOKIE_CSRF_ANONIMO = "csrf_anonimo"
