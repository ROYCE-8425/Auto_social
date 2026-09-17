import React, { useEffect, useState } from 'react'
import {
  MessageSquare,
  UserPlus,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Users,
  ArrowRight,
  Bot,
  Activity,
  Calendar,
  Sparkles,
  ShieldCheck,
  Moon,
  Gamepad2,
  GraduationCap,
  Layers,
  Settings2,
  Sliders,
  Check,
  Save,
  Info,
  Power,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react'
import { api, CareDraft, CareEvent, CareState, CareFeatures, CarePageSettings, CareStats } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useCareScope } from '../lib/scope'
import { formatTime, timeAgo } from '../lib/utils'

interface OverviewProps {
  onNavigate: (tab: string) => void
}

export const Overview: React.FC<OverviewProps> = ({ onNavigate }) => {
  const { user, role, can } = useAuth()
  const { scope, scopeBrand, scopePageId, eligiblePages, activeBrand, scopeLabel } = useCareScope()

  const [careState, setCareState] = useState<CareState | null>(null)
  const [scopedStats, setScopedStats] = useState<CareStats | null>(null)
  const [events, setEvents] = useState<CareEvent[]>([])
  const [drafts, setDrafts] = useState<CareDraft[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  // Local settings editor state
  const [cfgEnabled, setCfgEnabled] = useState<boolean>(true)
  const [cfgMode, setCfgMode] = useState<string>('suggest')
  const [cfgFeatures, setCfgFeatures] = useState<CareFeatures>({
    poll_comments: true,
    poll_messenger: true,
    auto_reply_comments: false,
    auto_reply_messenger: false,
    hide_spam: false,
  })
  const [pageOverrides, setPageOverrides] = useState<Record<string, CarePageSettings>>({})
  const [isSavingCfg, setIsSavingCfg] = useState<boolean>(false)
  const [saveCfgMsg, setSaveCfgMsg] = useState<{ text: string; ok: boolean } | null>(null)

  const isEditor = role === 'owner' || role === 'manager' || can('configure_care')

  const renderPlatformChip = (platform?: string) => {
    const p = (platform || 'facebook').toLowerCase()
    if (p === 'tiktok') {
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded font-bold bg-slate-900 text-white tracking-wide">
          TikTok
        </span>
      )
    }
    if (p === 'messenger') {
      return (
        <span className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
          Messenger
        </span>
      )
    }
    return (
      <span className="text-[10px] px-1.5 py-0.5 rounded font-medium bg-blue-50 text-blue-700 border border-blue-200">
        Facebook
      </span>
    )
  }

  // Load data according to active scope
  const loadScopedData = async () => {
    try {
      const [stateRes, inboxRes, statsRes] = await Promise.all([
        api.getCareState().catch(() => null),
        api.getInbox({
          limit: 20,
          brand: scopeBrand || undefined,
          page_id: scopePageId || undefined,
        }).catch(() => null),
        api.getCareStats({
          brand: scopeBrand || undefined,
          page_id: scopePageId || undefined,
        }).catch(() => null),
      ])

      if (stateRes) {
        setCareState(stateRes)
        if (stateRes.config) {
          setCfgEnabled(Boolean(stateRes.config.enabled))
          setCfgMode(stateRes.config.mode || 'suggest')
          if (stateRes.config.features) {
            setCfgFeatures((prev) => ({ ...prev, ...stateRes.config!.features }))
          }
          if (stateRes.config.pages) {
            setPageOverrides(stateRes.config.pages)
          }
        }
      }

      if (inboxRes) {
        setEvents(inboxRes.events || [])
        setDrafts(inboxRes.drafts || [])
        if (inboxRes.stats) {
          setScopedStats(inboxRes.stats)
        }
      }

      if (statsRes?.stats) {
        setScopedStats(statsRes.stats)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadScopedData()
    const t = setInterval(loadScopedData, 20000)
    return () => clearInterval(t)
  }, [scope, scopeBrand, scopePageId])

  const stats = scopedStats || careState?.stats || {
    total_events: 0,
    events_24h: 0,
    leads_24h: 0,
    human_needed_24h: 0,
    replies_24h: 0,
    spam_hidden_24h: 0,
    pending_drafts: 0,
    total_customers: 0,
  }

  const pendingDrafts = drafts.filter((d) => d.status === 'pending')

  // Save Care settings
  const handleSaveSettings = async (
    overrideCfg?: {
      enabled?: boolean
      mode?: string
      features?: Partial<CareFeatures>
      pages?: Record<string, Partial<CarePageSettings>>
    }
  ) => {
    if (!isEditor || isSavingCfg) return
    setIsSavingCfg(true)
    setSaveCfgMsg(null)

    const payload = {
      enabled: overrideCfg?.enabled !== undefined ? overrideCfg.enabled : cfgEnabled,
      mode: overrideCfg?.mode !== undefined ? overrideCfg.mode : cfgMode,
      features: overrideCfg?.features || cfgFeatures,
      pages: overrideCfg?.pages || pageOverrides,
    }

    try {
      const res = await api.saveCareSettings(payload)
      if (res.ok) {
        setSaveCfgMsg({ text: 'Đã lưu cấu hình Care thành công!', ok: true })
        if (res.config) {
          setCfgEnabled(Boolean(res.config.enabled))
          setCfgMode(res.config.mode || 'suggest')
          if (res.config.features) setCfgFeatures((prev) => ({ ...prev, ...res.config!.features }))
          if (res.config.pages) setPageOverrides(res.config.pages)
        }
        await loadScopedData()
      } else {
        setSaveCfgMsg({ text: res.error || 'Lỗi lưu cấu hình', ok: false })
      }
    } catch (err: any) {
      setSaveCfgMsg({ text: err.message || 'Lỗi lưu cấu hình', ok: false })
    } finally {
      setIsSavingCfg(false)
      setTimeout(() => setSaveCfgMsg(null), 4000)
    }
  }

  // Update a single page override
  const handlePageOverrideChange = (pageId: string, patch: Partial<CarePageSettings>) => {
    setPageOverrides((prev) => {
      const current = prev[pageId] || {}
      const updated = {
        ...current,
        ...patch,
        features: {
          ...(current.features || {}),
          ...(patch.features || {}),
        },
      }
      return { ...prev, [pageId]: updated }
    })
  }

  // Banner text computation
  const getBannerInfo = () => {
    const isCareActive = cfgEnabled

    if (activeBrand === 'bsn') {
      return {
        badge: 'Nhóm Game Bản Quyền BSN',
        badgeIcon: Gamepad2,
        badgeColor: 'text-purple-400',
        title: scope === 'page' ? scopeLabel : 'Game Giá Rẻ BSN',
        desc: isCareActive
          ? 'Javis đang lắng nghe tương tác fanpage và chuẩn bị câu trả lời tư vấn game bản quyền BSN.'
          : 'Javis Care hiện đang tạm tắt. Bật công tắc Care tổng bên dưới để bắt đầu lắng nghe tương tác.',
      }
    }

    if (activeBrand === 'saoviet') {
      return {
        badge: 'Đào Tạo Tin Học Sao Việt',
        badgeIcon: GraduationCap,
        badgeColor: 'text-saoviet-400',
        title: scope === 'page' ? scopeLabel : 'Trung Tâm Vận Hành Sao Việt',
        desc: isCareActive
          ? 'Javis đang lắng nghe tương tác fanpage và chuẩn bị câu trả lời theo giáo trình Sao Việt.'
          : 'Javis Care hiện đang tạm tắt. Bật công tắc Care tổng bên dưới để bắt đầu lắng nghe tương tác.',
      }
    }

    return {
      badge: 'Toàn Bộ Hệ Thống Fanpage',
      badgeIcon: Layers,
      badgeColor: 'text-slate-300',
      title: 'Tất cả Fanpage đã kết nối',
      desc: isCareActive
        ? 'Javis đang lắng nghe tương tác trên các fanpage đã kết nối.'
        : 'Javis Care hiện đang tạm tắt. Bật công tắc Care tổng bên dưới để bắt đầu lắng nghe tương tác.',
    }
  }

  const banner = getBannerInfo()
  const BannerIcon = banner.badgeIcon

  const statCards = [
    {
      title: 'Bình luận 24h',
      value: stats.events_24h,
      icon: MessageSquare,
      color: 'text-blue-600 bg-blue-50 border-blue-100',
      actionTab: 'inbox',
    },
    {
      title: 'Lead 24h (Có SĐT)',
      value: stats.leads_24h,
      icon: UserPlus,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
      actionTab: 'customers',
    },
    {
      title: 'Nháp chờ duyệt',
      value: stats.pending_drafts,
      icon: Clock,
      color: 'text-amber-600 bg-amber-50 border-amber-100',
      highlight: stats.pending_drafts > 0,
      actionTab: 'inbox',
    },
    {
      title: 'Javis đã trả lời',
      value: stats.replies_24h,
      icon: CheckCircle2,
      color: 'text-indigo-600 bg-indigo-50 border-indigo-100',
      actionTab: 'inbox',
    },
    {
      title: 'Cần người hỗ trợ',
      value: stats.human_needed_24h,
      icon: AlertTriangle,
      color: 'text-rose-600 bg-rose-50 border-rose-100',
      actionTab: 'tasks',
    },
    {
      title: 'Khách trong CRM',
      value: stats.total_customers,
      icon: Users,
      color: 'text-saoviet-600 bg-saoviet-50 border-saoviet-100',
      actionTab: 'customers',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Top Banner: Dynamic Brand / Page Aware */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 shadow-md relative overflow-hidden">
        <div className="absolute right-0 top-0 w-80 h-full bg-gradient-to-l from-saoviet-600/20 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className={`flex items-center space-x-2 text-xs font-semibold uppercase tracking-wider mb-1 ${banner.badgeColor}`}>
              <BannerIcon className="w-3.5 h-3.5" />
              <span>{banner.badge}</span>
              <span className="text-slate-500 font-normal">|</span>
              <span className="text-slate-300 font-normal capitalize">Phạm vi: {scopeLabel}</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
              {banner.title}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-2xl">
              {banner.desc}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {stats.pending_drafts > 0 && (
              <button
                onClick={() => onNavigate('inbox')}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-saoviet-500 hover:bg-saoviet-600 text-white font-bold text-xs shadow-md transition-all cursor-pointer"
              >
                <span>Duyệt {stats.pending_drafts} nháp ngay</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={() => onNavigate('tasks')}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold transition-all cursor-pointer"
            >
              <span>Xem bảng việc</span>
            </button>
          </div>
        </div>
      </div>

      {/* 6 Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon
          return (
            <div
              key={idx}
              onClick={() => onNavigate(card.actionTab)}
              className={`bg-white rounded-2xl p-4 border transition-all cursor-pointer hover:shadow-md hover:-translate-y-0.5 ${
                card.highlight ? 'border-amber-400 ring-2 ring-amber-100' : 'border-slate-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 line-clamp-1">{card.title}</span>
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center border ${card.color}`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3 flex items-baseline">
                <span className="text-2xl font-black text-slate-900 tracking-tight">
                  {loading ? '—' : card.value}
                </span>
              </div>
              <div className="mt-2 text-[10px] text-slate-400 flex items-center space-x-1">
                <span>Nhấn để xem</span>
                <ArrowRight className="w-2.5 h-2.5" />
              </div>
            </div>
          )
        })}
      </div>

      {/* 2 Columns: Recent Inbox Items & System Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Pending Drafts or Recent Events (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-5 h-5 text-saoviet-500" />
              <h2 className="font-bold text-slate-900 text-base">
                {pendingDrafts.length > 0 ? `Nháp chờ duyệt (${pendingDrafts.length})` : 'Sự kiện tương tác gần đây'}
              </h2>
            </div>
            <button
              onClick={() => onNavigate('inbox')}
              className="text-xs font-semibold text-saoviet-600 hover:text-saoviet-700 flex items-center space-x-1"
            >
              <span>Vào hộp thư</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 mt-2">
            {pendingDrafts.length > 0
              ? pendingDrafts.slice(0, 5).map((draft) => {
                  const ev = events.find((e) => e.id === draft.event_id || e.object_id === draft.target_id)
                  return (
                    <div key={draft.id} className="py-3.5 hover:bg-slate-50/80 rounded-xl px-2 transition-colors">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-start space-x-3">
                          <div className="w-9 h-9 rounded-full bg-amber-100 text-amber-800 font-bold text-xs flex items-center justify-center flex-shrink-0">
                            {ev?.from_name ? ev.from_name.slice(0, 2).toUpperCase() : 'KH'}
                          </div>
                          <div>
                            <div className="flex items-center space-x-2">
                              <span className="font-bold text-xs text-slate-900">{ev?.from_name || 'Khách hàng'}</span>
                              {renderPlatformChip(ev?.platform || 'facebook')}
                              {draft.class && (
                                <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 font-medium">
                                  {draft.class}
                                </span>
                              )}
                            </div>
                            {ev?.body && (
                              <p className="text-xs text-slate-700 mt-1 leading-relaxed line-clamp-2">
                                "{ev.body}"
                              </p>
                            )}
                            <div className="mt-2 p-2 rounded-lg bg-saoviet-50/60 border border-saoviet-100 text-xs text-slate-800">
                              <span className="font-semibold text-saoviet-700 text-[11px] block mb-0.5">
                                Javis soạn nháp:
                              </span>
                              <span className="italic text-slate-600 line-clamp-2">{draft.proposed}</span>
                            </div>
                          </div>
                        </div>

                        <div className="text-right flex-shrink-0">
                          <span className="text-[10px] text-slate-400 block">{timeAgo(draft.created_ts)}</span>
                          <span className="inline-block mt-1.5 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                            Chờ duyệt
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                })
              : events.slice(0, 5).map((item) => (
                  <div key={item.id} className="py-3.5 hover:bg-slate-50/80 rounded-xl px-2 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start space-x-3">
                        <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                          {item.from_name ? item.from_name.slice(0, 2).toUpperCase() : 'KH'}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-xs text-slate-900">{item.from_name || 'Khách hàng'}</span>
                            {renderPlatformChip(item.platform || 'facebook')}
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 capitalize">
                              {item.kind}
                            </span>
                            {item.class && (
                              <span
                                className={`text-[10px] px-1.5 py-0.2 rounded font-medium ${
                                  item.class === 'lead'
                                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                    : 'bg-blue-50 text-blue-700'
                                }`}
                              >
                                {item.class}
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-slate-700 mt-1 leading-relaxed line-clamp-2">
                            "{item.body}"
                          </p>
                        </div>
                      </div>

                      <div className="text-right flex-shrink-0">
                        <span className="text-[10px] text-slate-400 block">{timeAgo(item.created_ts)}</span>
                        <span className="inline-block mt-1.5 text-[10px] font-medium text-slate-500">
                          {formatTime(item.created_ts)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}

            {events.length === 0 && drafts.length === 0 && (
              <div className="py-12 text-center text-slate-400 text-xs">
                <Bot className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <span>Chưa có bình luận hoặc nháp mới nào trong 24 giờ qua</span>
              </div>
            )}
          </div>
        </div>

        {/* Right: Quick Info, Care Settings & Health Status (1 col) */}
        <div className="space-y-6">
          {/* Global Care Configuration Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <Sliders className="w-4 h-4 text-saoviet-600" />
                <h3 className="font-bold text-slate-900 text-sm">Cài đặt & Công tắc Care</h3>
              </div>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  cfgEnabled
                    ? 'bg-emerald-100 text-emerald-800'
                    : 'bg-slate-100 text-slate-600'
                }`}
              >
                {cfgEnabled ? 'Đang bật' : 'Đang tắt'}
              </span>
            </div>

            {/* Master Care Switch */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
              <div>
                <span className="font-bold text-xs text-slate-900 block">Care tổng (Master)</span>
                <span className="text-[11px] text-slate-500 block">
                  Bật/tắt toàn bộ dịch vụ quét & phản hồi Javis
                </span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  disabled={!isEditor || isSavingCfg}
                  checked={cfgEnabled}
                  onChange={(e) => setCfgEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600 disabled:opacity-50"></div>
              </label>
            </div>

            {/* Care Mode Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 block">
                Chế độ vận hành (Toàn cục)
              </label>
              <select
                disabled={!isEditor || isSavingCfg}
                value={cfgMode}
                onChange={(e) => setCfgMode(e.target.value)}
                className="w-full text-xs font-medium p-2.5 rounded-xl border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-saoviet-500 disabled:opacity-60"
              >
                <option value="suggest">Chỉ nháp (Tạo nháp chờ duyệt - Mặc định an toàn)</option>
                <option value="semi">Bán tự động (FAQ tự gửi, case mới tạo nháp)</option>
                <option value="full">Tự động hoàn toàn (Javis tự trả lời tất cả)</option>
              </select>
            </div>

            {/* Feature Toggles */}
            <div className="space-y-2 pt-1 border-t border-slate-100">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Công tắc từng chức năng
              </span>

              {/* 1. Poll Comments */}
              <div className="flex items-center justify-between py-1.5">
                <div>
                  <span className="text-xs font-semibold text-slate-800 block">Kéo bình luận</span>
                  <span className="text-[10px] text-slate-400">Tự động quét comment từ bài viết</span>
                </div>
                <input
                  type="checkbox"
                  disabled={!isEditor || isSavingCfg}
                  checked={cfgFeatures.poll_comments}
                  onChange={(e) =>
                    setCfgFeatures((prev) => ({ ...prev, poll_comments: e.target.checked }))
                  }
                  className="rounded text-saoviet-600 focus:ring-saoviet-500 h-4 w-4 border-slate-300 cursor-pointer disabled:opacity-50"
                />
              </div>

              {/* 2. Poll Messenger */}
              <div className="flex items-center justify-between py-1.5">
                <div>
                  <span className="text-xs font-semibold text-slate-800 block">Kéo hộp thư IB</span>
                  <span className="text-[10px] text-slate-400">Quét tin nhắn Messenger Business</span>
                </div>
                <input
                  type="checkbox"
                  disabled={!isEditor || isSavingCfg}
                  checked={cfgFeatures.poll_messenger}
                  onChange={(e) =>
                    setCfgFeatures((prev) => ({ ...prev, poll_messenger: e.target.checked }))
                  }
                  className="rounded text-saoviet-600 focus:ring-saoviet-500 h-4 w-4 border-slate-300 cursor-pointer disabled:opacity-50"
                />
              </div>

              {/* 3. Auto Reply Comments */}
              <div className="flex items-center justify-between py-1.5">
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-xs font-semibold text-slate-800">Tự trả lời bình luận</span>
                    {cfgFeatures.auto_reply_comments && (
                      <span className="text-[9px] px-1 py-0.2 rounded bg-amber-50 text-amber-700 font-bold border border-amber-200">
                        {cfgMode === 'suggest' ? 'Chỉ nháp' : 'Tự rep'}
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-400">Mặc định tắt · Cần mode Tự động</span>
                </div>
                <input
                  type="checkbox"
                  disabled={!isEditor || isSavingCfg}
                  checked={cfgFeatures.auto_reply_comments}
                  onChange={(e) =>
                    setCfgFeatures((prev) => ({ ...prev, auto_reply_comments: e.target.checked }))
                  }
                  className="rounded text-saoviet-600 focus:ring-saoviet-500 h-4 w-4 border-slate-300 cursor-pointer disabled:opacity-50"
                />
              </div>

              {/* 4. Auto Reply Messenger */}
              <div className="flex items-center justify-between py-1.5">
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-xs font-semibold text-slate-800">Tự trả lời IB</span>
                    {cfgFeatures.auto_reply_messenger && (
                      <span className="text-[9px] px-1 py-0.2 rounded bg-amber-50 text-amber-700 font-bold border border-amber-200">
                        {cfgMode === 'suggest' ? 'Chỉ nháp' : 'Tự rep'}
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-400">Mặc định tắt · Cần mode Tự động</span>
                </div>
                <input
                  type="checkbox"
                  disabled={!isEditor || isSavingCfg}
                  checked={cfgFeatures.auto_reply_messenger}
                  onChange={(e) =>
                    setCfgFeatures((prev) => ({ ...prev, auto_reply_messenger: e.target.checked }))
                  }
                  className="rounded text-saoviet-600 focus:ring-saoviet-500 h-4 w-4 border-slate-300 cursor-pointer disabled:opacity-50"
                />
              </div>

              {/* 5. Hide Spam */}
              <div className="flex items-center justify-between py-1.5">
                <div>
                  <span className="text-xs font-semibold text-slate-800 block">Ẩn spam / quảng cáo</span>
                  <span className="text-[10px] text-slate-400">Tự động ẩn bình luận rác hoặc chửi bậy</span>
                </div>
                <input
                  type="checkbox"
                  disabled={!isEditor || isSavingCfg}
                  checked={cfgFeatures.hide_spam}
                  onChange={(e) =>
                    setCfgFeatures((prev) => ({ ...prev, hide_spam: e.target.checked }))
                  }
                  className="rounded text-saoviet-600 focus:ring-saoviet-500 h-4 w-4 border-slate-300 cursor-pointer disabled:opacity-50"
                />
              </div>
            </div>

            {/* Mode Suggest Protection Alert */}
            {cfgMode === 'suggest' && (cfgFeatures.auto_reply_comments || cfgFeatures.auto_reply_messenger) && (
              <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-[11px] leading-relaxed flex items-start space-x-2">
                <Info className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <span>
                  <b>Chế độ đang là 'Chỉ nháp':</b> Dù bật công tắc tự trả lời, bot sẽ <b>không gửi tin ra Facebook</b> mà chỉ tạo nháp. Để bot thực sự gửi tin tự động, hãy đổi chế độ sang <b>Bán tự động</b> hoặc <b>Tự động hoàn toàn</b>.
                </span>
              </div>
            )}

            {/* Save Buttons & Feedback */}
            {isEditor && (
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => handleSaveSettings()}
                  disabled={isSavingCfg}
                  className="w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-xl bg-saoviet-500 hover:bg-saoviet-600 text-white font-bold text-xs shadow-sm transition-all cursor-pointer disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{isSavingCfg ? 'Đang lưu...' : 'Lưu cài đặt toàn cục'}</span>
                </button>
              </div>
            )}

            {saveCfgMsg && (
              <div
                className={`p-2 rounded-lg text-xs font-semibold text-center ${
                  saveCfgMsg.ok
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}
              >
                {saveCfgMsg.text}
              </div>
            )}

            {!isEditor && (
              <p className="text-[11px] text-slate-400 italic text-center">
                * Chỉ Quản lý hoặc Chủ máy mới có quyền thay đổi cấu hình Care.
              </p>
            )}
          </div>

          {/* Guidelines Box - Brand Adaptive */}
          <div className="bg-slate-100/90 rounded-2xl border border-slate-200 p-5">
            <div className="flex items-center space-x-2 text-slate-800 font-bold text-xs mb-2">
              <Calendar className="w-4 h-4 text-saoviet-600" />
              <span>
                {activeBrand === 'bsn' ? 'Quy trình CSKH Game BSN' : 'Quy trình CSKH Sao Việt'}
              </span>
            </div>
            <ul className="text-xs text-slate-600 space-y-2 list-disc list-inside">
              {activeBrand === 'bsn' ? (
                <>
                  <li>Kiểm tra nháp tư vấn game và giá bán trước khi bấm <b>Gửi phản hồi</b>.</li>
                  <li>Yêu cầu phức tạp hoặc cần nạp tài khoản: nhấn <b>Tạo việc giao người</b>.</li>
                  <li>Khi nhân viên nhắn tay trong Business Suite, Javis tự lùi lại 4 giờ.</li>
                </>
              ) : (
                <>
                  <li>Kiểm tra nháp Javis tạo trước khi nhấn <b>Gửi phản hồi</b>.</li>
                  <li>Nếu khách hỏi phức tạp, nhấn <b>Tạo việc giao người</b> để đưa vào bảng việc.</li>
                  <li>Khi nhắn tay Messenger, Javis tự lùi lại 4 giờ để nhân viên tư vấn liền mạch.</li>
                </>
              )}
            </ul>
          </div>
        </div>
      </div>

      {/* Per-Page Care Configuration Overrides Table */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <div className="flex items-center space-x-2">
              <Settings2 className="w-4 h-4 text-saoviet-600" />
              <h2 className="font-bold text-slate-900 text-base">
                Cấu hình chi tiết theo từng Fanpage
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Ghi đè bật/tắt Care, chế độ hoặc quyền tự trả lời cho riêng từng trang mà không ảnh hưởng page khác.
            </p>
          </div>

          {isEditor && (
            <button
              type="button"
              onClick={() => handleSaveSettings()}
              disabled={isSavingCfg}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow-sm transition-all cursor-pointer disabled:opacity-50 self-start sm:self-auto"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{isSavingCfg ? 'Đang lưu...' : 'Lưu thay đổi từng page'}</span>
            </button>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/70 text-slate-600 font-bold text-[11px] uppercase tracking-wider">
                <th className="py-2.5 px-3">Fanpage</th>
                <th className="py-2.5 px-3 text-center">Bật Care</th>
                <th className="py-2.5 px-3">Chế độ vận hành</th>
                <th className="py-2.5 px-3 text-center">Tự rep Comment</th>
                <th className="py-2.5 px-3 text-center">Tự rep IB</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {eligiblePages.map((p) => {
                const pid = String(p.page_id || p.id || '')
                if (!pid) return null
                const override = pageOverrides[pid] || {}
                const isPageCareOn = override.enabled !== undefined ? override.enabled : true
                const pageMode = override.mode || ''
                const autoCommentOn = override.features?.auto_reply_comments !== undefined
                  ? override.features.auto_reply_comments
                  : false
                const autoMsgOn = override.features?.auto_reply_messenger !== undefined
                  ? override.features.auto_reply_messenger
                  : false

                return (
                  <tr key={pid} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`text-[10px] font-bold px-1.5 py-0.2 rounded border ${
                            p.brand === 'bsn'
                              ? 'bg-purple-50 text-purple-700 border-purple-200'
                              : 'bg-saoviet-50 text-saoviet-700 border-saoviet-200'
                          }`}
                        >
                          {p.brand === 'bsn' ? 'BSN' : 'Sao Việt'}
                        </span>
                        <div>
                          <span className="font-bold text-slate-900 block">{p.name}</span>
                          <span className="text-[10px] text-slate-400 font-mono">ID: {pid}</span>
                        </div>
                      </div>
                    </td>

                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        disabled={!isEditor || isSavingCfg}
                        checked={isPageCareOn}
                        onChange={(e) =>
                          handlePageOverrideChange(pid, { enabled: e.target.checked })
                        }
                        className="rounded text-saoviet-600 focus:ring-saoviet-500 h-4 w-4 border-slate-300 cursor-pointer disabled:opacity-50"
                      />
                    </td>

                    <td className="py-3 px-3">
                      <select
                        disabled={!isEditor || isSavingCfg}
                        value={pageMode}
                        onChange={(e) =>
                          handlePageOverrideChange(pid, { mode: e.target.value })
                        }
                        className="text-xs p-1.5 rounded-lg border border-slate-200 bg-white text-slate-800 focus:outline-none focus:ring-1 focus:ring-saoviet-500 disabled:opacity-50"
                      >
                        <option value="">Theo toàn cục ({cfgMode === 'suggest' ? 'Chỉ nháp' : cfgMode === 'semi' ? 'Bán tự động' : 'Tự động'})</option>
                        <option value="suggest">Chỉ nháp (Gợi ý)</option>
                        <option value="semi">Bán tự động</option>
                        <option value="full">Hoàn toàn tự động</option>
                      </select>
                    </td>

                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        disabled={!isEditor || isSavingCfg}
                        checked={autoCommentOn}
                        onChange={(e) =>
                          handlePageOverrideChange(pid, {
                            features: {
                              ...(override.features || {}),
                              auto_reply_comments: e.target.checked,
                            },
                          })
                        }
                        className="rounded text-saoviet-600 focus:ring-saoviet-500 h-4 w-4 border-slate-300 cursor-pointer disabled:opacity-50"
                      />
                    </td>

                    <td className="py-3 px-3 text-center">
                      <input
                        type="checkbox"
                        disabled={!isEditor || isSavingCfg}
                        checked={autoMsgOn}
                        onChange={(e) =>
                          handlePageOverrideChange(pid, {
                            features: {
                              ...(override.features || {}),
                              auto_reply_messenger: e.target.checked,
                            },
                          })
                        }
                        className="rounded text-saoviet-600 focus:ring-saoviet-500 h-4 w-4 border-slate-300 cursor-pointer disabled:opacity-50"
                      />
                    </td>
                  </tr>
                )
              })}

              {eligiblePages.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-slate-400">
                    Chưa có fanpage nào được kết nối trong hệ thống.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

