import { useState } from 'react'
import { useDocuments } from '../api/documents'
import { DocumentUploadForm } from '../components/DocumentUploadForm'
import { DocumentList } from '../components/DocumentList'
import { Pagination } from '../components/Pagination'

const PAGE_SIZE = 20

export function DocumentsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading, isError } = useDocuments({ page, pageSize: PAGE_SIZE })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-900">Documentos</h1>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <DocumentUploadForm />
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}
        {isError && <p className="text-sm text-red-600">Não foi possível carregar os documentos.</p>}
        {data && (
          <>
            <DocumentList documents={data.items} />
            <div className="mt-4">
              <Pagination page={data.page} pages={data.pages} onPageChange={setPage} />
            </div>
          </>
        )}
      </div>
    </div>
  )
}
