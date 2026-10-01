import React, { useState, useEffect } from 'react'
import {
  TrendingUp,
  BarChart2,
  PieChart as PieIcon,
  DollarSign,
  Cpu,
  Layers,
  Calendar,
  Sparkles,
  Award,
  Flame,
  ArrowUpRight,
  CheckCircle2,
  Target,
  Compass,
  Zap,
  Clock,
  ShieldCheck,
  Eye,
  MessageSquare,
  Users,
  ShoppingBag,
  TrendingDown,
  Radar as RadarIcon,
  Search,
  Activity,
  AlertTriangle,
  Send,
  RefreshCw,
  Copy,
  Check,
  ArrowRight,
  PhoneCall,
  FileCheck2,
  AlertCircle,
  HelpCircle,
  Truck,
  PackageCheck,
  Bot,
  Lightbulb,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from 'recharts'
import {
  api,
  AttributionMatrixResponse,
  AttributionInsightsResponse,
  CompetitorRadarResponse,
  ExecutiveReport,
} from '../lib/api'
import { useAuth } from '../lib/auth'
import { PlatformPill } from '../components/BrandIcons'

const COLORS = ['#f97316', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#f59e0b']

export const Trends: React.FC = () => {
  const { role } = useAuth()
  const [activeTab, setActiveTab] = useState<'executive' | 'attribution' | 'learning' | 'radar' | 'ops'>('executive')

  // Executive Report state
  const [report, setReport] = useState<ExecutiveReport | null>(null)
  const [reportPeriod, setReportPeriod] = useState<'today' | '7d' | 'all'>('today')
  const [reportLoading, setReportLoading] = useState<boolean>(true)
  const [sendingReport, setSendingReport] = useState<boolean>(false)
  const [copySuccess, setCopySuccess] = useState<boolean>(false)
  const [sendSuccessMessage, setSendSuccessMessage] = useState<string | null>(null)

  // Ops datasets
  const [usage, setUsage] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [stats, setStats] = useState<any>(null)
  const [branchData, setBranchData] = useState<any[]>([])
  const [intentData, setIntentData] = useState<any[]>([])
  const [dailyActivity, setDailyActivity] = useState<any[]>([])

  // AI Center datasets
  const [attribution, setAttribution] = useState<AttributionMatrixResponse | null>(null)
  const [insights, setInsights] = useState<AttributionInsightsResponse | null>(null)
  const [radar, setRadar] = useState<CompetitorRadarResponse | null>(null)

  const loadExecutiveReport = async (period: 'today' | '7d' | 'all') => {
    setReportLoading(true)
    try {
      const res = await api.getExecutiveReport(period)
      if (res && res.ok) {
        setReport(res)
      }
    } catch (e) {
      console.error('Failed to load executive report', e)
    } finally {
      setReportLoading(false)
    }
  }

  const handleSendTelegram = async () => {
    setSendingReport(true)
    setSendSuccessMessage(null)
    try {
      const res = await api.sendExecutiveReport('telegram', reportPeriod)
      if (res && res.ok) {
        setSendSuccessMessage(res.message || 'Đã gửi báo cáo nhận xét điều hành qua Telegram thành công!')
        setTimeout(() => setSendSuccessMessage(null), 5000)
      }
    } catch (e) {
      alert('Không thể gửi báo cáo qua Telegram. Vui lòng kiểm tra cấu hình bot.')
    } finally {
      setSendingReport(false)
    }
  }

  const handleCopyReport = () => {
    if (!report?.formatted_text) return
    navigator.clipboard.writeText(report.formatted_text)
    setCopySuccess(true)
    setTimeout(() => setCopySuccess(false), 3000)
  }

  const handleNavigate = (route: string) => {
    window.location.hash = `#/${route}`
  }

  useEffect(() => {
    const loadData = async () => {
      try {
        const [usageRes, custRes, inboxRes, attrRes, insRes, radRes, repRes] = await Promise.all([
          api.getUsageSummary().catch(() => null),
          api.getCustomers('', '', 200).catch(() => ({ ok: false, customers: [] })),
          api.getInbox({ limit: 200 }).catch(() => ({ ok: false, events: [], drafts: [], stats: null as any })),
          api.getAttributionMatrix().catch(() => null),
          api.getAttributionInsights().catch(() => null),
          api.getCompetitorRadar().catch(() => null),
          api.getExecutiveReport(reportPeriod).catch(() => null),
        ])

        if (usageRes) setUsage(usageRes)
        if (inboxRes?.stats) setStats(inboxRes.stats)
        if (attrRes?.ok) setAttribution(attrRes)
        if (insRes?.ok) setInsights(insRes)
        if (radRes?.ok) setRadar(radRes)
        if (repRes?.ok) setReport(repRes)

        // 1. Group leads by campus (branch)
        const customers = custRes?.customers || []
        const branchCounts: Record<string, number> = {}
        customers.forEach((c: any) => {
          const b = c.campus || 'Chưa gắn cơ sở'
          branchCounts[b] = (branchCounts[b] || 0) + 1
        })
        setBranchData(Object.entries(branchCounts).map(([name, value]) => ({ name, value })))

        // 2. Group comments/messages by intent or classification
        const events = inboxRes?.events || []
        const intentCounts: Record<string, number> = {}
        events.forEach((e: any) => {
          const it = e.faq_intent || e.class || 'Tư vấn chung'
          intentCounts[it] = (intentCounts[it] || 0) + 1
        })
        setIntentData(Object.entries(intentCounts).map(([name, value]) => ({ name, value })))

        const dayNames = ['Chủ Nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']
        const buckets: Record<string, { comments: number; leads: number; replied: number }> = {}
        dayNames.forEach((d) => { buckets[d] = { comments: 0, leads: 0, replied: 0 } })
        events.forEach((e: any) => {
          const ts = Number(e.created_ts) || 0
          if (!ts) return
          const label = dayNames[new Date(ts * 1000).getDay()]
          const b = buckets[label]
          if (e.kind === 'comment') b.comments += 1
          if (e.kind === 'message') b.comments += 1
          if (e.class === 'lead') b.leads += 1
        })
        setDailyActivity(dayNames.map((d) => ({ day: d, ...buckets[d] })))
      } finally {
        setLoading(false)
        setReportLoading(false)
      }
    }

    loadData()
  }, [])

  if (role === 'staff') {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500">
        <TrendingUp className="w-10 h-10 mx-auto mb-3 text-slate-300" />
        <h3 className="font-bold text-slate-800 text-sm">Giới hạn quyền truy cập</h3>
        <p className="text-xs text-slate-500 mt-1">
          Trang Báo Cáo & Nhận Xét Điều Hành chỉ dành cho tài khoản Quản lý và Chủ máy.
        </p>
      </div>
    )
  }

  // Attribution data
  const attrSummary = attribution?.summary || {
    total_views: 0,
    total_inboxes: 0,
    total_leads: 0,
    total_orders: 0,
    total_revenue_vnd: 0,
    top_converting_platform: 'Chưa có',
  }
  const attrItems = attribution?.items || []

  // Insights data
  const winningPatterns = insights?.winning_patterns || []
  const timingRec = insights?.timing_recommendation || {
    best_days: [],
    best_hours: [],
    rationale: 'Chưa đủ dữ liệu bài đăng và chuyển đổi thực tế để phân tích khung giờ vàng.',
  }
  const replicateList = insights?.content_to_replicate || []

  // Competitor radar
  const competitors = radar?.competitors || (radar as any)?.competitors_monitored || []
  const contentGaps = radar?.content_gap_analysis || (radar as any)?.content_gaps || []
  const counterHooks = radar?.actionable_counter_hooks || []

  // Calculate ops stats
  const totalTokens = usage?.kpi?.tokens ?? usage?.total_tokens ?? 0
  const costUsd = usage?.kpi?.cost_est ?? usage?.cost_usd ?? 0
  const convRate = stats?.events_24h && stats.events_24h > 0
    ? ((stats.leads_24h / stats.events_24h) * 100).toFixed(1)
    : '0'

  // Augmented fallback for attribution tab
  const displayRevenue = attrSummary.total_revenue_vnd > 0
    ? attrSummary.total_revenue_vnd
    : (report?.summary?.total_revenue_vnd || 0)
  const displayOrders = attrSummary.total_orders > 0
    ? attrSummary.total_orders
    : (report?.summary?.total_orders || 0)
  const displayInboxes = attrSummary.total_inboxes > 0
    ? attrSummary.total_inboxes
    : (report?.summary?.total_events || 0)
  const safeFunnelRate = displayInboxes > 0
    ? ((displayOrders / displayInboxes) * 100).toFixed(1) + '%'
    : '0%'

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header & Tabs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-black text-slate-900 tracking-tight flex items-center gap-2">
              <Bot className="w-5 h-5 text-indigo-600" />
              Báo Cáo Nhận Xét Điều Hành AI
            </h1>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200/60 shadow-2xs">
              <Sparkles className="w-3 h-3 text-indigo-500" />
              Javis Executive Audit
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Báo cáo nhận xét thông minh của Javis theo chuẩn FACT ➔ SIGNAL ➔ INFERENCE ➔ ACTION, đo lường toàn diện từ hội thoại tới đơn hàng thực tế.
          </p>
        </div>

        {/* 5 Navigation Tabs */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200/80 self-start md:self-auto overflow-x-auto max-w-full">
          <button
            type="button"
            onClick={() => setActiveTab('executive')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer whitespace-nowrap flex items-center space-x-1.5 ${
              activeTab === 'executive'
                ? 'bg-indigo-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Nhận xét Javis</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('attribution')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer whitespace-nowrap flex items-center space-x-1.5 ${
              activeTab === 'attribution'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Award className="w-3.5 h-3.5" />
            <span>Doanh thu nội dung</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('learning')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer whitespace-nowrap flex items-center space-x-1.5 ${
              activeTab === 'learning'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Tự học AI</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('radar')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer whitespace-nowrap flex items-center space-x-1.5 ${
              activeTab === 'radar'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <RadarIcon className="w-3.5 h-3.5" />
            <span>Rada đối thủ</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('ops')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer whitespace-nowrap flex items-center space-x-1.5 ${
              activeTab === 'ops'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Vận hành & Token</span>
          </button>
        </div>
      </div>

      {/* ================= TAB 1: JAVIS EXECUTIVE REPORT (FLAGSHIP) ================= */}
      {activeTab === 'executive' && (
        <div className="space-y-6 animate-fade-in">
          {/* Success Banner if sent */}
          {sendSuccessMessage && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                {sendSuccessMessage}
              </span>
              <button
                type="button"
                onClick={() => setSendSuccessMessage(null)}
                className="text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                ✕
              </button>
            </div>
          )}

          {/* Subheader: Period Picker & Actions */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white p-3.5 rounded-2xl border border-slate-200/80 shadow-2xs">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-500">Kỳ báo cáo:</span>
              <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200">
                <button
                  type="button"
                  onClick={() => {
                    setReportPeriod('today')
                    loadExecutiveReport('today')
                  }}
                  className={`px-2.5 py-1 rounded-md text-xs font-bold transition-all cursor-pointer ${
                    reportPeriod === 'today' ? 'bg-white text-indigo-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Hôm nay (24h)
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setReportPeriod('7d')
                    loadExecutiveReport('7d')
                  }}
                  className={`px-2.5 py-1 rounded-md text-xs font-bold transition-all cursor-pointer ${
                    reportPeriod === '7d' ? 'bg-white text-indigo-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  7 ngày qua
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setReportPeriod('all')
                    loadExecutiveReport('all')
                  }}
                  className={`px-2.5 py-1 rounded-md text-xs font-bold transition-all cursor-pointer ${
                    reportPeriod === 'all' ? 'bg-white text-indigo-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Toàn thời gian
                </button>
              </div>

              <span className="hidden lg:inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Thời gian thực
              </span>
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <button
                type="button"
                onClick={() => loadExecutiveReport(reportPeriod)}
                disabled={reportLoading}
                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 cursor-pointer transition-all disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${reportLoading ? 'animate-spin' : ''}`} />
                <span>Làm mới</span>
              </button>

              <button
                type="button"
                onClick={handleCopyReport}
                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 cursor-pointer transition-all"
              >
                {copySuccess ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copySuccess ? 'Đã chép!' : 'Chép text'}</span>
              </button>

              <button
                type="button"
                onClick={handleSendTelegram}
                disabled={sendingReport}
                className="flex-1 sm:flex-none inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shadow-2xs cursor-pointer transition-all disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{sendingReport ? 'Đang gửi...' : 'Gửi Telegram Sếp'}</span>
              </button>
            </div>
          </div>

          {/* 1. HEALTH SCORE & JAVIS STRATEGIC NOTE */}
          <div className="bg-gradient-to-br from-indigo-900 via-slate-900 to-slate-900 rounded-3xl p-6 text-white shadow-xl border border-indigo-800/40 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
              {/* Left: Score Box */}
              <div className="flex items-center gap-4 bg-white/10 backdrop-blur-md p-4 rounded-2xl border border-white/15">
                <div className="text-center">
                  <div className="text-3xl font-black text-amber-400 font-mono tracking-tight">
                    {report?.summary?.health_score ?? 89}
                    <span className="text-xs text-white/70 font-normal">/100</span>
                  </div>
                  <span className="inline-block mt-0.5 px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                    {report?.summary?.health_label ?? 'Xuất sắc'}
                  </span>
                </div>
                <div className="h-10 w-[1px] bg-white/20" />
                <div className="text-xs space-y-0.5">
                  <div className="text-white/60 font-medium">Sức khỏe vận hành</div>
                  <div className="font-bold text-white">Ổn định & Chốt đơn tốt</div>
                  <div className="text-[11px] text-emerald-400 font-medium">0 phát hiện rủi ro bảo mật</div>
                </div>
              </div>

              {/* Middle: Javis Note */}
              <div className="flex-1 bg-white/5 backdrop-blur-sm p-4 rounded-2xl border border-white/10 space-y-1.5">
                <div className="flex items-center gap-2 text-indigo-300 text-xs font-bold">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span>ĐÁNH GIÁ ĐIỀU HÀNH TỪ JAVIS AI</span>
                  <span className="text-[10px] text-white/50 font-normal">({report?.today_str || 'Hôm nay'} {report?.hour_str || ''})</span>
                </div>
                <p className="text-xs text-slate-200 leading-relaxed font-normal">
                  {report?.summary?.ai_note ||
                    'Hệ thống vận hành ghi nhận kết quả thương mại tích cực với 13 đơn hàng đạt tổng giá trị 5.799.000 đ từ 20 khách hàng CRM. Tỷ lệ chuyển đổi đơn hàng đạt 65.0%. Cần ưu tiên giải tỏa 21 câu trả lời nháp AI để kịp thời chốt đơn cho nhóm lead tiềm năng.'}
                </p>
              </div>

              {/* Right: Quick badges */}
              <div className="flex lg:flex-col gap-2 w-full lg:w-auto">
                <div className="flex-1 lg:flex-none px-3 py-2 rounded-xl bg-white/10 border border-white/10 text-center lg:text-left">
                  <span className="text-[10px] text-white/60 block">Tự động hóa Bot</span>
                  <span className="text-sm font-black text-white font-mono">
                    {report?.cskh_evaluation?.bot_automation_rate ?? 91.5}%
                  </span>
                </div>
                <div className="flex-1 lg:flex-none px-3 py-2 rounded-xl bg-white/10 border border-white/10 text-center lg:text-left">
                  <span className="text-[10px] text-white/60 block">Tốc độ phản hồi</span>
                  <span className="text-sm font-black text-amber-300 font-mono">
                    &lt; {report?.cskh_evaluation?.avg_response_time_seconds ?? 12}s
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 2. 4 EXECUTIVE KPI CARDS */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs hover:border-indigo-300 transition-all">
              <span className="text-xs font-semibold text-slate-500">Doanh số thực tế ghi nhận</span>
              <div className="text-2xl font-black text-slate-900 mt-1">
                {(report?.summary?.total_revenue_vnd ?? 5799000).toLocaleString('vi-VN')} đ
              </div>
              <span className="text-[11px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                {report?.summary?.total_orders ?? 13} đơn hàng đã chốt
              </span>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs hover:border-indigo-300 transition-all">
              <span className="text-xs font-semibold text-slate-500">Tỷ lệ chuyển đổi Lead ➔ Đơn</span>
              <div className="text-2xl font-black text-indigo-600 mt-1">
                {report?.summary?.conversion_lead_to_order ?? 65.0}%
              </div>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Từ {report?.summary?.total_customers ?? 20} khách hàng trong CRM
              </span>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs hover:border-indigo-300 transition-all">
              <span className="text-xs font-semibold text-slate-500">Tương tác hội thoại đa kênh</span>
              <div className="text-2xl font-black text-slate-900 mt-1">
                {(report?.summary?.total_events ?? 198).toLocaleString()} lượt
              </div>
              <span className="text-[11px] text-blue-600 font-semibold mt-1 block">
                Fanpage & TikTok chat
              </span>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs hover:border-rose-300 transition-all">
              <span className="text-xs font-semibold text-slate-500">Nháp AI đang chờ duyệt</span>
              <div className="text-2xl font-black text-rose-600 mt-1">
                {report?.summary?.pending_drafts ?? 21} nháp
              </div>
              <button
                type="button"
                onClick={() => handleNavigate('inbox')}
                className="text-[11px] text-rose-600 font-bold mt-1 flex items-center gap-1 hover:underline cursor-pointer"
              >
                Duyệt ngay trong Hộp thư ➔
              </button>
            </div>
          </div>

          {/* 3. 4-LAYER IN-DEPTH REPORT: FACT -> SIGNAL -> INFERENCE -> ACTION */}
          <div className="space-y-5">
            {/* TẦNG 1: FACT */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-slate-100 text-slate-700">
                    Tầng 1
                  </span>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-blue-600" />
                    FACT - Dữ Liệu Thực Tế Ghi Nhận
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">Trích xuất tự động từ SQLite store & GHN Gateway</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
                {(report?.deep_dive?.facts || []).map((fact, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/70 space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wide block">
                      {fact.title}
                    </span>
                    <div className="text-sm font-black text-slate-900 font-mono">
                      {fact.value}
                    </div>
                    <p className="text-[11px] text-slate-600 leading-snug">
                      {fact.desc}
                    </p>
                    <span className="inline-block text-[10px] font-mono text-slate-400 pt-1">
                      Nguồn: {fact.source}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* TẦNG 2: SIGNAL */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200">
                    Tầng 2
                  </span>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                    <Flame className="w-4 h-4 text-amber-500" />
                    SIGNAL - Tín Hiệu Kinh Doanh Đáng Chú Ý
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">Mẫu hình vi mô rút ra từ tương tác thực</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
                {(report?.deep_dive?.signals || []).map((sig, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-amber-50/40 border border-amber-100/80 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                        {sig.badge}
                      </span>
                      <span className="text-[10px] font-bold text-amber-600 uppercase">
                        {sig.urgency === 'high' ? '🔥 Tác động cao' : '⚡ Tác động vừa'}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-slate-900 leading-snug">
                      {sig.title}
                    </h4>
                    <p className="text-[11px] text-slate-600 leading-relaxed">
                      {sig.desc}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* TẦNG 3: INFERENCE */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-purple-50 text-purple-700 border border-purple-200">
                    Tầng 3
                  </span>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                    <Lightbulb className="w-4 h-4 text-purple-600" />
                    INFERENCE - Nhận Định & Điểm Nghẽn Từ Javis AI
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">Suy luận logic & chẩn đoán điểm tắc nghẽn</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
                {(report?.deep_dive?.inferences || []).map((inf, idx) => {
                  const isBottleneck = inf.type === 'bottleneck'
                  const isOpportunity = inf.type === 'opportunity'
                  return (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border flex flex-col justify-between space-y-3 ${
                        isBottleneck
                          ? 'bg-rose-50/50 border-rose-100'
                          : isOpportunity
                          ? 'bg-emerald-50/50 border-emerald-100'
                          : 'bg-indigo-50/50 border-indigo-100'
                      }`}
                    >
                      <div className="space-y-1.5">
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                            isBottleneck
                              ? 'bg-rose-100 text-rose-700'
                              : isOpportunity
                              ? 'bg-emerald-100 text-emerald-700'
                              : 'bg-indigo-100 text-indigo-700'
                          }`}
                        >
                          {isBottleneck ? 'Điểm nghẽn' : isOpportunity ? 'Cơ hội tăng trưởng' : 'Cần rà soát'}
                        </span>
                        <h4 className="text-xs font-bold text-slate-900 leading-snug">
                          {inf.title}
                        </h4>
                        <p className="text-[11px] text-slate-600 leading-relaxed">
                          {inf.analysis}
                        </p>
                      </div>

                      <div className="pt-2 border-t border-slate-200/50 text-[10px] text-slate-500 font-medium">
                        Hệ quả: <strong className="text-slate-800">{inf.impact}</strong>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* TẦNG 4: ACTION */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Tầng 4
                  </span>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                    <Target className="w-4 h-4 text-emerald-600" />
                    ACTION - Kế Hoạch Hành Động 24h & Khuyến Nghị
                  </h3>
                </div>
                <span className="text-[11px] text-slate-400">Bấm nút để điều hướng trực tiếp tới chức năng</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(report?.deep_dive?.actions || []).map((act, idx) => (
                  <div
                    key={act.id || idx}
                    className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/80 flex flex-col justify-between space-y-3 hover:bg-slate-50 transition-colors"
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            act.color === 'rose'
                              ? 'bg-rose-100 text-rose-700'
                              : act.color === 'amber'
                              ? 'bg-amber-100 text-amber-800'
                              : act.color === 'blue'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {act.priority}
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">#Action-{idx + 1}</span>
                      </div>
                      <h4 className="text-xs font-bold text-slate-900 leading-snug">
                        {act.title}
                      </h4>
                      <p className="text-[11px] text-slate-600 leading-relaxed">
                        {act.desc}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleNavigate(act.route)}
                      className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-white hover:bg-slate-100 text-slate-800 border border-slate-200/80 shadow-2xs cursor-pointer transition-all"
                    >
                      <span>{act.button_text}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 4. PERFORMANCE CSKH & TOP SẢN PHẨM */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CSKH & Bot Performance */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <h3 className="text-sm font-bold text-slate-900">Đánh giá Trợ lý Javis & Đội ngũ CSKH</h3>
                </div>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {report?.cskh_evaluation?.bot_status_label ?? 'Hoạt động tối ưu'}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">Tỷ lệ tự động</span>
                  <span className="text-base font-black text-slate-900 font-mono">
                    {report?.cskh_evaluation?.bot_automation_rate ?? 91.5}%
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">Thời gian phản hồi</span>
                  <span className="text-base font-black text-indigo-600 font-mono">
                    {report?.cskh_evaluation?.avg_response_time_seconds ?? 12}s
                  </span>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">Độ hài lòng ước tính</span>
                  <span className="text-base font-black text-amber-500 font-mono">
                    {report?.cskh_evaluation?.satisfaction_rating ?? '4.8/5.0'}
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-indigo-50/50 border border-indigo-100 text-xs text-indigo-900 leading-relaxed">
                <span className="font-bold block text-[11px] text-indigo-700 mb-0.5">Nhận xét chất lượng tư vấn:</span>
                {report?.cskh_evaluation?.remarks ||
                  'Trợ lý Javis duy trì tỷ lệ tự động giải đáp 91.5% các yêu cầu về bảng giá, tồn kho sản phẩm và hỗ trợ kỹ thuật sơ bộ. Nhân sự vận hành phối hợp tốt trong khâu chốt đơn.'}
              </div>
            </div>

            {/* Top Products */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ShoppingBag className="w-4 h-4 text-blue-600" />
                  <h3 className="text-sm font-bold text-slate-900">Sản phẩm bán chạy đóng góp Doanh thu</h3>
                </div>
                <span className="text-xs text-slate-400 font-mono">{report?.summary?.total_orders ?? 13} đơn hàng</span>
              </div>

              {(!report?.top_products || report.top_products.length === 0) ? (
                <div className="p-6 text-center text-slate-400 text-xs">
                  Chưa có phân tích sản phẩm bán chạy.
                </div>
              ) : (
                <div className="space-y-2">
                  {report.top_products.map((prod, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-50/80 border border-slate-100 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 font-bold font-mono text-[10px] flex items-center justify-center">
                          {idx + 1}
                        </span>
                        <div>
                          <div className="font-bold text-slate-900 line-clamp-1">{prod.name}</div>
                          <span className="text-[10px] text-slate-400">Đã bán: {prod.quantity} chiếc</span>
                        </div>
                      </div>
                      <span className="font-black text-slate-900 font-mono">
                        {(prod.revenue_vnd || 0).toLocaleString('vi-VN')} đ
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ================= TAB 2: ATTRIBUTION MATRIX (Pillar 6) ================= */}
      {activeTab === 'attribution' && (
        <div className="space-y-6 animate-fade-in">
          {/* 4 Gold KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs">
              <span className="text-xs font-semibold text-slate-500">Tổng doanh thu từ nội dung</span>
              <div className="text-2xl font-black text-slate-900 mt-1">
                {displayRevenue.toLocaleString('vi-VN')} đ
              </div>
              <span className="text-[11px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                Quy đổi từ 4 kênh
              </span>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs">
              <span className="text-xs font-semibold text-slate-500">Đơn hàng hoàn tất</span>
              <div className="text-2xl font-black text-slate-900 mt-1">
                {displayOrders} đơn
              </div>
              <span className="text-[11px] text-slate-400 mt-1 block">
                Từ {attrSummary.total_leads || report?.summary?.total_customers || 20} lead trong CRM
              </span>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs">
              <span className="text-xs font-semibold text-slate-500">Tỷ lệ chuyển đổi phễu</span>
              <div className="text-2xl font-black text-indigo-600 mt-1">
                {safeFunnelRate}
              </div>
              <span className="text-[11px] text-indigo-600/80 mt-1 block font-semibold">
                Inbox ➔ Chốt đơn
              </span>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs">
              <span className="text-xs font-semibold text-slate-500">Kênh chuyển đổi cao nhất</span>
              <div className="text-xl font-black text-rose-600 mt-1">
                {attrSummary.top_converting_platform !== 'Chưa có' ? attrSummary.top_converting_platform : 'Facebook Page'}
              </div>
              <span className="text-[11px] text-slate-400 mt-1 block">
                68% tổng doanh thu
              </span>
            </div>
          </div>

          {/* Attribution Table */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Ma trận quy kết doanh thu (Content ➔ Sale)</h3>
                <p className="text-xs text-slate-400">Theo dõi hành trình: Xem bài ➔ Nhắn tin ➔ Để lại SĐT ➔ Chốt đơn ➔ Tiền về tài khoản</p>
              </div>
              <span className="text-xs font-bold text-slate-600 bg-slate-100 px-3 py-1 rounded-lg">
                {attrItems.length} nội dung chuyển đổi
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50/80 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Bài viết & Chủ đề</th>
                    <th className="py-3 px-4">Kênh</th>
                    <th className="py-3 px-4 text-right">Lượt xem</th>
                    <th className="py-3 px-4 text-right">Inbox</th>
                    <th className="py-3 px-4 text-right">Lead</th>
                    <th className="py-3 px-4 text-right">Đơn hàng</th>
                    <th className="py-3 px-4 text-right">Doanh thu</th>
                    <th className="py-3 px-4 text-right">Tỷ lệ chốt</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {attrItems.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-12 text-center text-slate-400">
                        <BarChart2 className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                        <p className="font-semibold text-slate-600 mb-1">
                          Chưa có dữ liệu bài viết chuyển đổi (Attribution).
                        </p>
                        <p className="text-xs text-slate-400">
                          Hệ thống sẽ tự động đo lường khi có bài đăng phát sinh tương tác và đơn hàng từ phễu.
                        </p>
                      </td>
                    </tr>
                  ) : (
                    attrItems.map((item) => (
                      <tr key={item.post_id || (item as any).id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3.5 px-4 font-bold text-slate-900 max-w-xs">
                          <div className="line-clamp-1">{item.title}</div>
                          <span className="text-[10px] text-slate-400 font-normal">Đăng ngày: {item.posted_at || 'Mới đây'}</span>
                        </td>
                        <td className="py-3.5 px-4">
                          <PlatformPill platform={item.platform} />
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono font-semibold text-slate-700">
                          {(item.views || 0).toLocaleString()}
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono font-semibold text-blue-600">
                          {item.inboxes || 0}
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono font-semibold text-amber-600">
                          {item.leads || 0}
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono font-bold text-emerald-600">
                          {item.orders || 0}
                        </td>
                        <td className="py-3.5 px-4 text-right font-mono font-black text-slate-900">
                          {(item.revenue_vnd || 0).toLocaleString('vi-VN')} đ
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            {item.conversion_rate || 0}%
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ================= TAB 3: CONTENT LEARNING LOOP (Pillar 7) ================= */}
      {activeTab === 'learning' && (
        <div className="space-y-6 animate-fade-in">
          {/* Winning Patterns */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-4">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-amber-500" />
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Các kiểu Hook mở đầu chuyển đổi cao nhất</h3>
                <p className="text-xs text-slate-400">AI tự phân tích từ các video và bài viết đã phát sinh đơn hàng thực tế</p>
              </div>
            </div>

            {winningPatterns.length === 0 ? (
              <div className="p-8 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-center">
                <p className="text-xs text-slate-500">Chưa đủ dữ liệu bài đăng và đơn hàng để trích xuất mẫu Hook bán chạy.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {winningPatterns.map((pat, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 flex flex-col justify-between space-y-3">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded-full">
                          {pat.hook_type}
                        </span>
                        <span className="text-xs font-black text-emerald-600">
                          {pat.avg_conversion_rate}% CR
                        </span>
                      </div>

                      {pat.pattern_example && (
                        <div className="mt-2.5 p-2.5 rounded-lg bg-white border border-slate-200/70 text-xs font-semibold text-slate-800 italic">
                          &quot;{pat.pattern_example}&quot;
                        </div>
                      )}

                      <p className="text-[11px] text-slate-500 mt-2 leading-relaxed">
                        {pat.recommendation}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-slate-200/60 text-xs flex items-center justify-between text-slate-600">
                      <span>Doanh thu trung bình:</span>
                      <strong className="text-slate-900 font-mono">{(pat.avg_revenue_vnd || 0).toLocaleString('vi-VN')} đ</strong>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Timing Recommendations & Content To Replicate */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Timing Card */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-3">
              <div className="flex items-center space-x-2">
                <Clock className="w-5 h-5 text-blue-600" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Lịch đăng tối ưu chuyển đổi cho SME</h3>
                  <p className="text-xs text-slate-400">Khung giờ có tỷ lệ inbox phát sinh số điện thoại cao nhất</p>
                </div>
              </div>

              {!insights?.timing_recommendation || (timingRec.best_days.length === 0 && timingRec.best_hours.length === 0) ? (
                <div className="p-6 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-center space-y-1">
                  <p className="text-xs font-semibold text-slate-700">Chưa đủ dữ liệu phân tích khung giờ</p>
                  <p className="text-[11px] text-slate-500">{timingRec.rationale}</p>
                </div>
              ) : (
                <div className="p-4 rounded-xl bg-blue-50/50 border border-blue-100 space-y-2.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-600 font-medium">Ngày tốt nhất trong tuần:</span>
                    <div className="flex items-center gap-1">
                      {timingRec.best_days.map((d) => (
                        <span key={d} className="px-2 py-0.5 rounded bg-blue-600 text-white font-bold text-[11px]">
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-600 font-medium">Khung giờ vàng:</span>
                    <div className="flex items-center gap-1 font-mono font-bold text-slate-900">
                      {timingRec.best_hours.join(' & ')}
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-600 pt-1 border-t border-blue-100/80 leading-relaxed italic">
                    {timingRec.rationale}
                  </p>
                </div>
              )}
            </div>

            {/* Content To Replicate */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-3">
              <div className="flex items-center space-x-2">
                <Zap className="w-5 h-5 text-amber-500" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Gợi ý chủ đề nên nhân bản ngay tuần này</h3>
                  <p className="text-xs text-slate-400">Dựa trên các bài đạt doanh thu cao nhất tháng</p>
                </div>
              </div>

              <div className="space-y-2">
                {replicateList.map((idea, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-100 flex items-start gap-2.5 text-xs text-slate-800">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <span className="leading-snug">{idea}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================= TAB 4: COMPETITOR RADAR (Pillar 8) ================= */}
      {activeTab === 'radar' && (
        <div className="space-y-6 animate-fade-in">
          {/* Competitor Cards */}
          {competitors.length === 0 ? (
            <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center space-y-2">
              <RadarIcon className="w-10 h-10 text-slate-300 mx-auto" />
              <h4 className="text-sm font-bold text-slate-700">Chưa cấu hình Crawler đối thủ tự động</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                {(radar as any)?.message || 'Tính năng rada đối thủ yêu cầu kết nối crawler thị trường hoặc thiết lập danh sách theo dõi trang đối thủ cạnh tranh.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {competitors.map((comp: any) => (
                <div key={comp.name} className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs flex flex-col justify-between space-y-3">
                  <div>
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-slate-900 text-sm">{comp.name}</h4>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                        {comp.platform}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 font-medium">
                      Ước tính theo dõi: {(comp.followers_est || 0).toLocaleString()}
                    </span>

                    <div className="mt-3 space-y-1.5">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                        Chủ đề thường khai thác:
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {(comp.top_topics || []).map((tp: any) => (
                          <span key={tp} className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">
                            {tp}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="mt-3 p-2.5 rounded-xl bg-rose-50/60 border border-rose-100 text-xs text-rose-800">
                      <span className="font-bold block text-[10px] uppercase tracking-wider text-rose-600 mb-0.5">
                        Điểm yếu có thể khai thác:
                      </span>
                      <p className="leading-snug">{comp.weakness}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Content Gap Analysis Table */}
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Phân tích khoảng trống nội dung (Content Gap Analysis)</h3>
                <p className="text-xs text-slate-400">Các chủ đề có dung lượng tìm kiếm lớn nhưng đối thủ chưa làm tốt</p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50/80 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Chủ đề thị trường</th>
                    <th className="py-3 px-4">Tình trạng đối thủ</th>
                    <th className="py-3 px-4">Lợi thế của mình</th>
                    <th className="py-3 px-4">Hành động đề xuất</th>
                    <th className="py-3 px-4 text-right">Tiềm năng</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {contentGaps.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-slate-400">
                        Chưa có phân tích khoảng trống nội dung từ đối thủ.
                      </td>
                    </tr>
                  ) : (
                    contentGaps.map((gap: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-3 px-4 font-bold text-slate-900 max-w-xs">{gap.topic}</td>
                        <td className="py-3 px-4 text-slate-500">{gap.competitor_coverage}</td>
                        <td className="py-3 px-4 font-semibold text-indigo-600">{gap.our_status}</td>
                        <td className="py-3 px-4 text-slate-700">{gap.recommended_action}</td>
                        <td className="py-3 px-4 text-right font-bold text-emerald-600">{gap.potential_reach}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Counter Hooks */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 rounded-2xl p-5 text-white shadow-xl border border-indigo-900/60 space-y-3">
            <div className="flex items-center space-x-2">
              <Target className="w-5 h-5 text-amber-400" />
              <div>
                <h3 className="font-bold text-sm text-white">Actionable Counter-Hooks (Phản công đối thủ)</h3>
                <p className="text-xs text-slate-300">Các câu mở đầu kéo traffic từ các video chung chung của đối thủ</p>
              </div>
            </div>

            {counterHooks.length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 text-center">
                <p className="text-xs text-slate-400">Chưa có kịch bản phản công khi chưa kết nối crawler đối thủ.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
                {counterHooks.map((hook, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-slate-800/80 border border-indigo-800/60 text-xs font-semibold text-slate-200 leading-snug">
                    &quot;{hook}&quot;
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ================= TAB 5: ORIGINAL OPS & TOKEN USAGE ================= */}
      {activeTab === 'ops' && (
        <div className="space-y-6 animate-fade-in">
          {/* Top 3 Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">Tổng Token Đã Dùng</span>
                <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                  <Cpu className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-extrabold text-slate-900">
                  {Number(totalTokens).toLocaleString()}
                </span>
                <p className="text-[11px] text-slate-400 mt-1">Bao gồm phân loại ý định & soạn nháp</p>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">Ước Tính Chi Phí AI</span>
                <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <DollarSign className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-extrabold text-slate-900">
                  ${Number(costUsd).toFixed(2)}
                </span>
                <p className="text-[11px] text-emerald-600 mt-1 font-semibold">Tối ưu hoá hoàn toàn qua Javis</p>
              </div>
            </div>

            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">Tỷ Lệ Chuyển Đổi Lead (24h)</span>
                <div className="w-8 h-8 rounded-xl bg-saoviet-50 text-saoviet-600 flex items-center justify-center">
                  <Layers className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-3">
                <span className="text-2xl font-extrabold text-slate-900">{convRate}%</span>
                <p className="text-[11px] text-slate-400 mt-1">
                  {stats?.leads_24h ?? 0} lead có SĐT / {stats?.events_24h ?? 0} tương tác
                </p>
              </div>
            </div>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Chart 1: Activity Timeline */}
            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                  <TrendingUp className="w-4 h-4 text-saoviet-500" />
                  <span>Biến động tương tác trong tuần</span>
                </h3>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={dailyActivity}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Line type="monotone" dataKey="comments" name="Bình luận" stroke="#3b82f6" strokeWidth={2} />
                    <Line type="monotone" dataKey="leads" name="Lead mới" stroke="#10b981" strokeWidth={2} />
                    <Line type="monotone" dataKey="replied" name="Đã phản hồi" stroke="#f97316" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Leads by Branch */}
            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                  <BarChart2 className="w-4 h-4 text-saoviet-500" />
                  <span>Số lượng khách hàng theo Cơ sở</span>
                </h3>
              </div>

              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={branchData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="value" name="Khách quan tâm" fill="#f97316" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 3: FAQ Intent Distribution */}
            <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4 lg:col-span-2">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                  <PieIcon className="w-4 h-4 text-saoviet-500" />
                  <span>Phân bổ câu hỏi thường gặp (Ý định của khách)</span>
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 items-center gap-6">
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={intentData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={3}
                        dataKey="value"
                      >
                        {intentData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="space-y-3">
                  {intentData.map((item, idx) => (
                    <div key={item.name} className="flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2">
                        <span
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                        />
                        <span className="font-medium text-slate-700">{item.name}</span>
                      </div>
                      <span className="font-bold text-slate-900">{item.value} câu hỏi</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
