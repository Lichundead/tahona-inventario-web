import uuid
from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import EmailStr
from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    full_name: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(default_factory=get_datetime_utc)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Categoría
class CategoriaBase(SQLModel):
    nombre: str = Field(unique=True, min_length=1, max_length=100)


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)


class Categoria(CategoriaBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(default_factory=get_datetime_utc)


class CategoriaPublic(CategoriaBase):
    id: uuid.UUID


class CategoriasPublic(SQLModel):
    data: list[CategoriaPublic]
    count: int


# Producto. RN-01/RN-02: only stock_minimo is stored; stock is computed from transacciones
class ProductoBase(SQLModel):
    nombre: str = Field(unique=True, index=True, min_length=1, max_length=255)
    # Packaging unit counted in whole numbers: "bulto", "botella", "unidad"
    unidad: str = Field(default="unidad", min_length=1, max_length=50)
    stock_minimo: int = Field(default=0, ge=0)
    alerta_caducidad: bool = True
    categoria_id: uuid.UUID = Field(foreign_key="categoria.id", ondelete="RESTRICT")


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(SQLModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    unidad: str | None = Field(default=None, min_length=1, max_length=50)
    stock_minimo: int | None = Field(default=None, ge=0)
    alerta_caducidad: bool | None = None
    categoria_id: uuid.UUID | None = None


class Producto(ProductoBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(default_factory=get_datetime_utc)


class ProductoPublic(ProductoBase):
    id: uuid.UUID
    created_at: datetime | None = None
    stock: int = 0


class ProductosPublic(SQLModel):
    data: list[ProductoPublic]
    count: int


# Transacción. RN-06: never edited or deleted; corrections are new rows with es_ajuste
class TipoTransaccion(StrEnum):
    entrada = "entrada"
    salida = "salida"


class TransaccionBase(SQLModel):
    tipo: TipoTransaccion
    cantidad: int = Field(gt=0)  # RN-03
    es_ajuste: bool = False
    # Batch expiry, required on entradas of productos with alerta_caducidad
    fecha_vencimiento: date | None = None
    nota: str | None = Field(default=None, max_length=255)
    producto_id: uuid.UUID = Field(foreign_key="producto.id", ondelete="RESTRICT")


class TransaccionCreate(TransaccionBase):
    pass


class Transaccion(TransaccionBase, table=True):
    __table_args__ = (CheckConstraint("cantidad > 0", name="cantidad_positiva"),)
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    fecha: datetime = Field(default_factory=get_datetime_utc, index=True)
    usuario_id: uuid.UUID = Field(foreign_key="user.id", ondelete="RESTRICT")


class TransaccionPublic(TransaccionBase):
    id: uuid.UUID
    fecha: datetime
    usuario_id: uuid.UUID


class TransaccionesPublic(SQLModel):
    data: list[TransaccionPublic]
    count: int


# Alerta
class TipoAlerta(StrEnum):
    stock_minimo = "stock_minimo"
    caducidad = "caducidad"


class EstadoAlerta(StrEnum):
    activa = "activa"
    cerrada = "cerrada"


class Alerta(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tipo: TipoAlerta
    estado: EstadoAlerta = Field(default=EstadoAlerta.activa, index=True)
    mensaje: str = Field(max_length=255)
    fecha_generacion: datetime = Field(default_factory=get_datetime_utc)
    fecha_cierre: datetime | None = None
    producto_id: uuid.UUID = Field(foreign_key="producto.id", ondelete="CASCADE")
    # The entrada (batch) a caducidad alert refers to
    transaccion_id: uuid.UUID | None = Field(
        default=None, foreign_key="transaccion.id", ondelete="CASCADE"
    )


class AlertaPublic(SQLModel):
    id: uuid.UUID
    tipo: TipoAlerta
    estado: EstadoAlerta
    mensaje: str
    fecha_generacion: datetime
    fecha_cierre: datetime | None
    producto_id: uuid.UUID
    transaccion_id: uuid.UUID | None


class AlertasPublic(SQLModel):
    data: list[AlertaPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
