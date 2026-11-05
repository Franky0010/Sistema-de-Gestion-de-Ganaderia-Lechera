"""S1-HT-02-BASE: transacciones, restricciones y auditoría de animales y estados (PB-03)."""
import json
import threading
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app import auditoria, migraciones, servicio_usuarios
from app.database import crear_engine
from app.main import app
from app.models import Animal, Auditoria, Base, EstadoAnimal, Ordeno
from app.servicio_animales import hoy

from .conftest import CLAVE, cliente_con_sesion, escribir, iniciar_sesion, pedir_csrf

HOY = hoy()
INGRESO = HOY - timedelta(days=30)


def nuevo(**cambios):
    base = {"arete": "V-025", "nombre": "Luna", "raza": "Holstein", "procedencia": "Compra",
            "fecha_ingreso": INGRESO.isoformat(), "fecha_nacimiento": "2022-03-15",
            "edad_estimada_meses": None, "estado_inicial": "en_produccion"}
    return {**base, **cambios}


def cambio(**cambios):
    base = {"estado": "seco", "fecha_desde": (HOY - timedelta(days=10)).isoformat(),
            "motivo": "Fin del período productivo", "version": 1}
    return {**base, **cambios}


def crear(admin, **cambios):
    r = escribir(admin, "POST", "/api/v1/animales", nuevo(**cambios))
    assert r.status_code == 201, r.text
    return r.json()


def totales(api):
    return api.contar(Animal), api.contar(EstadoAnimal), api.contar(Auditoria)


def codigo(r):
    return r.status_code, r.json()["error"]["code"]


# ---------- alta (PB-03) ----------

def test_alta_valida_guarda_animal_estado_inicial_y_auditoria(api):
    admin = cliente_con_sesion(api, "admin")
    antes = api.contar(Auditoria)
    a = crear(admin)
    assert (a["arete"], a["estado_actual"], a["estado_desde"], a["version"]) == ("V-025", "en_produccion", INGRESO.isoformat(), 1)
    assert api.filas(select(EstadoAnimal.estado, EstadoAnimal.fecha_desde, EstadoAnimal.responsable_id)) == [("en_produccion", INGRESO, 1)]
    fila = api.consultar(select(Auditoria).where(Auditoria.entidad == "animal", Auditoria.entidad_id == a["id"]))[0]
    assert (fila.accion, fila.usuario, fila.usuario_id, fila.antes) == ("crear", "admin@finca.co", 1, None)
    assert fila.momento is not None and api.contar(Auditoria) == antes + 1
    despues = json.loads(fila.despues)
    assert (despues["arete"], despues["estado"], despues["fecha_ingreso"]) == ("V-025", "en_produccion", INGRESO.isoformat())


def test_arete_se_normaliza_y_no_se_repite_ni_se_reutiliza(api):
    admin = cliente_con_sesion(api, "admin")
    assert crear(admin, arete="  v-030  ")["arete"] == "V-030"
    antes = totales(api)
    r = escribir(admin, "POST", "/api/v1/animales", nuevo(arete="V-030"))
    assert codigo(r) == (409, "ARETE_DUPLICADO") and "arete" in r.json()["error"]["fields"]
    assert totales(api) == antes  # sin animal, sin estado y sin auditoría huérfanos


@pytest.mark.parametrize("cambios, campo", [
    ({"fecha_ingreso": (HOY + timedelta(days=1)).isoformat()}, "fecha_ingreso"),
    ({"fecha_nacimiento": (HOY + timedelta(days=1)).isoformat()}, "fecha_nacimiento"),
    ({"fecha_nacimiento": (INGRESO + timedelta(days=1)).isoformat()}, "fecha_nacimiento"),
    ({"edad_estimada_meses": 12}, "fecha_nacimiento"),                      # ambos
    ({"fecha_nacimiento": None}, "fecha_nacimiento"),                        # ninguno
    ({"fecha_nacimiento": None, "edad_estimada_meses": -1}, "edad_estimada_meses"),
    ({"estado_inicial": "fuera_del_hato"}, "estado_inicial"),
    ({"raza": "  "}, "raza"),
    ({"arete": "X" * 41}, "arete"),
])
def test_alta_invalida_se_rechaza_sin_escribir_nada(api, cambios, campo):
    admin = cliente_con_sesion(api, "admin")
    antes = totales(api)
    r = escribir(admin, "POST", "/api/v1/animales", nuevo(**cambios))
    assert codigo(r) == (422, "VALIDACION") and campo in r.json()["error"]["fields"]
    assert totales(api) == antes


