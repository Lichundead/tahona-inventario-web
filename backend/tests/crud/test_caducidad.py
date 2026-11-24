from datetime import timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import (
    Alerta,
    EstadoAlerta,
    Producto,
    TipoAlerta,
    TipoTransaccion,
    TransaccionCreate,
    get_datetime_utc,
)
from tests.utils.inventario import create_random_producto
from tests.utils.user import create_random_user

DIAS = settings.DIAS_AVISO_CADUCIDAD


def mover(
    db: Session,
    producto: Producto,
    tipo: TipoTransaccion,
    cantidad: int,
    vence_en_dias: int | None = None,
) -> None:
    vence = (
        get_datetime_utc().date() + timedelta(days=vence_en_dias)
        if vence_en_dias is not None
        else None
    )
    crud.registrar_transaccion(
        session=db,
        producto=producto,
        transaccion_in=TransaccionCreate(
            tipo=tipo,
            cantidad=cantidad,
            fecha_vencimiento=vence,
            producto_id=producto.id,
        ),
        usuario_id=create_random_user(db).id,
    )


def alertas_caducidad(db: Session, producto: Producto) -> list[Alerta]:
    db.expire_all()  # the API writes through its own session
    return list(
        db.exec(
            select(Alerta).where(
                Alerta.producto_id == producto.id,
                Alerta.tipo == TipoAlerta.caducidad,
            )
        ).all()
    )


def test_lote_por_vencer_genera_una_sola_alerta(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    producto = create_random_producto(db, alerta_caducidad=True)
    mover(db, producto, TipoTransaccion.entrada, 3, vence_en_dias=DIAS)
    for _ in range(3):
        r = client.get(
            f"{settings.API_V1_STR}/alertas/", headers=normal_user_token_headers
        )
        assert r.status_code == 200
    alertas = alertas_caducidad(db, producto)
    assert len(alertas) == 1
    assert alertas[0].estado == EstadoAlerta.activa
    assert alertas[0].transaccion_id is not None


def test_sin_alerta_si_vence_lejos_sin_stock_o_desactivada(db: Session) -> None:
    lejos = create_random_producto(db, alerta_caducidad=True)
    mover(db, lejos, TipoTransaccion.entrada, 3, vence_en_dias=DIAS + 1)

    desactivada = create_random_producto(db, alerta_caducidad=False)
    mover(db, desactivada, TipoTransaccion.entrada, 3, vence_en_dias=1)

    sin_stock = create_random_producto(db, alerta_caducidad=True)
    mover(db, sin_stock, TipoTransaccion.entrada, 3, vence_en_dias=DIAS + 1)
    mover(db, sin_stock, TipoTransaccion.salida, 3)

    crud.sincronizar_alertas_caducidad(session=db)
    db.commit()
    for producto in (lejos, desactivada, sin_stock):
        assert alertas_caducidad(db, producto) == []


def test_salida_a_cero_cierra_y_lote_vencido_sigue_activo(db: Session) -> None:
    agotado = create_random_producto(db, alerta_caducidad=True)
    mover(db, agotado, TipoTransaccion.entrada, 2, vence_en_dias=1)
    assert len(alertas_caducidad(db, agotado)) == 1
    mover(db, agotado, TipoTransaccion.salida, 2)
    [alerta] = alertas_caducidad(db, agotado)
    assert alerta.estado == EstadoAlerta.cerrada
    assert alerta.fecha_cierre is not None

    # A closed alert stays closed even if the producto gets stock again
    mover(db, agotado, TipoTransaccion.entrada, 1, vence_en_dias=DIAS + 10)
    assert [a.estado for a in alertas_caducidad(db, agotado)] == [EstadoAlerta.cerrada]

    vencido = create_random_producto(db, alerta_caducidad=True)
    mover(db, vencido, TipoTransaccion.entrada, 2, vence_en_dias=-3)
    crud.sincronizar_alertas_caducidad(session=db)
    db.commit()
    [alerta] = alertas_caducidad(db, vencido)
    assert alerta.estado == EstadoAlerta.activa
