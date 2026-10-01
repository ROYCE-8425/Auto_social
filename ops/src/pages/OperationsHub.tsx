import React, { useState, useEffect } from 'react'
import {
  Users,
  FileText,
  BookOpen,
  Mail,
  BarChart3,
  Kanban,
  DollarSign,
  Calendar,
  Layers,
  ArrowRight,
  Sparkles,
  Bot,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Clock,
  ShieldCheck,
  ChevronRight,
  X,
  Award,
  Eye,
  Check,
  Briefcase,
  FolderGit2,
  Sliders,
  Play,
  RotateCcw,
  Target,
  Rocket,
  TrendingUp,
  CheckSquare,
  MessageSquare,
  Zap,
  Loader2,
  Copy,
  ShoppingBag,
  Package,
  Settings,
  Database,
  ExternalLink,
} from 'lucide-react'
import { useAuth } from '../lib/auth'
import {
  api,
  CampaignAutopilotPayload,
  CampaignAutopilotResponse,
  CampaignRecord,
  HubSummaryModuleItem,
  OpsHubSummaryResponse,
} from '../lib/api'
import { OperationsInsightDrawer } from '../components/OperationsInsightDrawer'

interface OperationsHubProps {
  onNavigate?: (tab: string) => void
}

const getModuleIcon = (iconName: string) => {
  switch (iconName) {
    case 'Users':
      return Users
    case 'ShoppingBag':
      return ShoppingBag
    case 'MessageSquare':
      return MessageSquare
    case 'CheckSquare':
      return CheckSquare
    case 'TrendingUp':
      return TrendingUp
    case 'DollarSign':
      return DollarSign
    case 'Package':
      return Package
    case 'BookOpen':
      return BookOpen
    case 'Calendar':
      return Calendar
    case 'FileText':
      return FileText
    case 'Briefcase':
      return Briefcase
    default:
      return Layers
  }
}

