import React, { createContext, useContext, useEffect, useState } from 'react'
import { api, OpsUser, OpsRole } from './api'

export const ROLE_LABELS: Record<OpsRole, string> = {
  owner: 'Chủ sở hữu / Giám đốc',
  manager: 'Quản lý vận hành',
  cskh: 'Chuyên viên CSKH & Tư vấn',
  sales: 'Chuyên viên Kinh doanh',
  warehouse: 'Nhân viên Kho & Vận chuyển',
  marketing: 'Chuyên viên Marketing & TikTok',
  technical: 'Kỹ thuật viên Kênh nối',
  staff: 'Nhân viên chung',
}

export const ROLE_BADGES: Record<OpsRole, { bg: string; text: string; border: string; label: string }> = {
  owner: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', label: 'Chủ máy' },
  manager: { bg: 'bg-indigo-50', text: 'text-indigo-700', border: 'border-indigo-200', label: 'Quản lý' },
  cskh: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', label: 'CSKH' },
  sales: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', label: 'Kinh doanh' },
  warehouse: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', label: 'Kho vận' },
  marketing: { bg: 'bg-pink-50', text: 'text-pink-700', border: 'border-pink-200', label: 'Marketing' },
  technical: { bg: 'bg-cyan-50', text: 'text-cyan-700', border: 'border-cyan-200', label: 'Kỹ thuật' },
  staff: { bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200', label: 'Nhân viên' },
}

interface AuthContextType {
  user: OpsUser | null
  role: OpsRole | null
  isLoading: boolean
  login: (creds: { username: string; password: string }) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  can: (action: string) => boolean
  getRoleLabel: (r?: OpsRole | null) => string
  getRoleBadge: (r?: OpsRole | null) => { bg: string; text: string; border: string; label: string }
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<OpsUser | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const refreshUser = async () => {
    try {
      const data = await api.getMe()
      if (data && data.user) {
        setUser(data.user)
      } else {
        setUser(null)
      }
    } catch {
      setUser(null)
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

    // 1. Kiểm tra quyền từ danh sách permissions máy chủ trả về
    if (user.permissions && Array.isArray(user.permissions)) {
      if (user.permissions.includes('*')) return true
      if (user.permissions.includes(action)) return true
    }

    // 2. Logic kiểm tra fallback cục bộ
    switch (action) {
      // Buồng lái & Quản trị cao nhất (Chỉ Owner)
      case 'manage_users':
      case 'console_cockpit':
      case 'kill_switch':
      case 'care_mode_full':
        return false

      // Quản lý cao cấp (Chỉ Manager)
      case 'view_usage':
      case 'view_token_cost':
      case 'merge_crm':
      case 'delete_crm':
      case 'poll_now':
      case 'care_config':
      case 'shipping_config':
      case 'unmask_phone':
        return r === 'manager'

      // Marketing & Xu hướng
      case 'view_trends':
      case 'manage_campaigns':
      case 'post_tiktok':
      case 'competitor_radar':
      case 'attribution_matrix':
        return r === 'manager' || r === 'marketing'

      // Kho vận & Vận đơn
      case 'create_shipment':
        return r === 'manager' || r === 'warehouse'

      // Đơn hàng
      case 'confirm_order':
        return r === 'manager' || r === 'sales' || r === 'warehouse'
      case 'cancel_order':
        return r === 'manager' || r === 'sales'
      case 'create_order':
      case 'edit_order':
        return r === 'manager' || r === 'sales' || r === 'cskh' || r === 'staff'

      // CSKH & Duyệt nháp
      case 'send_draft':
      case 'reject_draft':
      case 'handoff':
      case 'release_takeover':
        return r === 'manager' || r === 'cskh' || r === 'staff'

      // Kỹ thuật & QA
      case 'manage_channels':
      case 'run_qa':
        return r === 'manager' || r === 'technical'

      // Xem dữ liệu thông thường
      case 'view_crm':
      case 'view_orders':
      case 'view_tasks':
      case 'view_directory':
      case 'view_channels':
        return true

      default:
        return false
    }
  }

  const getRoleLabel = (r?: OpsRole | null): string => {
    if (!r) return 'Chưa xác định'
    return ROLE_LABELS[r] || r
  }

  const getRoleBadge = (r?: OpsRole | null) => {
    if (!r || !ROLE_BADGES[r]) {
      return ROLE_BADGES.staff
    }
    return ROLE_BADGES[r]
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
        getRoleLabel,
        getRoleBadge,
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
