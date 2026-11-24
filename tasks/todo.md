# Tareas

Plan: `tasks/plan.md`. Reparto y reglas para trabajar en paralelo: sección "Reparto del equipo" del plan.

Comandos de verificación:
- Backend: `cd backend && uv run bash scripts/test.sh`
- Frontend: `cd frontend && bun run build && bun run lint`
- E2E: `bun run test` (Playwright, con el backend y el frontend corriendo)
- Cliente: `bash scripts/generate-client.sh` después de cambiar modelos o rutas

---

## Fase 1: Catálogo

### Tarea 1: Lista de productos con stock

**Responsable:** A (hecha)

**Descripción:** La página `/productos` muestra el catálogo con `DataTable`: nombre, categoría, unidad, stock actual, stock mínimo y un indicador visible cuando el stock está por debajo del mínimo. Usa `ProductosService.readProductos` y `CategoriasService.readCategorias` para mostrar el nombre de la categoría.

**Criterios de aceptación:**
- [x] La tabla lista todos los productos con su stock calculado por la API
- [x] Los productos con `stock < stock_minimo` se distinguen con un `Badge` y texto, no solo con color
- [x] Mientras carga se ve un estado de carga, y si no hay productos, un mensaje de vacío

**Verificación:**
- [x] `bun run build` y `bun run lint` pasan
- [x] Nuevo `frontend/tests/productos.spec.ts`: crea un producto por la API y lo ve en la tabla
- [x] Manual: un producto con stock 0 y mínimo 5 aparece marcado (lo cubre la prueba E2E)

**Dependencias:** Ninguna

**Archivos probables:**
- `frontend/src/routes/_layout/productos.tsx`
- `frontend/src/components/Productos/columns.tsx`
- `frontend/tests/productos.spec.ts`

**Tamaño:** S

### Tarea 2: Crear, editar y borrar productos (superusuario)

**Responsable:** A

**Descripción:** Diálogos para crear y editar un producto (nombre, unidad, stock mínimo, categoría, `alerta_caducidad`) y para borrarlo, siguiendo el patrón de `Admin/AddUser`, `EditUser` y `DeleteUser`. Solo los ve un superusuario. Si el producto tiene movimientos, el borrado devuelve 409 (RN-07) y ese error se muestra como mensaje legible.

**Criterios de aceptación:**
- [ ] Un superusuario crea, edita y borra productos; la tabla se actualiza sin recargar
- [ ] Un usuario normal no ve los botones de crear, editar ni borrar
- [ ] Borrar un producto con movimientos muestra el motivo, sin error genérico

**Verificación:**
- [ ] `bun run build` y `bun run lint` pasan
- [ ] `productos.spec.ts`: flujo de crear, editar y borrar, más el caso del 409
- [ ] Manual: entrar con un usuario normal y comprobar que no ve las acciones

**Dependencias:** Tarea 1

**Archivos probables:**
- `frontend/src/components/Productos/AddProducto.tsx`
- `frontend/src/components/Productos/EditProducto.tsx`
- `frontend/src/components/Productos/DeleteProducto.tsx`
- `frontend/src/components/Productos/ProductoActionsMenu.tsx`
- `frontend/tests/productos.spec.ts`

**Tamaño:** M

### Tarea 3: Gestionar categorías (superusuario)

**Responsable:** A

**Descripción:** Crear, renombrar y borrar categorías desde un diálogo en `/productos`, para no añadir otra página. Borrar una categoría que tiene productos devuelve 409 y se muestra el motivo.

**Criterios de aceptación:**
- [ ] Un superusuario crea, renombra y borra categorías
- [ ] Una categoría nueva aparece de inmediato en el selector del formulario de producto
- [ ] Borrar una categoría en uso muestra el motivo

**Verificación:**
- [ ] `bun run build` y `bun run lint` pasan
- [ ] `productos.spec.ts`: crear una categoría y usarla en un producto nuevo

**Dependencias:** Tarea 2

