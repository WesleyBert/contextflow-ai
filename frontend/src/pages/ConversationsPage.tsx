import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useConversations, useCreateConversation } from '../api/conversations'
import { Pagination } from '../components/Pagination'
import { ApiError } from '../api/client'

const PAGE_SIZE = 20

export function ConversationsPage() {
  const [page, setPage] = useState(1)
  const [title, setTitle] = useState('')
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { data, isLoading, isError } = useConversations({ page, pageSize: PAGE_SIZE })
  const createConversation = useCreateConversation()

  async function handleCreate(event: FormEvent): Promise<void> {
    event.preventDefault()
    setError(null)
    try {
      const conversation = await createConversation.mutateAsync(title || 'Nova conversa')
      setTitle('')
      navigate(`/conversations/${conversation.id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível criar a conversa')
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-slate-900">Conversas</h1>

      <form onSubmit={handleCreate} className="flex items-center gap-3">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Título da conversa"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none"
        />
        <button
          type="submit"
          disabled={createConversation.isPending}
          className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          {createConversation.isPending ? 'Criando...' : 'Nova conversa'}
        </button>
      </form>
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="rounded-lg border border-slate-200 bg-white p-4">
        {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}
        {isError && <p className="text-sm text-red-600">Não foi possível carregar as conversas.</p>}
        {data && data.items.length === 0 && (
          <p className="py-8 text-center text-sm text-slate-500">Nenhuma conversa ainda.</p>
        )}
        {data && data.items.length > 0 && (
          <ul className="divide-y divide-slate-100">
            {data.items.map((conversation) => (
              <li key={conversation.id}>
                <button
                  type="button"
                  onClick={() => navigate(`/conversations/${conversation.id}`)}
                  className="flex w-full items-center justify-between py-3 text-left text-sm hover:text-slate-600"
                >
                  <span className="font-medium text-slate-900">{conversation.title}</span>
                  <span className="text-slate-400">
                    {new Date(conversation.created_at).toLocaleString('pt-BR')}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {data && (
          <div className="mt-4">
            <Pagination page={data.page} pages={data.pages} onPageChange={setPage} />
          </div>
        )}
      </div>
    </div>
  )
}
