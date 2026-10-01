import React, { useState, useEffect } from 'react'
import {
  Settings as SettingsIcon,
  ShieldCheck,
  ShieldAlert,
  Radio,
  Clock,
  ExternalLink,
  RefreshCw,
  Server,
  UserCheck,
  Lock,
  ChevronRight,
  Sliders,
  AlertTriangle,
  Package,
  Bot,
} from 'lucide-react'
import { useAuth } from '../lib/auth'
import { api, CareState } from '../lib/api'
import { PlatformConnections } from '../components/PlatformConnections'
import { ShippingSettings } from '../components/ShippingSettings'
import { ProductCatalogSettings } from '../components/ProductCatalogSettings'
import { AutomationRulesSettings } from '../components/AutomationRulesSettings'
import { JavisAutomationControls } from '../components/JavisAutomationControls'
import { RolePermissionsMatrix } from '../components/RolePermissionsMatrix'


export const SettingsPage: React.FC = () => {
  const { user, role, can, getRoleLabel } = useAuth()
  const [careState, setCareState] = useState<CareState | null>(null)
  const [isLoadingCare, setIsLoadingCare] = useState<boolean>(false)
  const [activeSubTab, setActiveSubTab] = useState<'platforms' | 'products' | 'automation' | 'shipping' | 'agent' | 'account'>('platforms')

  const fetchCareState = async () => {
    setIsLoadingCare(true)
    try {
      const data = await api.getCareState()
      setCareState(data)
    } catch {
      // ignore
    } finally {
      setIsLoadingCare(false)
    }
  }

  useEffect(() => {
    fetchCareState()
  }, [])

  const isAuthorized = role === 'owner' || role === 'manager' || (role as string) === 'admin'

  const roleLabel = getRoleLabel(role)

  if (!isAuthorized) {
    return (
      <div className="max-w-3xl mx-auto py-12 px-4 text-center space-y-4 animate-fade-in">
        <div className="w-16 h-16 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mx-auto shadow-sm">
          <Lock className="w-8 h-8" />
        </div>
        <h1 className="text-xl font-bold text-slate-900">Giới hạn quyền truy cập</h1>
        <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
          Khu vực Cài đặt và Kết nối Nền tảng chỉ dành riêng cho vai trò <strong className="text-slate-800">Quản lý (Manager)</strong> hoặc <strong className="text-slate-800">Chủ máy (Owner)</strong>. Tài khoản của bạn hiện là <span className="font-semibold text-slate-700">{roleLabel}</span>.
        </p>
        <div className="pt-2">
          <a
            href="#overview"
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition-colors shadow-2xs"
          >
            <span>Quay lại Tổng quan</span>
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* ================= HEADER ================= */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-slate-800 via-indigo-900 to-blue-900 flex items-center justify-center text-white shadow-md shadow-slate-900/20">
            <SettingsIcon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Cài Đặt Vận Hành &amp; Kết Nối
              </h1>
              <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[10px] font-bold border border-slate-200 uppercase font-mono">
                {role || 'admin'}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Quản trị kết nối mạng xã hội, đơn vị vận chuyển (GHN/GHTK), trạng thái bot Javis và thông tin tài khoản.
            </p>
          </div>
        </div>

        {/* Sub-tab navigation pills */}
        <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold shrink-0">
          <button
            type="button"
            onClick={() => setActiveSubTab('platforms')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeSubTab === 'platforms'
                ? 'bg-white text-slate-900 shadow-2xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Kết nối nền tảng
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('products')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer inline-flex items-center gap-1.5 ${
              activeSubTab === 'products'
                ? 'bg-white text-slate-900 shadow-2xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Package className="w-3.5 h-3.5" />
            <span>Catalog</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('automation')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer inline-flex items-center gap-1.5 ${
              activeSubTab === 'automation'
                ? 'bg-white text-slate-900 shadow-2xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Bot className="w-3.5 h-3.5" />
            <span>Automation</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('shipping')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeSubTab === 'shipping'
                ? 'bg-white text-slate-900 shadow-2xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Vận chuyển &amp; GHN
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('agent')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeSubTab === 'agent'
                ? 'bg-white text-slate-900 shadow-2xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Giám sát trực ca
          </button>
          <button
            type="button"
            onClick={() => setActiveSubTab('account')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
              activeSubTab === 'account'
                ? 'bg-white text-slate-900 shadow-2xs font-bold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Phân quyền tài khoản
          </button>
        </div>
      </div>

      {/* ================= SUB-TAB 1: KẾT NỐI NỀN TẢNG (CHÍNH) ================= */}
      {activeSubTab === 'platforms' && (
        <div className="space-y-6">
          <PlatformConnections />
        </div>
      )}

      {/* ================= SUB-TAB: VẬN CHUYỂN & GHN ================= */}
      {activeSubTab === 'products' && (
        <div className="space-y-6">
          <ProductCatalogSettings />
        </div>
      )}

      {activeSubTab === 'automation' && (
        <div className="space-y-6">
          <AutomationRulesSettings />
        </div>
      )}

      {activeSubTab === 'shipping' && (
        <div className="space-y-6">
          <ShippingSettings />
        </div>
      )}

      {/* ================= SUB-TAB 2: GIÁM SÁT TRỰC CA (AGENT & POLLING) ================= */}
      {activeSubTab === 'agent' && (
        <div className="space-y-6">
          <JavisAutomationControls
            initialState={careState}
            onSaved={(state) => setCareState(state)}
          />

          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <Server className="w-5 h-5 text-indigo-600" />
                  <span>Trạng Thái Trực Ca &amp; Giám Sát Tự Động</span>
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Thông tin tiến trình polling ngầm, trạng thái Javis Care Agent và kiểm soát khẩn cấp.
                </p>
              </div>

              <button
                type="button"
                onClick={fetchCareState}
                disabled={isLoadingCare}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isLoadingCare ? 'animate-spin text-blue-600' : ''}`} />
                <span>Cập nhật tiến trình</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                  Trạng thái Javis Care Bot
                </span>
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-sm font-bold text-slate-900">
                    {careState?.config?.kill_switch ? 'Đã tạm dừng (Kill Switch)' : 'Đang hoạt động tự động'}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Bot tự động quét hội thoại, soạn tin nháp và đồng bộ CRM.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                  Cơ chế Polling Chu kỳ
                </span>
                <div className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-bold text-slate-900">60 giây / chu kỳ</span>
                </div>
                <p className="text-[11px] text-slate-500">
                  Tự động quét bình luận và tin nhắn Facebook qua Fanpage Care Poller.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                  Buồng lái kiểm soát tối cao
                </span>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-700">Chỉ dành cho Owner</span>
                  {role === 'owner' ? (
                    <a
                      href="/app"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 text-xs font-bold text-blue-600 hover:text-blue-700"
                    >
                      <span>Mở Buồng Lái</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  ) : (
                    <span className="text-xs text-slate-400 italic">Cần tài khoản Owner</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500">
                  Quản lý kill-switch, sửa model AI, nạp token Facebook/TikTok trực tiếp tại /app.
                </p>
              </div>
            </div>

            {careState?.config?.kill_switch && (
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start space-x-3">
                <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-bold block">Khẩn cấp: Trợ lý AI đang bị khóa bởi Kill Switch</span>
                  <p className="text-rose-700">
                    Toàn bộ quá trình tự động soạn phản hồi và tương tác đang dừng. Chỉ chủ máy (Owner) mới có quyền tắt Kill Switch trong Buồng lái.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ================= SUB-TAB 3: PHÂN QUYỀN TÀI KHOẢN (ACCOUNT & ROLES) ================= */}
      {activeSubTab === 'account' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <UserCheck className="w-5 h-5 text-purple-600" />
                  <span>Phiên Đăng Nhập &amp; Năng Lực Phân Quyền</span>
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Chi tiết vai trò và các hành động được phép thực hiện trên hệ thống Ops.
                </p>
              </div>

              {role === 'owner' && (
                <a
                  href="#users"
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-purple-600 text-white text-xs font-semibold hover:bg-purple-700 transition-colors shadow-2xs"
                >
                  <span>Quản lý tài khoản nhân sự</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </a>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-3">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                  Thông tin người dùng hiện tại
                </span>
                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-500">Tên đăng nhập:</span>
                    <span className="font-mono font-bold text-slate-800">{user?.username || '—'}</span>
                  </div>
                  <div className="flex items-center justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-500">Họ và tên:</span>
                    <span className="font-bold text-slate-800">{user?.name || '—'}</span>
                  </div>
                  <div className="flex items-center justify-between py-1 border-b border-slate-200/60">
                    <span className="text-slate-500">Vai trò hệ thống:</span>
                    <span className="font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200">
                      {roleLabel}
                    </span>
                  </div>
                  <div className="flex items-center justify-between py-1">
                    <span className="text-slate-500">Mã định danh (ID):</span>
                    <span className="font-mono text-slate-500">{user?.id || '—'}</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-3">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                  Danh sách quyền hạn được cấp
                </span>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { key: 'view_crm', label: 'Xem CRM & Khách hàng' },
                    { key: 'view_tasks', label: 'Xem việc cần làm' },
                    { key: 'send_draft', label: 'Duyệt gửi nháp trả lời' },
                    { key: 'reject_draft', label: 'Từ chối câu trả lời mẫu' },
                    { key: 'handoff', label: 'Chuyển giao người thật' },
                    { key: 'poll_now', label: 'Quét bình luận thủ công' },
                    { key: 'view_trends', label: 'Xem xu hướng & chi phí' },
                    { key: 'merge_crm', label: 'Gộp dữ liệu khách hàng' },
                    { key: 'delete_crm', label: 'Xóa bản ghi CRM' },
                    { key: 'manage_users', label: 'Quản trị danh sách nhân sự' },
                    { key: 'kill_switch', label: 'Kích hoạt Kill Switch khẩn' },
                  ].map((perm) => {
                    const isGranted = can(perm.key)
                    return (
                      <div
                        key={perm.key}
                        className={`p-2 rounded-lg border text-[11px] flex items-center space-x-1.5 ${
                          isGranted
                            ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800 font-semibold'
                            : 'bg-white border-slate-200 text-slate-400 opacity-60'
                        }`}
                      >
                        {isGranted ? (
                          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        ) : (
                          <Lock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        )}
                        <span className="truncate">{perm.label}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Bộ Thiết Lập & Quản Lý Phân Quyền Theo Vai Trò (RBAC Editor) */}
          <RolePermissionsMatrix />
        </div>
      )}
    </div>
  )
}
