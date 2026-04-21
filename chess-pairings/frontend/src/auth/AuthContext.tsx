import {
  createContext,
  startTransition,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react'
import { api } from '@/api/client'
import type { AuthToken, User } from '@/api/types'
import { clearStoredAccessToken, getStoredAccessToken, setStoredAccessToken } from '@/auth/storage'

type AuthContextValue = {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<User>
  logout: () => void
  refreshUser: () => Promise<void>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = getStoredAccessToken()
    if (!token) {
      setIsLoading(false)
      return
    }

    void api
      .getMe()
      .then((currentUser) => {
        startTransition(() => {
          setUser(currentUser)
          setIsLoading(false)
        })
      })
      .catch(() => {
        clearStoredAccessToken()
        startTransition(() => {
          setUser(null)
          setIsLoading(false)
        })
      })
  }, [])

  async function login(username: string, password: string) {
    const response: AuthToken = await api.login({ username, password })
    setStoredAccessToken(response.access_token)
    startTransition(() => {
      setUser(response.user)
    })
    return response.user
  }

  function logout() {
    clearStoredAccessToken()
    startTransition(() => {
      setUser(null)
    })
  }

  async function refreshUser() {
    const token = getStoredAccessToken()
    if (!token) {
      startTransition(() => {
        setUser(null)
      })
      return
    }
    const currentUser = await api.getMe()
    startTransition(() => {
      setUser(currentUser)
    })
  }

  async function changePassword(currentPassword: string, newPassword: string) {
    const updatedUser = await api.changePassword({
      current_password: currentPassword,
      new_password: newPassword,
    })
    startTransition(() => {
      setUser(updatedUser)
    })
  }

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      login,
      logout,
      refreshUser,
      changePassword,
    }),
    [isLoading, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
