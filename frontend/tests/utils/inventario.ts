import type { APIRequestContext } from "@playwright/test"
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
