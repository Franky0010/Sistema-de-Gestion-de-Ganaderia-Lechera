"""PB-01 (login, logout, expiración) y HT-01 (cookies, CSRF, hash)."""
from sqlalchemy import select

from app.models import Sesion, Usuario
from tests.conftest import CLAVE, USUARIOS, cliente_con_sesion, escribir, iniciar_sesion, pedir_csrf

EMAIL = USUARIOS["operario"][1]


def test_csrf_no_se_cachea_y_crea_cookie_anonima(api):
    c = api.nuevo_cliente()
    r = c.get("/api/v1/auth/csrf")
    assert r.status_code == 200 and r.json()["csrf_token"]
    assert r.headers["cache-control"] == "no-store"
    assert "csrf_anonimo" in c.cookies


def test_login_valido_cookie_segura_y_sin_token_en_json(api):
    c = api.nuevo_cliente()
    r = iniciar_sesion(c, EMAIL)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["usuario"] == {"id": 2, "nombre": "Oscar Operario", "email": EMAIL, "rol": "operario", "activo": True}
    assert cuerpo["csrf_token"] and "hash_clave" not in r.text and "password" not in r.text
    cookie = next(h for h in r.headers.get_list("set-cookie") if h.startswith("sesion="))
    bajo = cookie.lower()
    assert "httponly" in bajo and "secure" in bajo and "samesite=lax" in bajo
    valor = cookie.split("=", 1)[1].split(";", 1)[0]
    assert valor not in r.text  # el token de sesión nunca viaja en el JSON
    assert c.get("/api/v1/auth/session").json()["usuario"]["email"] == EMAIL


def test_correo_se_normaliza_al_iniciar_sesion(api):
    assert iniciar_sesion(api.nuevo_cliente(), "  OPERARIO@Finca.CO ").status_code == 200


def test_contrasena_guardada_con_hash_adaptativo(api):
    for u in api.consultar(select(Usuario)):
        assert u.hash_clave.startswith("scrypt$") and CLAVE not in u.hash_clave


def test_credenciales_invalidas_no_revelan_si_la_cuenta_existe(api):
    mala = iniciar_sesion(api.nuevo_cliente(), EMAIL, "contraseña-incorrecta")
    inexistente = iniciar_sesion(api.nuevo_cliente(), "nadie@finca.co", "contraseña-incorrecta")
    assert mala.status_code == inexistente.status_code == 401
    assert mala.json() == inexistente.json()
    assert mala.json()["error"]["code"] == "CREDENCIALES_INVALIDAS"


def test_cuenta_inactiva_solo_se_revela_con_contrasena_correcta(api):
    admin = cliente_con_sesion(api, "admin")
    assert escribir(admin, "PATCH", "/api/v1/usuarios/2", {"activo": False, "motivo": "Prueba"}).status_code == 200
    correcta = iniciar_sesion(api.nuevo_cliente(), EMAIL)
    incorrecta = iniciar_sesion(api.nuevo_cliente(), EMAIL, "contraseña-incorrecta")
    assert (correcta.status_code, correcta.json()["error"]["code"]) == (403, "CUENTA_INACTIVA")
    assert (incorrecta.status_code, incorrecta.json()["error"]["code"]) == (401, "CREDENCIALES_INVALIDAS")


def test_escritura_sin_csrf_o_con_origen_ajeno_se_rechaza(api):
    c = api.nuevo_cliente()
    cuerpo = {"email": EMAIL, "password": CLAVE}
    assert c.post("/api/v1/auth/login", json=cuerpo).json()["error"]["code"] == "CSRF_INVALIDO"
    assert c.post("/api/v1/auth/login", json=cuerpo,
                  headers={"X-CSRF-Token": "falso.token"}).status_code == 403
    r = c.post("/api/v1/auth/login", json=cuerpo,
               headers={"X-CSRF-Token": pedir_csrf(c), "Origin": "https://sitio-malicioso.example"})
    assert (r.status_code, r.json()["error"]["code"]) == (403, "CSRF_INVALIDO")
    assert api.contar(Sesion) == 0  # ninguna sesión creada


def test_logout_revoca_la_sesion(api):
    c = cliente_con_sesion(api, "operario")
    token_viejo = c.cookies.get("sesion")
    assert escribir(c, "POST", "/api/v1/auth/logout").status_code == 204
    assert c.get("/api/v1/auth/session").status_code == 401
    # Reutilizar la cookie anterior tampoco sirve: la sesión quedó revocada en el servidor.
    r = api.nuevo_cliente().get("/api/v1/auth/session", headers={"Cookie": f"sesion={token_viejo}"})
    assert r.json()["error"]["code"] == "SESION_EXPIRADA"


def test_sesion_expira_a_los_30_minutos_de_inactividad(api):
    c = cliente_con_sesion(api, "operario")
    api.reloj.avanzar(minutes=29)
    assert c.get("/api/v1/auth/session").status_code == 200  # la actividad renueva el plazo
    api.reloj.avanzar(minutes=29)
    assert c.get("/api/v1/auth/session").status_code == 200
    api.reloj.avanzar(minutes=31)
    r = c.get("/api/v1/auth/session")
    assert (r.status_code, r.json()["error"]["code"]) == (401, "SESION_EXPIRADA")


def test_pedir_csrf_no_prolonga_la_sesion(api):
    c = cliente_con_sesion(api, "operario")
    api.reloj.avanzar(minutes=20)
    c.get("/api/v1/auth/csrf")
    api.reloj.avanzar(minutes=11)
    assert c.get("/api/v1/auth/session").status_code == 401


def test_nuevo_login_rota_la_sesion(api):
    c = cliente_con_sesion(api, "operario")
    vieja = c.cookies.get("sesion")
    assert iniciar_sesion(c, EMAIL).status_code == 200
    assert c.cookies.get("sesion") != vieja
    r = api.nuevo_cliente().get("/api/v1/auth/session", headers={"Cookie": f"sesion={vieja}"})
    assert r.status_code == 401


def test_limite_de_intentos_devuelve_429_con_retry_after(api):
    c = api.nuevo_cliente()
    for _ in range(5):
        assert iniciar_sesion(c, EMAIL, "contraseña-incorrecta").status_code == 401
    r = iniciar_sesion(c, EMAIL, CLAVE)  # incluso la correcta queda bloqueada
    assert (r.status_code, r.json()["error"]["code"]) == (429, "LIMITE_SOLICITUDES")
    assert int(r.headers["retry-after"]) > 0


def test_sin_sesion_las_rutas_protegidas_devuelven_401(api):
    assert api.nuevo_cliente().get("/api/v1/usuarios").json()["error"]["code"] == "SESION_EXPIRADA"
