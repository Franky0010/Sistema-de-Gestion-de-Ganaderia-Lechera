"""Reglas de negocio de animales y estados (PB-03, base de HT-02).

Cada operación de escritura es UNA transacción: animal/estado + versión + auditoría se
confirman juntos o se revierten juntos. Todo lo que puede fallar por reglas se valida antes
de escribir; lo que depende de la concurrencia (arete único, un cambio por día, versión) lo
decide la base de datos dentro de la transacción.

- fechas.py:        fecha de negocio (America/Bogota).
- validaciones.py:  reglas de entrada del alta.
- serializadores.py: representación pública y snapshots de auditoría.
- consultas.py:     lecturas (detalle, historial); el estado vigente lo resuelve el repositorio.
- comandos.py:      escrituras (alta y cambio de estado).
"""
from .comandos import MENSAJE_ESTADOS, MOTIVO_ALTA, cambiar_estado, crear_animal
from .consultas import animal_publico, listar_estados, obtener_animal
from .fechas import hoy
from .serializadores import estado_publico, snapshot
from .validaciones import ESTADOS_ALTA

__all__ = [
    "ESTADOS_ALTA", "MENSAJE_ESTADOS", "MOTIVO_ALTA",
    "animal_publico", "cambiar_estado", "crear_animal", "estado_publico",
    "hoy", "listar_estados", "obtener_animal", "snapshot",
]
