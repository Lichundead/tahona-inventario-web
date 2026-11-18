import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/informes")({
  component: Informes,
  head: () => ({
    meta: [
      {
        title: "Informes - Tahona Inventario",
      },
    ],
  }),
})

function Informes() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Informes</h1>
        <p className="text-muted-foreground">
          Movimientos e inventario por periodo, exportables a PDF y Excel
        </p>
      </div>
    </div>
  )
}
