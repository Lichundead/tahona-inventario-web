import { EllipsisVertical, Pencil } from "lucide-react"
import { useState } from "react"

import type { ProductoPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import useAuth from "@/hooks/useAuth"
import DeleteProducto from "./DeleteProducto"
import ProductoForm from "./ProductoForm"

export const ProductoActionsMenu = ({
  producto,
}: {
  producto: ProductoPublic
}) => {
  const [open, setOpen] = useState(false)
  const { user } = useAuth()

  // The API also rejects these for non-superusers; this only hides the menu
  if (!user?.is_superuser) return null

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Acciones de ${producto.nombre}`}
        >
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <ProductoForm
          producto={producto}
          onSuccess={() => setOpen(false)}
          trigger={
            <DropdownMenuItem onSelect={(e) => e.preventDefault()}>
              <Pencil />
              Editar
            </DropdownMenuItem>
          }
        />
        <DeleteProducto producto={producto} onSuccess={() => setOpen(false)} />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