def test_solo_el_administrador_escribe_y_se_exige_csrf(api):
    antes = totales(api)
    operario = cliente_con_sesion(api, "operario")
    assert codigo(escribir(operario, "POST", "/api/v1/animales", nuevo())) == (403, "SIN_PERMISO")
    propietario = cliente_con_sesion(api, "propietario")
    assert codigo(escribir(propietario, "POST", "/api/v1/animales", nuevo())) == (403, "SIN_PERMISO")
    admin = cliente_con_sesion(api, "admin")
    assert codigo(admin.post("/api/v1/animales", json=nuevo())) == (403, "CSRF_INVALIDO")
    assert totales(api) == antes
    a = crear(admin)
    assert operario.get(f"/api/v1/animales/{a['id']}").status_code == 200  # los 3 roles leen
    assert api.nuevo_cliente().get(f"/api/v1/animales/{a['id']}").status_code == 401


def test_si_falla_la_auditoria_el_alta_se_revierte_completa(api, monkeypatch):
    admin = cliente_con_sesion(api, "admin")
    antes = totales(api)

    def falla(*_a, **_k):
        raise RuntimeError("fallo simulado antes del commit")

    monkeypatch.setattr(auditoria, "registrar", falla)
    with pytest.raises(RuntimeError):
        escribir(admin, "POST", "/api/v1/animales", nuevo())
    assert totales(api) == antes  # ni animal, ni estado, ni auditoría


def test_campos_obligatorios_ausentes(api):
    admin = cliente_con_sesion(api, "admin")
    antes = totales(api)
    r = escribir(admin, "POST", "/api/v1/animales", {"nombre": "Luna"})  # sin nada más
    assert codigo(r) == (422, "VALIDACION")
    assert {"arete", "raza", "procedencia", "fecha_ingreso", "estado_inicial"} <= set(r.json()["error"]["fields"])
    assert totales(api) == antes


def test_el_nombre_es_opcional(api):
    admin = cliente_con_sesion(api, "admin")
    cuerpo = nuevo(arete="V-040")
    del cuerpo["nombre"]
    assert escribir(admin, "POST", "/api/v1/animales", cuerpo).json()["nombre"] is None
    assert crear(admin, arete="V-041", nombre="   ")["nombre"] is None


def test_el_cliente_no_puede_fijar_responsable_ni_datos_de_auditoria(api):
    admin = cliente_con_sesion(api, "admin")
    antes = totales(api)
    for extra in ({"responsable_id": 3}, {"usuario": "otro@finca.co"}, {"momento": "2020-01-01T00:00:00Z"}):
        assert codigo(escribir(admin, "POST", "/api/v1/animales", nuevo(**extra))) == (422, "VALIDACION")
    assert totales(api) == antes
    crear(admin, arete="V-050")
    assert api.filas(select(EstadoAnimal.responsable_id)) == [(1,)]  # siempre el de la sesión


