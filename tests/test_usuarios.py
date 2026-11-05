"""PB-02 (cuentas), PB-11 (permisos por rol) y HT-02 (integridad y auditoría de usuarios)."""
import json

import pytest
from sqlalchemy import select

from app import auditoria
from app.models import Auditoria, Sesion, Usuario
from tests.conftest import USUARIOS, cliente_con_sesion, escribir, iniciar_sesion

NUEVO = {"nombre": "  Nora Nueva ", "email": "  Nora@Finca.CO ", "password": "otra-clave-12", "rol": "operario"}


def test_admin_crea_usuario_normalizado_sin_exponer_el_hash(api):
    admin = cliente_con_sesion(api, "admin")
    r = escribir(admin, "POST", "/api/v1/usuarios", NUEVO)
    assert r.status_code == 201
    assert r.json() == {"id": 4, "nombre": "Nora Nueva", "email": "nora@finca.co", "rol": "operario", "activo": True}
    assert "hash" not in r.text and "password" not in r.text
    assert iniciar_sesion(api.nuevo_cliente(), "nora@finca.co", "otra-clave-12").status_code == 200


def test_creacion_queda_auditada_sin_secretos(api):
    admin = cliente_con_sesion(api, "admin")
    escribir(admin, "POST", "/api/v1/usuarios", NUEVO)
    fila = api.consultar(select(Auditoria).where(Auditoria.entidad == "usuario", Auditoria.entidad_id == 4))[0]
    assert (fila.accion, fila.usuario, fila.usuario_id) == ("crear", "admin@finca.co", 1)
    assert json.loads(fila.despues) == {"nombre": "Nora Nueva", "email": "nora@finca.co", "rol": "operario", "activo": True}
    assert "otra-clave-12" not in (fila.despues or "") and "scrypt" not in (fila.despues or "")


def test_correo_duplicado_sin_distinguir_mayusculas_ni_inactivos(api):
    admin = cliente_con_sesion(api, "admin")
    escribir(admin, "PATCH", "/api/v1/usuarios/2", {"activo": False})
    r = escribir(admin, "POST", "/api/v1/usuarios", {**NUEVO, "email": "OPERARIO@finca.co"})
    assert (r.status_code, r.json()["error"]["code"]) == (409, "EMAIL_DUPLICADO")
    assert api.contar(Usuario) == 3


@pytest.mark.parametrize("cambio, campo", [
    ({"email": "no-es-correo"}, "email"), ({"password": "corta"}, "password"),
    ({"rol": "veterinario"}, "rol"), ({"nombre": "   "}, "nombre"), ({"nombre": "x" * 121}, "nombre"),
])
def test_validaciones_devuelven_422_por_campo_sin_crear_nada(api, cambio, campo):
    admin = cliente_con_sesion(api, "admin")
    r = escribir(admin, "POST", "/api/v1/usuarios", {**NUEVO, **cambio})
    assert r.status_code == 422 and campo in r.json()["error"]["fields"]
    assert api.contar(Usuario) == 3 and api.contar(Auditoria) == 3  # solo las 3 altas de la fixture


@pytest.mark.parametrize("rol", ["operario", "propietario"])
def test_otros_roles_no_administran_cuentas_y_no_cambia_nada(api, rol):
    c = cliente_con_sesion(api, rol)
    antes = (api.contar(Usuario), api.contar(Auditoria))
    for metodo, ruta, cuerpo in [("GET", "/api/v1/usuarios", None), ("GET", "/api/v1/usuarios/1", None),
                                 ("POST", "/api/v1/usuarios", NUEVO),
                                 ("PATCH", "/api/v1/usuarios/1", {"rol": "propietario"})]:
        r = escribir(c, metodo, ruta, cuerpo)
        assert (r.status_code, r.json()["error"]["code"]) == (403, "SIN_PERMISO"), (metodo, ruta)
    assert (api.contar(Usuario), api.contar(Auditoria)) == antes
    assert api.consultar(select(Usuario.rol).where(Usuario.id == 1)) == ["administrador"]


def test_escritura_sin_csrf_no_persiste(api):
    admin = cliente_con_sesion(api, "admin")
    r = admin.post("/api/v1/usuarios", json=NUEVO)
    assert (r.status_code, r.json()["error"]["code"]) == (403, "CSRF_INVALIDO")
    assert api.contar(Usuario) == 3


