import React, { useState, useEffect } from 'react'
import {
  LayoutDashboard,
  Inbox,
  Users,
  CheckSquare,
  TrendingUp,
  FileText,
  UserCog,
  LogOut,
  ExternalLink,
  Bot,
  AlertTriangle,
  Menu,
  X,
  RefreshCw,
} from 'lucide-react'
import { useAuth } from '../lib/auth'
import { api, CareState } from '../lib/api'

interface LayoutProps {
  currentTab: string
  onSelectTab: (tab: string) => void
  children: React.ReactNode
}

export const Layout: React.FC<LayoutProps> = ({ currentTab, onSelectTab, children }) => {
  const { user, role, logout, can } = useAuth()
  const [careState, setCareState] = useState<CareState | null>(null)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [pollMsg, setPollMsg] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    const fetchState = () => {
      api.getCareState()
        .then((s) => { if (mounted) setCareState(s) })
        .catch(() => {})
    }
    fetchState()
    const interval = setInterval(fetchState, 30000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  const handlePollNow = async () => {
    if (!can('poll_now') || isPolling) return
    setIsPolling(true)
    setPollMsg(null)
    try {
      const res = await api.pollNow()
      setPollMsg(res.result?.status ? `Quét: ${res.result.status}` : 'Đã quét xong')
      setTimeout(() => setPollMsg(null), 4000)
    } catch (err: any) {
      setPollMsg(err.message || 'Lỗi khi quét')
      setTimeout(() => setPollMsg(null), 4000)
    } finally {
      setIsPolling(false)
    }
  }

  const roleLabel = {
    staff: 'Nhân viên',
    manager: 'Quản lý',
    owner: 'Chủ máy',
  }[role || 'staff']

  const roleBadgeColor = {
    staff: 'bg-blue-50 text-blue-700 border-blue-200',
    manager: 'bg-purple-50 text-purple-700 border-purple-200',
    owner: 'bg-orange-50 text-saoviet-700 border-saoviet-200',
  }[role || 'staff']

  const navItems = [
    { id: 'overview', label: 'Tổng quan', icon: LayoutDashboard, show: true },
    {
      id: 'inbox',
      label: 'Hộp thư & Nháp',
      icon: Inbox,
      show: true,
      badge: careState?.stats?.pending_drafts || 0,
    },
    { id: 'customers', label: 'Khách hàng CRM', icon: Users, show: true },
    { id: 'tasks', label: 'Việc cần làm', icon: CheckSquare, show: true },
    { id: 'trends', label: 'Xu hướng & Chi phí', icon: TrendingUp, show: can('view_trends') },
    { id: 'audit', label: 'Nhật ký', icon: FileText, show: true },
    { id: 'users', label: 'Tài khoản nhân sự', icon: UserCog, show: role === 'owner' },
  ].filter((item) => item.show)

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col pb-16 md:pb-0">
      {/* Top Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Title */}
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-saoviet-600 to-saoviet-400 flex items-center justify-center text-white font-black text-xl shadow-md shadow-saoviet-200">
                SV
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-extrabold text-slate-900 text-lg tracking-tight">SAO VIỆT</span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-saoviet-100 text-saoviet-800 uppercase tracking-wider">
                    OPS
                  </span>
                </div>
                <p className="text-xs text-slate-500 font-medium hidden sm:block">
                  Trung tâm vận hành & Chăm sóc khách hàng
                </p>
              </div>
            </div>

            {/* Middle: Brain Status Pill */}
            <div className="hidden lg:flex items-center space-x-3">
              {careState?.config?.kill_switch ? (
                <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-red-50 border border-red-200 text-red-700 text-xs font-semibold animate-pulse">
                  <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                  <span>Dừng khẩn cấp (Kill Switch đang bật)</span>
                </div>
              ) : careState?.config?.enabled ? (
                <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                  <Bot className="w-3.5 h-3.5 text-emerald-600 ml-1" />
                  <span>
                    Javis đang trực: {careState.config?.mode === 'full' ? 'Tự động trả lời' : careState.config?.mode === 'semi' ? 'Bán tự động' : 'Tạo nháp chờ duyệt'}
                  </span>
                </div>
              ) : (
                <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-slate-600 text-xs font-medium">
                  <span className="w-2 h-2 rounded-full bg-slate-400" />
                  <span>Javis Care: Đang tắt</span>
                </div>
              )}

              {can('poll_now') && (
                <button
                  onClick={handlePollNow}
                  disabled={isPolling}
                  title="Quét bình luận ngay"
                  className="flex items-center space-x-1 px-2.5 py-1 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin text-saoviet-600' : ''}`} />
                  <span>Quét ngay</span>
                </button>
              )}

              {pollMsg && (
                <span className="text-xs font-semibold text-saoviet-700 bg-saoviet-50 px-2 py-0.5 rounded border border-saoviet-200 animate-fade-in">
                  {pollMsg}
                </span>
              )}
            </div>

            {/* Right: User Profile & Actions */}
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
                <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center ring-2 ring-white">
                  {user?.name ? user.name.slice(0, 2).toUpperCase() : 'NV'}
                </div>
                <div className="hidden sm:block text-left">
                  <div className="text-xs font-bold text-slate-900 leading-tight">
                    {user?.name || user?.username}
                  </div>
                  <span className={`inline-block text-[10px] font-semibold px-1.5 py-0.2 rounded border ${roleBadgeColor}`}>
                    {roleLabel}
                  </span>
                </div>
              </div>

              {/* Owner cockpit switch button */}
              {role === 'owner' && (
                <a
                  href="/app"
                  title="Vào buồng lái điều khiển Javis (chủ máy)"
                  className="hidden sm:flex items-center space-x-1 px-2.5 py-1 text-xs font-semibold text-slate-700 hover:text-saoviet-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
                >
                  <span>Buồng lái</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}

              {/* Logout button */}
              <button
                onClick={logout}
                title="Đăng xuất"
                className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
              </button>

              {/* Mobile menu trigger */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="md:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>

          {/* Desktop Navigation Bar */}
          <nav className="hidden md:flex space-x-1 py-1 border-t border-slate-100 overflow-x-auto">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = currentTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectTab(item.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    active
                      ? 'bg-saoviet-500 text-white font-semibold shadow-sm shadow-saoviet-200'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${active ? 'text-white' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span
                      className={`text-xs px-1.5 py-0.2 rounded-full font-bold ${
                        active ? 'bg-white text-saoviet-600' : 'bg-saoviet-100 text-saoviet-700'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Mobile Dropdown Menu (Header expansion) */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-4 space-y-1 shadow-lg animate-in slide-in-from-top duration-200">
            {navItems.map((item) => {
              const Icon = item.icon
              const active = currentTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onSelectTab(item.id)
                    setIsMobileMenuOpen(false)
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium ${
                    active ? 'bg-saoviet-500 text-white' : 'text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-saoviet-100 text-saoviet-800 font-bold">
                      {item.badge}
                    </span>
                  )}
                </button>
              )
            })}

            {role === 'owner' && (
              <a
                href="/app"
                className="flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium text-saoviet-700 hover:bg-saoviet-50"
              >
                <ExternalLink className="w-5 h-5" />
                <span>Buồng lái máy chủ (/app)</span>
              </a>
            )}
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>

      {/* Mobile Fixed Bottom Navigation Bar (5 core tabs) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-40 px-2 py-1 shadow-lg flex items-center justify-around">
        {[
          { id: 'overview', label: 'Tổng quan', icon: LayoutDashboard },
          { id: 'inbox', label: 'Hộp thư', icon: Inbox, badge: careState?.stats?.pending_drafts },
          { id: 'customers', label: 'Khách', icon: Users },
          { id: 'tasks', label: 'Việc', icon: CheckSquare },
          { id: 'more', label: 'Thêm', icon: Menu },
        ].map((item) => {
          const Icon = item.icon
          const active = currentTab === item.id || (item.id === 'more' && ['trends', 'audit', 'users'].includes(currentTab))
          return (
            <button
              key={item.id}
              onClick={() => {
                if (item.id === 'more') {
                  setIsMobileMenuOpen(true)
                } else {
                  onSelectTab(item.id)
                }
              }}
              className={`flex flex-col items-center justify-center py-1 px-3 rounded-lg relative ${
                active ? 'text-saoviet-600 font-bold' : 'text-slate-500'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-[10px] mt-0.5">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="absolute top-0 right-2 w-4 h-4 rounded-full bg-saoviet-500 text-white text-[9px] font-bold flex items-center justify-center">
                  {item.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>
    </div>
  )
}