def test_dos_altas_simultaneas_con_el_mismo_arete_solo_crean_una(api):
    with api.SessionLocal() as db:  # un segundo administrador: iniciar sesión dos veces con el mismo usuario revoca la primera
        servicio_usuarios.crear_usuario(db, None, nombre="Otro Admin", email="admin2@finca.co", password=CLAVE, rol="administrador")
    clientes = [cliente_con_sesion(api, "admin"), api.nuevo_cliente()]
    assert iniciar_sesion(clientes[1], "admin2@finca.co").status_code == 200
    tokens = [pedir_csrf(c) for c in clientes]
    antes = totales(api)
    barrera, estados = threading.Barrier(2), []

    def alta(i):
        barrera.wait()
        estados.append(clientes[i].post("/api/v1/animales", json=nuevo(), headers={"X-CSRF-Token": tokens[i]}).status_code)

    hilos = [threading.Thread(target=alta, args=(i,)) for i in range(2)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    assert sorted(estados) == [201, 409]
    assert totales(api) == (antes[0] + 1, antes[1] + 1, antes[2] + 1)  # un animal, un estado, una auditoría


# ---------- cambio de estado ----------

def test_cambio_de_estado_sube_version_y_audita_antes_y_despues(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    r = escribir(admin, "POST", f"/api/v1/animales/{a['id']}/estados", cambio())
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert (cuerpo["estado"]["estado"], cuerpo["estado"]["responsable_id"], cuerpo["animal"]["estado_actual"], cuerpo["animal"]["version"]) == ("seco", 1, "seco", 2)
    fila = api.consultar(select(Auditoria).where(Auditoria.entidad == "animal", Auditoria.accion == "cambiar_estado"))[0]
    assert (fila.usuario, fila.motivo) == ("admin@finca.co", "Fin del período productivo")
    assert json.loads(fila.antes) == {"estado": "en_produccion", "version": 1}
    assert json.loads(fila.despues)["estado"] == "seco" and json.loads(fila.despues)["version"] == 2


def test_motivo_obligatorio_y_estado_valido(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    antes = totales(api)
    for cuerpo, campo in [(cambio(motivo="  "), "motivo"), (cambio(estado="volando"), "estado"),
                          (cambio(fecha_desde=(HOY + timedelta(days=1)).isoformat()), "fecha_desde"),
                          (cambio(fecha_desde=(INGRESO - timedelta(days=1)).isoformat()), "fecha_desde"),
                          (cambio(estado="en_produccion", fecha_desde=HOY.isoformat()), "estado")]:  # igual al vigente
        r = escribir(admin, "POST", f"/api/v1/animales/{a['id']}/estados", cuerpo)
        assert codigo(r) == (422, "VALIDACION") and campo in r.json()["error"]["fields"], cuerpo
    assert totales(api) == antes and api.filas(select(Animal.version)) == [(1,)]


def test_version_obsoleta_se_rechaza_y_no_cambia_nada(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    ruta = f"/api/v1/animales/{a['id']}/estados"
    assert escribir(admin, "POST", ruta, cambio()).status_code == 201
    antes = totales(api)
    r = escribir(admin, "POST", ruta, cambio(estado="no_productivo", fecha_desde=HOY.isoformat(), version=1))
    assert codigo(r) == (409, "VERSION_OBSOLETA")
    assert totales(api) == antes and api.filas(select(Animal.version)) == [(2,)]


def test_un_solo_cambio_por_animal_y_dia_incluido_el_inicial(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    r = escribir(admin, "POST", f"/api/v1/animales/{a['id']}/estados", cambio(fecha_desde=INGRESO.isoformat()))
    assert codigo(r) == (409, "CAMBIO_DIARIO_DUPLICADO")
    assert escribir(admin, "POST", f"/api/v1/animales/{a['id']}/estados", cambio()).status_code == 201
    r = escribir(admin, "POST", f"/api/v1/animales/{a['id']}/estados", cambio(estado="no_productivo", version=2))
    assert codigo(r) == (409, "CAMBIO_DIARIO_DUPLICADO")


def test_estado_incompatible_con_ordenos_vigentes_pero_no_con_anulados(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    ruta = f"/api/v1/animales/{a['id']}/estados"
    with api.SessionLocal() as db:
        db.add(Ordeno(animal_id=a["id"], fecha=HOY - timedelta(days=5), turno="mañana", centilitros_producidos=1000,
                      centilitros_descartados=0, anulado=False, creado_por="t"))
        db.commit()
    antes = totales(api)
    assert codigo(escribir(admin, "POST", ruta, cambio())) == (409, "ESTADO_INCOMPATIBLE")
    assert totales(api) == antes
    with api.SessionLocal() as db:
        db.query(Ordeno).update({"anulado": True})
        db.commit()
    assert escribir(admin, "POST", ruta, cambio()).status_code == 201


def test_animal_retirado_no_admite_cambios(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    with api.SessionLocal() as db:  # la salida real es PB-06; aquí se simula con una fila
        db.add(EstadoAnimal(animal_id=a["id"], estado="fuera_del_hato", fecha_desde=HOY - timedelta(days=2), motivo="Venta", responsable_id=1))
        db.commit()
    r = escribir(admin, "POST", f"/api/v1/animales/{a['id']}/estados", cambio())
    assert codigo(r) == (409, "ESTADO_INCOMPATIBLE")


def test_animal_inexistente_es_404(api):
    admin = cliente_con_sesion(api, "admin")
    assert admin.get("/api/v1/animales/999").json()["error"]["code"] == "NO_ENCONTRADO"
    assert codigo(escribir(admin, "POST", "/api/v1/animales/999/estados", cambio())) == (404, "NO_ENCONTRADO")


def test_si_falla_la_auditoria_el_cambio_de_estado_se_revierte_incluida_la_version(api, monkeypatch):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    antes = totales(api)

    def falla(*_a, **_k):
        raise RuntimeError("fallo simulado antes del commit")

    monkeypatch.setattr(auditoria, "registrar", falla)
    with pytest.raises(RuntimeError):
        escribir(admin, "POST", f"/api/v1/animales/{a['id']}/estados", cambio())
    assert totales(api) == antes
    assert api.filas(select(Animal.version)) == [(1,)]  # la versión tampoco subió


# ---------- restricciones y claves foráneas en la base de datos ----------

def _falla(api, *objetos):
    with api.SessionLocal() as db:
        db.add_all(objetos)
        with pytest.raises(IntegrityError):
            db.commit()


def test_la_base_rechaza_datos_incoherentes(api):
    _falla(api, Animal(arete="v-001"))                                                         # arete en minúsculas
    _falla(api, Animal(arete="  V-002  "))                                                     # espacios extremos
    _falla(api, Animal(arete=""))                                                              # arete vacío
    _falla(api, Animal(arete="A1", fecha_nacimiento=INGRESO, edad_estimada_meses=5))          # ambos
    _falla(api, Animal(arete="A2", edad_estimada_meses=-3))                                    # negativa
    _falla(api, Animal(arete="A3", fecha_ingreso=INGRESO, fecha_nacimiento=HOY))               # nacimiento > ingreso


def test_la_base_rechaza_referencias_y_estados_invalidos(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    _falla(api, EstadoAnimal(animal_id=999, estado="seco", fecha_desde=HOY, motivo="x", responsable_id=1))   # FK animal
    _falla(api, EstadoAnimal(animal_id=a["id"], estado="seco", fecha_desde=HOY, motivo="x", responsable_id=999))  # FK usuario
    _falla(api, EstadoAnimal(animal_id=a["id"], estado="volando", fecha_desde=HOY, motivo="x", responsable_id=1))  # CHECK
    _falla(api, EstadoAnimal(animal_id=a["id"], estado="seco", fecha_desde=INGRESO, motivo="x", responsable_id=1))  # un cambio/día
    _falla(api, EstadoAnimal(animal_id=a["id"], estado="seco", fecha_desde=HOY, motivo="  ", responsable_id=1))   # motivo vacío


# ---------- S1-PB-04-BE: estados, historial e incompatibilidades ----------

def dia(n):
    return (HOY - timedelta(days=n)).isoformat()


def cambiar(admin, animal_id, estado, fecha, version, motivo="Cambio de prueba"):
    return escribir(admin, "POST", f"/api/v1/animales/{animal_id}/estados",
                    {"estado": estado, "fecha_desde": fecha, "motivo": motivo, "version": version})


def ordeno(api, animal_id, fecha, anulado=False):
    with api.SessionLocal() as db:
        db.add(Ordeno(animal_id=animal_id, fecha=fecha, turno="mañana", centilitros_producidos=1000,
                      centilitros_descartados=0, anulado=anulado, creado_por="prueba"))
        db.commit()


@pytest.mark.parametrize("estado", ["en_produccion", "seco", "no_productivo", "fuera_del_hato"])
def test_los_cuatro_estados_son_validos_en_un_cambio(api, estado):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin, estado_inicial="seco" if estado == "en_produccion" else "en_produccion")
    r = cambiar(admin, a["id"], estado, dia(5), 1)
    assert r.status_code == 201, r.text
    assert (r.json()["estado"]["estado"], r.json()["animal"]["estado_actual"]) == (estado, estado)


def test_el_alta_sigue_sin_admitir_fuera_del_hato(api):
    admin = cliente_con_sesion(api, "admin")
    r = escribir(admin, "POST", "/api/v1/animales", nuevo(estado_inicial="fuera_del_hato"))
    assert codigo(r) == (422, "VALIDACION") and "estado_inicial" in r.json()["error"]["fields"]


def test_despues_de_salir_del_hato_no_hay_mas_cambios(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    assert cambiar(admin, a["id"], "fuera_del_hato", dia(5), 1).status_code == 201
    antes = totales(api)
    assert codigo(cambiar(admin, a["id"], "en_produccion", dia(1), 2)) == (409, "ESTADO_INCOMPATIBLE")
    assert totales(api) == antes


def test_la_salida_del_hato_debe_ser_el_ultimo_cambio(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    assert cambiar(admin, a["id"], "seco", dia(5), 1).status_code == 201
    antes = totales(api)
    r = cambiar(admin, a["id"], "fuera_del_hato", dia(10), 2)  # retroactiva, con un cambio posterior
    assert codigo(r) == (409, "ESTADO_INCOMPATIBLE") and "fecha_desde" in r.json()["error"]["fields"]
    assert totales(api) == antes


@pytest.mark.parametrize("estado", ["seco", "no_productivo", "fuera_del_hato"])
def test_ordeno_vigente_bloquea_todo_estado_no_productivo_incluida_la_frontera(api, estado):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    ordeno(api, a["id"], HOY - timedelta(days=5))
    antes = totales(api)
    assert codigo(cambiar(admin, a["id"], estado, dia(5), 1)) == (409, "ESTADO_INCOMPATIBLE")  # mismo día del ordeño
    assert totales(api) == antes
    assert cambiar(admin, a["id"], estado, dia(4), 1).status_code == 201  # el día siguiente: ya no lo contradice


def test_ordenos_de_otro_animal_no_interfieren(api):
    admin = cliente_con_sesion(api, "admin")
    a, b = crear(admin, arete="V-060"), crear(admin, arete="V-061")
    ordeno(api, b["id"], HOY - timedelta(days=2))
    assert cambiar(admin, a["id"], "seco", dia(5), 1).status_code == 201


def test_cambio_retroactivo_solo_compara_ordenos_de_su_tramo(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    assert cambiar(admin, a["id"], "seco", dia(20), 1).status_code == 201          # prod -> seco(20)
    assert cambiar(admin, a["id"], "en_produccion", dia(10), 2).status_code == 201  # -> prod(10)
    ordeno(api, a["id"], HOY - timedelta(days=5))                                   # ordeño en el tramo productivo actual
    # no_productivo desde el día 25 rige hasta el día 20 (siguiente cambio): el ordeño del día 5 no lo contradice
    assert cambiar(admin, a["id"], "no_productivo", dia(25), 3).status_code == 201
    # pero un ordeño dentro del tramo sí lo bloquea
    b = crear(admin, arete="V-070")
    assert cambiar(admin, b["id"], "seco", dia(20), 1).status_code == 201
    ordeno(api, b["id"], HOY - timedelta(days=22))                                  # cae en el tramo prod -> (seco día 20)
    assert codigo(cambiar(admin, b["id"], "no_productivo", dia(25), 2)) == (409, "ESTADO_INCOMPATIBLE")


def test_ordenos_anulados_no_bloquean(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    ordeno(api, a["id"], HOY - timedelta(days=3), anulado=True)
    assert cambiar(admin, a["id"], "seco", dia(5), 1).status_code == 201


def test_incompatibilidad_con_un_ordeno_real_registrado_por_la_api_del_poc(api):
    """Dato de ordeño real (POST /ordenos del PoC), no una fila insertada a mano."""
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    poc = TestClient(app, base_url="https://testserver")
    r = poc.post("/ordenos", headers={"X-Usuario": "operario@finca.co"},
                 json={"animal_id": a["id"], "fecha": dia(3), "turno": "mañana",
                       "litros_producidos": "12.50", "litros_descartados": "0"})
    assert r.status_code == 201, r.text
    assert codigo(cambiar(admin, a["id"], "seco", dia(5), 1)) == (409, "ESTADO_INCOMPATIBLE")


@pytest.mark.xfail(strict=True, reason="PENDIENTE PB-07: POST /ordenos aún no consulta el estado del animal")
def test_pendiente_el_registro_de_ordenos_debe_rechazar_animales_no_productivos(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    assert cambiar(admin, a["id"], "seco", dia(5), 1).status_code == 201
    r = TestClient(app, base_url="https://testserver").post(
        "/ordenos", headers={"X-Usuario": "operario@finca.co"},
        json={"animal_id": a["id"], "fecha": dia(1), "turno": "mañana",
              "litros_producidos": "10", "litros_descartados": "0"})
    assert r.status_code in (409, 422)  # hoy responde 201: la integración queda pendiente


def test_historial_conserva_fecha_motivo_responsable_en_orden_cronologico(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    assert cambiar(admin, a["id"], "seco", dia(10), 1, motivo="Fin de lactancia").status_code == 201
    # llega después pero con fecha anterior: el historial se ordena por fecha efectiva, no por llegada
    assert cambiar(admin, a["id"], "no_productivo", dia(20), 2, motivo="Corrección retroactiva").status_code == 201
    r = admin.get(f"/api/v1/animales/{a['id']}/estados").json()
    assert [(e["estado"], e["fecha_desde"]) for e in r["items"]] == [
        ("en_produccion", dia(30)), ("no_productivo", dia(20)), ("seco", dia(10))]
    assert (r["total"], r["page"], r["page_size"]) == (3, 1, 20)
    por_estado = {e["estado"]: e for e in r["items"]}
    assert (por_estado["seco"]["motivo"], por_estado["seco"]["responsable_id"], por_estado["seco"]["animal_id"]) == ("Fin de lactancia", 1, a["id"])
    assert por_estado["en_produccion"]["motivo"] == "Estado inicial al registrar el animal"
    assert admin.get(f"/api/v1/animales/{a['id']}/estados?page=2&page_size=2").json()["items"][0]["estado"] == "seco"
    assert admin.get(f"/api/v1/animales/{a['id']}/estados?page_size=101").status_code == 422


def test_historial_lo_leen_los_tres_roles_y_no_existe_para_animal_inexistente(api):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    for rol in ("operario", "propietario"):
        assert cliente_con_sesion(api, rol).get(f"/api/v1/animales/{a['id']}/estados").status_code == 200
    assert api.nuevo_cliente().get(f"/api/v1/animales/{a['id']}/estados").status_code == 401
    assert admin.get("/api/v1/animales/999/estados").json()["error"]["code"] == "NO_ENCONTRADO"


def test_el_historial_no_se_puede_alterar_ni_por_la_api_ni_por_la_base(api, tmp_path):
    admin = cliente_con_sesion(api, "admin")
    a = crear(admin)
    for metodo in ("PUT", "PATCH", "DELETE"):
        assert escribir(admin, metodo, f"/api/v1/animales/{a['id']}/estados", {}).status_code == 405
    engine = crear_engine(f"sqlite:///{tmp_path / 'h.db'}")
    Base.metadata.create_all(engine)
    migraciones.proteger_historial(engine)
    migraciones.proteger_historial(engine)  # idempotente
    with engine.begin() as con:
        con.execute(text("INSERT INTO usuario (nombre, email, hash_clave, rol, activo, creado_en, actualizado_en) VALUES ('u','u@f.co','x','administrador',1,'2026-01-01','2026-01-01')"))
        con.execute(text("INSERT INTO animal (arete, version) VALUES ('A1', 1)"))
        con.execute(text("INSERT INTO estado_animal (animal_id, estado, fecha_desde, motivo, responsable_id, creado_en) VALUES (1,'seco','2026-01-01','m',1,'2026-01-01')"))
    for sentencia in ("UPDATE estado_animal SET motivo = 'alterado'", "DELETE FROM estado_animal"):
        with pytest.raises(Exception):
            with engine.begin() as con:
                con.execute(text(sentencia))
    engine.dispose()


def test_dos_cambios_simultaneos_con_la_misma_version_solo_aplican_uno(api):
    with api.SessionLocal() as db:
        servicio_usuarios.crear_usuario(db, None, nombre="Otro Admin", email="admin2@finca.co", password=CLAVE, rol="administrador")
    clientes = [cliente_con_sesion(api, "admin"), api.nuevo_cliente()]
    assert iniciar_sesion(clientes[1], "admin2@finca.co").status_code == 200
    a = crear(clientes[0])
    tokens = [pedir_csrf(c) for c in clientes]
    barrera, estados = threading.Barrier(2), []

    def intento(i):
        barrera.wait()
        estados.append(clientes[i].post(
            f"/api/v1/animales/{a['id']}/estados", headers={"X-CSRF-Token": tokens[i]},
            json={"estado": "seco" if i == 0 else "no_productivo", "fecha_desde": dia(5), "motivo": "Carrera", "version": 1}).status_code)

    hilos = [threading.Thread(target=intento, args=(i,)) for i in range(2)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    assert sorted(estados) == [201, 409]
    assert api.filas(select(Animal.version)) == [(2,)] and api.contar(EstadoAnimal) == 2  # inicial + uno solo