import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense } from "react"

import { CategoriasService, ProductosService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import { columns, type ProductoTableData } from "@/components/Productos/columns"
import { Skeleton } from "@/components/ui/skeleton"

// shortcut: loads the whole catalog in one request, paginate server-side if it grows past ~1000
const LIMIT = 1000

export const Route = createFileRoute("/_layout/productos")({
  component: Productos,
  head: () => ({
    meta: [
      {
        title: "Productos - Tahona Inventario",
      },
    ],
  }),
})

function ProductosTableContent() {
  const { data: productos } = useSuspenseQuery({
    queryKey: ["productos"],
    queryFn: async () =>
      (await ProductosService.readProductos({ query: { limit: LIMIT } })).data,
  })
  const { data: categorias } = useSuspenseQuery({
    queryKey: ["categorias"],
    queryFn: async () =>
      (await CategoriasService.readCategorias({ query: { limit: LIMIT } }))
        .data,
  })

  if (productos.data.length === 0) {
    return (
      <p className="rounded-md border p-8 text-center text-muted-foreground">
        Todavía no hay productos en el catálogo.
      </p>
    )
  }

  const nombres = new Map(categorias.data.map((c) => [c.id, c.nombre]))
  const tableData: ProductoTableData[] = productos.data.map((p) => ({
    ...p,
    categoria: nombres.get(p.categoria_id) ?? "",
  }))

  return <DataTable columns={columns} data={tableData} />
}

function Productos() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Productos</h1>
        <p className="text-muted-foreground">
          Catálogo con el stock actual de cada producto
        </p>
      </div>
      <Suspense
        fallback={
          <div className="flex flex-col gap-3" aria-busy="true">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        }
      >
        <ProductosTableContent />
      </Suspense>
    </div>
  )
}
