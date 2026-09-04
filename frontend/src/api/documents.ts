import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'
import type { DocumentResponse, DocumentStatusResponse, Page } from '../types/api'

export interface ListDocumentsParams {
  page: number
  pageSize: number
  status?: string
  q?: string
}

function toQueryString(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      search.set(key, String(value))
    }
  }
  const query = search.toString()
  return query ? `?${query}` : ''
}

export function listDocuments(params: ListDocumentsParams): Promise<Page<DocumentResponse>> {
  const query = toQueryString({
    page: params.page,
    page_size: params.pageSize,
    status: params.status,
    q: params.q,
  })
  return apiFetch<Page<DocumentResponse>>(`/documents${query}`)
}

export function uploadDocument(file: File): Promise<DocumentResponse> {
  const formData = new FormData()
  formData.append('file', file)
  return apiFetch<DocumentResponse>('/documents', { method: 'POST', body: formData })
}

export function getDocumentStatus(documentId: string): Promise<DocumentStatusResponse> {
  return apiFetch<DocumentStatusResponse>(`/documents/${documentId}/status`)
}

export function deleteDocument(documentId: string): Promise<void> {
  return apiFetch<void>(`/documents/${documentId}`, { method: 'DELETE' })
}

export function useDocuments(params: ListDocumentsParams) {
  return useQuery({
    queryKey: ['documents', params],
    queryFn: () => listDocuments(params),
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

const IN_PROGRESS_STATUSES = new Set(['pending', 'processing'])

export function useDocumentStatus(documentId: string, initialStatus: string) {
  const queryClient = useQueryClient()
  return useQuery({
    // Namespace própria (não prefixada por "documents") — a invalidação abaixo, ao
    // atingir um status terminal, usa o prefixo "documents" pra atualizar a listagem;
    // se essa query estivesse sob o mesmo prefixo, a invalidação bateria nela mesma e
    // disparava um refetch imediato a cada ciclo, virando um loop infinito de requisições.
    queryKey: ['documentStatus', documentId],
    queryFn: () => getDocumentStatus(documentId),
    initialData: { id: documentId, status: initialStatus } as DocumentStatusResponse,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status && !IN_PROGRESS_STATUSES.has(status)) {
        void queryClient.invalidateQueries({ queryKey: ['documents'], exact: false })
        return false
      }
      return 2000
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}
