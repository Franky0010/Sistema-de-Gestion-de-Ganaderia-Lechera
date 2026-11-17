"""Reglas de negocio de los servicios probadas SIN base de datos.

Es posible porque los servicios dependen de los puertos (app/services/puertos.py) y no de
SQLAlchemy: aquí se les entrega una unidad de trabajo en memoria (tests/memoria.py). Estas
pruebas son rápidas y complementan a las de integración (que sí usan SQLite).
"""
import datetime as dt
from decimal import Decimal

import pytest

from app.core.excepciones import ErrorApi
from app.models import Sesion
from app.services import animales as servicio_animales
from app.services import auditoria, ordenos
from app.services import usuarios as servicio_usuarios

from .memoria import UnidadDeTrabajoMemoria

CLAVE = "Clave-segura-1"
INGRESO = dt.date(2020, 1, 1)


def crear_admin(uow, email="ana@finca.co"):
    return servicio_usuarios.crear_usuario(uow, None, nombre="Ana Admin", email=email, password=CLAVE, rol="administrador")


def alta_animal(uow, actor, arete="A-100"):
    return servicio_animales.crear_animal(uow, actor, {
        "arete": arete, "nombre": "Estrella", "raza": "Holstein", "procedencia": "Finca La Esperanza",
        "fecha_ingreso": INGRESO, "fecha_nacimiento": dt.date(2018, 1, 1), "edad_estimada_meses": None,
        "estado_inicial": "en_produccion"})


# ------------------------------------------------------------------ usuarios
def test_crear_usuario_guarda_el_usuario_y_su_auditoria():
    uow = UnidadDeTrabajoMemoria()
    admin = crear_admin(uow)
    assert admin.id == 1 and admin.email == "ana@finca.co"
    assert [a.accion for a in uow.confirmados("auditoria")] == ["crear"]


def test_correo_duplicado_responde_409_y_no_deja_rastro():
    uow = UnidadDeTrabajoMemoria()
    crear_admin(uow)
    with pytest.raises(ErrorApi) as error:
        crear_admin(uow, email="ANA@finca.co")  # el correo se normaliza a minúsculas
    assert (error.value.status, error.value.code) == (409, "EMAIL_DUPLICADO")
    assert len(uow.confirmados("usuarios")) == 1
    assert len(uow.confirmados("auditoria")) == 1  # la del segundo intento se descartó


def test_no_se_puede_degradar_al_ultimo_administrador():
    uow = UnidadDeTrabajoMemoria()
    admin = crear_admin(uow)
    with pytest.raises(ErrorApi) as error:
        servicio_usuarios.actualizar_usuario(uow, admin, admin.id, {"rol": "operario"})
    assert error.value.code == "ULTIMO_ADMINISTRADOR"
    assert admin.rol == "administrador"  # el rollback deshizo el cambio
    assert len(uow.confirmados("auditoria")) == 1


def test_desactivar_exige_motivo_y_revoca_las_sesiones():
    uow = UnidadDeTrabajoMemoria()
    admin = crear_admin(uow)
    operario = servicio_usuarios.crear_usuario(uow, admin, nombre="Luis Gómez", email="luis@finca.co",
                                               password=CLAVE, rol="operario")
    ahora = dt.datetime(2026, 1, 1, 12, 0)
    sesion = Sesion(usuario_id=operario.id, hash_token="h" * 64, creada_en=ahora, ultimo_uso=ahora)
    uow.sesiones.agregar(sesion)
    uow.commit()

    with pytest.raises(ErrorApi) as error:
        servicio_usuarios.actualizar_usuario(uow, admin, operario.id, {"activo": False})
    assert error.value.status == 422 and sesion.revocada_en is None

    servicio_usuarios.actualizar_usuario(uow, admin, operario.id, {"activo": False}, "Ya no trabaja aquí")
    assert operario.activo is False and sesion.revocada_en is not None
    assert uow.confirmados("auditoria")[-1].accion == "desactivar"


def test_listar_y_obtener_usuarios():
    uow = UnidadDeTrabajoMemoria()
    admin = crear_admin(uow)
    servicio_usuarios.crear_usuario(uow, admin, nombre="Luis Gómez", email="luis@finca.co", password=CLAVE, rol="operario")
    resultado = servicio_usuarios.listar_usuarios(uow.usuarios, "luis", 1, 20)
    assert resultado["total"] == 1 and resultado["items"][0].email == "luis@finca.co"
    assert servicio_usuarios.obtener_usuario(uow.usuarios, admin.id) is admin
    with pytest.raises(ErrorApi) as error:
        servicio_usuarios.obtener_usuario(uow.usuarios, 999)
    assert error.value.status == 404


