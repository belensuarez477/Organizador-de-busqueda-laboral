import pytest

ESTADOS = [
    "CV enviado",
    "En etapa de revisión",
    "En entrevista",
    "Finalizado",
    "Rechazado",
]


def datos(**cambios):
    base = {
        "titulo": "Desarrolladora Backend",
        "empresa": "Acme",
        "estado": "CV enviado",
        "fecha_postulacion": "2026-11-04",
        "enlace": "https://example.com/empleo",
        "rol": "Backend",
    }
    return {**base, **cambios}


def crear(client, **cambios):
    respuesta = client.post("/postulaciones", json=datos(**cambios))
    assert respuesta.status_code == 200
    return respuesta.json()


def test_health(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_listar_vacio(client):
    respuesta = client.get("/postulaciones")
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_estado_por_defecto(client):
    cuerpo = datos()
    del cuerpo["estado"]
    respuesta = client.post("/postulaciones", json=cuerpo)
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "CV enviado"


@pytest.mark.parametrize("estado", ESTADOS)
def test_ciclo_completo_por_estado(client, estado):
    creada = crear(client)
    id_ = creada["id"]

    actualizada = client.put(f"/postulaciones/{id_}", json=datos(estado=estado))
    assert actualizada.status_code == 200
    assert actualizada.json()["estado"] == estado

    assert client.get(f"/postulaciones/{id_}").json()["estado"] == estado
    assert [p["estado"] for p in client.get("/postulaciones").json()] == [estado]

    assert client.delete(f"/postulaciones/{id_}").status_code == 204
    assert client.get("/postulaciones").json() == []
    assert client.get(f"/postulaciones/{id_}").status_code == 404
    assert client.delete(f"/postulaciones/{id_}").status_code == 404


@pytest.mark.parametrize("estado", ESTADOS)
def test_crear_con_cada_estado(client, estado):
    assert crear(client, estado=estado)["estado"] == estado


def test_estado_invalido_en_post(client):
    respuesta = client.post("/postulaciones", json=datos(estado="Inventado"))
    assert respuesta.status_code == 422


def test_estado_invalido_en_put(client):
    id_ = crear(client)["id"]
    respuesta = client.put(f"/postulaciones/{id_}", json=datos(estado="Inventado"))
    assert respuesta.status_code == 422
    assert client.get(f"/postulaciones/{id_}").json()["estado"] == "CV enviado"


def test_campos_obligatorios(client):
    assert client.post("/postulaciones", json={}).status_code == 422


def test_put_reemplaza_los_campos(client):
    id_ = crear(client)["id"]
    respuesta = client.put(
        f"/postulaciones/{id_}", json=datos(empresa="Otra", rol="Frontend")
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["empresa"] == "Otra"
    assert respuesta.json()["rol"] == "Frontend"
    assert respuesta.json()["id"] == id_


def test_id_inexistente_devuelve_404(client):
    assert client.get("/postulaciones/999").status_code == 404
    assert client.put("/postulaciones/999", json=datos()).status_code == 404
    assert client.delete("/postulaciones/999").status_code == 404


def test_id_no_numerico(client):
    assert client.get("/postulaciones/abc").status_code == 422
    assert client.put("/postulaciones/abc", json=datos()).status_code == 422
    assert client.delete("/postulaciones/abc").status_code == 422
