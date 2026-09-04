import { useDeleteDocument, useDocumentStatus } from '../api/documents'
import { StatusBadge } from './StatusBadge'
import type { DocumentResponse } from '../types/api'

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function DocumentRow({ document }: { document: DocumentResponse }) {
  const { data } = useDocumentStatus(document.id, document.status)
  const deleteDocument = useDeleteDocument()
  const status = data?.status ?? document.status

  return (
    <tr className="border-b border-slate-100 last:border-0">
      <td className="py-3 pr-4 text-sm text-slate-900">{document.filename}</td>
      <td className="py-3 pr-4 text-sm text-slate-500">{formatSize(document.size_bytes)}</td>
      <td className="py-3 pr-4">
        <StatusBadge status={status} />
      </td>
      <td className="py-3 pr-4 text-sm text-slate-500">
        {new Date(document.created_at).toLocaleString('pt-BR')}
      </td>
      <td className="py-3 text-right">
        <button
          type="button"
          onClick={() => deleteDocument.mutate(document.id)}
          disabled={deleteDocument.isPending}
          className="text-sm text-red-600 hover:underline disabled:opacity-50"
        >
          Excluir
        </button>
      </td>
    </tr>
  )
}

export function DocumentList({ documents }: { documents: DocumentResponse[] }) {
  if (documents.length === 0) {
    return <p className="py-8 text-center text-sm text-slate-500">Nenhum documento ainda.</p>
  }

  return (
    <table className="w-full text-left">
      <thead>
        <tr className="border-b border-slate-200 text-xs uppercase text-slate-400">
          <th className="py-2 pr-4 font-medium">Arquivo</th>
          <th className="py-2 pr-4 font-medium">Tamanho</th>
          <th className="py-2 pr-4 font-medium">Status</th>
          <th className="py-2 pr-4 font-medium">Enviado em</th>
          <th className="py-2" />
        </tr>
      </thead>
      <tbody>
        {documents.map((document) => (
          <DocumentRow key={document.id} document={document} />
        ))}
      </tbody>
    </table>
  )
}
