import { expect, test } from "@playwright/test"
import { createProducto, findRow } from "./utils/inventario"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

test("Lista un producto con su categoría y stock", async ({
  page,
  request,
}) => {
  const { producto, categoria } = await createProducto(request, {
    stock_minimo: 2,
    entrada: 3,
  })

  await page.goto("/productos")

  const row = await findRow(page, producto.nombre)
  await expect(row).toContainText(categoria.nombre)
  await expect(row).toContainText("3 unidad")
  await expect(row).toContainText("OK")
})

test("Marca los productos bajo el stock mínimo", async ({ page, request }) => {
  const { producto } = await createProducto(request, { stock_minimo: 5 })

  await page.goto("/productos")

  await expect(await findRow(page, producto.nombre)).toContainText("Stock bajo")
})

test.describe("Gestión de productos (superusuario)", () => {
  test("Crea un producto desde el formulario", async ({ page, request }) => {
    const { categoria } = await createProducto(request)
    const nombre = `Nuevo ${Math.random().toString(36).substring(7)}`

    await page.goto("/productos")
    await page.getByRole("button", { name: "Añadir producto" }).click()
    await page.getByLabel("Nombre").fill(nombre)
    await page.getByRole("combobox").click()
    await page.getByRole("option", { name: categoria.nombre }).click()
    await page.getByLabel("Unidad").fill("bulto")
    await page.getByLabel("Stock mínimo").fill("4")
    await page.getByRole("button", { name: "Guardar" }).click()

    await expect(page.getByText("Producto creado")).toBeVisible()
    const row = await findRow(page, nombre)
    await expect(row).toContainText("0 bulto")
    await expect(row).toContainText("Stock bajo")
  })

  test("Edita el stock mínimo de un producto", async ({ page, request }) => {
    const { producto } = await createProducto(request, { stock_minimo: 5 })

    await page.goto("/productos")
    const row = await findRow(page, producto.nombre)
    await row
      .getByRole("button", { name: `Acciones de ${producto.nombre}` })
      .click()
    await page.getByRole("menuitem", { name: "Editar" }).click()
    await page.getByLabel("Stock mínimo").fill("0")
    await page.getByRole("button", { name: "Guardar" }).click()

    await expect(page.getByText("Producto actualizado")).toBeVisible()
    await page.reload()
    await expect(await findRow(page, producto.nombre)).toContainText("OK")
  })

  test("Elimina un producto sin movimientos", async ({ page, request }) => {
    const { producto } = await createProducto(request)

    await page.goto("/productos")
    const row = await findRow(page, producto.nombre)
    await row
      .getByRole("button", { name: `Acciones de ${producto.nombre}` })
      .click()
    await page.getByRole("menuitem", { name: "Eliminar" }).click()
    await page.getByRole("button", { name: "Eliminar" }).click()

    await expect(page.getByText("Producto eliminado")).toBeVisible()
    await page.reload()
    await expect(await findRow(page, producto.nombre)).toHaveCount(0)
  })

  test("No elimina un producto con movimientos (RN-07)", async ({
    page,
    request,
  }) => {
    const { producto } = await createProducto(request, { entrada: 1 })

    await page.goto("/productos")
    const row = await findRow(page, producto.nombre)
    await row
      .getByRole("button", { name: `Acciones de ${producto.nombre}` })
      .click()
    await page.getByRole("menuitem", { name: "Eliminar" }).click()
    await page.getByRole("button", { name: "Eliminar" }).click()

    await expect(
      page.getByText("el registro tiene datos asociados"),
    ).toBeVisible()
    await page.reload()
    await expect(await findRow(page, producto.nombre)).toHaveCount(1)
  })
})

test.describe("Usuario sin permisos de administración", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("No ve las acciones de catálogo", async ({ page, request }) => {
    const { producto } = await createProducto(request)
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.goto("/productos")

    await expect(await findRow(page, producto.nombre)).toBeVisible()
    await expect(
      page.getByRole("button", { name: "Añadir producto" }),
    ).toHaveCount(0)
    await expect(
      page.getByRole("button", { name: /^Acciones de / }),
    ).toHaveCount(0)
  })
})
