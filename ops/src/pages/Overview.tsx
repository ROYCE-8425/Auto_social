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
} from 'lucide-react'
import { api, CareDraft, CareEvent, CareState } from '../lib/api'
import { formatTime, timeAgo } from '../lib/utils'

interface OverviewProps {
  onNavigate: (tab: string) => void
}

export const Overview: React.FC<OverviewProps> = ({ onNavigate }) => {
  const [careState, setCareState] = useState<CareState | null>(null)
  const [events, setEvents] = useState<CareEvent[]>([])
  const [drafts, setDrafts] = useState<CareDraft[]>([])
  const [loading, setLoading] = useState<boolean>(true)

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

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const [stateRes, inboxRes] = await Promise.all([
          api.getCareState().catch(() => null),
          api.getInbox({ limit: 20 }).catch(() => null),
        ])
        if (mounted) {
          if (stateRes) setCareState(stateRes)
          if (inboxRes) {
            setEvents(inboxRes.events || [])
            setDrafts(inboxRes.drafts || [])
          }
        }
      } finally {
        if (mounted) setLoading(false)
      }
    }
    load()
    const t = setInterval(load, 20000)
    return () => {
      mounted = false
      clearInterval(t)
    }
  }, [])

  const stats = careState?.stats || {
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
      {/* Top Banner: Status + Quick Handoff Notice */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 shadow-md relative overflow-hidden">
        <div className="absolute right-0 top-0 w-80 h-full bg-gradient-to-l from-saoviet-600/20 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-saoviet-400 text-xs font-semibold uppercase tracking-wider mb-1">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Hệ thống trợ lý Javis Care</span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
              {careState?.facebook_label ? `Fanpage: ${careState.facebook_label}` : 'Trung Tâm Vận Hành Sao Việt'}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-2xl">
              {careState?.config?.enabled
                ? `Javis đang lắng nghe tương tác fanpage và chuẩn bị câu trả lời theo giáo trình Sao Việt.`
                : `Javis Care hiện đang tạm tắt. Vui lòng liên hệ Quản lý nếu cần bật tính năng tự động.`}
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

        {/* Right: Quick Info & Health Status (1 col) */}
        <div className="space-y-6">
          {/* Fanpage Connection Health Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
            <h3 className="font-bold text-slate-900 text-sm flex items-center space-x-2 mb-3">
              <Activity className="w-4 h-4 text-saoviet-500" />
              <span>Trạng thái kết nối</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500">Fanpage Facebook</span>
                <span className="font-semibold text-slate-800">
                  {careState?.facebook_label || (careState?.facebook_connected ? 'Đã liên kết' : 'Chưa liên kết')}
                </span>
              </div>

              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500">Quyền hạn</span>
                <span className={`font-semibold ${careState?.connection_perm === 'full' ? 'text-emerald-700' : 'text-slate-600'}`}>
                  {careState?.connection_perm === 'full' ? 'Toàn quyền (Đọc & Gửi)' : 'Chỉ đọc (Read-only)'}
                </span>
              </div>

              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500">Chế độ hoạt động</span>
                <span className="font-semibold text-saoviet-700 capitalize">
                  {careState?.config?.mode === 'full' ? 'Tự động trả lời' : careState?.config?.mode === 'semi' ? 'Bán tự động' : 'Tạo nháp (Gợi ý)'}
                </span>
              </div>

              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500">Giờ im lặng</span>
                <span className="font-medium text-slate-700 flex items-center space-x-1">
                  {careState?.is_quiet ? (
                    <>
                      <Moon className="w-3.5 h-3.5 text-amber-500" />
                      <span className="text-amber-700 font-semibold">Đang yên tĩnh</span>
                    </>
                  ) : (
                    <span>{careState?.config?.quiet_hours ? `${careState.config.quiet_hours} (Bình thường)` : 'Bình thường'}</span>
                  )}
                </span>
              </div>

              <div className="flex items-center justify-between py-2">
                <span className="text-slate-500">Hàng rào an toàn</span>
                <span className="font-semibold text-emerald-700 flex items-center space-x-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Đang bảo vệ</span>
                </span>
              </div>
            </div>
          </div>

          {/* Guidelines Box */}
          <div className="bg-saoviet-50/80 rounded-2xl border border-saoviet-200/80 p-5">
            <div className="flex items-center space-x-2 text-saoviet-800 font-bold text-xs mb-2">
              <Calendar className="w-4 h-4 text-saoviet-600" />
              <span>Quy trình CSKH Sao Việt</span>
            </div>
            <ul className="text-xs text-slate-700 space-y-2 list-disc list-inside">
              <li>Kiểm tra nháp Javis tạo trước khi nhấn <b>Gửi phản hồi</b>.</li>
              <li>Nếu khách hỏi phức tạp, nhấn <b>Tạo việc giao người</b> để đưa vào bảng việc.</li>
              <li>Khi nhắn tay Messenger, Javis tự lùi lại 4 giờ để nhân viên tư vấn liền mạch.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

