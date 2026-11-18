# Tahona Inventario

Aplicación web de inventario para la Pastelería Tahona. Basada en [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template): FastAPI + SQLModel + PostgreSQL en el backend, React 19 + TanStack Router/Query + Tailwind en el frontend.

## Requisitos

Instala estas herramientas una sola vez. Después de instalar cada una, cierra y vuelve a abrir la terminal, y comprueba que funciona con el comando de la última columna.

| Herramienta | Para qué sirve | Cómo instalarla | Comprobar |
| --- | --- | --- | --- |
| [Git](https://git-scm.com/downloads) | Descargar el código y subir cambios | En Windows, el instalador trae Git Bash, que sirve para los comandos `bash` de este README | `git --version` |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Instala Python 3.14 y las dependencias del backend | macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh \| sh`<br>Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` | `uv --version` |
| [bun](https://bun.sh) | Instala las dependencias del frontend y lo arranca | macOS/Linux: `curl -fsSL https://bun.sh/install \| bash`<br>Windows (PowerShell): `powershell -c "irm bun.sh/install.ps1 \| iex"` | `bun --version` |
| Docker con Compose | Corre PostgreSQL y Mailpit sin instalarlos | Windows o macOS: [Docker Desktop](https://www.docker.com/products/docker-desktop/). En macOS también sirve [OrbStack](https://orbstack.dev), que es más liviano | `docker compose version` |

No hace falta instalar Python ni PostgreSQL por separado: uv descarga el Python correcto y Docker trae la base de datos. En macOS, `brew install docker` solo instala el comando `docker`, sin Compose ni el motor; usa Docker Desktop u OrbStack.

## Configuración inicial

Esto se hace una vez, después de clonar.

1. Descarga el código y entra a la carpeta:

   ```bash
   git clone https://github.com/Lichundead/tahona-inventario-web.git
   cd tahona-inventario-web
   ```

2. Crea tus archivos de configuración a partir de los de ejemplo. Los `.env` no se suben a GitHub, así que cada persona tiene los suyos:

   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   ```

   En PowerShell, usa `copy` en lugar de `cp`. Para trabajar en local no necesitas cambiar nada. Si quieres otro usuario administrador, edita `FIRST_SUPERUSER` y `FIRST_SUPERUSER_PASSWORD` en `.env` antes del paso 4.

3. Arranca la base de datos y el servidor de correo de prueba. Abre Docker Desktop u OrbStack antes, porque el motor tiene que estar corriendo:

   ```bash
   docker compose up -d db mailpit
   ```

   La base de datos usa el puerto 5432. Si tienes otro PostgreSQL abierto (por ejemplo Postgres.app), ciérralo primero.

4. Instala el backend, crea las tablas y el usuario administrador:

   ```bash
   cd backend
   uv sync
   uv run bash scripts/prestart.sh
   ```

   Si `bash` no existe en tu terminal de Windows, corre por separado `uv run alembic upgrade head` y `uv run python app/initial_data.py`, que es lo mismo que hace `prestart.sh`.

5. Arranca el backend y deja esa terminal abierta:

   ```bash
   uv run fastapi dev
   ```

6. En otra terminal, desde la carpeta principal del proyecto, instala y arranca el frontend:

   ```bash
   bun install
   bun run dev
   ```

7. Abre http://localhost:5173 y entra con el correo y la contraseña de `FIRST_SUPERUSER` y `FIRST_SUPERUSER_PASSWORD` (por defecto `admin@example.com` y `changethis`).

Otras direcciones útiles: la documentación interactiva de la API está en http://localhost:8000/docs, y los correos que envía la aplicación (por ejemplo, recuperar contraseña) llegan a Mailpit en http://localhost:8025.

## Día a día

Para volver a trabajar otro día, basta con los pasos 3, 5 y 6: `docker compose up -d db mailpit`, luego `uv run fastapi dev` en `backend/` y `bun run dev` en la carpeta principal. Para apagar la base de datos: `docker compose down` (los datos se conservan).

Después de cambiar modelos o rutas del backend:

```bash
cd backend && uv run alembic revision --autogenerate -m "describe el cambio"
cd .. && bash scripts/generate-client.sh   # regenera frontend/src/client
```

Pruebas del backend: `cd backend && uv run bash scripts/test.sh`. Las pruebas borran todos los usuarios y el inventario de la base de datos que usan, así que no las corras contra datos que quieras conservar.

Sin Docker: apunta `DATABASE_URL` a tu propio PostgreSQL, por ejemplo
`DATABASE_URL=postgresql://postgres:x@localhost:5433/app uv run fastapi dev`. Sin Mailpit, los correos de recuperación de contraseña no se envían.

## Problemas frecuentes

| Mensaje | Causa y solución |
| --- | --- |
| `unknown shorthand flag: 'd' in -d` o `unknown command: docker compose` | Falta Docker Compose. Instala Docker Desktop u OrbStack. |
| `failed to connect to the docker API` | El motor de Docker no está corriendo. Abre Docker Desktop u OrbStack. |
| `port is already allocated` al arrancar `db` | Otro programa usa el puerto 5432. Cierra el otro PostgreSQL. |
| `Field required` con `SECRET_KEY` o `DATABASE_URL` al arrancar el backend | Falta el archivo `.env`. Repite el paso 2. |
| La página carga pero no puedes iniciar sesión | El backend no está corriendo, o falta `frontend/.env`. Revisa los pasos 2 y 5. |

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
