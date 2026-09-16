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
} from 'lucide-react'
import { api, CareState, CustomerItem, InboxItem } from '../lib/api'
import { formatTime, timeAgo } from '../lib/utils'

interface OverviewProps {
  onNavigate: (tab: string) => void
}

export const Overview: React.FC<OverviewProps> = ({ onNavigate }) => {
  const [careState, setCareState] = useState<CareState | null>(null)
  const [inboxItems, setInboxItems] = useState<InboxItem[]>([])
  const [customerCount, setCustomerCount] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    let mounted = true
    const load = async () => {
      try {
        const [stateRes, inboxRes, custRes] = await Promise.all([
          api.getCareState().catch(() => null),
          api.getInbox().catch(() => ({ items: [] })),
          api.getCustomers().catch(() => ({ customers: [] })),
        ])
        if (mounted) {
          if (stateRes) setCareState(stateRes)
          setInboxItems(inboxRes?.items || [])
          setCustomerCount(custRes?.customers?.length || 0)
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

  const stats = careState?.stats_24h || {}
  const pendingDrafts = inboxItems.filter((i) => i.status === 'pending')

  const statCards = [
    {
      title: 'Bình luận 24h',
      value: stats.comments ?? inboxItems.length,
      icon: MessageSquare,
      color: 'text-blue-600 bg-blue-50 border-blue-100',
      actionTab: 'inbox',
    },
    {
      title: 'Lead tiềm năng',
      value: stats.leads ?? inboxItems.filter((i) => i.intent === 'lead' || i.phone).length,
      icon: UserPlus,
      color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
      actionTab: 'customers',
    },
    {
      title: 'Nháp chờ duyệt',
      value: pendingDrafts.length,
      icon: Clock,
      color: 'text-amber-600 bg-amber-50 border-amber-100',
      highlight: pendingDrafts.length > 0,
      actionTab: 'inbox',
    },
    {
      title: 'Đã phản hồi',
      value: stats.replied ?? inboxItems.filter((i) => i.status === 'sent').length,
      icon: CheckCircle2,
      color: 'text-indigo-600 bg-indigo-50 border-indigo-100',
      actionTab: 'inbox',
    },
    {
      title: 'Cần người hỗ trợ',
      value: stats.handoff ?? inboxItems.filter((i) => i.status === 'handoff').length,
      icon: AlertTriangle,
      color: 'text-rose-600 bg-rose-50 border-rose-100',
      actionTab: 'tasks',
    },
    {
      title: 'Khách tích luỹ (CRM)',
      value: customerCount,
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
              {careState?.page_name ? `Fanpage: ${careState.page_name}` : 'Trung Tâm Vận Hành Sao Việt'}
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-2xl">
              {careState?.enabled
                ? `Javis đang lắng nghe tương tác fanpage và chuẩn bị câu trả lời theo giáo trình Sao Việt.`
                : `Javis Care hiện đang tạm tắt. Vui lòng liên hệ Quản lý nếu cần bật tính năng tự động.`}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {pendingDrafts.length > 0 && (
              <button
                onClick={() => onNavigate('inbox')}
                className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-saoviet-500 hover:bg-saoviet-600 text-white font-bold text-xs shadow-md transition-all cursor-pointer"
              >
                <span>Duyệt {pendingDrafts.length} nháp ngay</span>
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
        {/* Left: Pending Drafts or Recent Comments (2 cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-5 h-5 text-saoviet-500" />
              <h2 className="font-bold text-slate-900 text-base">Bình luận & Nháp chờ xử lý</h2>
            </div>
            <button
              onClick={() => onNavigate('inbox')}
              className="text-xs font-semibold text-saoviet-600 hover:text-saoviet-700 flex items-center space-x-1"
            >
              <span>Xem tất cả ({inboxItems.length})</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 mt-2">
            {inboxItems.slice(0, 5).map((item) => (
              <div key={item.id || item.comment_id} className="py-3.5 hover:bg-slate-50/80 rounded-xl px-2 transition-colors">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start space-x-3">
                    <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                      {item.author_name ? item.author_name.slice(0, 2).toUpperCase() : 'KH'}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-xs text-slate-900">{item.author_name}</span>
                        {item.phone && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">
                            SĐT: {item.phone}
                          </span>
                        )}
                        {item.intent && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 font-medium">
                            {item.intent}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-700 mt-1 leading-relaxed line-clamp-2">
                        "{item.message}"
                      </p>
                      {item.draft_response && (
                        <div className="mt-2 p-2 rounded-lg bg-saoviet-50/60 border border-saoviet-100 text-xs text-slate-800">
                          <span className="font-semibold text-saoviet-700 text-[11px] block mb-0.5">
                            Javis soạn nháp:
                          </span>
                          <span className="italic text-slate-600 line-clamp-2">{item.draft_response}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="text-right flex-shrink-0">
                    <span className="text-[10px] text-slate-400 block">{timeAgo(item.created_time)}</span>
                    <span
                      className={`inline-block mt-1.5 text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        item.status === 'pending'
                          ? 'bg-amber-100 text-amber-800'
                          : item.status === 'sent'
                          ? 'bg-emerald-100 text-emerald-800'
                          : item.status === 'handoff'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {item.status === 'pending'
                        ? 'Chờ duyệt'
                        : item.status === 'sent'
                        ? 'Đã gửi'
                        : item.status === 'handoff'
                        ? 'Đã giao'
                        : 'Đã bỏ'}
                    </span>
                  </div>
                </div>
              </div>
            ))}

            {inboxItems.length === 0 && (
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
                  {careState?.page_name || (careState?.connected ? 'Đã liên kết' : 'Chưa liên kết')}
                </span>
              </div>

              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500">Chế độ hoạt động</span>
                <span className="font-semibold text-saoviet-700 capitalize">
                  {careState?.mode === 'full' ? 'Tự động + tin' : careState?.mode === 'semi' ? 'Bán tự động' : 'Tạo nháp (Gợi ý)'}
                </span>
              </div>

              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-slate-500">Quét lần cuối</span>
                <span className="font-medium text-slate-600">
                  {careState?.last_poll_ts ? formatTime(careState.last_poll_ts) : 'Chưa quét'}
                </span>
              </div>

              <div className="flex items-center justify-between py-2">
                <span className="text-slate-500">Hàng rào an toàn</span>
                <span className="font-semibold text-emerald-700">Đang bảo vệ (Fail-safe)</span>
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
              <li>Kiểm tra nháp Javis tạo trước khi nhấn <b>Gửi</b>.</li>
              <li>Nếu khách hỏi phức tạp, nhấn <b>Tạo việc giao người</b>.</li>
              <li>Khi nhắn tay Messenger, Javis tự lùi lại 4 giờ để nhân viên tư vấn liền mạch.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
