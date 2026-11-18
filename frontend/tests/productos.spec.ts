import { expect, test } from "@playwright/test"
import { createProducto } from "./utils/inventario"

test("Lista un producto con su categoría y stock", async ({
  page,
  request,
}) => {
  const { producto, categoria } = await createProducto(request, {
    stock_minimo: 2,
    entrada: 3,
  })

  await page.goto("/productos")

  const row = page.getByRole("row").filter({ hasText: producto.nombre })
  await expect(row).toContainText(categoria.nombre)
  await expect(row).toContainText("3 unidad")
  await expect(row).toContainText("OK")
})

test("Marca los productos bajo el stock mínimo", async ({ page, request }) => {
  const { producto } = await createProducto(request, { stock_minimo: 5 })

  await page.goto("/productos")

  const row = page.getByRole("row").filter({ hasText: producto.nombre })
  await expect(row).toContainText("Stock bajo")
})
