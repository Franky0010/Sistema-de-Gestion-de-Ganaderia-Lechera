"""Pruebas de la PoC (sección 4.1 del documento de diseño).

1. Una creación válida deja un ordeño y su auditoría.
2. Dos solicitudes simultáneas con la misma clave, repetidas 50 veces sobre claves
   nuevas, producen una creación (201) y un conflicto (409).
3. Un fallo antes del commit deja cero registros nuevos.
4. Las cantidades inválidas no se persisten.
"""
import asyncio
import threading
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import func, select

from app import service
from app.database import crear_engine, crear_session_factory
from app.main import app, get_session
from app.models import Animal, Auditoria, Base, Ordeno

HEADERS = {"X-Usuario": "operario01"}
FECHA_BASE = date(2026, 10, 6)


@pytest.fixture
def entorno(tmp_path):
    # Archivo real (no :memory:): la concurrencia solo es representativa con varias conexiones.
    engine = crear_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    SessionLocal = crear_session_factory(engine)
    with SessionLocal() as s:
        animal = Animal(arete="V-001", nombre="Luna")
        s.add(animal)
        s.commit()
        animal_id = animal.id

    def _get_session():
        with SessionLocal() as s:
            yield s

    app.dependency_overrides[get_session] = _get_session
    yield SimpleNamespace(SessionLocal=SessionLocal, animal_id=animal_id)
    app.dependency_overrides.clear()
    engine.dispose()


def contar(SessionLocal, modelo) -> int:
    with SessionLocal() as s:
        return s.scalar(select(func.count()).select_from(modelo))


def payload(animal_id, fecha=FECHA_BASE, turno="mañana", prod="12.50", desc="0.50"):
    return {
        "animal_id": animal_id,
        "fecha": fecha.isoformat(),
        "turno": turno,
        "litros_producidos": prod,
        "litros_descartados": desc,
    }


# --- Prueba 1 ---------------------------------------------------------------
def test_creacion_valida_deja_un_ordeno_y_su_auditoria(entorno):
    with entorno.SessionLocal() as s:
        o = service.registrar_ordeno(
            s, animal_id=entorno.animal_id, fecha=FECHA_BASE, turno="mañana",
            litros_producidos=Decimal("12.50"), litros_descartados=Decimal("0.50"),
            usuario="operario01",
        )
        assert o.centilitros_producidos == 1250  # 12,50 L -> 1250 cL
    assert contar(entorno.SessionLocal, Ordeno) == 1
    assert contar(entorno.SessionLocal, Auditoria) == 1


def test_cero_litros_es_un_registro_valido(entorno):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            return await c.post("/ordenos", json=payload(entorno.animal_id, prod="0", desc="0"), headers=HEADERS)

    assert asyncio.run(run()).status_code == 201


# --- Prueba 2 ---------------------------------------------------------------
def test_dos_solicitudes_simultaneas_50_veces_una_creacion_y_un_conflicto(entorno):
    resultados = []

    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            for i in range(50):
                fecha = FECHA_BASE + timedelta(days=i)  # clave nueva en cada repetición
                cuerpo = payload(entorno.animal_id, fecha=fecha)
                r1, r2 = await asyncio.gather(
                    c.post("/ordenos", json=cuerpo, headers=HEADERS),
                    c.post("/ordenos", json=cuerpo, headers=HEADERS),
                )
                resultados.append(sorted([r1.status_code, r2.status_code]))

    asyncio.run(run())
    print(f"\n[PoC] repeticiones={len(resultados)} distintos_a_[201,409]="
          f"{sum(1 for r in resultados if r != [201, 409])}")
    assert all(r == [201, 409] for r in resultados)
    assert contar(entorno.SessionLocal, Ordeno) == 50
    assert contar(entorno.SessionLocal, Auditoria) == 50  # nada de auditorías huérfanas


