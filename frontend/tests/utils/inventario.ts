import type { APIRequestContext, Page } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "../config.ts"

const api = `${process.env.VITE_API_URL}/api/v1`
const random = () => Math.random().toString(36).substring(7)

async function call(
  request: APIRequestContext,
  path: string,
  data: object,
  token?: string,
) {
  const r = token
    ? await request.post(`${api}${path}`, {
        data,
        headers: { Authorization: `Bearer ${token}` },
      })
    : await request.post(`${api}${path}`, { form: data as never })
  if (!r.ok()) throw new Error(`${path}: ${r.status()} ${await r.text()}`)
  return r.json()
}

// Creates a categoria and a producto through the API, as the first superuser
export async function createProducto(
  request: APIRequestContext,
  { stock_minimo = 0, entrada = 0 } = {},
) {
  const { access_token: token } = await call(request, "/login/access-token", {
    username: firstSuperuser,
    password: firstSuperuserPassword,
  })
  const categoria = await call(
    request,
    "/categorias/",
    { nombre: `Categoria ${random()}` },
    token,
  )
  const producto = await call(
    request,
    "/productos/",
    {
      nombre: `Producto ${random()}`,
      stock_minimo,
      alerta_caducidad: false,
      categoria_id: categoria.id,
    },
    token,
  )
  if (entrada > 0) {
    await call(
      request,
      "/transacciones/",
      { producto_id: producto.id, tipo: "entrada", cantidad: entrada },
      token,
    )
  }
  return { producto, categoria }
}

// DataTable shows 10 rows per page and test data accumulates, so page until the row shows up
export async function findRow(page: Page, text: string) {
  const row = page.getByRole("row").filter({ hasText: text })
  const next = page.getByRole("button", { name: "Ir a la página siguiente" })
  await page.getByRole("row").nth(1).waitFor()
  while ((await row.count()) === 0 && (await next.isVisible())) {
    if (!(await next.isEnabled())) break
    await next.click()
  }
  return row
}
