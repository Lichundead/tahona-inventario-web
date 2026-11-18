import { createFileRoute } from "@tanstack/react-router"

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

function Productos() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Productos</h1>
        <p className="text-muted-foreground">
          Catálogo con el stock actual de cada producto
        </p>
      </div>
    </div>
  )
}
