import { useRef, useState, type FormEvent } from 'react'
import { useUploadDocument } from '../api/documents'
import { ApiError } from '../api/client'

export function DocumentUploadForm() {
  const uploadDocument = useUploadDocument()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault()
    const file = fileInputRef.current?.files?.[0]
    if (!file) return

    setError(null)
    try {
      await uploadDocument.mutateAsync(file)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível enviar o documento')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-3">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,.md"
        required
        className="text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-slate-800"
      />
      <button
        type="submit"
        disabled={uploadDocument.isPending}
        className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
      >
        {uploadDocument.isPending ? 'Enviando...' : 'Enviar'}
      </button>
      {error && <span className="text-sm text-red-600">{error}</span>}
    </form>
  )
}
