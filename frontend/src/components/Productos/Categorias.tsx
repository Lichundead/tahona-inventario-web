import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { AxiosError } from "axios"
import { Pencil, Trash2 } from "lucide-react"
import { type FormEvent, useState } from "react"

import { type CategoriaPublic, CategoriasService } from "@/client"
import { categoriasQueryOptions } from "@/components/Productos/ProductoForm"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

const Categorias = () => {
  const [nueva, setNueva] = useState("")
  const [editando, setEditando] = useState<CategoriaPublic | null>(null)
  const [borrando, setBorrando] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { data: categorias } = useQuery(categoriasQueryOptions)

  const onError = handleError.bind(showErrorToast)
  const onSettled = () =>
    queryClient.invalidateQueries({ queryKey: ["categorias"] })

  const crear = useMutation({
    mutationFn: (nombre: string) =>
      CategoriasService.createCategoria({ body: { nombre } }),
    onSuccess: () => {
      showSuccessToast("Categoría creada")
      setNueva("")
    },
    onError,
    onSettled,
  })

  const renombrar = useMutation({
    mutationFn: ({ id, nombre }: CategoriaPublic) =>
      CategoriasService.updateCategoria({ path: { id }, body: { nombre } }),
    onSuccess: () => {
      showSuccessToast("Categoría renombrada")
      setEditando(null)
    },
    onError,
    onSettled,
  })

  const eliminar = useMutation({
    mutationFn: (id: string) =>
      CategoriasService.deleteCategoria({ path: { id } }),
    onSuccess: () => showSuccessToast("Categoría eliminada"),
    // RN-08: the API answers 409 while the categoría still has productos
    onError: (err: Error) =>
      err instanceof AxiosError && err.response?.status === 409
        ? showErrorToast(
            "No se puede eliminar: la categoría tiene productos. Cámbialos de categoría primero.",
          )
        : onError(err),
    onSettled: () => {
      setBorrando(null)
      onSettled()
    },
  })

  const onCrear = (e: FormEvent) => {
    e.preventDefault()
    if (nueva.trim()) crear.mutate(nueva.trim())
  }

  const onRenombrar = (e: FormEvent) => {
    e.preventDefault()
    if (editando?.nombre.trim()) {
      renombrar.mutate({ ...editando, nombre: editando.nombre.trim() })
    }
  }

  return (
    <Dialog
      onOpenChange={() => {
        setEditando(null)
        setBorrando(null)
      }}
    >
      <DialogTrigger asChild>
        <Button variant="outline">Categorías</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Categorías</DialogTitle>
          <DialogDescription>
            Agrupan los productos del catálogo. Solo se puede eliminar una
            categoría sin productos.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={onCrear} className="flex flex-col gap-2">
          <Label htmlFor="nueva-categoria">Nueva categoría</Label>
          <div className="flex gap-2">
            <Input
              id="nueva-categoria"
              placeholder="Ej.: Lácteos"
              value={nueva}
              onChange={(e) => setNueva(e.target.value)}
              maxLength={100}
              required
            />
            <LoadingButton type="submit" loading={crear.isPending}>
              Añadir
            </LoadingButton>
          </div>
        </form>

        <ul className="flex max-h-80 flex-col overflow-y-auto border-t">
          {categorias?.data.length === 0 && (
            <li className="py-4 text-center text-sm text-muted-foreground">
              Todavía no hay categorías.
            </li>
          )}
          {categorias?.data.map((c) => (
            <li
              key={c.id}
              className="flex min-h-12 items-center gap-2 border-b py-1 text-sm"
            >
              {editando?.id === c.id ? (
                <form onSubmit={onRenombrar} className="flex flex-1 gap-2">
                  <Input
                    aria-label={`Nuevo nombre de ${c.nombre}`}
                    value={editando.nombre}
                    onChange={(e) =>
                      setEditando({ ...editando, nombre: e.target.value })
                    }
                    maxLength={100}
                    required
                    autoFocus
                  />
                  <LoadingButton
                    type="submit"
                    size="sm"
                    loading={renombrar.isPending}
                  >
                    Guardar
                  </LoadingButton>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => setEditando(null)}
                  >
                    Cancelar
                  </Button>
                </form>
              ) : borrando === c.id ? (
                <>
                  <span className="flex-1">¿Eliminar {c.nombre}?</span>
                  <LoadingButton
                    size="sm"
                    variant="destructive"
                    loading={eliminar.isPending}
                    onClick={() => eliminar.mutate(c.id)}
                  >
                    Eliminar
                  </LoadingButton>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setBorrando(null)}
                  >
                    Cancelar
                  </Button>
                </>
              ) : (
                <>
                  <span className="flex-1 truncate">{c.nombre}</span>
                  <Button
                    size="icon"
                    variant="ghost"
                    aria-label={`Renombrar ${c.nombre}`}
                    onClick={() => setEditando(c)}
                  >
                    <Pencil />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    aria-label={`Eliminar ${c.nombre}`}
                    onClick={() => setBorrando(c.id)}
                  >
                    <Trash2 />
                  </Button>
                </>
              )}
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  )
}

export default Categorias
