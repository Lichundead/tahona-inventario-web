import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, func, select

from app import crud
from app.api.deps import SessionDep, get_current_active_superuser, get_current_user
from app.models import (
    Categoria,
    Message,
    Producto,
    ProductoCreate,
    ProductoPublic,
    ProductosPublic,
    ProductoUpdate,
)

router = APIRouter(
    prefix="/productos",
    tags=["productos"],
    dependencies=[Depends(get_current_user)],
)


def _publico(session: Session, producto: Producto) -> ProductoPublic:
    stock = crud.get_stock(session=session, producto_id=producto.id)
    return ProductoPublic.model_validate(producto, update={"stock": stock})


def _check_categoria(session: Session, categoria_id: uuid.UUID | None) -> None:
    if categoria_id and not session.get(Categoria, categoria_id):
        raise HTTPException(status_code=404, detail="Categoría no encontrada")


@router.get("/", response_model=ProductosPublic)
def read_productos(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve productos with their current stock.
    """
    count = session.exec(select(func.count()).select_from(Producto)).one()
    stock = crud.stock_por_producto()
    statement = (
        select(Producto, func.coalesce(stock.c.stock, 0))
        .outerjoin(stock, col(Producto.id) == stock.c.producto_id)
        .order_by(col(Producto.nombre))
        .offset(skip)
        .limit(limit)
    )
    data = [
        ProductoPublic.model_validate(producto, update={"stock": s})
        for producto, s in session.exec(statement).all()
    ]
    return ProductosPublic(data=data, count=count)


@router.get("/{id}", response_model=ProductoPublic)
def read_producto(session: SessionDep, id: uuid.UUID) -> Any:
    """
    Get producto by ID.
    """
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _publico(session, producto)


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=ProductoPublic,
)
def create_producto(*, session: SessionDep, producto_in: ProductoCreate) -> Any:
    """
    Create new producto.
    """
    _check_categoria(session, producto_in.categoria_id)
    producto = Producto.model_validate(producto_in)
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return _publico(session, producto)


@router.patch(
    "/{id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=ProductoPublic,
)
def update_producto(
    *, session: SessionDep, id: uuid.UUID, producto_in: ProductoUpdate
) -> Any:
    """
    Update a producto.
    """
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    _check_categoria(session, producto_in.categoria_id)
    producto.sqlmodel_update(producto_in.model_dump(exclude_unset=True))
    session.add(producto)
    # A new stock_minimo can open or close the alert without any movement
    crud.sincronizar_alerta_stock(session=session, producto=producto)
    session.commit()
    session.refresh(producto)
    return _publico(session, producto)


@router.delete("/{id}", dependencies=[Depends(get_current_active_superuser)])
def delete_producto(session: SessionDep, id: uuid.UUID) -> Message:
    """
    Delete a producto. RN-07: fails with 409 once it has transacciones.
    """
    producto = session.get(Producto, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    session.delete(producto)
    session.commit()
    return Message(message="Producto eliminado")
