import { SourceList } from './SourceList'
import type { MessageResponse } from '../types/api'

export function MessageBubble({ message }: { message: MessageResponse }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2 text-sm ${
          isUser ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-900'
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        {!isUser && <SourceList sources={message.sources} />}
      </div>
    </div>
  )
}