**Archivos probables:**
- `frontend/src/components/Productos/Categorias.tsx`
- `frontend/src/routes/_layout/productos.tsx`

**Tamaño:** S

### Checkpoint: Catálogo
- [ ] Pruebas de backend y E2E en verde, `bun run build` limpio
- [ ] Un superusuario monta el catálogo completo sin usar `/docs`
- [ ] Revisión con el equipo antes de seguir

---

## Fase 2: Movimientos

### Tarea 4: Registrar entradas e historial de entradas

**Responsable:** B

**Descripción:** En `/entradas`, un formulario para registrar una entrada: producto, cantidad entera positiva, fecha de vencimiento y nota. La fecha es obligatoria si el producto tiene `alerta_caducidad`. Debajo, la tabla de entradas recientes. El backend necesita un filtro `tipo` en `GET /transacciones`, con su prueba. La tabla muestra el nombre del producto, no su id.

**Criterios de aceptación:**
- [ ] `GET /transacciones?tipo=entrada` devuelve solo entradas (prueba en `test_inventario.py`)
- [ ] El formulario pide la fecha de vencimiento solo cuando el producto la exige, y muestra el 400 de la API si falta
- [ ] Al registrar, la tabla y el stock de `/productos` se actualizan, invalidando las consultas de TanStack Query

**Verificación:**
- [ ] `uv run bash scripts/test.sh` pasa
- [ ] Cliente regenerado; `bun run build` y `bun run lint` pasan
- [ ] Nuevo `frontend/tests/movimientos.spec.ts`: registrar una entrada y ver el stock actualizado

**Dependencias:** Tarea 1

**Archivos probables:**
- `backend/app/api/routes/transacciones.py`
- `backend/tests/api/routes/test_inventario.py`
- `frontend/src/client/` (regenerado)
- `frontend/src/routes/_layout/entradas.tsx`
- `frontend/src/components/Movimientos/MovimientoForm.tsx`

**Tamaño:** M

### Tarea 5: Registrar salidas e historial de salidas

**Responsable:** B

**Descripción:** `/salidas` reutiliza el formulario de la Tarea 4 con `tipo=salida` y sin fecha de vencimiento. Muestra el stock disponible del producto elegido. Si la cantidad supera el stock (RN-04), se ve el mensaje de la API ("Stock insuficiente: hay N …").

**Criterios de aceptación:**
- [ ] Registrar una salida válida descuenta el stock
- [ ] Una salida mayor que el stock muestra el error de stock insuficiente y no registra nada
- [ ] Una salida que deja el stock bajo el mínimo genera la alerta (la crea el backend; aquí se comprueba de punta a punta)

**Verificación:**
- [ ] `bun run build` y `bun run lint` pasan
- [ ] `movimientos.spec.ts`: una salida válida y una salida con stock insuficiente

**Dependencias:** Tarea 4

**Archivos probables:**
- `frontend/src/routes/_layout/salidas.tsx`
- `frontend/src/components/Movimientos/MovimientoForm.tsx`

**Tamaño:** S

### Tarea 6: Ajustes de inventario (superusuario)

**Responsable:** B

**Descripción:** En los formularios de entrada y salida, una casilla "Es ajuste" que solo ve el superusuario (CU-10, CA-10). Un ajuste de entrada no exige fecha de vencimiento. Los ajustes se distinguen en el historial.

**Criterios de aceptación:**
- [ ] Solo el superusuario ve la casilla
- [ ] Un ajuste de entrada se registra sin fecha de vencimiento
- [ ] El historial marca los ajustes con un `Badge`

**Verificación:**
- [ ] `bun run build` y `bun run lint` pasan
- [ ] `movimientos.spec.ts`: ajuste como superusuario; la casilla no aparece para un usuario normal

**Dependencias:** Tareas 4 y 5

**Archivos probables:**
- `frontend/src/components/Movimientos/MovimientoForm.tsx`
- `frontend/src/components/Movimientos/columns.tsx`

**Tamaño:** S

