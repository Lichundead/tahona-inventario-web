import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/entradas")({
  component: Entradas,
  head: () => ({
    meta: [
      {
        title: "Entradas - Tahona Inventario",
      },
    ],
  }),
})

function Entradas() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Entradas</h1>
        <p className="text-muted-foreground">
          Registra los insumos que llegan a la bodega
        </p>
      </div>
    </div>
  )
}
