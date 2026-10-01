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
  Bell,
  ChevronDown,
  Layers,
  Share2,
  Settings,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ShoppingBag,
  Package,
  Zap,
  FolderLock,
} from 'lucide-react'
import { useAuth } from '../lib/auth'
import { api, CareState } from '../lib/api'
import { useCareScope } from '../lib/scope'
import { ScopeBar } from './ScopeBar'
import { OpsChatBubble } from './OpsChatBubble'

interface LayoutProps {
  currentTab: string
  onSelectTab: (tab: string) => void
  children: React.ReactNode
}

interface NavItem {
  id: string
  label: string
  icon: any
  show: boolean
  badge?: number
  section?: 'main' | 'system'
}

export const Layout: React.FC<LayoutProps> = ({ currentTab, onSelectTab, children }) => {
  const { user, role, logout, can, getRoleLabel } = useAuth()
  const { scope, scopeBrand, scopePageId, eligiblePages, setScope } = useCareScope()
  const [careState, setCareState] = useState<CareState | null>(null)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
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
      const res = await api.pollNow(scopePageId || undefined)
      setPollMsg(res.result?.status ? `Quét: ${res.result.status}` : 'Đã quét xong')
      setTimeout(() => setPollMsg(null), 4000)
    } catch (err: any) {
      setPollMsg(err.message || 'Lỗi khi quét')
      setTimeout(() => setPollMsg(null), 4000)
    } finally {
      setIsPolling(false)
    }
  }

  const roleLabel = getRoleLabel(role)

  const navItems: NavItem[] = [
    { id: 'overview', label: 'Tổng quan', icon: LayoutDashboard, show: true, section: 'main' },
    {
      id: 'inbox',
      label: 'Hộp thư',
      icon: Inbox,
      show: true,
      section: 'main',
      badge: careState?.stats?.pending_drafts || undefined,
    },
    { id: 'orders', label: 'Đơn hàng', icon: ShoppingBag, show: true, section: 'main' },
    { id: 'customers', label: 'Khách hàng', icon: Users, show: true, section: 'main' },
    { id: 'products', label: 'Kho sản phẩm', icon: Package, show: true, section: 'main' },
    { id: 'documents', label: 'Kho tài liệu', icon: FolderLock, show: true, section: 'main' },
    { id: 'automation', label: 'Kịch bản chốt đơn', icon: Zap, show: role === 'owner' || role === 'manager' || (role as string) === 'admin', section: 'main' },
    { id: 'publishing', label: 'Đăng bài & Kênh', icon: Share2, show: true, section: 'main' },
    { id: 'tasks', label: 'Việc cần làm', icon: CheckSquare, show: true, section: 'main' },
    { id: 'trends', label: 'Báo cáo', icon: TrendingUp, show: can('view_trends'), section: 'main' },
    { id: 'hub', label: 'AI Assistant', icon: Bot, show: true, section: 'system' },
    { id: 'settings', label: 'Cài đặt', icon: Settings, show: role === 'owner' || role === 'manager' || (role as string) === 'admin', section: 'system' },
    { id: 'users', label: 'Tài khoản nhân sự', icon: UserCog, show: role === 'owner', section: 'system' },
    { id: 'audit', label: 'Nhật ký hệ thống', icon: FileText, show: role === 'owner' || role === 'manager', section: 'system' },
  ].filter((item) => item.show) as NavItem[]

  const mainNavItems = navItems.filter((i) => i.section === 'main')
  const systemNavItems = navItems.filter((i) => i.section === 'system')

  const currentTabLabel = navItems.find((i) => i.id === currentTab)?.label || 'Bảng điều khiển'

  const renderNavButton = (item: NavItem) => {
    const Icon = item.icon
    const active = currentTab === item.id || (item.id === 'publishing' && ['tiktok', 'channels'].includes(currentTab))
    return (
      <button
        key={item.id}
        type="button"
        onClick={() => {
          onSelectTab(item.id)
          setIsMobileMenuOpen(false)
        }}
        title={item.label}
        className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all group relative ${
          active
            ? 'bg-emerald-500/15 text-emerald-400 font-bold border-l-4 border-emerald-500 shadow-xs'
            : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
        } ${isSidebarCollapsed ? 'justify-center px-2' : ''}`}
      >
        <Icon
          className={`w-5 h-5 shrink-0 transition-transform duration-200 group-hover:scale-110 ${
            active ? 'text-emerald-400' : 'text-slate-400 group-hover:text-slate-200'
          }`}
        />
        {!isSidebarCollapsed && (
          <span className="truncate tracking-wide">{item.label}</span>
        )}
        {item.badge !== undefined && item.badge > 0 && !isSidebarCollapsed && (
          <span className="ml-auto px-2 py-0.5 text-[10px] font-extrabold rounded-full bg-emerald-500 text-slate-950 shadow-xs">
            {item.badge}
          </span>
        )}
        {item.badge !== undefined && item.badge > 0 && isSidebarCollapsed && (
          <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        )}
      </button>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* ========================================================================= */}
      {/* DESKTOP VERTICAL SIDEBAR (MENU DỌC)                                       */}
      {/* ========================================================================= */}
      <aside
        className={`hidden md:flex flex-col bg-[#0B132B] text-slate-300 border-r border-slate-800/80 sticky top-0 h-screen z-40 transition-all duration-300 ease-in-out shrink-0 select-none shadow-xl ${
          isSidebarCollapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* Brand Header */}
        <div className="h-18 flex items-center px-4 border-b border-slate-800/80 justify-between">
          <div className={`flex items-center space-x-3 overflow-hidden ${isSidebarCollapsed ? 'justify-center w-full' : ''}`}>
            <div className="relative shrink-0">
              <img
                src="/logo.png"
                alt="Sèo Trum Logo"
                className="w-10 h-10 rounded-xl object-contain bg-white/5 border border-emerald-500/30 p-1 shadow-md shadow-emerald-500/10"
              />
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 ring-2 ring-[#0B132B]" />
            </div>
            {!isSidebarCollapsed && (
              <div className="overflow-hidden">
                <span className="font-black text-white text-base tracking-wider block truncate">
                  SÈO TRUM
                </span>
                <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest block truncate">
                  OPS SOCIAL HUB
                </span>
              </div>
            )}
          </div>

          {!isSidebarCollapsed && (
            <button
              type="button"
              onClick={() => setIsSidebarCollapsed(true)}
              className="text-slate-500 hover:text-slate-300 p-1 rounded-lg hover:bg-slate-800/50 transition-colors"
              title="Thu gọn menu"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Sidebar Nav Items */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6 custom-scrollbar">
          {/* Main Navigation */}
          <div className="space-y-1">
            {!isSidebarCollapsed && (
              <p className="px-3.5 text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                Nghiệp vụ
              </p>
            )}
            {mainNavItems.map(renderNavButton)}
          </div>

          {/* System & AI Navigation */}
          <div className="space-y-1 pt-2 border-t border-slate-800/60">
            {!isSidebarCollapsed && (
              <p className="px-3.5 text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                Trợ lý &amp; Cài đặt
              </p>
            )}
            {systemNavItems.map(renderNavButton)}
          </div>
        </div>

        {/* Sidebar Footer: User Card & Quick Actions */}
        <div className="p-3 border-t border-slate-800/80 bg-[#090F22]/60">
          <div className={`flex items-center space-x-3 p-2 rounded-xl bg-slate-800/40 border border-slate-800/60 ${isSidebarCollapsed ? 'justify-center p-1.5' : ''}`}>
            <div className="relative shrink-0">
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-emerald-600 to-teal-400 text-white font-bold text-xs flex items-center justify-center ring-2 ring-emerald-500/40 shadow-xs">
                {role === 'owner' ? 'CH' : user?.name ? user.name.slice(0, 2).toUpperCase() : 'NV'}
              </div>
              <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-[#0B132B]" />
            </div>

            {!isSidebarCollapsed && (
              <div className="flex-1 min-w-0 text-left">
                <p className="text-xs font-bold text-white truncate">
                  {role === 'owner' ? 'Chủ máy' : user?.name || 'Nhân viên'}
                </p>
                <p className="text-[10px] text-slate-400 truncate">
                  {roleLabel}
                </p>
              </div>
            )}

            {!isSidebarCollapsed && (
              <button
                type="button"
                onClick={logout}
                title="Đăng xuất"
                className="text-slate-400 hover:text-rose-400 p-1.5 rounded-lg hover:bg-slate-800 transition-colors shrink-0"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Expand button if collapsed */}
          {isSidebarCollapsed && (
            <div className="mt-2 flex justify-center">
              <button
                type="button"
                onClick={() => setIsSidebarCollapsed(false)}
                className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
                title="Mở rộng menu"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Owner Cockpit Button */}
          {!isSidebarCollapsed && role === 'owner' && (
            <a
              href="/app"
              title="Vào buồng lái điều khiển Javis AI"
              className="mt-2 w-full flex items-center justify-center space-x-1.5 py-1.5 px-3 rounded-lg text-[11px] font-semibold text-emerald-400 hover:text-emerald-300 bg-emerald-950/40 hover:bg-emerald-900/40 border border-emerald-800/50 transition-colors"
            >
              <span>Buồng lái máy chủ</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* MOBILE DRAWER OVERLAY & SIDEBAR                                           */}
      {/* ========================================================================= */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <div
            className="fixed inset-0 bg-slate-950/60 backdrop-blur-xs animate-fade-in"
            onClick={() => setIsMobileMenuOpen(false)}
          />
          <aside className="relative w-72 max-w-[80vw] bg-[#0B132B] text-slate-300 h-full flex flex-col z-50 shadow-2xl animate-in slide-in-from-left duration-200">
            <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800">
              <div className="flex items-center space-x-3">
                <img src="/logo.png" alt="Logo" className="w-8 h-8 rounded-lg bg-white/10 p-1" />
                <span className="font-black text-white text-base tracking-wider">SÈO TRUM OPS</span>
              </div>
              <button
                type="button"
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-3 py-4 space-y-4">
              <div className="space-y-1">
                {mainNavItems.map(renderNavButton)}
              </div>
              <div className="space-y-1 pt-2 border-t border-slate-800">
                {systemNavItems.map(renderNavButton)}
              </div>
            </div>

            <div className="p-4 border-t border-slate-800 bg-[#090F22]">
              <div className="flex items-center justify-between">
                <div className="text-left">
                  <p className="text-xs font-bold text-white">{user?.name || 'Nhân viên'}</p>
                  <p className="text-[10px] text-slate-400">{roleLabel}</p>
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className="text-slate-400 hover:text-rose-400 p-2"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MAIN RIGHT VIEW AREA (TOP HEADER + CONTENT)                               */}
      {/* ========================================================================= */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Top Header */}
        <header className="bg-white border-b border-slate-200/90 sticky top-0 z-30 shadow-2xs h-16 shrink-0">
          <div className="h-full px-4 sm:px-6 lg:px-8 flex items-center justify-between">
            {/* Left: Mobile trigger & Page Context */}
            <div className="flex items-center space-x-3 sm:space-x-4">
              <button
                type="button"
                onClick={() => setIsMobileMenuOpen(true)}
                className="md:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                title="Mở menu"
              >
                <Menu className="w-5 h-5" />
              </button>

              <div>
                <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  <span>{currentTabLabel}</span>
                </h1>
              </div>

              {/* Scope Filter Pills */}
              <div className="hidden lg:flex items-center space-x-1.5 pl-3 border-l border-slate-200">
                <button
                  type="button"
                  onClick={() => setScope('all')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    scope === 'all'
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  Tất cả ({eligiblePages.length || 2})
                </button>
                <button
                  type="button"
                  onClick={() => setScope('brand', 'bsn')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    scope === 'brand' && scopeBrand === 'bsn'
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  Game BSN
                </button>
                <button
                  type="button"
                  onClick={() => setScope('brand', 'saoviet')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                    scope === 'brand' && scopeBrand === 'saoviet'
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {eligiblePages.find((p) => (p.brand || '').toLowerCase() === 'saoviet')?.name || 'Royce Shop'}
                </button>
              </div>
            </div>

            {/* Right: Javis Status, Poll Button, Notification */}
            <div className="flex items-center space-x-2.5 sm:space-x-3">
              {/* Brain Status Pill */}
              {careState?.config?.kill_switch ? (
                <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs font-semibold animate-pulse">
                  <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                  <span className="hidden sm:inline">Dừng khẩn cấp</span>
                </div>
              ) : (
                <div className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                  <span className="hidden sm:inline">Javis đang trực</span>
                </div>
              )}

              {/* Poll Button */}
              {can('poll_now') && (
                <button
                  onClick={handlePollNow}
                  disabled={isPolling}
                  title="Quét bình luận và tin nhắn ngay"
                  className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors border border-blue-200 disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin text-blue-600' : 'text-blue-600'}`} />
                  <span className="hidden sm:inline">Quét ngay</span>
                </button>
              )}

              {pollMsg && (
                <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-1 rounded border border-blue-200 animate-fade-in hidden xl:inline">
                  {pollMsg}
                </span>
              )}

              {/* Notification Bell */}
              <button
                type="button"
                className="relative p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                title="Thông báo"
              >
                <Bell className="w-4.5 h-4.5" />
                <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white" />
              </button>
            </div>
          </div>
        </header>

        {/* Global Scope Bar for pages that need deeper breadcrumbs */}
        {!['overview', 'inbox', 'orders', 'products', 'automation', 'tasks', 'customers', 'hub', 'tiktok', 'channels', 'publishing', 'settings'].includes(currentTab) && <ScopeBar />}

        {/* Main Content Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-[1700px] w-full mx-auto">
          {children}
        </main>
      </div>

      {/* Floating Chat Assistant */}
      <OpsChatBubble />
    </div>
  )
}