### Checkpoint: Movimientos
- [ ] Pruebas de backend y E2E en verde
- [ ] Flujo completo: crear un producto, registrar una entrada, registrar una salida y ver el stock y la alerta
- [ ] Revisar la propuesta contra lo construido (riesgo 1 del plan)

---

## Fase 3: Alertas

### Tarea 7: Dashboard con alertas activas

**Responsable:** B

**Descripción:** El dashboard (`/`) reemplaza el saludo en inglés de la plantilla por la lista de alertas activas (`AlertasService.readAlertas`): tipo, producto y mensaje, con enlace a `/productos`. Si no hay alertas, muestra un estado vacío.

**Criterios de aceptación:**
- [ ] Las alertas activas aparecen ordenadas de la más reciente a la más antigua
- [ ] Cuando el stock se recupera, la alerta desaparece del dashboard
- [ ] No queda texto en inglés de la plantilla en el dashboard
- [ ] Crear un producto con `stock_minimo` > 0 abre su alerta de inmediato. Hoy `create_producto` no llama a `crud.sincronizar_alerta_stock`, y la alerta no aparece hasta el primer movimiento (prueba en `test_inventario.py`)

**Verificación:**
- [ ] `bun run build` y `bun run lint` pasan
- [ ] Nuevo `frontend/tests/dashboard.spec.ts`: una salida bajo el mínimo hace aparecer la alerta, y una entrada la quita

**Dependencias:** Tarea 5, solo para la prueba E2E. Con el arreglo de `create_producto`, la página puede empezarse antes.

**Archivos probables:**
- `backend/app/api/routes/productos.py` (una línea en `create_producto`)
- `backend/tests/api/routes/test_inventario.py`
- `frontend/src/routes/_layout/index.tsx`
- `frontend/tests/dashboard.spec.ts`

**Tamaño:** S


### Tarea 8: Alertas de caducidad automáticas (RF-023)

**Responsable:** A

**Descripción:** `crud.sincronizar_alertas_caducidad` crea una alerta `caducidad`, enlazada a la entrada (`transaccion_id`), cuando un lote vence en `DIAS_AVISO_CADUCIDAD` días o menos (5 por defecto, en `Settings`) y el producto tiene `alerta_caducidad` y stock > 0. Hay una sola alerta por lote, cualquiera que sea su estado, para que una alerta cerrada no reaparezca. Las alertas activas de caducidad del producto se cierran cuando su stock llega a 0. No se cierran al pasar la fecha. La función se llama desde `GET /alertas` y desde `crud.registrar_transaccion`. El dashboard de la Tarea 7 las muestra sin cambios.

**Criterios de aceptación:**
- [ ] Un lote que vence dentro de 5 días, con stock > 0, genera una sola alerta, aunque `GET /alertas` se llame varias veces
- [ ] No se genera alerta para un lote que vence en más de 5 días, para un producto sin stock ni para uno con `alerta_caducidad = false`
- [ ] Una salida que deja el producto en 0 cierra sus alertas de caducidad; un lote ya vencido con stock sigue con la alerta activa

**Verificación:**
- [ ] Pruebas nuevas en `backend/tests/crud/test_caducidad.py`; `uv run bash scripts/test.sh` pasa
- [ ] README: quitar "Falta generar la alerta…" de RF-023 y documentar `DIAS_AVISO_CADUCIDAD`

**Dependencias:** Ninguna para el backend. La Tarea 7 (B) solo hace falta para ver la alerta en el dashboard.

**Archivos probables:**
- `backend/app/crud.py`
- `backend/app/api/routes/alertas.py`
- `backend/app/core/config.py`
- `backend/tests/crud/test_caducidad.py`
- `README.md`

**Tamaño:** M

### Tarea 9: Descartar alertas de caducidad a mano

**Responsable:** A

**Descripción:** `POST /alertas/{id}/cerrar` cierra una alerta de caducidad: estado `cerrada` y `fecha_cierre`. Puede usarlo cualquier usuario. Las alertas de stock mínimo no se descartan a mano, porque el backend las volvería a abrir mientras el stock siga bajo (responde 400). En el dashboard, cada alerta de caducidad tiene un botón "Descartar".

