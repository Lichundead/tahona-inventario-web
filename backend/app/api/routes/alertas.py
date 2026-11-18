from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import col, func, select

from app.api.deps import SessionDep, get_current_user
from app.models import Alerta, AlertaPublic, AlertasPublic, EstadoAlerta

router = APIRouter(
    prefix="/alertas",
    tags=["alertas"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=AlertasPublic)
def read_alertas(
    session: SessionDep,
    estado: EstadoAlerta | None = EstadoAlerta.activa,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve alertas, active ones by default. Pass no estado to get all.
    """
    count_statement = select(func.count()).select_from(Alerta)
    statement = select(Alerta)
    if estado:
        count_statement = count_statement.where(Alerta.estado == estado)
        statement = statement.where(Alerta.estado == estado)
    count = session.exec(count_statement).one()
    statement = (
        statement.order_by(col(Alerta.fecha_generacion).desc())
        .offset(skip)
        .limit(limit)
    )
    alertas = session.exec(statement).all()
    return AlertasPublic(
        data=[AlertaPublic.model_validate(a) for a in alertas], count=count
    )
