import threading

from sqlmodel import Session

from app import crud
from app.core.db import engine
from app.models import Producto, TipoTransaccion, TransaccionCreate
from tests.utils.inventario import create_random_producto
from tests.utils.user import create_random_user


def test_salidas_simultaneas_no_dejan_stock_negativo(db: Session) -> None:
    # RNF-010: two salidas of the last unit at the same time; only one may pass
    producto = create_random_producto(db)
    usuario = create_random_user(db)
    crud.registrar_transaccion(
        session=db,
        producto=producto,
        transaccion_in=TransaccionCreate(
            tipo=TipoTransaccion.entrada, cantidad=1, producto_id=producto.id
        ),
        usuario_id=usuario.id,
    )
    barrera = threading.Barrier(2)
    resultados: list[str] = []

    def salida() -> None:
        with Session(engine) as session:
            p = session.get(Producto, producto.id)
            assert p
            barrera.wait()
            try:
                crud.registrar_transaccion(
                    session=session,
                    producto=p,
                    transaccion_in=TransaccionCreate(
                        tipo=TipoTransaccion.salida, cantidad=1, producto_id=p.id
                    ),
                    usuario_id=usuario.id,
                )
                resultados.append("ok")
            except crud.StockInsuficiente:
                resultados.append("sin stock")

    hilos = [threading.Thread(target=salida) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    assert sorted(resultados) == ["ok", "sin stock"]
    assert crud.get_stock(session=db, producto_id=producto.id) == 0
