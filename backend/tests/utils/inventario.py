from sqlmodel import Session

from app.models import Categoria, Producto
from tests.utils.utils import random_lower_string


def create_random_categoria(db: Session) -> Categoria:
    categoria = Categoria(nombre=random_lower_string())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def create_random_producto(
    db: Session, *, stock_minimo: int = 0, alerta_caducidad: bool = False
) -> Producto:
    categoria = create_random_categoria(db)
    producto = Producto(
        nombre=random_lower_string(),
        unidad="bulto",
        stock_minimo=stock_minimo,
        alerta_caducidad=alerta_caducidad,
        categoria_id=categoria.id,
    )
    db.add(producto)
    db.commit()
    db.refresh(producto)
    return producto
