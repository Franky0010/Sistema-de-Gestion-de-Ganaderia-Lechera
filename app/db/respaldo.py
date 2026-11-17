"""Respaldo y restauración de la base SQLite (RNF06: respaldo diario, restauración < 30 min).

- El respaldo usa la API de backup de SQLite: es consistente aunque el servidor esté escribiendo.
- Cada respaldo se verifica con PRAGMA integrity_check antes de darlo por bueno.
- Restaurar: detén uvicorn primero. Se guarda una copia 'poc.db.previo' de lo que había.

La línea de comandos está en app/cli/respaldo.py.
"""
import os
import shutil
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import make_url


def ruta_base() -> Path:
    return Path(make_url(os.getenv("POC_DATABASE_URL", "sqlite:///poc.db")).database)


def _integridad_ok(ruta: Path) -> bool:
    con = sqlite3.connect(ruta)
    try:
        return con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        con.close()


def crear_respaldo(origen: Path, carpeta: Path, conservar: int = 14) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"poc-{datetime.now():%Y%m%d-%H%M%S}.db"
    con_origen, con_destino = sqlite3.connect(origen), sqlite3.connect(destino)
    try:
        con_origen.backup(con_destino)
        con_destino.execute("PRAGMA journal_mode=DELETE")  # un solo archivo, sin -wal/-shm
    finally:
        con_destino.close()
        con_origen.close()
    if not _integridad_ok(destino):
        destino.unlink()
        raise RuntimeError("El respaldo quedó dañado y se descartó.")
    for viejo in sorted(carpeta.glob("poc-*.db"))[:-conservar]:  # rotación
        viejo.unlink()
    return destino


def restaurar(respaldo: Path, destino: Path) -> float:
    """Devuelve los segundos que tardó (el objetivo es menos de 30 minutos)."""
    inicio = time.perf_counter()
    if not respaldo.is_file():
        raise FileNotFoundError(f"No existe el respaldo {respaldo}")
    if not _integridad_ok(respaldo):
        raise RuntimeError("El respaldo está dañado; no se restauró nada.")
    if destino.exists():
        shutil.copy2(destino, destino.with_name(destino.name + ".previo"))
    for sufijo in ("-wal", "-shm"):
        Path(str(destino) + sufijo).unlink(missing_ok=True)
    shutil.copy2(respaldo, destino)
    return time.perf_counter() - inicio
