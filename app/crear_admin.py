"""Crea el primer administrador (sin él nadie puede iniciar sesión).

    python -m app.crear_admin --email admin@finca.co --nombre "Administrador"

La contraseña se pide por consola (o POC_ADMIN_PASSWORD para automatizar)."""
import argparse
import getpass
import os
import sys

from . import auditoria, migraciones, servicio_usuarios
from .db_deps import SessionLocal, engine
from .errores import ErrorApi
from .models import Base


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Crear el administrador inicial")
    parser.add_argument("--email", required=True)
    parser.add_argument("--nombre", required=True)
    args = parser.parse_args(argv)

    password = os.getenv("POC_ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Contraseña (8 a 128 caracteres): ")
        if password != getpass.getpass("Repite la contraseña: "):
            print("Las contraseñas no coinciden.")
            return 1

    migraciones.migrar(engine)
    Base.metadata.create_all(engine)
    auditoria.proteger_auditoria(engine)
    migraciones.proteger_historial(engine)
    with SessionLocal() as db:
        try:
            usuario = servicio_usuarios.crear_usuario(
                db, None, nombre=args.nombre, email=args.email, password=password, rol="administrador")
        except ErrorApi as error:
            print(f"No se creó el administrador: {error.message} {error.fields}")
            return 1
    print(f"Administrador creado: {usuario.email}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