def test_ocho_hilos_con_la_misma_clave_solo_uno_gana(entorno):
    barrera = threading.Barrier(8)
    resultados = []

    def intento():
        with entorno.SessionLocal() as s:
            barrera.wait()  # todos arrancan a la vez
            try:
                service.registrar_ordeno(
                    s, animal_id=entorno.animal_id, fecha=FECHA_BASE, turno="tarde",
                    litros_producidos=Decimal("10"), litros_descartados=Decimal("0"),
                    usuario="operario01",
                )
                resultados.append("ok")
            except service.DuplicadoError:
                resultados.append("duplicado")
            except service.BloqueoTransitorio:
                resultados.append("bloqueo")

    hilos = [threading.Thread(target=intento) for _ in range(8)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    print(f"\n[PoC] resultados 8 hilos: {sorted(resultados)}")
    assert resultados.count("ok") == 1
    assert resultados.count("duplicado") == 7
    assert contar(entorno.SessionLocal, Ordeno) == 1


# --- Prueba 3 ---------------------------------------------------------------
def test_fallo_antes_del_commit_deja_cero_registros(entorno, monkeypatch):
    def auditoria_que_falla(*_args, **_kwargs):
        raise RuntimeError("fallo simulado antes del commit")

    monkeypatch.setattr(service, "_insertar_auditoria", auditoria_que_falla)

    with entorno.SessionLocal() as s:
        with pytest.raises(RuntimeError):
            service.registrar_ordeno(
                s, animal_id=entorno.animal_id, fecha=FECHA_BASE, turno="mañana",
                litros_producidos=Decimal("12.50"), litros_descartados=Decimal("0.50"),
                usuario="operario01",
            )
    assert contar(entorno.SessionLocal, Ordeno) == 0  # el ordeño ya insertado se revirtió
    assert contar(entorno.SessionLocal, Auditoria) == 0


# --- Prueba 4 ---------------------------------------------------------------
@pytest.mark.parametrize(
    "prod, desc, motivo",
    [
        ("-1", "0", "producción negativa"),
        ("10", "-0.5", "descarte negativo"),
        ("10", "10.01", "descarte mayor que producción"),
        ("12.505", "0", "más de dos decimales"),
        ("abc", "0", "valor no numérico"),
        ("NaN", "0", "valor no finito"),
    ],
)
def test_cantidades_invalidas_no_se_persisten(entorno, prod, desc, motivo):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            return await c.post("/ordenos", json=payload(entorno.animal_id, prod=prod, desc=desc), headers=HEADERS)

    r = asyncio.run(run())
    assert r.status_code == 422, motivo
    assert contar(entorno.SessionLocal, Ordeno) == 0
    assert contar(entorno.SessionLocal, Auditoria) == 0


def test_animal_inexistente_devuelve_404_sin_escribir(entorno):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            return await c.post("/ordenos", json=payload(animal_id=9999), headers=HEADERS)

    assert asyncio.run(run()).status_code == 404
    assert contar(entorno.SessionLocal, Ordeno) == 0

@pytest.mark.parametrize("arete", ["", "   ", "\t\n"])
def test_arete_vacio_se_rechaza_sin_persistir(entorno, arete):
    inicial = contar(entorno.SessionLocal, Animal)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            return await c.post("/animales", json={"arete": arete})
    assert asyncio.run(run()).status_code == 422
    assert contar(entorno.SessionLocal, Animal) == inicial


def test_arete_normalizado_conserva_unicidad(entorno):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            nuevo = await c.post("/animales", json={"arete": "  v-002  "})
            repetido = await c.post("/animales", json={"arete": "V-002"})
            return nuevo, repetido
    nuevo, repetido = asyncio.run(run())
    assert nuevo.status_code == 201
    assert nuevo.json()["arete"] == "V-002"
    assert repetido.status_code == 409
    assert contar(entorno.SessionLocal, Animal) == 2


@pytest.mark.parametrize("cantidad", ["1E+10000", "92233720368547758.08", "1E-10000"])
@pytest.mark.parametrize("campo", ["litros_producidos", "litros_descartados"])
def test_cantidades_extremas_devuelven_422_sin_escribir(entorno, cantidad, campo):
    async def run():
        cuerpo = payload(entorno.animal_id)
        cuerpo[campo] = cantidad
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
            return await c.post("/ordenos", json=cuerpo, headers=HEADERS)
    assert asyncio.run(run()).status_code == 422
    assert contar(entorno.SessionLocal, Ordeno) == 0
    assert contar(entorno.SessionLocal, Auditoria) == 0


def test_limite_sqlite_se_persiste_sin_perder_precision(entorno):
    with entorno.SessionLocal() as s:
        o = service.registrar_ordeno(
            s, animal_id=entorno.animal_id, fecha=FECHA_BASE, turno="tarde",
            litros_producidos=Decimal("92233720368547758.07"),
            litros_descartados=Decimal("0"), usuario="operario01",
        )
        s.expire_all()
        assert s.get(Ordeno, o.id).centilitros_producidos == 9223372036854775807
    assert contar(entorno.SessionLocal, Auditoria) == 1