def test_actualizar_audita_valores_anteriores_y_nuevos(api):
    admin = cliente_con_sesion(api, "admin")
    r = escribir(admin, "PATCH", "/api/v1/usuarios/3", {"nombre": "Paula P.", "rol": "operario"})
    assert r.status_code == 200 and r.json()["rol"] == "operario"
    fila = api.consultar(select(Auditoria).where(Auditoria.entidad_id == 3, Auditoria.accion == "actualizar"))[0]
    assert json.loads(fila.antes)["rol"] == "propietario" and json.loads(fila.despues)["rol"] == "operario"


def test_sin_cambios_reales_no_audita(api):
    admin = cliente_con_sesion(api, "admin")
    antes = api.contar(Auditoria)
    assert escribir(admin, "PATCH", "/api/v1/usuarios/2", {"rol": "operario"}).status_code == 200
    assert api.contar(Auditoria) == antes


def test_patch_rechaza_vacio_nulos_y_campos_no_permitidos(api):
    admin = cliente_con_sesion(api, "admin")
    for cuerpo in [{}, {"nombre": None}, {"password": "nueva-clave-1"}, {"activo": "false"}]:
        assert escribir(admin, "PATCH", "/api/v1/usuarios/2", cuerpo).status_code == 422, cuerpo


def test_desactivar_revoca_sesiones_y_conserva_el_historial(api):
    operario = cliente_con_sesion(api, "operario")
    admin = cliente_con_sesion(api, "admin")
    assert escribir(admin, "PATCH", "/api/v1/usuarios/2", {"activo": False, "motivo": "Prueba"}).status_code == 200
    assert operario.get("/api/v1/auth/session").status_code == 401
    assert api.contar(Usuario, Usuario.id == 2) == 1  # el usuario sigue existiendo
    assert api.consultar(select(Auditoria.accion).where(Auditoria.entidad_id == 2))[-1] == "desactivar"
    assert api.contar(Sesion, Sesion.usuario_id == 2, Sesion.revocada_en.is_(None)) == 0


def test_no_se_puede_dejar_el_sistema_sin_administrador_activo(api):
    admin = cliente_con_sesion(api, "admin")
    for cuerpo in [{"activo": False, "motivo": "Prueba"}, {"rol": "operario"}]:
        r = escribir(admin, "PATCH", "/api/v1/usuarios/1", cuerpo)
        assert (r.status_code, r.json()["error"]["code"]) == (409, "ULTIMO_ADMINISTRADOR")
    assert api.filas(select(Usuario.activo, Usuario.rol).where(Usuario.id == 1)) == [(True, "administrador")]
    assert admin.get("/api/v1/auth/session").status_code == 200  # tampoco se revocó su sesión


def test_listado_paginado_y_con_busqueda(api):
    admin = cliente_con_sesion(api, "admin")
    r = admin.get("/api/v1/usuarios?page_size=2&page=2").json()
    assert (r["total"], r["page"], r["page_size"], [u["id"] for u in r["items"]]) == (3, 2, 2, [3])
    r = admin.get("/api/v1/usuarios?search=OPERA").json()
    assert r["total"] == 1 and r["items"][0]["email"] == "operario@finca.co"
    assert admin.get("/api/v1/usuarios?search=100%25").json()["total"] == 0  # % se trata como texto
    assert admin.get("/api/v1/usuarios?page=0").status_code == 422
    assert admin.get("/api/v1/usuarios?page_size=101").status_code == 422


def test_usuario_inexistente_devuelve_404(api):
    admin = cliente_con_sesion(api, "admin")
    assert admin.get("/api/v1/usuarios/999").json()["error"]["code"] == "NO_ENCONTRADO"
    assert escribir(admin, "PATCH", "/api/v1/usuarios/999", {"nombre": "X"}).status_code == 404


def test_si_falla_la_auditoria_se_revierte_todo(api, monkeypatch):
    admin = cliente_con_sesion(api, "admin")

    def falla(*_a, **_k):
        raise RuntimeError("fallo simulado antes del commit")

    monkeypatch.setattr(auditoria, "registrar", falla)
    with pytest.raises(RuntimeError):
        escribir(admin, "POST", "/api/v1/usuarios", NUEVO)
    with pytest.raises(RuntimeError):
        escribir(admin, "PATCH", "/api/v1/usuarios/2", {"nombre": "Cambiado"})
    assert api.contar(Usuario) == 3
    assert api.consultar(select(Usuario.nombre).where(Usuario.id == 2)) == ["Oscar Operario"]
