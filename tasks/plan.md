# Plan de implementación: Tahona Inventario (frontend de inventario, caducidad e informes)

Fuente: `README.md` (sección "Decisiones respecto a la propuesta"). El documento de la propuesta (RF/RN/CA/CU) no está en el repositorio; este plan se basa en lo que el README y el código citan de él.

## Resumen

El backend del dominio de inventario ya existe: categorías, productos con stock calculado (RN-01), entradas y salidas con bloqueo de concurrencia (RNF-010), ajustes solo para superusuario (CU-10), alertas de stock mínimo (RN-10/RN-11) y 409 en errores de integridad (RT-06), con pruebas de CA-02 a CA-10. Las páginas del frontend (`productos`, `entradas`, `salidas`, `informes`, dashboard) son solo títulos. Falta:

1. Las pantallas que usan esa API.
2. La alerta de caducidad (RF-023), que el README marca como pendiente.
3. Los informes por periodo exportables a PDF y Excel.

## Decisiones de arquitectura

- **Rebanadas verticales.** Cada tarea entrega una pantalla usable de punta a punta. Los cambios de backend que una pantalla necesite (por ejemplo, filtrar transacciones por `tipo` o por fechas) van en la misma tarea, con su prueba y el cliente regenerado (`bash scripts/generate-client.sh`).
- **Reusar los patrones de la plantilla.** `DataTable`, más diálogos como `Admin/AddUser`, `EditUser` y `DeleteUser`, `useCustomToast` y `handleError`. Componentes nuevos en `frontend/src/components/<Dominio>/`. Sin librerías de UI nuevas.
- **Caducidad (RF-023).** `crud.sincronizar_alertas_caducidad` se llama desde `GET /alertas` y después de cada transacción, sin programador de tareas (no hay ninguno en el proyecto). El aviso se da con 5 días de antelación, en un ajuste global `DIAS_AVISO_CADUCIDAD` que se puede cambiar en `.env`. Hay una sola alerta por lote (`transaccion_id`), aunque se haya cerrado, para que no reaparezca. Se cierra sola cuando el producto se queda sin stock, o a mano. No se cierra al pasar la fecha: un lote vencido con stock es justo lo que hay que ver.
- **Resumen diario y mensual.** Un endpoint `GET /informes/resumen?desde&hasta` calcula en SQL, por producto: stock inicial, entradas, salidas y stock final. Los ajustes cuentan dentro de entradas y salidas. El frontend envía los límites del día o del mes calculados en la hora local del navegador, para que un movimiento de las 8 p. m. no caiga en el día siguiente (las fechas se guardan en UTC).
- **Exportar.** En el frontend, con el resumen ya cargado: `.xlsx` y PDF con tabla, con librerías cargadas con `import()` dinámico para no engordar el bundle inicial. Candidatas: `write-excel-file` o `exceljs`, y `jspdf` con `jspdf-autotable`. Versión y API se verifican en la documentación al implementar.
- **Permisos.** Un usuario normal ve el catálogo y registra entradas y salidas. No crea, edita ni borra categorías o productos, no registra ajustes y no gestiona usuarios. La API ya lo aplica así.

## Lista de tareas

Detalle y criterios de aceptación en `tasks/todo.md`.

### Fase 1: Catálogo
- [x] Tarea 1: Lista de productos con stock
- [x] Tarea 2: Crear, editar y borrar productos (superusuario)
- [ ] Tarea 3: Gestionar categorías (superusuario)

### Checkpoint: Catálogo

### Fase 2: Movimientos
- [ ] Tarea 4: Registrar entradas e historial de entradas
- [ ] Tarea 5: Registrar salidas e historial de salidas
- [ ] Tarea 6: Ajustes de inventario (superusuario)

### Checkpoint: Movimientos

### Fase 3: Alertas
- [ ] Tarea 7: Dashboard con alertas activas
- [ ] Tarea 8: Alertas de caducidad automáticas (RF-023)
- [ ] Tarea 9: Descartar alertas de caducidad a mano

### Checkpoint: Alertas

### Fase 4: Informes
- [ ] Tarea 10: Resumen diario y mensual
- [ ] Tarea 11: Exportar el resumen a Excel (.xlsx)
- [ ] Tarea 12: Exportar el resumen a PDF

### Tema
- [x] Tarea 13: Aplicar el sistema de diseño Tahona
- [x] Tarea 14: Traducir al español los textos de la plantilla

### Checkpoint: Completo

## Reparto del equipo

