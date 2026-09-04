interface PaginationProps {
  page: number
  pages: number
  onPageChange: (page: number) => void
}

export function Pagination({ page, pages, onPageChange }: PaginationProps) {
  if (pages <= 1) return null

  return (
    <div className="flex items-center justify-center gap-3 text-sm text-slate-600">
      <button
        type="button"
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        className="rounded-md border border-slate-300 px-3 py-1 disabled:opacity-40"
      >
        Anterior
      </button>
      <span>
        Página {page} de {pages}
      </span>
      <button
        type="button"
        disabled={page >= pages}
        onClick={() => onPageChange(page + 1)}
        className="rounded-md border border-slate-300 px-3 py-1 disabled:opacity-40"
      >
        Próxima
      </button>
    </div>
  )
}
