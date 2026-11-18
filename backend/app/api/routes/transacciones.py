import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_user
from app.models import (
    Producto,
    TipoTransaccion,
    Transaccion,
    TransaccionCreate,
    TransaccionesPublic,
    TransaccionPublic,
)

router = APIRouter(prefix="/transacciones", tags=["transacciones"])


@router.get(
    "/", dependencies=[Depends(get_current_user)], response_model=TransaccionesPublic
)
def read_transacciones(
    session: SessionDep,
    producto_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve transacciones, newest first, optionally for one producto.
    """
    count_statement = select(func.count()).select_from(Transaccion)
    statement = select(Transaccion)
    if producto_id:
        count_statement = count_statement.where(Transaccion.producto_id == producto_id)
        statement = statement.where(Transaccion.producto_id == producto_id)
    count = session.exec(count_statement).one()
    statement = (
        statement.order_by(col(Transaccion.fecha).desc()).offset(skip).limit(limit)
    )
    transacciones = session.exec(statement).all()
    return TransaccionesPublic(
        data=[TransaccionPublic.model_validate(t) for t in transacciones], count=count
    )


@router.post("/", response_model=TransaccionPublic)
def create_transaccion(
    *, session: SessionDep, current_user: CurrentUser, transaccion_in: TransaccionCreate
) -> Any:
    """
    Register an entrada or salida. The stock is recalculated and alerts updated.
    """
    producto = session.get(Producto, transaccion_in.producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if transaccion_in.es_ajuste and not current_user.is_superuser:  # CU-10
        raise HTTPException(
            status_code=403, detail="Solo la administración puede registrar ajustes"
        )
    es_entrada = transaccion_in.tipo == TipoTransaccion.entrada
    if (
        es_entrada
        and producto.alerta_caducidad
        and not transaccion_in.es_ajuste
        and transaccion_in.fecha_vencimiento is None
    ):
        raise HTTPException(
            status_code=400, detail="Indica la fecha de vencimiento del lote"
        )
    if not es_entrada and transaccion_in.fecha_vencimiento is not None:
        raise HTTPException(
            status_code=400, detail="Las salidas no llevan fecha de vencimiento"
        )
    try:
        return crud.registrar_transaccion(
            session=session,
            producto=producto,
            transaccion_in=transaccion_in,
            usuario_id=current_user.id,
        )
    except crud.StockInsuficiente as e:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente: hay {e.disponible} {producto.unidad}",
        )
