import { useState, type FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { useMessages, useSendMessage } from '../api/conversations'
import { MessageBubble } from '../components/MessageBubble'
import { ApiError } from '../api/client'

export function ConversationPage() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const [content, setContent] = useState('')
  const [error, setError] = useState<string | null>(null)
  const { data: messages, isLoading } = useMessages(conversationId!)
  const sendMessage = useSendMessage(conversationId!)

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault()
    if (!content.trim()) return

    const pendingContent = content
    setContent('')
    setError(null)
    try {
      await sendMessage.mutateAsync(pendingContent)
    } catch (err) {
      setContent(pendingContent)
      setError(err instanceof ApiError ? err.message : 'Não foi possível enviar a mensagem')
    }
  }

  return (
    <div className="flex h-[calc(100vh-140px)] flex-col rounded-lg border border-slate-200 bg-white">
      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && <p className="text-sm text-slate-500">Carregando...</p>}
        <div className="flex flex-col gap-3">
          {messages?.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {sendMessage.isPending && (
            <div className="flex justify-end">
              <div className="max-w-[75%] rounded-lg bg-slate-900 px-4 py-2 text-sm text-white opacity-70">
                {content || 'Enviando...'}
              </div>
            </div>
          )}
          {sendMessage.isPending && (
            <div className="flex justify-start">
              <div className="rounded-lg bg-slate-100 px-4 py-2 text-sm text-slate-500">
                Pensando...
              </div>
            </div>
          )}
        </div>
      </div>
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-3 border-t border-slate-200 p-4"
      >
        <input
          type="text"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Digite sua pergunta..."
          disabled={sendMessage.isPending}
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-slate-500 focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={sendMessage.isPending}
          className="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
        >
          Enviar
        </button>
      </form>
      {error && <p className="px-4 pb-3 text-sm text-red-600">{error}</p>}
    </div>
  )
}
