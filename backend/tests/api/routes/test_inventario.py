import uuid
from typing import Any

import httpx
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.inventario import create_random_categoria, create_random_producto
from tests.utils.utils import random_lower_string

API = settings.API_V1_STR


def mover(
    client: TestClient,
    headers: dict[str, str],
    producto_id: uuid.UUID,
    tipo: str,
    cantidad: int,
    **extra: Any,
) -> httpx.Response:
    data = {"producto_id": str(producto_id), "tipo": tipo, "cantidad": cantidad}
    return client.post(f"{API}/transacciones/", headers=headers, json=data | extra)


def stock(client: TestClient, headers: dict[str, str], producto_id: uuid.UUID) -> int:
    r = client.get(f"{API}/productos/{producto_id}", headers=headers)
    assert r.status_code == 200
    return int(r.json()["stock"])


def alertas(
    client: TestClient, headers: dict[str, str], producto_id: uuid.UUID, estado: str
) -> list[dict[str, Any]]:
    r = client.get(f"{API}/alertas/", headers=headers, params={"estado": estado})
    return [a for a in r.json()["data"] if a["producto_id"] == str(producto_id)]


def test_entrada_suma_al_stock(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    # CA-02
    p = create_random_producto(db)
    assert (
        mover(client, normal_user_token_headers, p.id, "entrada", 10).status_code == 200
    )
    assert (
        mover(client, normal_user_token_headers, p.id, "entrada", 5).status_code == 200
    )
    assert stock(client, normal_user_token_headers, p.id) == 15


def test_salida_mayor_al_stock_se_rechaza(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    # CA-03, RN-04
    p = create_random_producto(db)
    mover(client, normal_user_token_headers, p.id, "entrada", 3)
    r = mover(client, normal_user_token_headers, p.id, "salida", 5)
    assert r.status_code == 400
    assert r.json()["detail"] == "Stock insuficiente: hay 3 bulto"
    assert stock(client, normal_user_token_headers, p.id) == 3


def test_cantidad_no_positiva_se_rechaza(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    # RN-03, EA-04
    p = create_random_producto(db)
    for cantidad in (0, -1):
        r = mover(client, normal_user_token_headers, p.id, "entrada", cantidad)
        assert r.status_code == 422


def test_alerta_stock_minimo_se_abre_una_vez_y_se_cierra(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    h = normal_user_token_headers
    p = create_random_producto(db, stock_minimo=10)
    mover(client, h, p.id, "entrada", 12)
    assert alertas(client, h, p.id, "activa") == []
    # CA-04
    mover(client, h, p.id, "salida", 4)
    assert stock(client, h, p.id) == 8
    assert len(alertas(client, h, p.id, "activa")) == 1
    # CA-05
    mover(client, h, p.id, "salida", 2)
    assert len(alertas(client, h, p.id, "activa")) == 1
    # CA-06
    mover(client, h, p.id, "entrada", 10)
    assert stock(client, h, p.id) == 16
    assert alertas(client, h, p.id, "activa") == []
    assert len(alertas(client, h, p.id, "cerrada")) == 1


def test_ajuste_solo_superusuario_y_conserva_historial(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    p = create_random_producto(db)
    mover(client, normal_user_token_headers, p.id, "entrada", 10)
    mover(client, normal_user_token_headers, p.id, "salida", 5)  # the wrong one
    r = mover(client, normal_user_token_headers, p.id, "entrada", 5, es_ajuste=True)
    assert r.status_code == 403
    # CA-10
    r = mover(client, superuser_token_headers, p.id, "entrada", 5, es_ajuste=True)
    assert r.status_code == 200
    assert stock(client, superuser_token_headers, p.id) == 10
    r = client.get(
        f"{API}/transacciones/",
        headers=superuser_token_headers,
        params={"producto_id": str(p.id)},
    )
    assert r.json()["count"] == 3


def test_fecha_vencimiento_segun_producto(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    h = normal_user_token_headers
    p = create_random_producto(db, alerta_caducidad=True)
    assert mover(client, h, p.id, "entrada", 2).status_code == 400
    r = mover(client, h, p.id, "entrada", 2, fecha_vencimiento="2026-12-01")
    assert r.status_code == 200
    assert r.json()["fecha_vencimiento"] == "2026-12-01"
    r = mover(client, h, p.id, "salida", 1, fecha_vencimiento="2026-12-01")
    assert r.status_code == 400
    sin_control = create_random_producto(db, alerta_caducidad=False)
    assert mover(client, h, sin_control.id, "entrada", 2).status_code == 200


def test_usuario_normal_no_gestiona_catalogo(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    # CA-09, RNF-002
    categoria = create_random_categoria(db)
    r = client.post(
        f"{API}/productos/",
        headers=normal_user_token_headers,
        json={"nombre": random_lower_string(), "categoria_id": str(categoria.id)},
    )
    assert r.status_code == 403
    r = client.post(
        f"{API}/categorias/",
        headers=normal_user_token_headers,
        json={"nombre": random_lower_string()},
    )
    assert r.status_code == 403


def test_superusuario_crea_producto(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    categoria = create_random_categoria(db)
    data = {
        "nombre": random_lower_string(),
        "unidad": "botella",
        "stock_minimo": 4,
        "categoria_id": str(categoria.id),
    }
    r = client.post(f"{API}/productos/", headers=superuser_token_headers, json=data)
    assert r.status_code == 200
    content = r.json()
    assert content["unidad"] == "botella"
    assert content["stock"] == 0
    assert content["alerta_caducidad"] is True
    # RN-09
    r = client.post(f"{API}/productos/", headers=superuser_token_headers, json=data)
    assert r.status_code == 409


def test_no_se_elimina_categoria_con_productos(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # CA-07, RN-08
    p = create_random_producto(db)
    r = client.delete(
        f"{API}/categorias/{p.categoria_id}", headers=superuser_token_headers
    )
    assert r.status_code == 409
    assert r.json()["detail"] == (
        "No se puede completar: el registro tiene datos asociados"
    )
    r = client.get(f"{API}/categorias/", headers=superuser_token_headers)
    assert str(p.categoria_id) in [c["id"] for c in r.json()["data"]]


def test_no_se_elimina_producto_con_movimientos(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # RN-07
    p = create_random_producto(db)
    mover(client, superuser_token_headers, p.id, "entrada", 1)
    r = client.delete(f"{API}/productos/{p.id}", headers=superuser_token_headers)
    assert r.status_code == 409
    assert r.json()["detail"] == (
        "No se puede completar: el registro tiene datos asociados"
    )
    vacio = create_random_producto(db)
    r = client.delete(f"{API}/productos/{vacio.id}", headers=superuser_token_headers)
    assert r.status_code == 200


def test_sin_token_no_hay_acceso(client: TestClient) -> None:
    assert client.get(f"{API}/productos/").status_code == 401


def test_listado_de_productos_incluye_stock(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    p = create_random_producto(db)
    mover(client, normal_user_token_headers, p.id, "entrada", 7)
    r = client.get(f"{API}/productos/", headers=normal_user_token_headers)
    assert r.status_code == 200
    por_id = {item["id"]: item for item in r.json()["data"]}
    assert por_id[str(p.id)]["stock"] == 7


def test_cambiar_stock_minimo_abre_y_cierra_alerta(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    h = superuser_token_headers
    p = create_random_producto(db, stock_minimo=0)
    mover(client, h, p.id, "entrada", 5)
    r = client.patch(f"{API}/productos/{p.id}", headers=h, json={"stock_minimo": 10})
    assert r.status_code == 200
    assert r.json()["stock"] == 5
    assert len(alertas(client, h, p.id, "activa")) == 1
    client.patch(f"{API}/productos/{p.id}", headers=h, json={"stock_minimo": 2})
    assert alertas(client, h, p.id, "activa") == []


def test_superusuario_gestiona_categorias(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    h = superuser_token_headers
    r = client.post(f"{API}/categorias/", headers=h, json={"nombre": "Lácteos"})
    assert r.status_code == 200
    id = r.json()["id"]
    r = client.patch(
        f"{API}/categorias/{id}", headers=h, json={"nombre": "Lácteos y huevos"}
    )
    assert r.json()["nombre"] == "Lácteos y huevos"
    assert client.delete(f"{API}/categorias/{id}", headers=h).status_code == 200
    assert client.delete(f"{API}/categorias/{id}", headers=h).status_code == 404
