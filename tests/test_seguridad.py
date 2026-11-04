"""HT-01: primitivas de seguridad (sin base de datos ni HTTP)."""
from datetime import datetime, timedelta

from app import seguridad


def test_hash_adaptativo_con_sal_y_verificacion():
    h1 = seguridad.hashear_password("clave-segura-1")
    h2 = seguridad.hashear_password("clave-segura-1")
    assert h1.startswith("scrypt$") and "clave-segura-1" not in h1
    assert h1 != h2  # sal distinta en cada hash
    assert seguridad.verificar_password("clave-segura-1", h1)
    assert not seguridad.verificar_password("otra-clave-99", h1)


def test_verificar_con_hash_corrupto_devuelve_false():
    assert not seguridad.verificar_password("x", "basura")
    assert not seguridad.verificar_password("x", "md5$1$2$3$4$5")


def test_password_con_caracter_no_codificable_no_lanza_error():
    h = seguridad.hashear_password("clave-segura-1")
    assert not seguridad.verificar_password("\ud800mala", h)


def test_token_de_sesion_se_guarda_solo_como_hash():
    t = seguridad.generar_token()
    assert len(t) >= 40 and seguridad.hash_token(t) != t and len(seguridad.hash_token(t)) == 64


def test_csrf_ligado_a_su_vinculo():
    token = seguridad.crear_csrf("sesion-A")
    assert seguridad.validar_csrf(token, "sesion-A")
    assert not seguridad.validar_csrf(token, "sesion-B")
    assert not seguridad.validar_csrf(None, "sesion-A")
    assert not seguridad.validar_csrf("sin-punto", "sesion-A")
    assert not seguridad.validar_csrf(token, None)
    nonce, _, firma = token.partition(".")
    assert not seguridad.validar_csrf(f"{nonce}.{'0' * len(firma)}", "sesion-A")


def test_limitador_bloquea_al_quinto_fallo_y_libera_con_el_tiempo():
    lim = seguridad.LimitadorIntentos(maximo=5, ventana=timedelta(minutes=15))
    t0 = datetime(2026, 11, 2, 12, 0, 0)
    for i in range(4):
        lim.registrar_fallo("k", t0 + timedelta(seconds=i))
        assert lim.segundos_de_espera("k", t0 + timedelta(seconds=i)) == 0
    lim.registrar_fallo("k", t0 + timedelta(seconds=4))
    assert lim.segundos_de_espera("k", t0 + timedelta(seconds=5)) > 0
    assert lim.segundos_de_espera("otra", t0) == 0  # claves independientes
    assert lim.segundos_de_espera("k", t0 + timedelta(minutes=16)) == 0


def test_limitador_limpiar_tras_exito():
    lim = seguridad.LimitadorIntentos(maximo=2)
    t0 = datetime(2026, 11, 2)
    lim.registrar_fallo("k", t0)
    lim.registrar_fallo("k", t0)
    assert lim.segundos_de_espera("k", t0) > 0
    lim.limpiar("k")
    assert lim.segundos_de_espera("k", t0) == 0
