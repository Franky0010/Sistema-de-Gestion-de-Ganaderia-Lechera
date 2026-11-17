"""Reglas de negocio de cuentas de usuario (PB-02, HT-02): validación, unicidad de correo,
desactivación lógica y auditoría en la misma transacción.

- validaciones.py: reglas de entrada (correo, contraseña, rol, nombre).
- comandos.py:     escrituras (crear, actualizar) con auditoría en la misma transacción.
- consultas.py:    lecturas (listado paginado y búsqueda).
"""
from .comandos import actualizar_usuario, crear_usuario, snapshot
from .consultas import listar_usuarios, obtener_usuario
from .validaciones import ROLES, normalizar_email

__all__ = [
    "ROLES", "actualizar_usuario", "crear_usuario", "listar_usuarios", "normalizar_email",
    "obtener_usuario", "snapshot",
]
