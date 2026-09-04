export interface UserResponse {
  id: string
  email: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed'

export interface DocumentResponse {
  id: string
  filename: string
  content_type: string
  size_bytes: number
  status: DocumentStatus
  created_at: string
}

export interface DocumentStatusResponse {
  id: string
  status: DocumentStatus
}

export interface ConversationResponse {
  id: string
  title: string
  created_at: string
}

export interface MessageSourceResponse {
  document_id: string
  document_filename: string
  chunk_index: number
  snippet: string
}

export type MessageFeedback = 'up' | 'down' | null

export interface MessageResponse {
  id: string
  role: string
  content: string
  sources: MessageSourceResponse[]
  feedback: MessageFeedback
  created_at: string
}

export interface MessageExchangeResponse {
  user_message: MessageResponse
  assistant_message: MessageResponse
}
