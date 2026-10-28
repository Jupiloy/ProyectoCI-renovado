export const etiquetaPorEstado: Record<string, string> = {
  DRAFT: "Borrador",
  READY: "En revisión",
  CHANGES_REQUESTED: "Con observaciones",
  APPROVED: "Aprobado",
}

export function etiquetaEstadoCapitulo(status: string): string {
  return etiquetaPorEstado[status] ?? status
}
