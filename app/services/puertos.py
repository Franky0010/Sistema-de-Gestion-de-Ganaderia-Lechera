"""Puertos de persistencia: lo que los servicios necesitan de la base de datos.

Son interfaces (typing.Protocol) definidas AQUÍ, del lado de los servicios, y no en la capa de
datos: así la dependencia apunta hacia la abstracción (principio de inversión de dependencias).
Los servicios solo conocen estos contratos; app/repositories/ los implementa con SQLAlchemy y las
pruebas pueden implementarlos con objetos en memoria.

Contrato general:
- Los métodos de lectura no modifican nada.
- `agregar` solo registra la entidad en la unidad de trabajo; la escritura real ocurre en
  `flush()` o `commit()`, donde puede lanzarse ErrorIntegridad.
- Nada se confirma hasta que el servicio llama a `commit()`.
"""
from datetime import date, datetime
from typing import Protocol, Sequence

from app.models import Animal, Auditoria, EstadoAnimal, Ordeno, Sesion, Usuario


class RepositorioUsuarios(Protocol):
    def obtener(self, usuario_id: int) -> Usuario | None:
        """Usuario por id, o None si no existe."""
        ...

    def obtener_por_email(self, email: str) -> Usuario | None:
        """Usuario por correo ya normalizado (minúsculas), o None."""
        ...

    def agregar(self, usuario: Usuario) -> None:
        """Registra un usuario nuevo en la unidad de trabajo."""
        ...

    def buscar(self, texto: str, page: int, page_size: int) -> tuple[Sequence[Usuario], int]:
        """Página de usuarios ordenada por id y total que cumple el filtro.

        `texto` busca (sin distinguir mayúsculas) en nombre y correo; vacío o solo espacios
        significa sin filtro. El total se calcula ANTES de paginar."""
        ...

    def contar_administradores_activos(self) -> int:
        """Cuántos usuarios activos con rol administrador existen."""
        ...


class RepositorioSesiones(Protocol):
    def agregar(self, sesion: Sesion) -> None:
        """Registra una sesión nueva."""
        ...

    def obtener_con_usuario(self, hash_token: str) -> tuple[Sesion, Usuario] | None:
        """Sesión y su dueño a partir del hash del token, o None si no hay coincidencia."""
        ...

    def revocar_activas_de(self, usuario_id: int, instante: datetime) -> None:
        """Marca como revocadas todas las sesiones aún activas de un usuario."""
        ...


class RepositorioAnimales(Protocol):
    def obtener(self, animal_id: int) -> Animal | None:
        """Animal por id, o None si no existe."""
        ...

    def agregar(self, animal: Animal) -> None:
        """Registra un animal nuevo."""
        ...

    def incrementar_version(self, animal_id: int, version_esperada: int) -> bool:
        """Compara y actualiza la versión en una sola operación atómica.

        Devuelve True si la versión coincidía y se incrementó; False si alguien más ya la
        había cambiado (control de concurrencia optimista)."""
        ...


class RepositorioEstados(Protocol):
    def agregar(self, estado: EstadoAnimal) -> None:
        """Registra un cambio de estado nuevo."""
        ...

    def vigente_en(self, animal_id: int, fecha: date) -> EstadoAnimal | None:
        """Estado vigente del animal en una fecha: el último con fecha_desde <= fecha."""
        ...

    def siguiente_a(self, animal_id: int, fecha: date) -> EstadoAnimal | None:
        """Primer estado con fecha_desde posterior a la fecha dada, o None."""
        ...

    def listar(self, animal_id: int, page: int, page_size: int) -> tuple[Sequence[EstadoAnimal], int]:
        """Página del historial (más antiguo primero) y total de cambios del animal."""
        ...

    def tiene_estado(self, animal_id: int, estado: str) -> bool:
        """True si el animal tuvo alguna vez ese estado."""
        ...

    def existe_cambio_en(self, animal_id: int, fecha: date) -> bool:
        """True si ya hay un cambio de estado registrado con esa fecha_desde."""
        ...


class RepositorioOrdenos(Protocol):
    def agregar(self, ordeno: Ordeno) -> None:
        """Registra un ordeño nuevo."""
        ...

    def hay_vigentes(self, animal_id: int, desde: date, hasta: date | None = None) -> bool:
        """True si hay ordeños no anulados con fecha >= desde (y < hasta, si se indica)."""
        ...


class RepositorioAuditoria(Protocol):
    def agregar(self, registro: Auditoria) -> None:
        """Registra una entrada de auditoría (solo inserción; nunca se modifica)."""
        ...

    def buscar(self, *, entidad: str | None, entidad_id: int | None, accion: str | None,
               usuario_id: int | None, page: int, page_size: int) -> tuple[Sequence[Auditoria], int]:
        """Página de auditoría (más reciente primero) y total, con filtros opcionales."""
        ...


class UnidadDeTrabajo(Protocol):
    """Una transacción lógica: agrupa los repositorios y decide cuándo se confirma.

    Cada operación de escritura de un servicio es UNA unidad de trabajo: o se confirma
    completa con commit() o se descarta completa con rollback()."""

    usuarios: RepositorioUsuarios
    sesiones: RepositorioSesiones
    animales: RepositorioAnimales
    estados: RepositorioEstados
    ordenos: RepositorioOrdenos
    auditoria: RepositorioAuditoria

    def flush(self) -> None:
        """Envía a la base lo pendiente sin confirmar (asigna ids y activa restricciones).

        Puede lanzar ErrorIntegridad o BaseDeDatosOcupada."""
        ...

    def commit(self) -> None:
        """Confirma la transacción. Puede lanzar ErrorIntegridad o BaseDeDatosOcupada."""
        ...

    def rollback(self) -> None:
        """Descarta todo lo no confirmado."""
        ...

    def refrescar(self, entidad: object) -> None:
        """Recarga una entidad desde la base (tras un commit, para ver valores reales)."""
        ...
