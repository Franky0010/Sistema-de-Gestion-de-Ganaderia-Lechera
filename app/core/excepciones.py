"""Excepciones compartidas de la aplicación.

- ErrorApi: error de negocio con código y mensaje del contrato; la capa HTTP
  (app/api/manejadores_errores.py) lo traduce al formato de error de la API.
- ErrorIntegridad: el motor de datos rechazó una escritura por una restricción.
- BaseDeDatosOcupada: la base siguió bloqueada tras la espera acotada.

Las dos últimas las lanza la capa de repositorios al traducir los errores del driver, de modo
que los servicios no necesitan importar SQLAlchemy para reaccionar a ellos.
"""


class ErrorApi(Exception):
    def __init__(self, status: int, code: str, message: str, fields=None, headers=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.fields = fields or {}
        self.headers = headers


class ErrorIntegridad(Exception):
    """Una restricción de la base (única, clave foránea o CHECK) rechazó la escritura.

    `detalle` conserva el texto original del motor (p. ej. "UNIQUE constraint failed:
    animal.arete"); el servicio lo inspecciona para saber qué regla se violó."""

    def __init__(self, detalle: str):
        super().__init__(detalle)
        self.detalle = detalle


class BaseDeDatosOcupada(Exception):
    """La base siguió bloqueada tras la espera acotada; el cliente puede reintentar."""