**Criterios de aceptación:**
- [ ] Descartar una alerta de caducidad la quita del dashboard, y no vuelve a aparecer en la siguiente consulta
- [ ] Intentar cerrar una alerta de stock mínimo devuelve 400, y la UI no muestra el botón
- [ ] Cerrar una alerta que no existe devuelve 404

**Verificación:**
- [ ] Pruebas en `test_caducidad.py` o `test_inventario.py`; `uv run bash scripts/test.sh` pasa
- [ ] Cliente regenerado; `bun run build` y `bun run lint` pasan
- [ ] `dashboard.spec.ts`: descartar una alerta de caducidad

**Dependencias:** Tarea 8 (A) y Tarea 7 (B), por el botón en el dashboard

**Archivos probables:**
- `backend/app/api/routes/alertas.py`
- `backend/tests/crud/test_caducidad.py`
- `frontend/src/client/` (regenerado)
- `frontend/src/routes/_layout/index.tsx`

**Tamaño:** S

### Checkpoint: Alertas
- [ ] Pruebas de backend y E2E en verde
- [ ] Las alertas de stock y de caducidad se ven en el dashboard; las de caducidad se pueden descartar

---

## Fase 4: Informes

### Tarea 10: Resumen diario y mensual

**Responsable:** C

**Descripción:** `GET /informes/resumen?desde=…&hasta=…` recibe dos `datetime` con zona horaria (`hasta` excluido) y devuelve, por producto: nombre, unidad, stock inicial (suma de movimientos antes de `desde`), entradas, salidas y stock final. Los ajustes cuentan dentro de entradas y salidas. Todo se calcula en una consulta SQL, reutilizando `_cantidad_con_signo`. En `/informes` se elige "Día" o "Mes" y una fecha. El frontend calcula los límites en la hora local y muestra la tabla.

**Criterios de aceptación:**
- [ ] Para un día con movimientos conocidos, el stock inicial + entradas − salidas = stock final, y coincide con el stock de `/productos` cuando el periodo llega hasta hoy (prueba en backend)
- [ ] Un movimiento justo en `desde` cuenta en el periodo, y uno justo en `hasta` no (prueba en backend)
- [ ] Un movimiento a las 8 p. m. hora local aparece en ese día, no en el siguiente
- [ ] Los productos sin movimientos en el periodo aparecen con su stock, y entradas y salidas en 0

**Verificación:**
- [ ] Nuevo `backend/tests/api/routes/test_informes.py`; `uv run bash scripts/test.sh` pasa
- [ ] Cliente regenerado; `bun run build` y `bun run lint` pasan
- [ ] Manual: el resumen del mes coincide con los movimientos registrados en las fases anteriores

**Dependencias:** Ninguna. Usa las transacciones que ya existen.

**Archivos probables:**
- `backend/app/api/routes/informes.py` (nuevo) y `backend/app/api/main.py`
- `backend/app/models.py` (`ResumenProducto`, `ResumenPublic`)
- `backend/tests/api/routes/test_informes.py`
- `frontend/src/client/` (regenerado)
- `frontend/src/routes/_layout/informes.tsx`

**Tamaño:** M

### Tarea 11: Exportar el resumen a Excel (.xlsx)

**Responsable:** C

**Descripción:** Un botón "Excel" en `/informes` descarga el resumen que se está viendo como `.xlsx`: periodo en el título, columnas con nombre en español y cantidades como números, no como texto. La librería se carga con `import()` solo al pulsar el botón. Antes de elegirla, comprobar en su documentación la versión actual y que no tenga vulnerabilidades conocidas.

**Criterios de aceptación:**
- [ ] El archivo se abre en Excel con tildes correctas y las cantidades como números
- [ ] El nombre del archivo incluye el periodo (`resumen-2026-11.xlsx`, `resumen-2026-11-18.xlsx`)
- [ ] La librería no está en el bundle inicial

