"""S1-HT-02-BASE: transacciones, restricciones y auditoría de animales y estados (PB-03)."""
import json
import threading
from datetime import timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import auditoria, servicio_usuarios
from app.models import Animal, Auditoria, EstadoAnimal, Ordeno
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
    for cuerpo, campo in [(cambio(motivo="  "), "motivo"), (cambio(estado="fuera_del_hato"), "estado"),
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