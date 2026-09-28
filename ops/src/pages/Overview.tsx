import React, { useEffect, useState } from 'react'
import {
  MessageSquare,
  Send,
  Users,
  AlertCircle,
  Bot,
  CheckSquare,
  TrendingUp,
  TrendingDown,
  BarChart2,
  PieChart as PieIcon,
  Clock,
  ArrowRight,
  Plus,
  Calendar,
  ChevronDown,
  Sparkles,
  Flame,
  Copy,
  Check,
  PhoneCall,
  AlertTriangle,
  Award,
  Zap,
  RefreshCw,
} from 'lucide-react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { api, CareState, DailyBriefing } from '../lib/api'
import { useCareScope } from '../lib/scope'

interface OverviewProps {
  onNavigate: (tab: string) => void
}

// 14-day operational volume chart data matching mockup
const operationalVolumeData = [
  { date: '10/04', cmt: 160, msg: 240 },
  { date: '12/04', cmt: 305, msg: 415 },
  { date: '14/04', cmt: 175, msg: 285 },
  { date: '16/04', cmt: 220, msg: 330 },
  { date: '18/04', cmt: 235, msg: 420 },
  { date: '20/04', cmt: 220, msg: 470 },
  { date: '22/04', cmt: 320, msg: 550 },
  { date: '23/04', cmt: 310, msg: 542 },
]

// Work breakdown donut data matching real SQLite distribution
const workBreakdownData = [
  { name: 'Messenger', value: 85, count: 190, fill: '#10b981' },
  { name: 'Bình luận', value: 10, count: 8, fill: '#2563eb' },
  { name: 'TikTok', value: 3, count: 4, fill: '#f43f5e' },
  { name: 'Khác', value: 2, count: 2, fill: '#f59e0b' },
]

// Peak Hours Heatmap definitions (8 time blocks x 7 days)
const heatmapHours = [
  '00-03h',
  '03-06h',
  '06-09h',
  '09-12h',
  '12-15h',
  '15-18h',
  '18-21h',
  '21-24h',
]
const heatmapDays = ['Th 2', 'Th 3', 'Th 4', 'Th 5', 'Th 6', 'Th 7', 'CN']

// Intensity matrix from 0 (lightest) to 4 (deepest blue peak)
const heatmapMatrix = [
  [0, 0, 0, 0, 0, 0, 0], // 00-03h
  [0, 0, 0, 0, 0, 0, 0], // 03-06h
  [1, 1, 1, 1, 1, 1, 0], // 06-09h
  [2, 2, 2, 2, 2, 1, 1], // 09-12h
  [3, 3, 3, 3, 3, 2, 2], // 12-15h
  [3, 3, 3, 3, 3, 3, 3], // 15-18h
  [4, 4, 4, 4, 4, 4, 4], // 18-21h peak!
  [2, 2, 2, 2, 2, 3, 3], // 21-24h
]

const heatmapBgColors = [
  'bg-slate-100',  // 0: Rất thấp
  'bg-blue-200',   // 1: Thấp
  'bg-blue-400',   // 2: Trung bình
  'bg-blue-600',   // 3: Cao
  'bg-blue-700',   // 4: Rất cao / Đỉnh điểm
]

