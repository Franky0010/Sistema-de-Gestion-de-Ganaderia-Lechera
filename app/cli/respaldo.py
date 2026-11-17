"""Respaldo y restauración de la base SQLite desde la línea de comandos.

    python -m app.cli.respaldo crear [--carpeta respaldos] [--conservar 14]
    python -m app.cli.respaldo restaurar respaldos/poc-20261104-020000.db

La lógica está en app/db/respaldo.py. Restaurar: detén uvicorn primero.
"""
import argparse
import sys
from pathlib import Path

from app.db.respaldo import crear_respaldo, restaurar, ruta_base


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Respaldo y restauración de la base de datos")
    sub = parser.add_subparsers(dest="orden", required=True)
    c = sub.add_parser("crear")
    c.add_argument("--carpeta", default="respaldos")
    c.add_argument("--conservar", type=int, default=14)
    r = sub.add_parser("restaurar")
    r.add_argument("archivo")
    args = parser.parse_args(argv)
    try:
        if args.orden == "crear":
            print(f"Respaldo creado: {crear_respaldo(ruta_base(), Path(args.carpeta), args.conservar)}")
        else:
            segundos = restaurar(Path(args.archivo), ruta_base())
            print(f"Base restaurada en {segundos:.2f} s.")
    except (RuntimeError, FileNotFoundError) as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
