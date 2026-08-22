import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { getMe, login as loginRequest } from '../api/endpoints'
import { setUnauthorizedHandler, tokenStore } from '../api/client'
import type { User } from '../types/api'

interface AuthValue {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}
const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setLoading] = useState(Boolean(tokenStore.get()))
  const logout = useCallback(() => { tokenStore.clear(); setUser(null) }, [])

  useEffect(() => {
    setUnauthorizedHandler(logout)
    if (tokenStore.get()) getMe().then(setUser).catch(() => logout()).finally(() => setLoading(false))
    return () => setUnauthorizedHandler(undefined)
  }, [logout])

  const login = useCallback(async (email: string, password: string) => {
    const result = await loginRequest(email, password)
    tokenStore.set(result.access_token)
    try { setUser(await getMe()) } catch (error) { logout(); throw error }
  }, [logout])

  const value = useMemo(() => ({ user, isLoading, login, logout }), [user, isLoading, login, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used within AuthProvider')
  return value
}
