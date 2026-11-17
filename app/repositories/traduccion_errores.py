"""Traduce los errores del driver a las excepciones de dominio de app/core/excepciones.py."""
import functools

from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.excepciones import BaseDeDatosOcupada, ErrorIntegridad


def traducir_errores(funcion):
    """Decorador para métodos que tocan la base.

    - IntegrityError  -> ErrorIntegridad (conserva el texto original del motor).
    - OperationalError "locked" -> BaseDeDatosOcupada.
    - Cualquier otro error pasa sin cambios.
    """
    @functools.wraps(funcion)
    def envoltura(*args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        except IntegrityError as exc:
            raise ErrorIntegridad(str(exc.orig)) from exc
        except OperationalError as exc:
            if "locked" in str(exc.orig).lower():
                raise BaseDeDatosOcupada(str(exc.orig)) from exc
            raise
    return envoltura