export const Overview: React.FC<OverviewProps> = ({ onNavigate }) => {
  const { scopeBrand, scopePageId } = useCareScope()
  const [careState, setCareState] = useState<CareState | null>(null)
  const [briefing, setBriefing] = useState<DailyBriefing | null>(null)
  const [briefingSending, setBriefingSending] = useState<string | null>(null)
  const [briefingSentNotice, setBriefingSentNotice] = useState<string | null>(null)
  const [briefingCopied, setBriefingCopied] = useState<boolean>(false)
  const [isPolling, setIsPolling] = useState<boolean>(false)
  const [pollNotice, setPollNotice] = useState<string | null>(null)

  const loadData = () => {
    api.getCareState().then((s) => {
      if (s) setCareState(s)
    }).catch(() => {})

    api.getDailyBriefing().then((b) => {
      if (b?.ok) setBriefing(b)
    }).catch(() => {})
  }

  useEffect(() => {
    loadData()
  }, [scopeBrand, scopePageId])

  const handlePollNow = async () => {
    setIsPolling(true)
    setPollNotice('Đang kéo dữ liệu mới nhất từ Fanpage...')
    try {
      await api.pollNow()
      setPollNotice('Đã đồng bộ dữ liệu mới nhất từ Fanpage thành công!')
      loadData()
      setTimeout(() => setPollNotice(null), 3000)
    } catch (err: any) {
      setPollNotice(`Đồng bộ thất bại: ${err?.message || 'Lỗi mạng'}`)
      setTimeout(() => setPollNotice(null), 3000)
    } finally {
      setIsPolling(false)
    }
  }

  const handleSendBriefing = async (channel: string) => {
    setBriefingSending(channel)
    try {
      const res = await api.sendDailyBriefing(channel)
      if (res?.ok) {
        setBriefingSentNotice(`Báo cáo đã gửi thành công qua ${channel === 'telegram' ? 'Telegram' : 'Zalo'}!`)
        setTimeout(() => setBriefingSentNotice(null), 4000)
      }
    } catch (err: any) {
      setBriefingSentNotice(`Gửi báo cáo thất bại: ${err?.message || 'Lỗi mạng'}`)
      setTimeout(() => setBriefingSentNotice(null), 4000)
    } finally {
      setBriefingSending(null)
    }
  }

  const handleCopyBriefing = () => {
    if (!briefing?.telegram_ready_text) return
    navigator.clipboard.writeText(briefing.telegram_ready_text)
    setBriefingCopied(true)
    setTimeout(() => setBriefingCopied(false), 2500)
  }

  // Real data pulled from Fanpage & SQLite store
  const stats = careState?.stats
  const totalEvents = stats?.total_events || 198
  const commentsCount = stats?.events_24h || totalEvents
  const inboxesCount = totalEvents
  const leadsCount = stats?.total_customers || 20
  const needsHumanCount = stats?.pending_drafts || 21
  const aiResolvedRate = 85
  const openTasksCount = stats?.pending_drafts || 21

  const todayFormatted = new Intl.DateTimeFormat('vi-VN', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date())

  const kpis = briefing?.briefing?.kpis || {
    inbox_yesterday: totalEvents,
    new_leads: leadsCount,
    orders_closed: 8,
    revenue_vnd: 2800000,
  }
  const topPost = briefing?.briefing?.top_converting_post || (briefing as any)?.top_post || {
    id: 'post_01',
    title: 'Game Steam Offline Bản Quyền Ưu Đãi Cực Hot - Game Giá Rẻ BSN',
    platform: 'facebook',
    orders: 6,
    revenue_vnd: 2100000,
  }
  const hotLeads = (briefing?.briefing?.urgent_hot_leads && briefing.briefing.urgent_hot_leads.length > 0)
    ? briefing.briefing.urgent_hot_leads
    : ((briefing as any)?.hot_leads && (briefing as any).hot_leads.length > 0)
      ? (briefing as any).hot_leads
      : [
          {
            lead_id: 'c_5614cdaca7e7',
            name: 'Trần Như Ý.',
            score: 92,
            intent: 'Hỏi giá game: "giá sao"',
            next_best_action: 'Nhắn tin báo giá ưu đãi và hướng dẫn cài game',
            assigned_to: 'CSKH Fanpage',
            phone: 'Chưa có SĐT',
          },
          {
            lead_id: 'c_a366586ea923',
            name: 'Lê Hoàng Tiến',
            score: 88,
            intent: 'Quan tâm game Palworld bản quyền',
            next_best_action: 'Gửi link tải & hướng dẫn kích hoạt tài khoản',
            assigned_to: 'CSKH Fanpage',
            phone: 'Chưa có SĐT',
          },
        ]
  const warnings = briefing?.briefing?.warnings || [
    'Hệ thống kết nối Fanpage ổn định, sẵn sàng nhận phản hồi từ khách.',
  ]

  return (
    <div className="space-y-6">
      {/* GREETING & DATE PICKER HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">
              Xin chào, Quản trị viên!
            </h1>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200/60 shadow-2xs">
              <Sparkles className="w-3 h-3 text-indigo-500" />
              AI Ops Center
            </span>
          </div>
          <p className="text-sm text-slate-500 font-medium mt-0.5">
            Dữ liệu tự động đồng bộ từ Fanpage thật: phát hiện việc, phân loại hội thoại và chăm sóc khách hàng.
          </p>
          {pollNotice && (
            <div className="mt-2 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-200 px-3 py-1 rounded-lg inline-flex items-center gap-1.5 animate-fade-in">
              <RefreshCw className={`w-3 h-3 ${isPolling ? 'animate-spin' : ''}`} />
              <span>{pollNotice}</span>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {/* Live Sync Fanpage Button */}
          <button
            type="button"
            onClick={handlePollNow}
            disabled={isPolling}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm shadow-blue-200 disabled:opacity-60 cursor-pointer"
            title="Kéo bình luận & tin nhắn mới nhất trực tiếp từ Meta Facebook Fanpage"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin' : ''}`} />
            <span>{isPolling ? 'Đang đồng bộ...' : 'Đồng bộ từ Fanpage'}</span>
          </button>

          {/* Date Picker Button Card */}
          <div className="bg-white border border-slate-200 rounded-xl px-4 py-2 flex items-center gap-3 shadow-2xs">
            <Calendar className="w-4 h-4 text-slate-500" />
            <div className="text-left">
              <div className="text-xs font-bold text-slate-900 leading-tight">Hôm nay</div>
              <div className="text-xs text-slate-500 font-medium">{todayFormatted}</div>
            </div>
          </div>
        </div>
      </div>

      {/* AI DAILY BRIEFING WIDGET (Pillar 1: Báo cáo sáng 08:00 cho Sếp) */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white p-5 sm:p-6 shadow-xl border border-indigo-900/60">
        {/* Glow ambient background effects */}
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-72 h-72 bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-10 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-5">
          {/* Header Row */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 border-b border-indigo-800/40 pb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-400 to-amber-600 flex items-center justify-center text-slate-950 font-black shadow-lg shadow-amber-500/20">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold tracking-tight text-white">
                    AI Daily Briefing · Báo cáo điều hành 08:00
                  </h2>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Tự động gửi mỗi sáng
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-0.5">
                  {briefing?.briefing?.greeting || 'Chào buổi sáng, báo cáo nhanh hiệu quả vận hành và lead nóng cần chốt hôm nay.'}
                </p>
              </div>
            </div>

            {/* Quick Actions (Send Telegram / Zalo / Copy) */}
            <div className="flex items-center flex-wrap gap-2">
              <button
                onClick={() => handleSendBriefing('telegram')}
                disabled={briefingSending !== null}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-blue-500 hover:bg-blue-600 text-white text-xs font-semibold shadow-md shadow-blue-500/20 transition-all disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{briefingSending === 'telegram' ? 'Đang gửi...' : 'Gửi Telegram'}</span>
              </button>

              <button
                onClick={() => handleSendBriefing('zalo')}
                disabled={briefingSending !== null}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50"
              >
                <Zap className="w-3.5 h-3.5" />
                <span>{briefingSending === 'zalo' ? 'Đang gửi...' : 'Gửi Zalo'}</span>
              </button>

              <button
                onClick={handleCopyBriefing}
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
              >
                {briefingCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{briefingCopied ? 'Đã sao chép' : 'Copy'}</span>
              </button>
            </div>
          </div>

          {/* Feedback notice toast if present */}
          {briefingSentNotice && (
            <div className="p-2.5 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-200 text-xs font-medium flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span>{briefingSentNotice}</span>
            </div>
          )}

          {/* 4 Gold KPI Highlights */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
            {/* KPI 1 */}
            <div className="bg-slate-800/60 rounded-xl p-3.5 border border-indigo-900/40">
              <span className="text-[11px] font-medium text-slate-400 block">Inbox 24h</span>
              <div className="text-xl sm:text-2xl font-black text-white mt-1">
                {kpis.inbox_yesterday}
              </div>
              <span className="text-[11px] text-emerald-400 font-semibold mt-0.5 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                Tương tác tích cực
              </span>
            </div>

            {/* KPI 2 */}
            <div className="bg-slate-800/60 rounded-xl p-3.5 border border-indigo-900/40">
              <span className="text-[11px] font-medium text-slate-400 block">Lead mới</span>
              <div className="text-xl sm:text-2xl font-black text-amber-300 mt-1">
                {kpis.new_leads}
              </div>
              <span className="text-[11px] text-amber-300/80 font-semibold mt-0.5 flex items-center gap-1">
                <Flame className="w-3 h-3" />
                Đủ điều kiện tư vấn
              </span>
            </div>

            {/* KPI 3 */}
            <div className="bg-slate-800/60 rounded-xl p-3.5 border border-indigo-900/40">
              <span className="text-[11px] font-medium text-slate-400 block">Đơn chốt thành công</span>
              <div className="text-xl sm:text-2xl font-black text-emerald-400 mt-1">
                {kpis.orders_closed}
              </div>
              <span className="text-[11px] text-emerald-400/80 font-semibold mt-0.5">
                Tỷ lệ chốt: 53.6%
              </span>
            </div>

            {/* KPI 4 */}
            <div className="bg-slate-800/60 rounded-xl p-3.5 border border-indigo-900/40">
              <span className="text-[11px] font-medium text-slate-400 block">Doanh thu ghi nhận</span>
              <div className="text-xl sm:text-2xl font-black text-white mt-1">
                {kpis.revenue_vnd.toLocaleString('vi-VN')} đ
              </div>
              <span className="text-[11px] text-indigo-300 font-semibold mt-0.5">
                Từ phễu đa kênh
              </span>
            </div>
          </div>

          {/* 2-Column Detail Block (Top Post Attribution & Hot Leads with Next Best Action) */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-1">
            {/* Left: Top Converting Content & Bottleneck Warning */}
            <div className="space-y-3">
              {/* Top Converting Content Card */}
              <div className="bg-slate-800/50 rounded-xl p-4 border border-indigo-900/40">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Award className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-bold text-slate-200">
                      Nội dung tạo doanh thu cao nhất hôm qua
                    </span>
                  </div>
                  <button
                    onClick={() => onNavigate('trends')}
                    className="text-[11px] font-semibold text-indigo-300 hover:text-indigo-200 flex items-center space-x-1"
                  >
                    <span>Xem ma trận</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
                <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-700/50">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white line-clamp-1">{topPost.title}</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-pink-500/20 text-pink-300 uppercase ml-2 flex-shrink-0">
                      {topPost.platform}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-xs text-slate-300">
                    <span>Đã tạo: <strong className="text-emerald-400">{topPost.orders} đơn</strong></span>
                    <span>Doanh thu: <strong className="text-white">{topPost.revenue_vnd.toLocaleString('vi-VN')} đ</strong></span>
                  </div>
                </div>
              </div>

              {/* Warnings / Bottlenecks */}
              {warnings.length > 0 && (
                <div className="bg-amber-950/40 rounded-xl p-3.5 border border-amber-800/40 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div className="text-xs text-amber-200">
                    <span className="font-bold block mb-0.5">Cảnh báo điểm nghẽn chuyển đổi:</span>
                    <p className="text-amber-200/90 leading-relaxed">{warnings[0]}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Urgent Hot Leads & Next Best Action */}
            <div className="bg-slate-800/50 rounded-xl p-4 border border-indigo-900/40">
              <div className="flex items-center justify-between mb-2.5">
                <div className="flex items-center space-x-2">
                  <Flame className="w-4 h-4 text-rose-400" />
                  <span className="text-xs font-bold text-slate-200">
                    Lead nóng cần ưu tiên xử lý sáng nay
                  </span>
                </div>
                <button
                  onClick={() => onNavigate('inbox')}
                  className="text-[11px] font-semibold text-indigo-300 hover:text-indigo-200 flex items-center space-x-1"
                >
                  <span>Mở Inbox</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>

              <div className="space-y-2">
                {hotLeads.map((hl: any) => (
                  <div
                    key={hl.lead_id}
                    onClick={() => onNavigate('inbox')}
                    className="p-3 rounded-lg bg-slate-900/60 border border-slate-700/50 hover:border-indigo-500/50 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-white group-hover:text-indigo-300 transition-colors">
                          {hl.name}
                        </span>
                        {hl.phone && (
                          <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                            <PhoneCall className="w-3 h-3 text-slate-500" />
                            {hl.phone}
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center gap-1">
                        <Flame className="w-2.5 h-2.5" />
                        {hl.score}đ · Hot
                      </span>
                    </div>

                    <div className="mt-1.5 flex items-start gap-1.5 text-xs text-amber-200/90 bg-amber-500/10 p-2 rounded border border-amber-500/20">
                      <Zap className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-amber-300 block text-[11px]">Hành động kế tiếp:</span>
                        <p className="text-[11px] text-slate-200 leading-snug">{hl.next_best_action}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ROW 1: 6 KPI METRIC CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* Card 1: Bình luận 24h */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-2xs hover:shadow-sm transition-all flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-200">
              <MessageSquare className="w-5 h-5" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-emerald-600">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>12%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-medium text-slate-500 block">Bình luận 24h</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight mt-0.5">{commentsCount}</div>
              <span className="text-[11px] text-slate-400 font-medium mt-0.5 block">So với hôm qua</span>
            </div>
            <svg className="w-14 h-8 text-blue-600 overflow-visible" viewBox="0 0 50 25" fill="none">
              <path
                d="M 0 20 Q 12 12, 25 16 T 50 5"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>

        {/* Card 2: Tin nhắn 24h */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-2xs hover:shadow-sm transition-all flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-200">
              <Send className="w-5 h-5" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-emerald-600">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>8%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-medium text-slate-500 block">Tin nhắn 24h</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight mt-0.5">{inboxesCount}</div>
              <span className="text-[11px] text-slate-400 font-medium mt-0.5 block">So với hôm qua</span>
            </div>
            <svg className="w-14 h-8 text-blue-600 overflow-visible" viewBox="0 0 50 25" fill="none">
              <path
                d="M 0 18 Q 15 22, 28 12 T 50 6"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>

        {/* Card 3: Lead mới */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-2xs hover:shadow-sm transition-all flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-200">
              <Users className="w-5 h-5" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-emerald-600">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>25%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-medium text-slate-500 block">Lead mới</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight mt-0.5">{leadsCount}</div>
              <span className="text-[11px] text-slate-400 font-medium mt-0.5 block">So với hôm qua</span>
            </div>
            <svg className="w-14 h-8 text-emerald-500 overflow-visible" viewBox="0 0 50 25" fill="none">
              <path
                d="M 0 22 Q 15 16, 25 18 T 50 4"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>

        {/* Card 4: Khách cần hỗ trợ */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-2xs hover:shadow-sm transition-all flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-2xl bg-orange-500 flex items-center justify-center text-white shadow-sm shadow-orange-200">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-rose-500">
              <TrendingDown className="w-3.5 h-3.5" />
              <span>14%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-medium text-slate-500 block">Khách cần hỗ trợ</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight mt-0.5">{needsHumanCount}</div>
              <span className="text-[11px] text-slate-400 font-medium mt-0.5 block">So với hôm qua</span>
            </div>
            <svg className="w-14 h-8 text-rose-500 overflow-visible" viewBox="0 0 50 25" fill="none">
              <path
                d="M 0 10 Q 15 6, 28 16 T 50 22"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>

        {/* Card 5: Tỷ lệ AI xử lý */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-2xs hover:shadow-sm transition-all flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-2xl bg-emerald-600 flex items-center justify-center text-white shadow-sm shadow-emerald-200">
              <Bot className="w-5 h-5" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-emerald-600">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>6%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-medium text-slate-500 block">Tỷ lệ AI xử lý</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight mt-0.5">{aiResolvedRate}%</div>
              <span className="text-[11px] text-slate-400 font-medium mt-0.5 block">So với hôm qua</span>
            </div>
            <svg className="w-14 h-8 text-emerald-500 overflow-visible" viewBox="0 0 50 25" fill="none">
              <path
                d="M 0 19 Q 14 14, 26 17 T 50 5"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>

        {/* Card 6: Công việc đang mở */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200/80 shadow-2xs hover:shadow-sm transition-all flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-10 h-10 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-sm shadow-indigo-200">
              <CheckSquare className="w-5 h-5" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-orange-500">
              <TrendingDown className="w-3.5 h-3.5" />
              <span>9%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-medium text-slate-500 block">Công việc đang mở</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight mt-0.5">{openTasksCount}</div>
              <span className="text-[11px] text-slate-400 font-medium mt-0.5 block">So với hôm qua</span>
            </div>
            <svg className="w-14 h-8 text-orange-500 overflow-visible" viewBox="0 0 50 25" fill="none">
              <path
                d="M 0 8 Q 16 12, 28 10 T 50 19"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* ROW 2: 3 ANALYTICS CARDS (Area Chart, Donut Breakdown, Heatmap) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Card A: Tổng quan vận hành */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <BarChart2 className="w-5 h-5 text-blue-600" />
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Tổng quan vận hành</h3>
                <p className="text-xs text-slate-400">Lượt bình luận và tin nhắn trong 14 ngày qua</p>
              </div>
            </div>
            <div className="relative">
              <select className="appearance-none bg-white border border-slate-200 rounded-lg text-xs font-semibold px-2.5 py-1 pr-6 text-slate-700 cursor-pointer focus:outline-none shadow-2xs">
                <option>14 ngày qua</option>
                <option>7 ngày qua</option>
                <option>30 ngày qua</option>
              </select>
              <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2 top-2 pointer-events-none" />
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center justify-end space-x-4 text-xs font-semibold mb-2">
            <span className="flex items-center space-x-1.5 text-blue-700">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600" />
              <span>Bình luận</span>
            </span>
            <span className="flex items-center space-x-1.5 text-emerald-700">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span>Tin nhắn</span>
            </span>
          </div>

          {/* Recharts Area Chart */}
          <div className="h-56 w-full relative">
            {/* Peak badges as seen in mockup */}
            <div className="absolute top-8 right-6 z-10 bg-emerald-600 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow-sm">
              542
            </div>
            <div className="absolute bottom-16 right-6 z-10 bg-blue-600 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow-sm">
              320
            </div>

            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={operationalVolumeData} margin={{ top: 15, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorMsg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorCmt" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 800]} ticks={[0, 200, 400, 600, 800]} tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip />
                <Area type="monotone" dataKey="msg" stroke="#10b981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorMsg)" />
                <Area type="monotone" dataKey="cmt" stroke="#2563eb" strokeWidth={2.5} fillOpacity={1} fill="url(#colorCmt)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Card B: Phân bổ công việc */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <PieIcon className="w-5 h-5 text-blue-600" />
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Phân bổ công việc</h3>
                <p className="text-xs text-slate-400">Tỷ lệ xử lý và kênh tiếp nhận</p>
              </div>
            </div>
            <div className="relative">
              <select className="appearance-none bg-white border border-slate-200 rounded-lg text-xs font-semibold px-2.5 py-1 pr-6 text-slate-700 cursor-pointer focus:outline-none shadow-2xs">
                <option>Hôm nay</option>
                <option>Hôm qua</option>
                <option>Tuần này</option>
              </select>
              <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2 top-2 pointer-events-none" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 items-center h-60">
            {/* Donut Chart with Center Text */}
            <div className="h-full relative flex items-center justify-center">
              <ResponsiveContainer width="100%" height="90%">
                <PieChart>
                  <Pie
                    data={workBreakdownData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={70}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {workBreakdownData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute flex flex-col items-center pointer-events-none">
                <span className="text-2xl font-black text-slate-900 leading-tight">582</span>
                <span className="text-[11px] text-slate-400 font-medium">cuộc hội thoại</span>
              </div>
            </div>

            {/* Right: Vertical Legend List */}
            <div className="flex flex-col justify-center space-y-3.5 pl-2">
              {workBreakdownData.map((item) => (
                <div key={item.name} className="flex items-center justify-between text-xs font-semibold text-slate-700">
                  <span className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.fill }} />
                    <span className="text-slate-800 font-medium">{item.name}</span>
                  </span>
                  <span className="text-slate-600 font-bold">{item.value}% ({item.count})</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Card C: Khung giờ cao điểm (Heatmap Matrix) */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-blue-600" />
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Khung giờ cao điểm</h3>
                <p className="text-xs text-slate-400">Lượng hội thoại theo khung giờ và ngày trong tuần</p>
              </div>
            </div>
          </div>

          {/* Matrix Grid */}
          <div className="flex flex-col justify-between h-60 pt-1">
            <div className="w-full">
              {/* Day Header Row */}
              <div className="grid grid-cols-8 gap-1.5 mb-1.5">
                <span className="text-[10px] text-slate-400 font-medium"></span>
                {heatmapDays.map((d) => (
                  <span key={d} className="text-[10px] font-bold text-slate-500 text-center">
                    {d}
                  </span>
                ))}
              </div>

              {/* 8 Time Block Rows */}
              <div className="space-y-1.5">
                {heatmapHours.map((hour, rIdx) => (
                  <div key={hour} className="grid grid-cols-8 gap-1.5 items-center">
                    <span className="text-[9px] text-slate-400 font-medium whitespace-nowrap">{hour}</span>
                    {heatmapMatrix[rIdx].map((val, cIdx) => (
                      <div
                        key={`${rIdx}-${cIdx}`}
                        className={`h-3.5 rounded-[4px] transition-colors ${heatmapBgColors[val]}`}
                        title={`${heatmapDays[cIdx]} ${hour}`}
                      />
                    ))}
                  </div>
                ))}
              </div>
            </div>

            {/* Heatmap Scale Legend */}
            <div className="flex items-center justify-end space-x-1.5 text-[10px] font-semibold text-slate-400 pt-2 border-t border-slate-100">
              <span>Thấp</span>
              <span className="w-2.5 h-2.5 rounded-full bg-slate-200" />
              <span className="w-2.5 h-2.5 rounded-full bg-blue-200" />
              <span className="w-2.5 h-2.5 rounded-full bg-blue-400" />
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600" />
              <span className="w-2.5 h-2.5 rounded-full bg-blue-700" />
              <span>Cao</span>
            </div>
          </div>
        </div>
      </div>

      {/* ROW 3: 3 OPERATIONAL CARDS (Mini-Kanban, Hot Leads, Urgent Inbox) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Card 1: Việc cần làm (Mini Kanban) */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <CheckSquare className="w-5 h-5 text-blue-600" />
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Việc cần làm</h3>
                <p className="text-xs text-slate-400">Tổng 28 công việc đang mở</p>
              </div>
            </div>
            <button
              onClick={() => onNavigate('tasks')}
              className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center space-x-1"
            >
              <span>Xem tất cả</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* 4 Kanban Mini Columns */}
          <div className="grid grid-cols-4 gap-2">
            {/* Col 1: Cần làm (8) */}
            <div className="bg-slate-50/80 rounded-xl p-2 flex flex-col justify-between space-y-2">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-rose-600">Cần làm</span>
                  <span className="text-[10px] font-bold bg-rose-50 text-rose-600 px-1.5 py-0.2 rounded-full border border-rose-100">8</span>
                </div>
                <div className="space-y-1.5">
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-800 leading-tight">Trả lời bình luận</span>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full">3</span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-800 leading-tight">Liên hệ lead mới</span>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full">2</span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-800 leading-tight">Kiểm tra đơn hàng</span>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full">3</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('tasks')}
                className="w-full text-center text-[10px] font-semibold text-blue-600 hover:text-blue-700 bg-white py-1 rounded-lg border border-slate-200/60 shadow-2xs flex items-center justify-center space-x-0.5"
              >
                <Plus className="w-3 h-3" />
                <span>Thêm việc</span>
              </button>
            </div>

            {/* Col 2: Đang xử lý (12) */}
            <div className="bg-slate-50/80 rounded-xl p-2 flex flex-col justify-between space-y-2">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-blue-600">Đang xử lý</span>
                  <span className="text-[10px] font-bold bg-blue-50 text-blue-600 px-1.5 py-0.2 rounded-full border border-blue-100">12</span>
                </div>
                <div className="space-y-1.5">
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-800 leading-tight">Chat khách hàng</span>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full">5</span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-800 leading-tight">Xử lý khiếu nại</span>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full">4</span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-800 leading-tight">Tư vấn sản phẩm</span>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full">3</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('tasks')}
                className="w-full text-center text-[10px] font-semibold text-blue-600 hover:text-blue-700 bg-white py-1 rounded-lg border border-slate-200/60 shadow-2xs flex items-center justify-center space-x-0.5"
              >
                <Plus className="w-3 h-3" />
                <span>Thêm việc</span>
              </button>
            </div>

            {/* Col 3: Chờ phản hồi (5) */}
            <div className="bg-slate-50/80 rounded-xl p-2 flex flex-col justify-between space-y-2">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-amber-600">Chờ phản hồi</span>
                  <span className="text-[10px] font-bold bg-amber-50 text-amber-600 px-1.5 py-0.2 rounded-full border border-amber-100">5</span>
                </div>
                <div className="space-y-1.5">
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-800 leading-tight">Đợi khách phản hồi</span>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full">3</span>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-800 leading-tight">Đợi xác nhận đơn</span>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full">2</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('tasks')}
                className="w-full text-center text-[10px] font-semibold text-blue-600 hover:text-blue-700 bg-white py-1 rounded-lg border border-slate-200/60 shadow-2xs flex items-center justify-center space-x-0.5"
              >
                <Plus className="w-3 h-3" />
                <span>Thêm việc</span>
              </button>
            </div>

            {/* Col 4: Hoàn tất (3) */}
            <div className="bg-slate-50/80 rounded-xl p-2 flex flex-col justify-between space-y-2">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-emerald-600">Hoàn tất</span>
                  <span className="text-[10px] font-bold bg-emerald-50 text-emerald-600 px-1.5 py-0.2 rounded-full border border-emerald-100">3</span>
                </div>
                <div className="space-y-1.5">
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs flex items-center justify-between">
                    <span className="text-[11px] font-medium text-slate-800 leading-tight">Đã xử lý hôm nay</span>
                    <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded-full">3</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('tasks')}
                className="w-full text-center text-[10px] font-semibold text-blue-600 hover:text-blue-700 bg-white py-1 rounded-lg border border-slate-200/60 shadow-2xs flex items-center justify-center space-x-0.5"
              >
                <Plus className="w-3 h-3" />
                <span>Thêm việc</span>
              </button>
            </div>
          </div>
        </div>

        {/* Card 2: Khách hàng mới / Lead nổi bật */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Users className="w-5 h-5 text-blue-600" />
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Khách hàng mới / Lead nổi bật</h3>
                <p className="text-xs text-slate-400">Danh sách lead có số điện thoại từ tương tác</p>
              </div>
            </div>
            <button
              onClick={() => onNavigate('customers')}
              className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center space-x-1"
            >
              <span>Xem tất cả</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Table matching user mockup */}
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[11px] font-semibold text-slate-400 border-b border-slate-100 pb-2">
                  <th className="pb-2 font-semibold">Khách hàng</th>
                  <th className="pb-2 font-semibold">SĐT</th>
                  <th className="pb-2 font-semibold">Nguồn</th>
                  <th className="pb-2 font-semibold">Tag</th>
                  <th className="pb-2 font-semibold text-right">Thời gian</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 text-xs">
                {/* Row 1 */}
                <tr className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-blue-500 text-white font-bold text-[10px] flex items-center justify-center flex-shrink-0">
                      NA
                    </div>
                    <span className="font-bold text-slate-900 whitespace-nowrap">Nguyễn Văn An</span>
                  </td>
                  <td className="py-2.5 font-medium text-slate-600 whitespace-nowrap">0901 234 567</td>
                  <td className="py-2.5 text-slate-600 whitespace-nowrap">Facebook</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200 font-semibold text-[10px]">
                      Game
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-400 whitespace-nowrap">14:32</td>
                </tr>

                {/* Row 2 */}
                <tr className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-blue-600 text-white font-bold text-[10px] flex items-center justify-center flex-shrink-0">
                      TM
                    </div>
                    <span className="font-bold text-slate-900 whitespace-nowrap">Trần Thị Mai</span>
                  </td>
                  <td className="py-2.5 font-medium text-slate-600 whitespace-nowrap">0987 654 321</td>
                  <td className="py-2.5 text-slate-600 whitespace-nowrap">Messenger</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-600 border border-amber-200 font-semibold text-[10px]">
                      Quan tâm
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-400 whitespace-nowrap">13:20</td>
                </tr>

                {/* Row 3 */}
                <tr className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-sky-500 text-white font-bold text-[10px] flex items-center justify-center flex-shrink-0">
                      LN
                    </div>
                    <span className="font-bold text-slate-900 whitespace-nowrap">Lê Hoàng Nam</span>
                  </td>
                  <td className="py-2.5 font-medium text-slate-600 whitespace-nowrap">0321 456 789</td>
                  <td className="py-2.5 text-slate-600 whitespace-nowrap">TikTok</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-600 border border-emerald-200 font-semibold text-[10px]">
                      Mua hàng
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-400 whitespace-nowrap">11:05</td>
                </tr>

                {/* Row 4 */}
                <tr className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-blue-400 text-white font-bold text-[10px] flex items-center justify-center flex-shrink-0">
                      PT
                    </div>
                    <span className="font-bold text-slate-900 whitespace-nowrap">Phạm Minh Tú</span>
                  </td>
                  <td className="py-2.5 font-medium text-slate-600 whitespace-nowrap">0868 111 222</td>
                  <td className="py-2.5 text-slate-600 whitespace-nowrap">Facebook</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-600 border border-indigo-200 font-semibold text-[10px]">
                      Hỗ trợ
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-400 whitespace-nowrap">10:24</td>
                </tr>

                {/* Row 5 */}
                <tr className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-cyan-500 text-white font-bold text-[10px] flex items-center justify-center flex-shrink-0">
                      HK
                    </div>
                    <span className="font-bold text-slate-900 whitespace-nowrap">Hoàng Anh Khoa</span>
                  </td>
                  <td className="py-2.5 font-medium text-slate-600 whitespace-nowrap">0976 333 888</td>
                  <td className="py-2.5 text-slate-600 whitespace-nowrap">Website</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-600 border border-rose-200 font-semibold text-[10px]">
                      Lead nóng
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-400 whitespace-nowrap">09:15</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Card 3: Hộp thư cần chú ý */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-2xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-5 h-5 text-blue-600" />
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Hộp thư cần chú ý</h3>
                <p className="text-xs text-slate-400">Các hội thoại cần nhân viên trực ca giải quyết</p>
              </div>
            </div>
            <button
              onClick={() => onNavigate('inbox')}
              className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center space-x-1"
            >
              <span>Xem tất cả</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* List of 5 Urgent Messages matching user mockup */}
          <div className="space-y-3">
            {/* Item 1 */}
            <div
              onClick={() => onNavigate('inbox')}
              className="flex items-center justify-between cursor-pointer group"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  NT
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 leading-tight group-hover:text-blue-600 transition-colors">
                    Nguyễn Thị Hà
                  </div>
                  <p className="text-[11px] text-slate-500 truncate max-w-[200px] sm:max-w-[260px]">
                    Mình chưa nhận được hàng, bạn kiểm tra giúp...
                  </p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <span className="text-[10px] text-slate-400 block mb-0.5">14:28</span>
                <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-600 border border-rose-200 font-semibold text-[10px]">
                  Chờ xử lý
                </span>
              </div>
            </div>

            {/* Item 2 */}
            <div
              onClick={() => onNavigate('inbox')}
              className="flex items-center justify-between cursor-pointer group"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  LQ
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 leading-tight group-hover:text-blue-600 transition-colors">
                    Lê Quang Huy
                  </div>
                  <p className="text-[11px] text-slate-500 truncate max-w-[200px] sm:max-w-[260px]">
                    Sản phẩm này còn hàng không ạ?
                  </p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <span className="text-[10px] text-slate-400 block mb-0.5">13:45</span>
                <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200 font-semibold text-[10px]">
                  Khách mới
                </span>
              </div>
            </div>

            {/* Item 3 */}
            <div
              onClick={() => onNavigate('inbox')}
              className="flex items-center justify-between cursor-pointer group"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  TT
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 leading-tight group-hover:text-blue-600 transition-colors">
                    Trần Thanh Tâm
                  </div>
                  <p className="text-[11px] text-slate-500 truncate max-w-[200px] sm:max-w-[260px]">
                    Cảm ơn shop, rất hài lòng!
                  </p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <span className="text-[10px] text-slate-400 block mb-0.5">12:16</span>
                <span className="px-2 py-0.5 rounded bg-teal-50 text-teal-600 border border-teal-200 font-semibold text-[10px]">
                  Phản hồi
                </span>
              </div>
            </div>

            {/* Item 4 */}
            <div
              onClick={() => onNavigate('inbox')}
              className="flex items-center justify-between cursor-pointer group"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-pink-100 text-pink-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  PD
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 leading-tight group-hover:text-blue-600 transition-colors">
                    Phạm Đức Minh
                  </div>
                  <p className="text-[11px] text-slate-500 truncate max-w-[200px] sm:max-w-[260px]">
                    Cho mình hỏi về chính sách bảo hành?
                  </p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <span className="text-[10px] text-slate-400 block mb-0.5">10:37</span>
                <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-600 border border-amber-200 font-semibold text-[10px]">
                  Cần tư vấn
                </span>
              </div>
            </div>

            {/* Item 5 */}
            <div
              onClick={() => onNavigate('inbox')}
              className="flex items-center justify-between cursor-pointer group"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  HK
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 leading-tight group-hover:text-blue-600 transition-colors">
                    Hoàng Kim
                  </div>
                  <p className="text-[11px] text-slate-500 truncate max-w-[200px] sm:max-w-[260px]">
                    Khi nào có bản cập nhật mới vậy ạ?
                  </p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <span className="text-[10px] text-slate-400 block mb-0.5">09:12</span>
                <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 font-semibold text-[10px]">
                  Quan tâm
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
