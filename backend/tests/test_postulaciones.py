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


@pytest.mark.parametrize("campo", ["titulo", "empresa", "enlace", "rol"])
@pytest.mark.parametrize("valor", ["", "  ", "\n\t "])
def test_texto_vacio_se_rechaza(client, campo, valor):
    assert client.post("/postulaciones", json=datos(**{campo: valor})).status_code == 422
    assert client.get("/postulaciones").json() == []


@pytest.mark.parametrize("campo", ["titulo", "empresa", "enlace", "rol"])
def test_texto_vacio_en_put_se_rechaza(client, campo):
    id_ = crear(client)["id"]
    assert client.put(f"/postulaciones/{id_}", json=datos(**{campo: "  "})).status_code == 422
    assert client.get(f"/postulaciones/{id_}").json()[campo] == datos()[campo]


def test_titulo_es_obligatorio(client):
    cuerpo = datos()
    del cuerpo["titulo"]
    assert client.post("/postulaciones", json=cuerpo).status_code == 422
    assert client.put("/postulaciones/1", json=cuerpo).status_code == 422


def test_titulo_permite_espacios_entre_palabras(client):
    assert crear(client, titulo="Desarrolladora Backend Senior")["titulo"] == "Desarrolladora Backend Senior"


def test_texto_se_guarda_sin_espacios_sobrantes(client):
    assert crear(client, titulo="  Dev  ")["titulo"] == "Dev"


@pytest.mark.parametrize(
    "escrito,guardado",
    [
        ("Desarrolladora    Backend", "Desarrolladora Backend"),
        ("  Dev   Python \t Senior  ", "Dev Python Senior"),
        ("Dev\n\nPython", "Dev Python"),
    ],
)
def test_titulo_junta_espacios_repetidos(client, escrito, guardado):
    assert crear(client, titulo=escrito)["titulo"] == guardado


@pytest.mark.parametrize(
    "titulo",
    ["Desarrollador C#", "Programador .NET", "Dev C++", "Node.js Developer", "Python 3", "Ingeniería de Datos Ñ"],
)
def test_titulo_permite_numeros_y_simbolos_de_tecnologias(client, titulo):
    assert crear(client, titulo=titulo)["titulo"] == titulo


@pytest.mark.parametrize(
    "titulo",
    ["Dev <b>", "Dev; Ops", "Dev {x}", "Dev 😀", "Dev % $ ! ? * = ~ | ^", "Ingeniero/a [Datos]"],
)
def test_titulo_permite_caracteres_especiales(client, titulo):
    assert crear(client, titulo=titulo)["titulo"] == titulo


@pytest.mark.parametrize("titulo", ["Dev\x00", "Dev\x07", "Dev\x7f"])
def test_titulo_rechaza_caracteres_de_control(client, titulo):
    assert client.post("/postulaciones", json=datos(titulo=titulo)).status_code == 422


@pytest.mark.parametrize(
    "titulo",
    ["QA Tester", "Desarrollador C#", "Frontend HTML, CSS", "Angular 21"],
)
def test_rn002_titulos_validos(client, titulo):
    assert crear(client, titulo=titulo)["titulo"] == titulo


@pytest.mark.parametrize("titulo", ["!!!", "@#$%", "   #   ", "     ", "", "😀", "..."])
def test_rn002_titulos_sin_letras_ni_numeros_se_rechazan(client, titulo):
    assert client.post("/postulaciones", json=datos(titulo=titulo)).status_code == 422
    assert client.get("/postulaciones").json() == []


def test_rechazar_titulo_solo_simbolos(client):
    respuesta = client.post(
        "/postulaciones",
        json={
            "titulo": "!!!",
            "empresa": "Empresa ABC",
            "estado": "CV enviado",
            "fecha_postulacion": "2026-11-05",
            "enlace": "https://example.com",
            "rol": "QA Tester",
        },
    )

    assert respuesta.status_code == 422


@pytest.mark.parametrize("titulo", ["!!!", "@#$%", "     ", ""])
def test_rn002_en_put(client, titulo):
    id_ = crear(client)["id"]
    assert client.put(f"/postulaciones/{id_}", json=datos(titulo=titulo)).status_code == 422
    assert client.get(f"/postulaciones/{id_}").json()["titulo"] == datos()["titulo"]


def test_titulo_largo_se_mide_despues_de_normalizar(client):
    # 150 caracteres + espacios de relleno que no cuentan una vez normalizado
    assert crear(client, titulo="  " + "a" * 150 + "      " + "b" * 40 + "  ")["titulo"] == "a" * 150 + " " + "b" * 40


@pytest.mark.parametrize("campo", ["empresa", "rol"])
@pytest.mark.parametrize("valor", ["Dev 2", "123", "Acme3", "Back#end"])
def test_numeros_y_simbolos_se_rechazan(client, campo, valor):
    assert client.post("/postulaciones", json=datos(**{campo: valor})).status_code == 422
    assert client.get("/postulaciones").json() == []


@pytest.mark.parametrize("campo", ["empresa", "rol"])
def test_numeros_en_put_se_rechazan(client, campo):
    id_ = crear(client)["id"]
    assert client.put(f"/postulaciones/{id_}", json=datos(**{campo: "X9"})).status_code == 422
    assert client.get(f"/postulaciones/{id_}").json()[campo] == datos()[campo]


def test_titulo_con_numeros_en_put(client):
    id_ = crear(client)["id"]
    respuesta = client.put(f"/postulaciones/{id_}", json=datos(titulo="  Dev   C#  "))
    assert respuesta.status_code == 200
    assert respuesta.json()["titulo"] == "Dev C#"


@pytest.mark.parametrize("valor", ["Desarrolladora Frontend Jr.", "Ingeniería Back-end", "AT&T", "Perú Ñandú"])
def test_letras_con_acentos_y_signos_validos(client, valor):
    assert crear(client, titulo=valor)["titulo"] == valor


def test_enlace_acepta_numeros(client):
    assert crear(client, enlace="https://example.com/jobs/123")["enlace"].endswith("123")


@pytest.mark.parametrize(
    "campo,maximo", [("titulo", 200), ("empresa", 200), ("enlace", 500), ("rol", 100)]
)
def test_largo_maximo(client, campo, maximo):
    assert client.post("/postulaciones", json=datos(**{campo: "a" * maximo})).status_code == 200
    assert client.post("/postulaciones", json=datos(**{campo: "a" * (maximo + 1)})).status_code == 422


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
