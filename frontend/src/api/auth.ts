import { apiFetch } from './client'
import type { TokenResponse, UserResponse } from '../types/api'

export function registerUser(email: string, password: string): Promise<UserResponse> {
  return apiFetch<UserResponse>('/auth/register', {
    method: 'POST',
    json: { email, password },
    skipAuth: true,
  })
}

export function loginUser(email: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>('/auth/login', {
    method: 'POST',
    json: { email, password },
    skipAuth: true,
  })
}

export function fetchCurrentUser(): Promise<UserResponse> {
  return apiFetch<UserResponse>('/auth/me')
}