Tres personas. A es Sebastián, que hizo la Tarea 1. Cada una se queda con un área, para que casi no compartan archivos.

| Persona | Área | Tareas | Archivos propios |
|---|---|---|---|
| **A** (Sebastián) | Catálogo y caducidad | 2, 3, 8, 9 | `components/Productos/`, `routes/_layout/productos.tsx`, `crud.py` (caducidad), `routes/alertas.py`, `core/config.py` |
| **B** | Movimientos y dashboard | 4, 5, 6, 7 | `routes/transacciones.py`, `components/Movimientos/`, `entradas.tsx`, `salidas.tsx`, `_layout/index.tsx` |
| **C** | Informes | 10, 11, 12 | `routes/informes.py` (nuevo), `informes.tsx`, librerías de exportación en `package.json` |

Orden de cada persona y dependencias entre personas:

```
A:  2 ──► 3 ──► 8 ─────────► 9
                             ▲
B:  4 ──► 5 ──► 6 ──► 7 ─────┘   (la 9 pone el botón en el dashboard de la 7)
C:  10 ──► 11 ──► 12             (la 12 puede ir en paralelo con la 11)
```

- Las tres áreas pueden empezar ya. La única espera entre personas es la Tarea 9 de A, que necesita el dashboard de la Tarea 7 de B. Mientras tanto, A puede hacer el endpoint de la Tarea 9 y dejar el botón para el final.
- La carga es parecida: cada persona tiene una tarea M y el resto son S. A tiene una tarea más porque ya conoce el código.

### Reglas para no pisarse

1. **Ramas.** Primero se sube la Tarea 1 y este plan, y `feature/base-architecture` se fusiona a `main`. Después, una rama por tarea desde `main` (`feat/t04-entradas`) y un PR por tarea. Antes de abrir el PR: `git pull --rebase origin main`.
2. **Cliente generado (`frontend/src/client/`).** No se resuelven conflictos a mano. Si hay conflicto, quedarse con la versión de `main` y volver a correr `bash scripts/generate-client.sh` con el backend de la rama.
3. **Archivos compartidos.** Solo se añade, no se cambia lo que ya existe:
   - `backend/app/api/main.py`: C añade una línea, el router de informes.
   - `backend/app/models.py`: C añade los modelos del resumen al final.
   - `backend/app/crud.py`: A añade la caducidad; B no lo toca.
   - `frontend/tests/utils/inventario.ts`: cualquiera puede añadir funciones (por ejemplo, `registrarSalida`), pero sin cambiar la firma de `createProducto`.
4. **Migraciones.** Ninguna tarea del plan cambia tablas. Si alguien necesita una, lo avisa al equipo antes de crearla, para que no haya dos `alembic` heads.
5. **Base de datos.** Cada persona usa su propia base local. `scripts/test.sh` borra los datos, así que nunca se corre contra una base compartida.
6. **Checklist.** Quien termina una tarea marca sus casillas en `tasks/todo.md` dentro de su propio PR.

## Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| La propuesta no está en el repo y puede pedir cosas que el README no menciona | Alto | Revisar la propuesta contra este plan antes de empezar la Fase 2 |
| Las pruebas del backend borran la base de datos que usan | Medio | Correrlas solo contra la base de desarrollo, como indica el README |
| Cliente generado desactualizado tras cambiar el backend | Medio | Regenerar el cliente en la misma tarea que cambia la API; `bun run build` falla si los tipos no coinciden |
| Caducidad sin trazabilidad por lote: no se sabe qué lote consumió cada salida | Medio | Aceptado en el README. La alerta usa el stock total del producto, no el del lote |
| Conflictos entre ramas en el cliente generado o en archivos compartidos | Medio | Reglas 2 y 3 del reparto, y PR pequeños, uno por tarea |
| Las pruebas E2E dependen de datos del catálogo | Bajo | Cada spec de Playwright crea los datos que necesita mediante la API |

## Decisiones tomadas (2026-11-18)

1. Aviso de caducidad: entre 3 y 5 días antes. Se usa 5, configurable.
2. Cierre de la alerta de caducidad: cualquier regla sirve. Se cierra al quedarse sin stock o a mano, no al vencer.
3. Exportar: hacen falta `.xlsx` y PDF.
4. Informes: resumen diario y mensual.
5. Usuarios normales: no gestionan categorías, productos ni usuarios. Solo el superusuario crea, edita o borra productos.

## Preguntas abiertas

Ninguna por ahora.
