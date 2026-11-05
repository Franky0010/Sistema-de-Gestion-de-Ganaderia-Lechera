"""Reproduce Sprint 1 against the real FastAPI app and an isolated SQLite database.

Run with --verify for HTTP assertions or --serve for the live browser review.
All accounts and records are synthetic. The temporary database is removed on exit.
This does not demonstrate production HTTPS, performance targets or future modules.
"""
import argparse
from datetime import timedelta
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
PASSWORD = "Sprint1-Demo2026"
ACCOUNTS = {
    "admin": ("Administración Demo", "administrador"),
    "operario": ("Operario Demo", "operario"),
    "propietario": ("Propietario Demo", "propietario"),
}


def expect(response, status, code=None):
    """Fail with actionable HTTP evidence instead of silently continuing."""
    if response.status_code != status:
        raise AssertionError(f"Expected {status}, got {response.status_code}: {response.text}")
    body = response.json() if response.content else None
    if code and body.get("error", {}).get("code") != code:
        raise AssertionError(f"Expected {code}: {body}")
    return body


def write(client, method, path, body=None, status=200, code=None):
    token = expect(client.get("/api/v1/auth/csrf"), 200)["csrf_token"]
    response = client.request(method, path, json=body, headers={"X-CSRF-Token": token})
    return expect(response, status, code)


def login(client, account="admin"):
    return write(client, "POST", "/api/v1/auth/login", {
        "email": f"{account}@demo.local", "password": PASSWORD,
    })


def animal_data(today, arete, name):
    return {
        "arete": arete, "nombre": name, "raza": "Holstein",
        "procedencia": "Datos sintéticos de la demostración",
        "fecha_ingreso": (today - timedelta(days=2)).isoformat(),
        "fecha_nacimiento": None, "edad_estimada_meses": 36,
        "estado_inicial": "en_produccion",
    }


def seed(client, session_factory, services, today):
    """Use application services and HTTP routes to prepare reproducible records."""
    with session_factory() as db:
        for account, (name, role) in ACCOUNTS.items():
            services.crear_usuario(db, None, nombre=name, email=f"{account}@demo.local",
                                  password=PASSWORD, rol=role)
    login(client)
    for arete, name in [("DEMO-001", "Luna"), ("DEMO-002", "Estrella")]:
        write(client, "POST", "/api/v1/animales", animal_data(today, arete, name), 201)
    write(client, "POST", "/api/v1/auth/logout", status=204)


