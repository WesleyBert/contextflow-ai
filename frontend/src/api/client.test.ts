import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { apiFetch, ApiError, authEvents } from './client'
import { tokenStorage } from './tokenStorage'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('apiFetch', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('injeta o Authorization header com o access token salvo', async () => {
    tokenStorage.setTokens('access-1', 'refresh-1')
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await apiFetch('/documents')

    const [, options] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = options.headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer access-1')
  })

  it('em 401, renova o access token via /auth/refresh e repete a chamada original', async () => {
    tokenStorage.setTokens('access-expirado', 'refresh-1')
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { error: { message: 'expirado' } }))
      .mockResolvedValueOnce(
        jsonResponse(200, { access_token: 'access-novo', refresh_token: 'refresh-novo' }),
      )
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await apiFetch<{ ok: boolean }>('/documents')

    expect(result).toEqual({ ok: true })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(tokenStorage.getAccessToken()).toBe('access-novo')

    const [, retryOptions] = fetchMock.mock.calls[2] as [string, RequestInit]
    const retryHeaders = retryOptions.headers as Headers
    expect(retryHeaders.get('Authorization')).toBe('Bearer access-novo')
  })

  it('quando o refresh também falha, limpa os tokens e dispara o evento "expired"', async () => {
    tokenStorage.setTokens('access-expirado', 'refresh-invalido')
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { error: { message: 'expirado' } }))
      .mockResolvedValueOnce(jsonResponse(401, { error: { message: 'refresh inválido' } }))
    vi.stubGlobal('fetch', fetchMock)

    const onExpired = vi.fn()
    authEvents.addEventListener('expired', onExpired)

    await expect(apiFetch('/documents')).rejects.toBeInstanceOf(ApiError)

    expect(tokenStorage.getAccessToken()).toBeNull()
    expect(onExpired).toHaveBeenCalledTimes(1)

    authEvents.removeEventListener('expired', onExpired)
  })

  it('lança ApiError com a mensagem vinda do backend em erros que não são 401', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(422, { error: { message: 'Tipo de arquivo não suportado' } }),
    )
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiFetch('/documents', { method: 'POST' })).rejects.toMatchObject({
      status: 422,
      message: 'Tipo de arquivo não suportado',
    })
  })
})