**Verificación:**
- [ ] `bun run build` y `bun run lint` pasan; en la salida de `vite build`, la librería aparece en un chunk aparte
- [ ] `frontend/tests/informes.spec.ts`: la descarga ocurre y el nombre es el esperado
- [ ] Manual: abrir el archivo en Excel

**Dependencias:** Tarea 10

**Archivos probables:**
- `frontend/package.json`
- `frontend/src/routes/_layout/informes.tsx`
- `frontend/tests/informes.spec.ts`

**Tamaño:** S

### Tarea 12: Exportar el resumen a PDF

**Responsable:** C

**Descripción:** Un botón "PDF" descarga el mismo resumen como PDF: título, periodo, fecha de generación y la tabla. La librería se carga con `import()`, igual que en la Tarea 11.

**Criterios de aceptación:**
- [ ] El PDF muestra el título, el periodo y la tabla completa, que continúa en páginas nuevas si no cabe
- [ ] Las tildes y la ñ se ven bien
- [ ] La librería no está en el bundle inicial

**Verificación:**
- [ ] `bun run build` y `bun run lint` pasan
- [ ] `informes.spec.ts`: la descarga ocurre
- [ ] Manual: abrir el PDF de un mes con más de 40 productos

**Dependencias:** Tarea 10. Puede hacerse en paralelo con la 11.

**Archivos probables:**
- `frontend/package.json`
- `frontend/src/routes/_layout/informes.tsx`

**Tamaño:** S

### Tarea 13: Aplicar el sistema de diseño Tahona

**Responsable:** A (hecha)

**Descripción:** Aplicar el kit de diseño (`tokens.css` y la guía de marca): colores de marca en `:root` y `.dark` de `index.css`, tokens nuevos `--brand` y `--destructive-foreground`, el logo `tahona-logo.webp` en lugar del de FastAPI, y el foco de teclado y los botones e insignias rojos con el contraste que pide el kit.

**Criterios de aceptación:**
- [x] Los tokens de `index.css` tienen los valores del kit en los dos temas
- [x] Botones e insignias `destructive` usan `destructive-foreground`, no blanco, y el anillo de foco usa `ring` sin opacidad
- [x] La barra lateral y el login muestran el logo de Tahona (32px o más); con la barra contraída se lee «Tahona» en texto

**Verificación:**
- [x] `bun run build` y `bun run lint` pasan
- [x] Manual: capturas del login y de `/productos` en claro y oscuro, foco de teclado y barra contraída

**Dependencias:** Ninguna

**Tamaño:** S

### Tarea 14: Traducir al español los textos de la plantilla

**Responsable:** A (hecha)

**Descripción:** Login, recuperar y restablecer contraseña, ajustes, usuarios, tabla paginada, menús, avisos y páginas de error estaban en inglés. Se tradujeron con tuteo neutro, como pide el kit, y `index.html` pasa a `lang="es"`. El aviso de eliminar usuario ahora dice lo que ocurre de verdad: no se puede eliminar un usuario con movimientos. El pie de página ya no enlaza a las redes de FastAPI.

**Criterios de aceptación:**
- [x] No queda texto visible en inglés en el frontend, salvo los mensajes de error que envía el backend
- [x] Los tests E2E buscan los textos en español

**Verificación:**
- [x] `bun run build` y `bun run lint` pasan; `bun run test`: 42 de 44 (los 2 fallos son los de paginación que arregla la Tarea 2)

**Dependencias:** Ninguna. Al fusionar con la Tarea 2, `findRow` en `tests/utils/inventario.ts` debe buscar «Ir a la página siguiente» en lugar de «Go to next page».

**Tamaño:** M

### Checkpoint: Completo
- [ ] Todas las pruebas en verde y `bun run build` limpio
- [ ] Los criterios de aceptación de la propuesta están cubiertos
- [ ] README actualizado ("Dónde está cada cosa" y "Decisiones")
- [ ] Listo para el PR de `feature/base-architecture` a `main`