export const OperationsHub: React.FC<OperationsHubProps> = ({ onNavigate }) => {
  // ============================================================
  // 1. Operations Hub Real Aggregator State
  // ============================================================
  const [hubSummary, setHubSummary] = useState<OpsHubSummaryResponse | null>(null)
  const [hubLoading, setHubLoading] = useState(true)
  const [activeInsightModule, setActiveInsightModule] = useState<HubSummaryModuleItem | null>(null)
  const [categoryFilter, setCategoryFilter] = useState<string>('all')

  const fetchHubSummary = async () => {
    setHubLoading(true)
    try {
      const res = await api.getOpsHubSummary()
      if (res && res.ok) {
        setHubSummary(res)
      }
    } catch (err) {
      console.error('Lỗi tải dữ liệu tổng hợp Hub:', err)
    } finally {
      setHubLoading(false)
    }
  }

  useEffect(() => {
    fetchHubSummary()
  }, [])

  const handleActionNavigate = (path: string) => {
    if (!onNavigate) return
    const cleanPath = path.startsWith('/ops/') ? path.replace('/ops/', '') : path
    const tabName = cleanPath.split('?')[0]
    onNavigate(tabName)
  }

  // ============================================================
  // 2. Trụ cột 09: AI Campaign Autopilot
  // ============================================================
  const [realCampaigns, setRealCampaigns] = useState<CampaignRecord[]>([])
  const [campaignsLoading, setCampaignsLoading] = useState(false)
  const [activeCampaignData, setActiveCampaignData] = useState<{
    campaign_id?: string
    task_ids?: string[]
    status?: string
    items?: any[]
  } | null>(null)
  const [autopilotError, setAutopilotError] = useState<string | null>(null)

  const [isAutopilotModalOpen, setIsAutopilotModalOpen] = useState(false)
  const [autopilotLoading, setAutopilotLoading] = useState(false)
  const [autopilotCopied, setAutopilotCopied] = useState(false)
  const [campaignTab, setCampaignTab] = useState<'milestones' | 'calendar' | 'objections' | 'checklist'>('milestones')
  const [campaignForm, setCampaignForm] = useState<CampaignAutopilotPayload>({
    goal: 'Tuyển 50 học viên khóa Tin học MOS thực chiến',
    budget_vnd: 10000000,
    target_revenue_vnd: 50000000,
    duration_weeks: 4,
    platforms: ['facebook', 'tiktok'],
  })
  const [campaignPlan, setCampaignPlan] = useState<CampaignAutopilotResponse['campaign_plan'] | null>(null)

  const fetchRealCampaigns = async () => {
    setCampaignsLoading(true)
    try {
      const res = await api.getCampaigns()
      if (res && res.ok && Array.isArray(res.campaigns)) {
        setRealCampaigns(res.campaigns)
        if (res.campaigns.length > 0 && !activeCampaignData) {
          const first = res.campaigns[0]
          setActiveCampaignData({
            campaign_id: first.id,
            task_ids: first.task_ids || [],
            status: first.status || 'active',
            items: first.items || [],
          })
          if (first.plan && first.plan.milestones) {
            setCampaignPlan(first.plan)
          }
        }
      }
    } catch (err) {
      console.error('Lỗi tải danh sách chiến dịch thật:', err)
    } finally {
      setCampaignsLoading(false)
    }
  }

  useEffect(() => {
    fetchRealCampaigns()
  }, [])

  const handleSelectCampaign = async (camp: CampaignRecord) => {
    setActiveCampaignData({
      campaign_id: camp.id,
      task_ids: camp.task_ids || [],
      status: camp.status || 'active',
      items: camp.items || [],
    })
    if (camp.plan && camp.plan.milestones) {
      setCampaignPlan(camp.plan)
    } else {
      try {
        const detail = await api.getCampaign(camp.id)
        if (detail && detail.ok && detail.campaign) {
          setCampaignPlan(detail.campaign.plan || null)
          setActiveCampaignData({
            campaign_id: detail.campaign.id,
            task_ids: detail.task_ids || [],
            status: detail.campaign.status || 'active',
            items: detail.items || [],
          })
        }
      } catch (err) {
        console.error('Lỗi tải chi tiết chiến dịch:', err)
      }
    }
    setIsAutopilotModalOpen(true)
  }

  const handleOpenCreateCampaign = () => {
    setCampaignForm({
      goal: '',
      budget_vnd: 10000000,
      target_revenue_vnd: 50000000,
      duration_weeks: 4,
      platforms: ['facebook', 'tiktok'],
    })
    setCampaignPlan(null)
    setActiveCampaignData(null)
    setAutopilotError(null)
    setIsAutopilotModalOpen(true)
  }

  const handleGenerateAutopilot = async () => {
    setAutopilotLoading(true)
    setAutopilotError(null)
    try {
      const res = await api.createCampaignAutopilot(campaignForm)
      if (res && res.ok) {
        setCampaignPlan(res.campaign_plan || (res as any))
        setActiveCampaignData({
          campaign_id: res.campaign_id,
          task_ids: res.task_ids || [],
          status: res.status || 'active',
          items: res.items || [],
        })
        await fetchRealCampaigns()
      } else {
        setAutopilotError((res as any)?.error || 'Không thể khởi tạo chiến dịch.')
      }
    } catch (err: any) {
      console.error('Lỗi khởi tạo chiến dịch AI Autopilot:', err)
      setAutopilotError(err?.message || 'Lỗi kết nối máy chủ.')
    } finally {
      setAutopilotLoading(false)
    }
  }

  const handleCopyPlan = () => {
    if (!campaignPlan) return
    const text = [
      `=== KẾ HOẠCH CHIẾN DỊCH AI AUTOPILOT ===`,
      `Mục tiêu: ${campaignPlan.goal}`,
      `Ngân sách: ${Number(campaignPlan.budget_vnd || 0).toLocaleString('vi-VN')} đ`,
      `Doanh số kỳ vọng: ${Number(campaignPlan.target_revenue_vnd || 0).toLocaleString('vi-VN')} đ`,
      `Dự phóng ROI: ${campaignPlan.roi_projected || '5.0x'}`,
      ``,
      `--- CÁC MỐC TUẦN (MILESTONES) ---`,
      ...(campaignPlan.milestones || []).map((m) => `Tuần ${m.week}: ${m.theme} | KPI: ${m.kpi_target} | Hành động: ${m.key_action}`),
      ``,
      `--- LỊCH 12 BÀI ĐA NỀN TẢNG ---`,
      ...(campaignPlan.content_calendar || []).map((c) => `Ngày ${c.day} [${(c.platform || '').toUpperCase()}]: Hook: "${c.hook || ''}" -> CTA: "${c.cta || ''}" (Target: ${c.lead_target || 4} leads)`),
      ``,
      `--- KỊCH BẢN XỬ LÝ TỪ CHỐI ---`,
      ...(campaignPlan.sales_objection_playbook || []).map((s) => `Từ chối: "${s.customer_objection}"\n-> Phản hồi: ${s.ai_counter_argument}\n-> Đề nghị chốt: ${s.closing_offer}`),
      ``,
      `--- CHECKLIST NGHIỆM THU ---`,
      ...(campaignPlan.review_checklist || []).map((item, idx) => `[${idx + 1}] ${item}`),
    ].join('\n')

    navigator.clipboard.writeText(text)
    setAutopilotCopied(true)
    setTimeout(() => setAutopilotCopied(false), 2000)
  }

  // Filter modules
  const allModules = hubSummary?.modules || []
  const filteredModules = allModules.filter((m) => {
    if (categoryFilter === 'all') return true
    if (categoryFilter === 'warning') return m.status === 'warning'
    if (categoryFilter === 'needs_config') return m.status === 'needs_config'
    return m.category === categoryFilter
  })

  const exec = hubSummary?.executive_summary

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* ================= HERO: TRUNG TÂM CHỈ HUY VẬN HÀNH (COMMAND CENTER) ================= */}
      <div className="bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-950 border border-slate-800 rounded-3xl p-6 text-white shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/4 w-72 h-72 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-6">
          {/* Header Title */}
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="space-y-1.5 max-w-2xl">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-300 text-xs font-bold">
                <Bot className="w-3.5 h-3.5 text-indigo-400" />
                <span>Executive Command Center · Bảng điều phối vận hành thật</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
                Trung tâm Chỉ huy &amp; Điều phối Vận hành
              </h1>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Không phải nơi nhập liệu thủ công. Đây là trung tâm phân tích dữ liệu thật từ{' '}
                <strong className="text-white">CRM, Hộp thư, Đơn hàng, Tasks, Sản phẩm</strong> để trả lời 3 câu hỏi vận hành cốt lõi và điều phối hành động tức thì.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={fetchHubSummary}
                disabled={hubLoading}
                className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${hubLoading ? 'animate-spin text-indigo-400' : ''}`} />
                <span>Làm mới số liệu</span>
              </button>
            </div>
          </div>

          {/* 3 Câu hỏi Vận hành Cốt lõi (Answer Panels) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {/* Câu 1: Hôm nay có gì cần xử lý? */}
            <div className="bg-slate-900/80 border border-amber-500/30 rounded-2xl p-4 flex flex-col justify-between space-y-3">
              <div className="space-y-1">
                <div className="text-[11px] font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                  <span className="w-4 h-4 rounded-full bg-amber-500/20 text-amber-300 text-[10px] flex items-center justify-center font-mono">1</span>
                  <span>Hôm nay có gì cần xử lý?</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-amber-300">
                    {exec ? exec.need_action_today : 0}
                  </span>
                  <span className="text-xs text-slate-400">mục khẩn cấp cần hành động</span>
                </div>
              </div>
              <div className="text-[11px] text-slate-300 space-y-0.5 pt-2 border-t border-slate-800">
                <div>• {exec ? exec.orders_draft : 0} đơn hàng nháp chờ xác nhận</div>
                <div>• {exec ? exec.inbox_drafts_total : 0} bản nháp AI cần duyệt trước khi gửi</div>
                <div>• {exec ? exec.tasks_urgent : 0} công việc gắn cờ khẩn cấp</div>
              </div>
            </div>

            {/* Câu 2: Dữ liệu thật đang báo vấn đề gì? */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between space-y-3">
              <div className="space-y-1">
                <div className="text-[11px] font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5">
                  <span className="w-4 h-4 rounded-full bg-indigo-500/20 text-indigo-400 text-[10px] flex items-center justify-center font-mono">2</span>
                  <span>Dữ liệu thật báo vấn đề gì?</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black text-white">
                    {exec ? exec.critical_alerts : 0}
                  </span>
                  <span className="text-xs text-slate-400">điểm nghẽn vận hành phát hiện</span>
                </div>
              </div>
              <div className="text-[11px] text-slate-300 space-y-0.5 pt-2 border-t border-slate-800">
                <div>• Doanh thu ghi nhận: <strong className="text-emerald-400">{exec ? Number(exec.revenue_recorded).toLocaleString('vi-VN') : 0} đ</strong></div>
                <div>• Tổng CRM Lead: <strong className="text-white">{exec ? exec.crm_customers_total : 0} khách</strong> ({exec ? exec.hot_leads_count : 0} hot lead)</div>
                <div>• Sổ đơn: <strong className="text-white">{exec ? exec.orders_total : 0} đơn hàng</strong> đang theo dõi</div>
              </div>
            </div>

            {/* Câu 3: Bấm vào đâu để hành động ngay? */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between space-y-3">
              <div className="space-y-1">
                <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <span className="w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] flex items-center justify-center font-mono">3</span>
                  <span>Bấm vào đâu để hành động ngay?</span>
                </div>
                <div className="text-xs text-slate-400">Chuyển tiếp trực tiếp tới buồng lái chuyên trách:</div>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => handleActionNavigate('/ops/orders')}
                  className="py-1.5 px-2.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/60 border border-indigo-500/40 text-indigo-200 text-xs font-semibold transition-all flex items-center justify-between cursor-pointer"
                >
                  <span>Sổ đơn ({exec ? exec.orders_draft : 0})</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
                <button
                  type="button"
                  onClick={() => handleActionNavigate('/ops/inbox')}
                  className="py-1.5 px-2.5 rounded-lg bg-blue-600/30 hover:bg-blue-600/60 border border-blue-500/40 text-blue-200 text-xs font-semibold transition-all flex items-center justify-between cursor-pointer"
                >
                  <span>Hộp thư ({exec ? exec.inbox_drafts_total : 0})</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
                <button
                  type="button"
                  onClick={() => handleActionNavigate('/ops/customers')}
                  className="py-1.5 px-2.5 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/60 border border-emerald-500/40 text-emerald-200 text-xs font-semibold transition-all flex items-center justify-between cursor-pointer"
                >
                  <span>CRM Lead</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
                <button
                  type="button"
                  onClick={() => handleActionNavigate('/ops/tasks')}
                  className="py-1.5 px-2.5 rounded-lg bg-purple-600/30 hover:bg-purple-600/60 border border-purple-500/40 text-purple-200 text-xs font-semibold transition-all flex items-center justify-between cursor-pointer"
                >
                  <span>Kanban ({exec ? exec.tasks_urgent : 0})</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ================= TRỤ CỘT 09: AI CAMPAIGN AUTOPILOT LAUNCHER ================= */}
      <div className="bg-gradient-to-br from-indigo-950 via-slate-900 to-purple-950 border border-indigo-500/30 rounded-3xl p-6 shadow-xl relative overflow-hidden text-white">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-2.5 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-400/30 text-purple-200 text-xs font-semibold">
              <Rocket className="w-3.5 h-3.5 text-purple-400" />
              <span>Trụ cột 09 · AI Campaign Autopilot</span>
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center space-x-2">
                <span>Điều phối chiến dịch theo mục tiêu doanh số</span>
              </h2>
              <p className="text-xs sm:text-sm text-slate-300 mt-1 leading-relaxed">
                Nhập mục tiêu &amp; ngân sách: AI phân rã lộ trình 4 tuần, thiết kế lịch 12 bài nội dung đa nền tảng, tạo kịch bản xử lý từ chối giá cao cho tư vấn viên và tự động sinh task lên Kanban.
              </p>
            </div>
          </div>

          <div className="shrink-0 flex items-center gap-3">
            <button
              type="button"
              onClick={handleOpenCreateCampaign}
              className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-2xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/25 transition-all cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-purple-200" />
              <span>Khởi tạo chiến dịch mới với AI</span>
            </button>
            {campaignPlan && (
              <button
                type="button"
                onClick={() => setIsAutopilotModalOpen(true)}
                className="flex items-center justify-center space-x-1.5 px-4 py-2.5 rounded-2xl bg-purple-900/60 hover:bg-purple-800/80 border border-purple-500/40 text-purple-200 text-xs font-semibold transition-all cursor-pointer"
              >
                <Eye className="w-3.5 h-3.5 text-purple-300" />
                <span>Xem kế hoạch</span>
              </button>
            )}
          </div>
        </div>

        {/* Real Stored Campaigns List */}
        {realCampaigns.length > 0 && (
          <div className="mt-4 pt-4 border-t border-indigo-500/20">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-300">
                Chiến dịch đã lưu trữ trong CSDL ({realCampaigns.length})
              </span>
              <span className="text-[10px] text-slate-400">Lưu SQLite &amp; Đồng bộ Kanban Tasks</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              {realCampaigns.slice(0, 3).map((camp) => (
                <div
                  key={camp.id}
                  onClick={() => handleSelectCampaign(camp)}
                  className="p-3 rounded-xl border border-slate-700/70 bg-slate-900/60 hover:border-indigo-400/60 transition-all cursor-pointer flex items-center justify-between"
                >
                  <div className="min-w-0 pr-2">
                    <div className="text-xs font-bold text-white truncate">{camp.goal}</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      {Number(camp.budget_vnd || 0).toLocaleString('vi-VN')} đ · {(camp.task_ids || []).length} tasks
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase shrink-0">
                    {camp.status || 'active'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ================= PHẦN PHÂN HỆ VẬN HÀNH THẬT (OPERATIONAL MODULES GRID) ================= */}
      <div className="space-y-4">
        {/* Section Header & Filters */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-1 border-b border-slate-200">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <span>Bảng Phân hệ Vận hành &amp; Điều phối Thực tế</span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                {allModules.length} phân hệ
              </span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Mỗi card chứa KPI thật, cảnh báo nghẽn, đề xuất hành động từ AI và nút chuyển buồng lái tương ứng.
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              type="button"
              onClick={() => setCategoryFilter('all')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                categoryFilter === 'all'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
              }`}
            >
              Tất cả ({allModules.length})
            </button>
            <button
              type="button"
              onClick={() => setCategoryFilter('warning')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1 ${
                categoryFilter === 'warning'
                  ? 'bg-amber-600 text-white shadow-xs'
                  : 'bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200'
              }`}
            >
              <AlertTriangle className="w-3 h-3" />
              <span>Cần xử lý ({allModules.filter((m) => m.status === 'warning').length})</span>
            </button>
            <button
              type="button"
              onClick={() => setCategoryFilter('Kinh doanh & Bán hàng')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                categoryFilter === 'Kinh doanh & Bán hàng'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
              }`}
            >
              Kinh doanh
            </button>
            <button
              type="button"
              onClick={() => setCategoryFilter('Vận hành & Hỗ trợ')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                categoryFilter === 'Vận hành & Hỗ trợ'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
              }`}
            >
              Vận hành
            </button>
            <button
              type="button"
              onClick={() => setCategoryFilter('needs_config')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                categoryFilter === 'needs_config'
                  ? 'bg-slate-800 text-white shadow-xs'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
              }`}
            >
              Needs config
            </button>
          </div>
        </div>

        {/* Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filteredModules.map((item) => {
            const Icon = getModuleIcon(item.icon)
            const isWarning = item.status === 'warning'
            const isNeedsConfig = item.status === 'needs_config'

            return (
              <div
                key={item.code}
                className={`bg-white border rounded-3xl p-5 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-4 group ${
                  isNeedsConfig
                    ? 'border-slate-200/80 bg-slate-50/40'
                    : isWarning
                    ? 'border-amber-200 hover:border-amber-400 ring-1 ring-amber-400/20'
                    : 'border-slate-200/90 hover:border-indigo-400'
                }`}
              >
                {/* 1. Header Row */}
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center space-x-3">
                      <div className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 border ${
                        isNeedsConfig
                          ? 'bg-slate-100 text-slate-500 border-slate-200'
                          : isWarning
                          ? 'bg-amber-50 text-amber-600 border-amber-200'
                          : 'bg-emerald-50 text-emerald-600 border-emerald-200'
                      }`}>
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-bold text-sm text-slate-900 group-hover:text-indigo-600 transition-colors">
                          {item.name}
                        </h3>
                        <div className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                          <Database className="w-3 h-3 text-slate-400" />
                          <span>{item.data_source_label}</span>
                        </div>
                      </div>
                    </div>

                    {isNeedsConfig ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500 border border-slate-200 shrink-0">
                        Needs config
                      </span>
                    ) : isWarning ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-700 border border-amber-200 inline-flex items-center gap-1 shrink-0">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                        <span>Cần xử lý</span>
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 inline-flex items-center gap-1 shrink-0">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        <span>Ổn định</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* 2. Real KPI Box */}
                <div className="bg-slate-50/80 border border-slate-100 rounded-2xl p-3.5 space-y-1">
                  <div className="flex items-baseline justify-between">
                    <span className="text-xl font-black text-slate-900 tracking-tight">{item.kpi.main}</span>
                    <span className="text-[11px] font-medium text-slate-500">{item.kpi.label}</span>
                  </div>
                  {item.kpi.sub && (
                    <div className="text-[11px] text-indigo-600 font-semibold">
                      • {item.kpi.sub}
                    </div>
                  )}
                </div>

                {/* 3. Alert Box */}
                <div className={`rounded-xl p-3 border text-xs space-y-1 ${
                  isNeedsConfig
                    ? 'bg-slate-100/50 border-slate-200 text-slate-500'
                    : isWarning
                    ? 'bg-amber-50/70 border-amber-200/80 text-amber-900'
                    : 'bg-emerald-50/40 border-emerald-200/60 text-slate-700'
                }`}>
                  <div className="flex items-start gap-2">
                    {isWarning ? (
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    )}
                    <span className="line-clamp-2 leading-relaxed">
                      {(item.alerts && item.alerts[0]) || 'Hệ thống vận hành bình thường'}
                    </span>
                  </div>
                </div>

                {/* 4. AI Recommendation Line */}
                <div className="text-[11px] text-slate-600 flex items-start gap-1.5 leading-relaxed bg-purple-50/40 p-2.5 rounded-xl border border-purple-100/60">
                  <Sparkles className="w-3.5 h-3.5 text-purple-500 shrink-0 mt-0.5" />
                  <span className="line-clamp-2">{item.recommended_action}</span>
                </div>

                {/* 5. Direct Action Buttons */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => setActiveInsightModule(item)}
                    className="py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors cursor-pointer"
                  >
                    Xem chi tiết
                  </button>

                  <button
                    type="button"
                    onClick={() => handleActionNavigate(item.primary_action.path)}
                    className={`py-2 px-3.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-xs ${
                      isNeedsConfig
                        ? 'bg-slate-800 hover:bg-slate-700 text-white'
                        : isWarning
                        ? 'bg-amber-600 hover:bg-amber-700 text-white shadow-amber-500/20'
                        : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-indigo-500/20'
                    }`}
                  >
                    <span>{item.primary_action.label}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ================= OPERATIONS INSIGHT DRAWER (SLIDE-OVER MODAL) ================= */}
      {activeInsightModule && (
        <OperationsInsightDrawer
          moduleItem={activeInsightModule}
          onClose={() => setActiveInsightModule(null)}
          onNavigate={onNavigate}
        />
      )}

      {/* ================= MODAL TRỤ CỘT 09: AI CAMPAIGN AUTOPILOT ================= */}
      {isAutopilotModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 overflow-y-auto animate-fade-in">
          <div className="bg-slate-900 border border-slate-700/80 rounded-3xl w-full max-w-5xl text-white shadow-2xl overflow-hidden my-6 max-h-[92vh] flex flex-col">
            {/* Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60 shrink-0">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-purple-500/20 border border-purple-500/40 text-purple-400 flex items-center justify-center">
                  <Rocket className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-base sm:text-lg font-bold text-white">
                      AI Campaign Autopilot
                    </h2>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
                      SME Operations
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Lập kế hoạch chiến dịch 4 tuần, lịch 12 bài nội dung và kịch bản chốt sale
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsAutopilotModalOpen(false)}
                className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              {autopilotError && (
                <div className="p-4 rounded-2xl bg-rose-500/20 border border-rose-500/40 text-rose-300 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{autopilotError}</span>
                </div>
              )}

              {/* Form Input Section */}
              <div className="bg-slate-950/40 border border-slate-800 rounded-2xl p-5 space-y-4">
                <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
                  <Sliders className="w-4 h-4 text-purple-400" />
                  <span>Tham số mục tiêu chiến dịch</span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Mục tiêu kinh doanh (Goal)
                    </label>
                    <input
                      type="text"
                      value={campaignForm.goal}
                      onChange={(e) => setCampaignForm({ ...campaignForm, goal: e.target.value })}
                      placeholder="Ví dụ: Bán 100 bộ sách Excel hoặc tuyển 50 học viên khóa MOS"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-hidden focus:border-purple-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Ngân sách dự kiến (VND)
                    </label>
                    <input
                      type="number"
                      value={campaignForm.budget_vnd}
                      onChange={(e) => setCampaignForm({ ...campaignForm, budget_vnd: Number(e.target.value) })}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-hidden focus:border-purple-500 font-mono"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Doanh thu kỳ vọng (VND)
                    </label>
                    <input
                      type="number"
                      value={campaignForm.target_revenue_vnd}
                      onChange={(e) => setCampaignForm({ ...campaignForm, target_revenue_vnd: Number(e.target.value) })}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-white text-xs focus:outline-hidden focus:border-purple-500 font-mono"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-end pt-2">
                  <button
                    type="button"
                    onClick={handleGenerateAutopilot}
                    disabled={autopilotLoading || !campaignForm.goal?.trim()}
                    className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-bold text-xs shadow-md shadow-purple-600/30 transition-all cursor-pointer"
                  >
                    {autopilotLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Đang phân tích &amp; sinh lộ trình...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 text-purple-200" />
                        <span>Sinh kế hoạch Autopilot mới</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Generated Plan View */}
              {campaignPlan && (
                <div className="space-y-4">
                  {/* Plan Tabs */}
                  <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                    <button
                      type="button"
                      onClick={() => setCampaignTab('milestones')}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
                        campaignTab === 'milestones'
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      Lộ trình 4 tuần ({campaignPlan.milestones?.length || 4})
                    </button>
                    <button
                      type="button"
                      onClick={() => setCampaignTab('calendar')}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
                        campaignTab === 'calendar'
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      Lịch 12 bài nội dung ({campaignPlan.content_calendar?.length || 12})
                    </button>
                    <button
                      type="button"
                      onClick={() => setCampaignTab('objections')}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
                        campaignTab === 'objections'
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      Xử lý từ chối ({campaignPlan.sales_objection_playbook?.length || 3})
                    </button>
                    <button
                      type="button"
                      onClick={() => setCampaignTab('checklist')}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
                        campaignTab === 'checklist'
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      Checklist nghiệm thu ({campaignPlan.review_checklist?.length || 5})
                    </button>
                  </div>

                  {/* Tab 1: Milestones */}
                  {campaignTab === 'milestones' && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {(campaignPlan.milestones || []).map((m) => (
                        <div key={m.week} className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-bold text-purple-400 bg-purple-950/60 px-2.5 py-0.5 rounded-full border border-purple-500/30">
                              Tuần {m.week}
                            </span>
                            <span className="text-[11px] text-emerald-400 font-semibold">{m.kpi_target}</span>
                          </div>
                          <h4 className="text-sm font-bold text-white">{m.theme}</h4>
                          <p className="text-xs text-slate-400 leading-relaxed">{m.key_action}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 2: Calendar */}
                  {campaignTab === 'calendar' && (
                    <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                      {(campaignPlan.content_calendar || []).map((item, idx) => (
                        <div key={idx} className="p-3.5 rounded-2xl bg-slate-950/60 border border-slate-800 text-xs space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <span className="font-bold text-white bg-slate-800 px-2 py-0.5 rounded">
                                Ngày {item.day}
                              </span>
                              <span className="uppercase text-[10px] font-bold text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-500/30">
                                {item.platform}
                              </span>
                            </div>
                            <span className="text-[11px] text-amber-300 font-medium">Mục tiêu: {item.lead_target} leads</span>
                          </div>
                          <div>
                            <span className="text-slate-400 font-semibold">Hook: </span>
                            <span className="text-slate-200">"{item.hook}"</span>
                          </div>
                          <div>
                            <span className="text-slate-400 font-semibold">CTA: </span>
                            <span className="text-purple-300">"{item.cta}"</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 3: Objections */}
                  {campaignTab === 'objections' && (
                    <div className="space-y-3">
                      {(campaignPlan.sales_objection_playbook || []).map((obj, idx) => (
                        <div key={idx} className="p-4 rounded-2xl bg-slate-950/60 border border-slate-800 space-y-2">
                          <div className="text-xs font-bold text-rose-300 flex items-center space-x-1.5">
                            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                            <span>Khách từ chối: "{obj.customer_objection}"</span>
                          </div>
                          <div className="text-xs text-slate-300 pl-5 border-l-2 border-purple-500/40 space-y-1">
                            <div><strong className="text-purple-300">AI phản hồi:</strong> {obj.ai_counter_argument}</div>
                            <div className="pt-1 text-emerald-300"><strong className="text-emerald-400">Chốt ưu đãi:</strong> {obj.closing_offer}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 4: Checklist */}
                  {campaignTab === 'checklist' && (
                    <div className="space-y-2">
                      {(campaignPlan.review_checklist || []).map((chk, idx) => (
                        <div key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center space-x-3 text-xs text-slate-200">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                          <span>{chk}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between shrink-0">
              <div className="text-[11px] text-slate-400">
                AI Operations Center · Tự động đồng bộ báo cáo và ma trận rủi ro
              </div>
              <div className="flex items-center space-x-2">
                {campaignPlan && (
                  <button
                    type="button"
                    onClick={handleCopyPlan}
                    className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition-colors cursor-pointer"
                  >
                    {autopilotCopied ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400">Đã chép kế hoạch!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Sao chép toàn bộ</span>
                      </>
                    )}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setIsAutopilotModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors cursor-pointer"
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
