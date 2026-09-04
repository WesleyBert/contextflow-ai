import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { fetchCurrentUser, loginUser, registerUser } from '../api/auth'
import { authEvents } from '../api/client'
import { tokenStorage } from '../api/tokenStorage'
import type { UserResponse } from '../types/api'

interface AuthContextValue {
  user: UserResponse | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const handleExpired = () => setUser(null)
    authEvents.addEventListener('expired', handleExpired)
    return () => authEvents.removeEventListener('expired', handleExpired)
  }, [])

  useEffect(() => {
    if (!tokenStorage.getAccessToken()) {
      setIsLoading(false)
      return
    }
    fetchCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsLoading(false))
  }, [])

  async function login(email: string, password: string): Promise<void> {
    const tokens = await loginUser(email, password)
    tokenStorage.setTokens(tokens.access_token, tokens.refresh_token)
    setUser(await fetchCurrentUser())
  }

  async function register(email: string, password: string): Promise<void> {
    await registerUser(email, password)
    await login(email, password)
  }

  function logout(): void {
    tokenStorage.clearTokens()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth precisa ser usado dentro de um AuthProvider')
  }
  return context
}
