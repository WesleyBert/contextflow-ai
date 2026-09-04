import type { DocumentStatus } from '../types/api'

const STYLES: Record<DocumentStatus, string> = {
  pending: 'bg-amber-100 text-amber-800',
  processing: 'bg-blue-100 text-blue-800',
  ready: 'bg-emerald-100 text-emerald-800',
  failed: 'bg-red-100 text-red-800',
}

const LABELS: Record<DocumentStatus, string> = {
  pending: 'pendente',
  processing: 'processando',
  ready: 'pronto',
  failed: 'falhou',
}

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STYLES[status]}`}>
      {LABELS[status]}
    </span>
  )
}
