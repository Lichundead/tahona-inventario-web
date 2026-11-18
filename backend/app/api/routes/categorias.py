import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, func, select

from app.api.deps import SessionDep, get_current_active_superuser, get_current_user
from app.models import (
    Categoria,
    CategoriaCreate,
    CategoriaPublic,
    CategoriasPublic,
    CategoriaUpdate,
    Message,
)

router = APIRouter(
    prefix="/categorias",
    tags=["categorias"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=CategoriasPublic)
def read_categorias(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve categorías.
    """
    count = session.exec(select(func.count()).select_from(Categoria)).one()
    statement = (
        select(Categoria).order_by(col(Categoria.nombre)).offset(skip).limit(limit)
    )
    categorias = session.exec(statement).all()
    return CategoriasPublic(
        data=[CategoriaPublic.model_validate(c) for c in categorias], count=count
    )


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=CategoriaPublic,
)
def create_categoria(*, session: SessionDep, categoria_in: CategoriaCreate) -> Any:
    """
    Create new categoría.
    """
    categoria = Categoria.model_validate(categoria_in)
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria


@router.patch(
    "/{id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=CategoriaPublic,
)
def update_categoria(
    *, session: SessionDep, id: uuid.UUID, categoria_in: CategoriaUpdate
) -> Any:
    """
    Update a categoría.
    """
    categoria = session.get(Categoria, id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    categoria.sqlmodel_update(categoria_in.model_dump(exclude_unset=True))
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria


@router.delete("/{id}", dependencies=[Depends(get_current_active_superuser)])
def delete_categoria(session: SessionDep, id: uuid.UUID) -> Message:
    """
    Delete a categoría. RN-08: fails with 409 while it has productos.
    """
    categoria = session.get(Categoria, id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    session.delete(categoria)
    session.commit()
    return Message(message="Categoría eliminada")
