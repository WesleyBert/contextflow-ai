import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from './client'
import type { ConversationResponse, MessageExchangeResponse, MessageResponse, Page } from '../types/api'

export interface ListConversationsParams {
  page: number
  pageSize: number
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

export function listConversations(
  params: ListConversationsParams,
): Promise<Page<ConversationResponse>> {
  const query = toQueryString({ page: params.page, page_size: params.pageSize })
  return apiFetch<Page<ConversationResponse>>(`/conversations${query}`)
}

export function createConversation(title: string): Promise<ConversationResponse> {
  return apiFetch<ConversationResponse>('/conversations', { method: 'POST', json: { title } })
}

export function listMessages(conversationId: string): Promise<MessageResponse[]> {
  return apiFetch<MessageResponse[]>(`/conversations/${conversationId}/messages`)
}

export function sendMessage(
  conversationId: string,
  content: string,
): Promise<MessageExchangeResponse> {
  return apiFetch<MessageExchangeResponse>(`/conversations/${conversationId}/messages`, {
    method: 'POST',
    json: { content },
  })
}

export function useConversations(params: ListConversationsParams) {
  return useQuery({
    queryKey: ['conversations', params],
    queryFn: () => listConversations(params),
  })
}

export function useCreateConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createConversation,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
  })
}

export function useMessages(conversationId: string) {
  return useQuery({
    queryKey: ['conversations', conversationId, 'messages'],
    queryFn: () => listMessages(conversationId),
  })
}

export function useSendMessage(conversationId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (content: string) => sendMessage(conversationId, content),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['conversations', conversationId, 'messages'],
      })
    },
  })
}
