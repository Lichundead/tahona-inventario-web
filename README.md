# Tahona Inventario

Aplicación web de inventario para la Pastelería Tahona. Basada en [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template): FastAPI + SQLModel + PostgreSQL en el backend, React 19 + TanStack Router/Query + Tailwind en el frontend.

## Ejecutar en local

Requisitos: [uv](https://docs.astral.sh/uv/), [bun](https://bun.sh) y Docker (o un PostgreSQL propio).

```bash
cp .env.example .env && cp frontend/.env.example frontend/.env
docker compose up -d db mailpit          # PostgreSQL y correo de prueba

cd backend
uv sync
uv run bash scripts/prestart.sh          # migraciones + superusuario inicial
uv run fastapi dev                       # API en http://localhost:8000/docs

cd ..                                     # en otra terminal
bun install
bun run dev                              # frontend en http://localhost:5173
```

Sin Docker: apunta `DATABASE_URL` a tu PostgreSQL, por ejemplo
`DATABASE_URL=postgresql://postgres:x@localhost:5433/app uv run fastapi dev`.

Superusuario inicial: `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` en `.env` (copiado de `.env.example`, no se versiona).

Después de cambiar modelos o rutas del backend:

```bash
cd backend && uv run alembic revision --autogenerate -m "describe el cambio"
cd .. && bash scripts/generate-client.sh   # regenera frontend/src/client
```

Pruebas del backend: `cd backend && uv run bash scripts/test.sh`.

## Dónde está cada cosa

| Qué | Dónde |
| --- | --- |
| Modelos y esquemas (Categoria, Producto, Transaccion, Alerta) | `backend/app/models.py` |
| Cálculo de stock, bloqueo de salidas concurrentes, alertas de stock mínimo | `backend/app/crud.py` |
| Endpoints `/api/v1/categorias`, `/productos`, `/transacciones`, `/alertas` | `backend/app/api/routes/` |
| Respuesta HTTP 409 a los errores de integridad (RT-06) | `backend/app/main.py` |
| Pruebas de los criterios de aceptación CA-02 a CA-10 y RNF-010 | `backend/tests/api/routes/test_inventario.py`, `backend/tests/crud/test_transaccion.py` |
| Páginas del frontend | `frontend/src/routes/_layout/` |

## Decisiones respecto a la propuesta

- RT-01: la plantilla ya no usa Copier, así que se copió con "Use this template".
- RN-03: las cantidades siguen siendo enteras. Cada producto tiene un campo `unidad` (bulto, botella, unidad) para saber qué se cuenta.
- RF-019 y CA-10: la Tabla 14 de la propuesta trata el ajuste como un tercer tipo de transacción. Aquí un ajuste es una entrada o salida con `es_ajuste = true`, que solo registra el superusuario, y su cantidad siempre es positiva.
- RF-023: cada producto tiene `alerta_caducidad`, activada por defecto, y con ella cada entrada exige `fecha_vencimiento`. Falta generar la alerta cuando un lote vence en N días y el producto aún tiene stock. Esa alerta no sabrá qué lote consumió cada salida.
- RT-06: la propuesta menciona el código `23503`, pero PostgreSQL responde `23001` cuando un `ON DELETE RESTRICT` bloquea un borrado. La API responde 409 en los dos casos.
- RN-13: no hay registro abierto. Se quitaron `/users/signup` y la opción de que cada usuario elimine su propia cuenta.