def verify(client, session_factory, today):
    """Follow the planning order and print the evidence for each story."""
    from sqlalchemy import select
    from app.models import Sesion
    from app import seguridad

    print("HT-01 | CSRF and protected routes")
    expect(client.get("/api/v1/usuarios"), 401)
    expect(client.post("/api/v1/auth/login", json={
        "email": "admin@demo.local", "password": PASSWORD,
    }), 403, "CSRF_INVALIDO")

    print("PB-01 | Login, logout and 30-minute inactivity expiration")
    write(client, "POST", "/api/v1/auth/login", {
        "email": "admin@demo.local", "password": "incorrecta",
    }, 401, "CREDENCIALES_INVALIDAS")
    login(client)
    expect(client.get("/api/v1/auth/session"), 200)
    # Move only this synthetic session's last-use timestamp to avoid a 31-minute wait.
    token_hash = seguridad.hash_token(client.cookies.get("sesion"))
    with session_factory() as db:
        session = db.scalar(select(Sesion).where(Sesion.hash_token == token_hash))
        session.ultimo_uso = seguridad.ahora() - timedelta(minutes=31)
        db.commit()
    expect(client.get("/api/v1/auth/session"), 401, "SESION_EXPIRADA")
    login(client)
    write(client, "POST", "/api/v1/auth/logout", status=204)
    expect(client.get("/api/v1/usuarios"), 401)
    login(client)

    print("PB-02 | Required fields, duplicate email, edit and deactivate")
    write(client, "POST", "/api/v1/usuarios", {}, 422)
    data = {"nombre": "Usuario Temporal", "email": "temporal@demo.local",
            "password": PASSWORD, "rol": "operario"}
    user = write(client, "POST", "/api/v1/usuarios", data, 201)
    write(client, "POST", "/api/v1/usuarios", {**data, "email": "TEMPORAL@demo.local"},
          409, "EMAIL_DUPLICADO")
    write(client, "PATCH", f"/api/v1/usuarios/{user['id']}", {"rol": "propietario"})
    write(client, "PATCH", f"/api/v1/usuarios/{user['id']}", {"activo": False}, 422)
    write(client, "PATCH", f"/api/v1/usuarios/{user['id']}", {
        "activo": False, "motivo": "Cuenta sintética finalizada",
    })
    write(client, "POST", "/api/v1/auth/logout", status=204)
    write(client, "POST", "/api/v1/auth/login", {
        "email": data["email"], "password": PASSWORD,
    }, 403, "CUENTA_INACTIVA")
    login(client)

    print("PB-03 | Animal registration, normalization, duplicates and dates")
    data = animal_data(today, " demo-003 ", "Lucero")
    animal = write(client, "POST", "/api/v1/animales", data, 201)
    assert animal["arete"] == "DEMO-003"
    write(client, "POST", "/api/v1/animales", data, 409, "ARETE_DUPLICADO")
    write(client, "POST", "/api/v1/animales", {
        **data, "arete": "FUTURO", "fecha_ingreso": (today + timedelta(days=1)).isoformat(),
    }, 422)

    print("PB-04 | State change, retained history and incompatible milking")
    path = f"/api/v1/animales/{animal['id']}/estados"
    change = {"estado": "seco", "fecha_desde": today.isoformat(),
              "motivo": "Fin del período productivo de prueba", "version": animal["version"]}
    changed = write(client, "POST", path, change, 201)
    history = expect(client.get(path), 200)
    assert history["total"] == 2
    write(client, "POST", path, {**change, "estado": "no_productivo",
          "version": changed["animal"]["version"]}, 409)
    # The legacy milking route supplies a fixture; it is not claimed as completed PB-07.
    expect(client.post("/ordenos", headers={"X-Usuario": "demo-fixture"}, json={
        "animal_id": 1, "fecha": today.isoformat(), "turno": "mañana",
        "litros_producidos": "10.00", "litros_descartados": "0.00",
    }), 201)
    first = expect(client.get("/api/v1/animales/1"), 200)
    write(client, "POST", "/api/v1/animales/1/estados", {
        **change, "version": first["version"],
    }, 409, "ESTADO_INCOMPATIBLE")

    print("PB-11 | Operario and Propietario cannot manage users or create animals")
    for role in ("operario", "propietario"):
        write(client, "POST", "/api/v1/auth/logout", status=204)
        login(client, role)
        expect(client.get("/api/v1/animales"), 200)
        expect(client.get("/api/v1/usuarios"), 403, "SIN_PERMISO")
        write(client, "POST", "/api/v1/animales", data, 403, "SIN_PERMISO")
    write(client, "POST", "/api/v1/auth/logout", status=204)
    login(client)

    print("HT-02 | Audit trail and unchanged data after rejected writes")
    audit = expect(client.get("/api/v1/auditoria"), 200)
    assert audit["total"] > 0
    before = expect(client.get("/api/v1/animales"), 200)["total"]
    audit_before = audit["total"]
    write(client, "POST", "/api/v1/animales", data, 409, "ARETE_DUPLICADO")
    assert expect(client.get("/api/v1/animales"), 200)["total"] == before
    assert expect(client.get("/api/v1/auditoria"), 200)["total"] == audit_before
    print("PASS | Seven sections verified. See docs/sprint-review-1.md for acceptance limits.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="Run the seven HTTP demonstration sections")
    mode.add_argument("--serve", action="store_true", help="Serve seeded API on port 8000 for the live UI demo")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="ganaderia-review-") as folder:
        os.environ["POC_DATABASE_URL"] = "sqlite:///" + (Path(folder) / "demo.db").as_posix()
        os.environ["POC_ORIGENES_PERMITIDOS"] = "http://localhost:5187,http://127.0.0.1:5187"
        os.environ["POC_COOKIE_SECURE"] = "0"
        from fastapi.testclient import TestClient
        from app.main import app
        from app.db_deps import engine, SessionLocal
        from app import servicio_animales, servicio_usuarios
        try:
            with TestClient(app) as client:
                today = servicio_animales.hoy()
                seed(client, SessionLocal, servicio_usuarios, today)
                if not args.serve:
                    verify(client, SessionLocal, today)
            if args.serve:
                import uvicorn
                print("Synthetic demo accounts: admin@demo.local, operario@demo.local, propietario@demo.local")
                print(f"Demo-only password: {PASSWORD}")
                print("Start frontend on localhost:5187. Ctrl+C removes this temporary database.")
                uvicorn.run(app, host="127.0.0.1", port=8000)
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
