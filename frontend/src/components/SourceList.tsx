import { useState } from 'react'
import type { MessageSourceResponse } from '../types/api'

export function SourceList({ sources }: { sources: MessageSourceResponse[] }) {
  const [isOpen, setIsOpen] = useState(false)

  if (sources.length === 0) return null

  return (
    <div className="mt-2 text-xs">
      <button
        type="button"
        onClick={() => setIsOpen((open) => !open)}
        className="font-medium text-slate-500 underline"
      >
        {isOpen ? 'Ocultar fontes' : `Ver ${sources.length} fonte(s)`}
      </button>
      {isOpen && (
        <ul className="mt-2 flex flex-col gap-2">
          {sources.map((source, index) => (
            <li
              key={`${source.document_id}-${source.chunk_index}`}
              className="rounded-md border border-slate-200 bg-slate-50 p-2"
            >
              <p className="font-medium text-slate-600">
                Fonte {index + 1}: {source.document_filename} (trecho {source.chunk_index})
              </p>
              <p className="mt-1 text-slate-500">{source.snippet}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
