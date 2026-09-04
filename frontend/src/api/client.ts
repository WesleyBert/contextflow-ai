import { tokenStorage } from './tokenStorage'

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/** Disparado quando o refresh token também expirou/é inválido — quem estiver ouvindo
 * (o AuthContext) reage limpando a sessão e mandando o usuário pro login. */
export const authEvents = new EventTarget()

interface RefreshResponseBody {
  access_token: string
  refresh_token: string
}

let refreshPromise: Promise<string> | null = null

async function requestNewAccessToken(): Promise<string> {
  const refreshToken = tokenStorage.getRefreshToken()
  if (!refreshToken) {
    throw new Error('sem refresh token')
  }

  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
  if (!response.ok) {
    throw new Error('refresh token expirado ou inválido')
  }

  const body = (await response.json()) as RefreshResponseBody
  tokenStorage.setTokens(body.access_token, body.refresh_token)
  return body.access_token
}

/** Garante que, mesmo com várias chamadas 401 ao mesmo tempo, só um POST /auth/refresh
 * saia — as outras esperam a mesma promise em vez de disparar refreshes concorrentes. */
function getRefreshedAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = requestNewAccessToken().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

export interface ApiFetchOptions extends Omit<RequestInit, 'body'> {
  /** Serializado como JSON e mandado com Content-Type: application/json. Não usar junto
   * com `body` (ex.: FormData de upload, que já define seu próprio Content-Type). */
  json?: unknown
  body?: BodyInit
  /** Pula a injeção de Authorization e o retry de refresh — usado em login/register. */
  skipAuth?: boolean
}

interface ErrorResponseBody {
  error?: { message?: string }
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { json, skipAuth, headers, ...rest } = options

  const doFetch = async (accessToken: string | null): Promise<Response> => {
    const finalHeaders = new Headers(headers)
    if (json !== undefined) {
      finalHeaders.set('Content-Type', 'application/json')
    }
    if (accessToken && !skipAuth) {
      finalHeaders.set('Authorization', `Bearer ${accessToken}`)
    }

    return fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      headers: finalHeaders,
      body: json !== undefined ? JSON.stringify(json) : rest.body,
    })
  }

  let response = await doFetch(tokenStorage.getAccessToken())

  if (response.status === 401 && !skipAuth) {
    try {
      const newAccessToken = await getRefreshedAccessToken()
      response = await doFetch(newAccessToken)
    } catch {
      tokenStorage.clearTokens()
      authEvents.dispatchEvent(new Event('expired'))
      throw new ApiError(401, 'Sessão expirada, faça login novamente')
    }
  }

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ErrorResponseBody | null
    throw new ApiError(response.status, body?.error?.message ?? `Erro ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}
