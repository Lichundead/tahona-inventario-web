import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/salidas")({
  component: Salidas,
  head: () => ({
    meta: [
      {
        title: "Salidas - Tahona Inventario",
      },
    ],
  }),
})

function Salidas() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Salidas</h1>
        <p className="text-muted-foreground">
          Registra los insumos que salen de la bodega
        </p>
      </div>
    </div>
  )
}
