import uuid
from typing import Any

from sqlmodel import Session, case, col, func, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Alerta,
    EstadoAlerta,
    Producto,
    TipoAlerta,
    TipoTransaccion,
    Transaccion,
    TransaccionCreate,
    User,
    UserCreate,
    UserUpdate,
    get_datetime_utc,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


class StockInsuficiente(Exception):
    def __init__(self, disponible: int) -> None:
        self.disponible = disponible


def _cantidad_con_signo() -> Any:
    return case(
        (col(Transaccion.tipo) == TipoTransaccion.salida, -col(Transaccion.cantidad)),
        else_=col(Transaccion.cantidad),
    )


def stock_por_producto() -> Any:
    """Subquery (producto_id, stock) for joining onto producto queries. RN-01."""
    return (
        select(
            col(Transaccion.producto_id).label("producto_id"),
            func.sum(_cantidad_con_signo()).label("stock"),
        )
        .group_by(col(Transaccion.producto_id))
        .subquery()
    )


def get_stock(*, session: Session, producto_id: uuid.UUID) -> int:
    statement = select(func.coalesce(func.sum(_cantidad_con_signo()), 0)).where(
        Transaccion.producto_id == producto_id
    )
    return int(session.exec(statement).one())


def sincronizar_alerta_stock(*, session: Session, producto: Producto) -> None:
    """RN-10/RN-11: one active alert while stock < stock_minimo, closed once it recovers."""
    stock = get_stock(session=session, producto_id=producto.id)
    activa = session.exec(
        select(Alerta).where(
            Alerta.producto_id == producto.id,
            Alerta.tipo == TipoAlerta.stock_minimo,
            Alerta.estado == EstadoAlerta.activa,
        )
    ).first()
    if stock < producto.stock_minimo and not activa:
        session.add(
            Alerta(
                tipo=TipoAlerta.stock_minimo,
                producto_id=producto.id,
                mensaje=f"{producto.nombre}: quedan {stock} {producto.unidad} "
                f"(mínimo {producto.stock_minimo})",
            )
        )
    elif stock >= producto.stock_minimo and activa:
        activa.estado = EstadoAlerta.cerrada
        activa.fecha_cierre = get_datetime_utc()
        session.add(activa)


def registrar_transaccion(
    *,
    session: Session,
    producto: Producto,
    transaccion_in: TransaccionCreate,
    usuario_id: uuid.UUID,
) -> Transaccion:
    # RNF-010: lock the producto row so concurrent salidas can't both pass the stock check
    session.refresh(producto, with_for_update=True)
    if transaccion_in.tipo == TipoTransaccion.salida:
        disponible = get_stock(session=session, producto_id=producto.id)
        if transaccion_in.cantidad > disponible:  # RN-04
            session.rollback()
            raise StockInsuficiente(disponible)
    transaccion = Transaccion.model_validate(
        transaccion_in, update={"usuario_id": usuario_id}
    )
    session.add(transaccion)
    session.flush()
    sincronizar_alerta_stock(session=session, producto=producto)
    session.commit()
    session.refresh(transaccion)
    return transaccion
