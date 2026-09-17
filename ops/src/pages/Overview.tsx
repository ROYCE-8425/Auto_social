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
  Send,
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
  const [commentEvents, setCommentEvents] = useState<CareEvent[]>([])
  const [commentDrafts, setCommentDrafts] = useState<CareDraft[]>([])
  const [messageEvents, setMessageEvents] = useState<CareEvent[]>([])
  const [messageDrafts, setMessageDrafts] = useState<CareDraft[]>([])
  const [actionLoading, setActionLoading] = useState<string | number | null>(null)
  const [actionMsg, setActionMsg] = useState<{ id: string | number; msg: string; type: 'success' | 'error' } | null>(null)
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
      const [stateRes, cmtInboxRes, msgInboxRes, statsRes] = await Promise.all([
        api.getCareState().catch(() => null),
        api.getInbox({
          limit: 10,
          kind: 'comment',
          brand: scopeBrand || undefined,
          page_id: scopePageId || undefined,
        }).catch(() => null),
        api.getInbox({
          limit: 10,
          kind: 'message',
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

      if (cmtInboxRes) {
        setCommentEvents(cmtInboxRes.events || [])
        setCommentDrafts(cmtInboxRes.drafts || [])
      }
      if (msgInboxRes) {
        setMessageEvents(msgInboxRes.events || [])
        setMessageDrafts(msgInboxRes.drafts || [])
      }

      if (statsRes?.stats) {
        setScopedStats(statsRes.stats)
      } else if (cmtInboxRes?.stats) {
        setScopedStats(cmtInboxRes.stats)
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

  const pendingCommentDrafts = commentDrafts.filter((d) => d.status === 'pending')
  const pendingMessageDrafts = messageDrafts.filter((d) => d.status === 'pending')
  const pendingCommentCount = stats.pending_comment_drafts ?? pendingCommentDrafts.length
  const pendingMessageCount = stats.pending_message_drafts ?? pendingMessageDrafts.length

  const handleSendDraft = async (draft: CareDraft) => {
    setActionLoading(draft.id)
    try {
      const res = await api.sendDraft(draft.id)
      if (res.ok) {
        setActionMsg({ id: draft.id, msg: 'Đã gửi thành công!', type: 'success' })
        setCommentDrafts((prev) => prev.filter((d) => d.id !== draft.id))
        setMessageDrafts((prev) => prev.filter((d) => d.id !== draft.id))
        loadScopedData()
      } else {
        setActionMsg({ id: draft.id, msg: res.error || 'Lỗi gửi phản hồi', type: 'error' })
      }
    } catch (err: any) {
      setActionMsg({ id: draft.id, msg: err.message || 'Lỗi gửi phản hồi', type: 'error' })
    } finally {
      setActionLoading(null)
    }
  }

  const handleRejectDraft = async (draft: CareDraft) => {
    setActionLoading(draft.id)
    try {
      const res = await api.rejectDraft(draft.id)
      if (res.ok) {
        setCommentDrafts((prev) => prev.filter((d) => d.id !== draft.id))
        setMessageDrafts((prev) => prev.filter((d) => d.id !== draft.id))
        loadScopedData()
      }
    } finally {
      setActionLoading(null)
    }
  }

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
        badge: 'Thương hiệu đào tạo',
        badgeIcon: GraduationCap,
        badgeColor: 'text-saoviet-400',
        title: scope === 'page' ? scopeLabel : 'Trung tâm vận hành đa thương hiệu',
        desc: isCareActive
          ? 'Javis đang lắng nghe fanpage và soạn nháp theo brand kit của từng thương hiệu.'
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
      navHash: 'inbox?tab=comments',
    },
    {
      title: 'Lead 24h (Có SĐT)',
      value: stats.leads_24h,
      icon: UserPlus,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
      actionTab: 'customers',
    },
    {
      title: 'Nháp comment chờ',
      value: pendingCommentCount,
      icon: MessageSquare,
      color: 'text-amber-600 bg-amber-50 border-amber-100',
      highlight: pendingCommentCount > 0,
      actionTab: 'inbox',
      navHash: 'inbox?tab=comments',
    },
    {
      title: 'Nháp IB chờ',
      value: pendingMessageCount,
      icon: Bot,
      color: 'text-indigo-600 bg-indigo-50 border-indigo-100',
      highlight: pendingMessageCount > 0,
      actionTab: 'inbox',
      navHash: 'inbox?tab=messenger',
    },
    {
      title: 'Javis đã trả lời',
      value: stats.replies_24h,
      icon: CheckCircle2,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
      actionTab: 'inbox',
    },
    {
      title: 'Cần người hỗ trợ',
      value: stats.human_needed_24h,
      icon: AlertTriangle,
      color: 'text-rose-600 bg-rose-50 border-rose-100',
      highlight: stats.human_needed_24h > 0,
      actionTab: 'tasks',
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
              {(pendingCommentCount > 0 || pendingMessageCount > 0) && (
                <>
                  <span className="text-slate-500 font-normal">|</span>
                  <span className="text-amber-300 font-bold capitalize">
                    {pendingCommentCount} bình luận · {pendingMessageCount} tin nhắn IB chờ duyệt
                  </span>
                </>
              )}
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
              {banner.title}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-2xl">
              {banner.desc}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {pendingCommentCount > 0 && (
              <button
                onClick={() => {
                  window.location.hash = 'inbox?tab=comments'
                  onNavigate('inbox')
                }}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-saoviet-500 hover:bg-saoviet-600 text-white font-bold text-xs shadow-md transition-all cursor-pointer"
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>Duyệt {pendingCommentCount} bình luận</span>
              </button>
            )}
            {pendingMessageCount > 0 && (
              <button
                onClick={() => {
                  window.location.hash = 'inbox?tab=messenger'
                  onNavigate('inbox')
                }}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-md transition-all cursor-pointer"
              >
                <Bot className="w-3.5 h-3.5" />
                <span>Duyệt {pendingMessageCount} tin nhắn IB</span>
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
              onClick={() => {
                if (card.navHash) window.location.hash = card.navHash
                onNavigate(card.actionTab)
              }}
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

      {/* 2 Separate Blocks: Comment Drafts & Messenger IB Drafts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Block 1: Bình luận chờ duyệt */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-5 h-5 text-saoviet-500" />
              <h2 className="font-bold text-slate-900 text-base">
                Bình luận chờ duyệt ({pendingCommentCount})
              </h2>
            </div>
            <button
              onClick={() => {
                window.location.hash = 'inbox?tab=comments'
                onNavigate('inbox')
              }}
              className="text-xs font-semibold text-saoviet-600 hover:text-saoviet-700 flex items-center space-x-1"
            >
              <span>Vào bình luận</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="divide-y divide-slate-100">
            {pendingCommentDrafts.length > 0 ? (
              pendingCommentDrafts.slice(0, 4).map((draft) => {
                const ev = commentEvents.find((e) => e.id === draft.event_id || e.object_id === draft.target_id)
                const isBusy = actionLoading === draft.id
                const customerName = draft.from_name || ev?.from_name || 'Khách hàng'
                const commentBody = draft.source_body || ev?.body
                return (
                  <div key={draft.id} className="py-3.5 hover:bg-slate-50/80 rounded-xl px-2 transition-colors space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start space-x-2.5">
                        <div className="w-8 h-8 rounded-full bg-amber-100 text-amber-800 font-bold text-xs flex items-center justify-center flex-shrink-0">
                          {customerName.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-xs text-slate-900">{customerName}</span>
                            {renderPlatformChip(draft.event_platform === 'tiktok' ? 'tiktok' : 'facebook')}
                            {draft.class && (
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 font-medium">
                                {draft.class}
                              </span>
                            )}
                          </div>
                          {commentBody && (
                            <p className="text-xs text-slate-700 mt-1 leading-relaxed line-clamp-2">
                              "{commentBody}"
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <span className="text-[10px] text-slate-400 block">{timeAgo(draft.created_ts)}</span>
                        <span className="inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                          Chờ duyệt
                        </span>
                      </div>
                    </div>

                    <div className="p-2.5 rounded-lg bg-saoviet-50/70 border border-saoviet-100 text-xs text-slate-800">
                      <span className="font-semibold text-saoviet-700 text-[11px] block mb-0.5">
                        Javis soạn nháp phản hồi:
                      </span>
                      <span className="italic text-slate-700 line-clamp-2">{draft.proposed}</span>
                    </div>

                    <div className="flex items-center justify-end space-x-2 pt-1">
                      <button
                        onClick={() => handleRejectDraft(draft)}
                        disabled={isBusy}
                        className="px-2.5 py-1 text-xs font-semibold text-slate-500 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                      >
                        Bỏ qua
                      </button>
                      <button
                        onClick={() => handleSendDraft(draft)}
                        disabled={isBusy}
                        className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-saoviet-500 hover:bg-saoviet-600 text-white font-bold text-xs shadow-sm transition-all"
                      >
                        <Send className="w-3 h-3" />
                        <span>{isBusy ? 'Đang gửi...' : 'Duyệt gửi'}</span>
                      </button>
                    </div>
                  </div>
                )
              })
            ) : commentEvents.length > 0 ? (
              commentEvents.slice(0, 3).map((item) => (
                <div key={item.id} className="py-3 hover:bg-slate-50/80 rounded-xl px-2 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-xs text-slate-900">{item.from_name || 'Khách hàng'}</span>
                        {renderPlatformChip(item.platform || 'facebook')}
                        {item.class && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 font-medium">
                            {item.class}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-700 mt-1 leading-relaxed line-clamp-2">
                        "{item.body}"
                      </p>
                    </div>
                    <span className="text-[10px] text-slate-400 flex-shrink-0">{timeAgo(item.created_ts)}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-10 text-center text-slate-400 text-xs">
                <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-emerald-400" />
                <p className="font-semibold text-slate-600 text-sm">Chưa có comment trên bài.</p>
                <p className="text-slate-400 mt-1">Khi có bình luận mới dưới bài viết, Javis sẽ chuẩn bị nháp tại đây.</p>
              </div>
            )}
          </div>
        </div>

        {/* Block 2: Tin nhắn IB chờ */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <Bot className="w-5 h-5 text-blue-500" />
              <h2 className="font-bold text-slate-900 text-base">
                Tin nhắn IB chờ ({pendingMessageCount})
              </h2>
            </div>
            <button
              onClick={() => {
                window.location.hash = 'inbox?tab=messenger'
                onNavigate('inbox')
              }}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-1"
            >
              <span>Vào hộp thư IB</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="divide-y divide-slate-100">
            {pendingMessageDrafts.length > 0 ? (
              pendingMessageDrafts.slice(0, 4).map((draft) => {
                const ev = messageEvents.find((e) => e.id === draft.event_id || e.object_id === draft.target_id)
                const isBusy = actionLoading === draft.id
                const customerName = draft.from_name || ev?.from_name || 'Khách Messenger'
                const msgBody = draft.source_body || ev?.body
                return (
                  <div key={draft.id} className="py-3.5 hover:bg-slate-50/80 rounded-xl px-2 transition-colors space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start space-x-2.5">
                        <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-800 font-bold text-xs flex items-center justify-center flex-shrink-0">
                          {customerName.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-xs text-slate-900">{customerName}</span>
                            <span className="text-[10px] px-1.5 py-0.2 rounded font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                              Messenger IB
                            </span>
                            {draft.class && (
                              <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 font-medium">
                                {draft.class}
                              </span>
                            )}
                          </div>
                          {msgBody && (
                            <p className="text-xs text-slate-700 mt-1 leading-relaxed line-clamp-2">
                              "{msgBody}"
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <span className="text-[10px] text-slate-400 block">{timeAgo(draft.created_ts)}</span>
                        <span className="inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
                          Chờ gửi IB
                        </span>
                      </div>
                    </div>

                    <div className="p-2.5 rounded-lg bg-blue-50/70 border border-blue-100 text-xs text-slate-800">
                      <span className="font-semibold text-blue-700 text-[11px] block mb-0.5">
                        Javis gợi ý câu trả lời IB:
                      </span>
                      <span className="italic text-slate-700 line-clamp-2">{draft.proposed}</span>
                    </div>

                    <div className="flex items-center justify-end space-x-2 pt-1">
                      <button
                        onClick={() => handleRejectDraft(draft)}
                        disabled={isBusy}
                        className="px-2.5 py-1 text-xs font-semibold text-slate-500 hover:text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                      >
                        Bỏ qua
                      </button>
                      <button
                        onClick={() => handleSendDraft(draft)}
                        disabled={isBusy}
                        className="flex items-center space-x-1 px-3 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-sm transition-all"
                      >
                        <Send className="w-3 h-3" />
                        <span>{isBusy ? 'Đang gửi...' : 'Gửi nháp IB'}</span>
                      </button>
                    </div>
                  </div>
                )
              })
            ) : messageEvents.length > 0 ? (
              messageEvents.slice(0, 3).map((item) => (
                <div key={item.id} className="py-3 hover:bg-slate-50/80 rounded-xl px-2 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-xs text-slate-900">{item.from_name || 'Khách Messenger'}</span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                          Messenger
                        </span>
                      </div>
                      <p className="text-xs text-slate-700 mt-1 leading-relaxed line-clamp-2">
                        "{item.body}"
                      </p>
                    </div>
                    <span className="text-[10px] text-slate-400 flex-shrink-0">{timeAgo(item.created_ts)}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-10 text-center text-slate-400 text-xs">
                <Bot className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <p className="font-semibold text-slate-600 text-sm">Chưa có tin nhắn hộp thư. Bấm Kéo hộp thư IB.</p>
                <p className="text-slate-400 mt-1">Tin nhắn từ Business Suite / Messenger sẽ được phân tích tại đây.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Settings & Guidelines Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Global Care Configuration Card (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
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

          {/* Guidelines Box - Brand Adaptive (1 col) */}
          <div className="lg:col-span-1 bg-slate-100/90 rounded-2xl border border-slate-200 p-5 h-fit">
            <div className="flex items-center space-x-2 text-slate-800 font-bold text-xs mb-2">
              <Calendar className="w-4 h-4 text-saoviet-600" />
              <span>
                {activeBrand === 'bsn' ? 'Quy trình CSKH Game BSN' : 'Quy trình CSKH (đào tạo)'}
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
                          {p.brand === 'bsn' ? 'BSN' : 'Đào tạo'}
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

