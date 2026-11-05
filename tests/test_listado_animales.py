"""PB-03/PB-11: cover the missing table endpoint through real HTTP requests."""
from .conftest import cliente_con_sesion, escribir
from .test_animales import crear, cambio


def test_list_filters_effective_state_before_pagination(api):
    admin = cliente_con_sesion(api, "admin")
    first = crear(admin, arete="LIST-01", nombre="Luna")
    second = crear(admin, arete="LIST-02", nombre="Luna dos", estado_inicial="seco")
    crear(admin, arete="LIST-03", nombre="Estrella")
    changed = escribir(admin, "POST", f"/api/v1/animales/{first['id']}/estados", cambio())
    assert changed.status_code == 201
    result = admin.get("/api/v1/animales", params={
        "search": "LUNA", "estado": "seco", "page_size": 1, "page": 2,
    })
    assert result.status_code == 200
    assert result.json()["total"] == 2
    assert [item["id"] for item in result.json()["items"]] == [second["id"]]
    assert admin.get("/api/v1/animales?search=%25").json()["total"] == 0
    assert admin.get("/api/v1/animales?estado=invalid").status_code == 422
    assert admin.get("/api/v1/animales?page=0").status_code == 422


def test_list_requires_session_and_allows_both_read_roles(api):
    with api.nuevo_cliente() as anonymous:
        assert anonymous.get("/api/v1/animales").status_code == 401
    admin = cliente_con_sesion(api, "admin")
    crear(admin)
    for role in ("operario", "propietario"):
        client = cliente_con_sesion(api, role)
        response = client.get("/api/v1/animales")
        assert response.status_code == 200
        assert response.json()["total"] == 1
