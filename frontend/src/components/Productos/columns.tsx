import type { ColumnDef } from "@tanstack/react-table"

import type { ProductoPublic } from "@/client"
import type { DataTableFeatures } from "@/components/Common/DataTable"
import { Badge } from "@/components/ui/badge"

export type ProductoTableData = ProductoPublic & {
  categoria: string
}

// RN-10: same rule the backend uses to open the stock_minimo alert
const stockBajo = (p: ProductoPublic) => (p.stock ?? 0) < (p.stock_minimo ?? 0)

export const columns: ColumnDef<DataTableFeatures, ProductoTableData>[] = [
  {
    accessorKey: "nombre",
    header: "Producto",
    cell: ({ row }) => (
      <span className="font-medium">{row.original.nombre}</span>
    ),
  },
  {
    accessorKey: "categoria",
    header: "Categoría",
    cell: ({ row }) => (
      <span className="text-muted-foreground">{row.original.categoria}</span>
    ),
  },
  {
    accessorKey: "stock",
    header: "Stock",
    cell: ({ row }) => (
      <span className="tabular-nums">
        {row.original.stock ?? 0}{" "}
        <span className="text-muted-foreground">{row.original.unidad}</span>
      </span>
    ),
  },
  {
    accessorKey: "stock_minimo",
    header: "Mínimo",
    cell: ({ row }) => (
      <span className="tabular-nums text-muted-foreground">
        {row.original.stock_minimo ?? 0}
      </span>
    ),
  },
  {
    id: "estado",
    header: "Estado",
    cell: ({ row }) =>
      stockBajo(row.original) ? (
        <Badge variant="destructive">Stock bajo</Badge>
      ) : (
        <Badge variant="secondary">OK</Badge>
      ),
  },
]
