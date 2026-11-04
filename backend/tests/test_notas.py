from datetime import datetime, timedelta, timezone

import pytest

from app.models import CONTENIDO_NOTA_MAX


def crear_postulacion(client, empresa="Acme"):
    respuesta = client.post(
        "/postulaciones",
        json={
            "titulo": "Dev",
            "empresa": empresa,
            "fecha_postulacion": "2026-11-04",
            "enlace": "https://example.com",
            "rol": "Backend",
        },
    )
    return respuesta.json()["id"]


def crear_nota(client, postulacion_id, contenido="Una nota"):
    return client.post(
        f"/postulaciones/{postulacion_id}/notas", json={"contenido": contenido}
    )


def test_crear_nota(client):
    id_ = crear_postulacion(client)
    respuesta = crear_nota(client, id_, "Me contactaron para coordinar una entrevista.")
    assert respuesta.status_code == 201
    nota = respuesta.json()
    assert nota["id"] == 1
    assert nota["contenido"] == "Me contactaron para coordinar una entrevista."
    assert nota["postulacion_id"] == id_


def test_fecha_automatica_en_utc(client):
    id_ = crear_postulacion(client)
    nota = crear_nota(client, id_).json()
    fecha = datetime.fromisoformat(nota["fecha_creacion"])
    assert fecha.utcoffset() == timedelta(0)
    assert abs(datetime.now(timezone.utc) - fecha) < timedelta(minutes=1)


def test_contenido_se_guarda_sin_espacios_sobrantes(client):
    id_ = crear_postulacion(client)
    assert crear_nota(client, id_, "  hola  ").json()["contenido"] == "hola"


def test_listar_sin_notas_devuelve_lista_vacia(client):
    id_ = crear_postulacion(client)
    respuesta = client.get(f"/postulaciones/{id_}/notas")
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_listar_de_mas_reciente_a_mas_antigua(client):
    id_ = crear_postulacion(client)
    for texto in ["primera", "segunda", "tercera"]:
        crear_nota(client, id_, texto)
    contenidos = [n["contenido"] for n in client.get(f"/postulaciones/{id_}/notas").json()]
    assert contenidos == ["tercera", "segunda", "primera"]


def test_solo_devuelve_notas_de_la_postulacion(client):
    a = crear_postulacion(client, "A")
    b = crear_postulacion(client, "B")
    crear_nota(client, a, "de A")
    crear_nota(client, b, "de B")
    notas_a = client.get(f"/postulaciones/{a}/notas").json()
    assert [n["contenido"] for n in notas_a] == ["de A"]
    assert all(n["postulacion_id"] == a for n in notas_a)


@pytest.mark.parametrize("contenido", ["", "   ", "\n\t "])
def test_contenido_vacio_se_rechaza(client, contenido):
    id_ = crear_postulacion(client)
    assert crear_nota(client, id_, contenido).status_code == 422
    assert client.get(f"/postulaciones/{id_}/notas").json() == []


def test_sin_contenido_se_rechaza(client):
    id_ = crear_postulacion(client)
    assert client.post(f"/postulaciones/{id_}/notas", json={}).status_code == 422


def test_largo_maximo(client):
    id_ = crear_postulacion(client)
    assert crear_nota(client, id_, "a" * CONTENIDO_NOTA_MAX).status_code == 201
    assert crear_nota(client, id_, "a" * (CONTENIDO_NOTA_MAX + 1)).status_code == 422


def test_postulacion_inexistente_devuelve_404(client):
    assert crear_nota(client, 999).status_code == 404
    assert client.get("/postulaciones/999/notas").status_code == 404


def test_borrar_postulacion_borra_sus_notas(client):
    id_ = crear_postulacion(client)
    otra = crear_postulacion(client, "Otra")
    crear_nota(client, id_, "se borra")
    crear_nota(client, otra, "se queda")

    assert client.delete(f"/postulaciones/{id_}").status_code == 204
    assert client.get(f"/postulaciones/{id_}/notas").status_code == 404
    assert len(client.get(f"/postulaciones/{otra}/notas").json()) == 1
