import React, { createContext, useContext, useEffect, useState } from 'react'
import { api, OpsUser } from './api'

interface AuthContextType {
  user: OpsUser | null
  role: 'staff' | 'manager' | 'owner' | null
  isLoading: boolean
  login: (creds: { username: string; password: string }) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  can: (action: string) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const DEFAULT_OWNER_USER: OpsUser = {
  id: 'owner',
  username: 'admin',
  role: 'owner',
  name: 'Chủ máy',
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<OpsUser | null>(DEFAULT_OWNER_USER)
  const [isLoading, setIsLoading] = useState<boolean>(false)

  const refreshUser = async () => {
    try {
      const data = await api.getMe()
      if (data && data.user) {
        setUser(data.user)
      } else {
        setUser(DEFAULT_OWNER_USER)
      }
    } catch {
      setUser(DEFAULT_OWNER_USER)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    refreshUser()

    const handleUnauthorized = () => {
      refreshUser()
    }
    window.addEventListener('ops:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('ops:unauthorized', handleUnauthorized)
  }, [])

  const login = async (creds: { username: string; password: string }) => {
    const res = await api.login(creds)
    if (res.ok && res.user) {
      setUser(res.user)
    }
  }

  const logout = async () => {
    try {
      await api.logout()
    } finally {
      await refreshUser()
    }
  }

  const can = (action: string): boolean => {
    if (!user) return false
    const r = user.role
    if (r === 'owner') return true

    switch (action) {
      case 'view_trends':
      case 'view_usage':
      case 'merge_crm':
      case 'delete_crm':
      case 'poll_now':
        return r === 'manager'
      case 'manage_users':
      case 'console_cockpit':
      case 'kill_switch':
        return false // manager và staff cấm tuyệt đối
      case 'send_draft':
      case 'reject_draft':
      case 'handoff':
      case 'release_takeover':
      case 'view_crm':
      case 'view_tasks':
        return true // cả staff và manager đều được
      default:
        return false
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role || null,
        isLoading,
        login,
        logout,
        refreshUser,
        can,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
