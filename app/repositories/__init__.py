"""Adaptadores de persistencia: implementan con SQLAlchemy los puertos de app/services/puertos.py.

Es la ÚNICA capa (junto con app/db/) que escribe consultas SQL. Los servicios no la importan:
reciben una UnidadDeTrabajo ya construida (ver app/api/dependencias/unidad_de_trabajo.py).
"""
from .animales import RepositorioAnimalesSQL
from .auditoria import RepositorioAuditoriaSQL
from .estados import RepositorioEstadosSQL
from .ordenos import RepositorioOrdenosSQL
from .sesiones import RepositorioSesionesSQL
from .unidad_de_trabajo import UnidadDeTrabajoSQL
from .usuarios import RepositorioUsuariosSQL

__all__ = [
    "RepositorioAnimalesSQL", "RepositorioAuditoriaSQL", "RepositorioEstadosSQL",
    "RepositorioOrdenosSQL", "RepositorioSesionesSQL", "RepositorioUsuariosSQL",
    "UnidadDeTrabajoSQL",
]
