import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { type ReactNode, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  CategoriasService,
  type ProductoPublic,
  ProductosService,
} from "@/client"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

export const categoriasQueryOptions = {
  queryKey: ["categorias"],
  queryFn: async () =>
    (await CategoriasService.readCategorias({ query: { limit: 1000 } })).data,
}

const formSchema = z.object({
  nombre: z.string().trim().min(1, { message: "Indica el nombre" }).max(255),
  unidad: z.string().trim().min(1, { message: "Indica la unidad" }).max(50),
  stock_minimo: z
    .number({ error: "Indica un número entero" })
    .int({ message: "Indica un número entero" })
    .min(0, { message: "No puede ser negativo" }),
  alerta_caducidad: z.boolean(),
  categoria_id: z.string().min(1, { message: "Elige una categoría" }),
})

type FormData = z.infer<typeof formSchema>

interface ProductoFormProps {
  // Without producto the dialog creates one; with it, it edits that producto
  producto?: ProductoPublic
  trigger: ReactNode
  onSuccess?: () => void
}

const ProductoForm = ({ producto, trigger, onSuccess }: ProductoFormProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()
  const { data: categorias } = useQuery(categoriasQueryOptions)

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    defaultValues: {
      nombre: producto?.nombre ?? "",
      unidad: producto?.unidad ?? "unidad",
      stock_minimo: producto?.stock_minimo ?? 0,
      alerta_caducidad: producto?.alerta_caducidad ?? true,
      categoria_id: producto?.categoria_id ?? "",
    },
  })

  const mutation = useMutation({
    mutationFn: (body: FormData) =>
      producto
        ? ProductosService.updateProducto({ path: { id: producto.id }, body })
        : ProductosService.createProducto({ body }),
    onSuccess: () => {
      showSuccessToast(producto ? "Producto actualizado" : "Producto creado")
      if (!producto) form.reset()
      setIsOpen(false)
      onSuccess?.()
    },
    onError: handleError.bind(showErrorToast),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["productos"] })
    },
  })

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {producto ? "Editar producto" : "Añadir producto"}
          </DialogTitle>
          <DialogDescription>
            El stock no se edita aquí: cambia con las entradas y salidas.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit((data) => mutation.mutate(data))}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="nombre"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Nombre <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Harina de trigo"
                        {...field}
                        required
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="categoria_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Categoría <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Elige una categoría" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {categorias?.data.map((c) => (
                          <SelectItem key={c.id} value={c.id}>
                            {c.nombre}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="unidad"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Unidad <span className="text-destructive">*</span>
                      </FormLabel>
                      <FormControl>
                        <Input placeholder="bulto, botella…" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="stock_minimo"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Stock mínimo</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={0}
                          step={1}
                          {...field}
                          onChange={(e) =>
                            field.onChange(e.target.valueAsNumber)
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="alerta_caducidad"
                render={({ field }) => (
                  <FormItem className="flex items-center gap-3 space-y-0">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                    <FormLabel className="font-normal">
                      Avisar caducidad (cada entrada pide fecha de vencimiento)
                    </FormLabel>
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Cancelar
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                Guardar
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default ProductoForm