def test_si_falla_la_auditoria_se_revierte_la_escritura(monkeypatch):
    uow = UnidadDeTrabajoMemoria()

    def falla(*_a, **_k):
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(auditoria, "registrar", falla)
    with pytest.raises(RuntimeError):
        crear_admin(uow)
    assert uow.confirmados("usuarios") == [] and uow.confirmados("auditoria") == []


# ------------------------------------------------------------------ animales
def test_arete_duplicado_responde_409():
    uow = UnidadDeTrabajoMemoria()
    admin = crear_admin(uow)
    alta_animal(uow, admin)
    with pytest.raises(ErrorApi) as error:
        alta_animal(uow, admin)
    assert error.value.code == "ARETE_DUPLICADO"
    assert len(uow.confirmados("animales")) == 1 and len(uow.confirmados("estados")) == 1


def test_cambio_de_estado_incrementa_la_version_y_se_audita():
    uow = UnidadDeTrabajoMemoria()
    admin = crear_admin(uow)
    animal = alta_animal(uow, admin)
    assert animal.version == 1
    nuevo, animal = servicio_animales.cambiar_estado(
        uow, admin, animal.id, estado="seco", fecha_desde=dt.date(2020, 6, 1), motivo="Fin de lactancia", version=1)
    assert nuevo.estado == "seco" and animal.version == 2
    publico = servicio_animales.animal_publico(uow.estados, animal)
    assert publico["estado_actual"] == "seco" and publico["version"] == 2
    assert uow.confirmados("auditoria")[-1].accion == "cambiar_estado"
    historial = servicio_animales.listar_estados(uow.estados, animal)
    assert [e["estado"] for e in historial["items"]] == ["en_produccion", "seco"]


def test_version_obsoleta_responde_409_y_no_cambia_nada():
    uow = UnidadDeTrabajoMemoria()
    admin = crear_admin(uow)
    animal = alta_animal(uow, admin)
    with pytest.raises(ErrorApi) as error:
        servicio_animales.cambiar_estado(uow, admin, animal.id, estado="seco", fecha_desde=dt.date(2020, 6, 1),
                                         motivo="x", version=7)
    assert error.value.code == "VERSION_OBSOLETA" and animal.version == 1
    assert len(uow.confirmados("estados")) == 1


def test_un_solo_cambio_de_estado_por_dia():
    uow = UnidadDeTrabajoMemoria()
    admin = crear_admin(uow)
    animal = alta_animal(uow, admin)
    with pytest.raises(ErrorApi) as error:  # el alta ya registró un estado el día del ingreso
        servicio_animales.cambiar_estado(uow, admin, animal.id, estado="seco", fecha_desde=INGRESO,
                                         motivo="x", version=1)
    assert error.value.code == "CAMBIO_DIARIO_DUPLICADO"


# ------------------------------------------------------------------ ordeños
def registrar(uow, fecha, turno="mañana"):
    return ordenos.registrar_ordeno(uow, animal_id=1, fecha=fecha, turno=turno, litros_producidos=Decimal("12.50"),
                                    litros_descartados=Decimal("0.50"), usuario="operario01")


def test_ordeno_duplicado_deja_un_solo_registro():
    uow = UnidadDeTrabajoMemoria()
    alta_animal(uow, crear_admin(uow))
    registrar(uow, dt.date(2020, 3, 1))
    with pytest.raises(ordenos.DuplicadoError):
        registrar(uow, dt.date(2020, 3, 1))
    assert len(uow.confirmados("ordenos")) == 1
    registrar(uow, dt.date(2020, 3, 1), turno="tarde")  # otro turno sí se permite
    assert len(uow.confirmados("ordenos")) == 2


def test_ordeno_de_animal_inexistente():
    uow = UnidadDeTrabajoMemoria()
    with pytest.raises(ordenos.AnimalNoExiste):
        registrar(uow, dt.date(2020, 3, 1))


def test_no_se_puede_pasar_a_seco_con_ordenos_vigentes():
    uow = UnidadDeTrabajoMemoria()
    admin = crear_admin(uow)
    animal = alta_animal(uow, admin)
    registrar(uow, dt.date(2020, 3, 1))
    with pytest.raises(ErrorApi) as error:
        servicio_animales.cambiar_estado(uow, admin, animal.id, estado="seco", fecha_desde=dt.date(2020, 2, 1),
                                         motivo="x", version=1)
    assert error.value.code == "ESTADO_INCOMPATIBLE"
    uow.confirmados("ordenos")[0].anulado = True  # al anular el ordeño, el cambio ya es posible
    servicio_animales.cambiar_estado(uow, admin, animal.id, estado="seco", fecha_desde=dt.date(2020, 2, 1),
                                     motivo="x", version=1)
