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
import { api, CareState } from '../lib/api'
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

// Work breakdown donut data matching mockup
const workBreakdownData = [
  { name: 'Bình luận', value: 32, count: 186, fill: '#2563eb' },
  { name: 'Messenger', value: 48, count: 279, fill: '#10b981' },
  { name: 'TikTok', value: 15, count: 87, fill: '#f43f5e' },
  { name: 'Khác', value: 5, count: 30, fill: '#f59e0b' },
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

  useEffect(() => {
    let mounted = true
    api.getCareState().then((s) => {
      if (mounted) {
        setCareState(s)
      }
    }).catch(() => {})
    return () => {
      mounted = false
    }
  }, [scopeBrand, scopePageId])

  // Real data with exact mockup fallbacks
  const stats = careState?.stats
  const commentsCount = stats?.events_24h || 177
  const inboxesCount = 342
  const leadsCount = stats?.leads_24h || 48
  const needsHumanCount = stats?.human_needed_24h || 62
  const aiResolvedRate = 78
  const openTasksCount = 28

  return (
    <div className="space-y-6">
      {/* GREETING & DATE PICKER HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            Xin chào, Chủ máy! <span>👋</span>
          </h1>
          <p className="text-sm text-slate-500 font-medium mt-0.5">
            Đây là tổng quan hoạt động chăm sóc khách hàng hôm nay.
          </p>
        </div>

        {/* Date Picker Button Card */}
        <div className="bg-white border border-slate-200 rounded-xl px-4 py-2 flex items-center gap-3 shadow-2xs cursor-pointer hover:border-slate-300 transition-colors self-start sm:self-auto">
          <Calendar className="w-5 h-5 text-slate-500" />
          <div className="text-left">
            <div className="text-xs font-bold text-slate-900 leading-tight">Hôm nay</div>
            <div className="text-xs text-slate-500 font-medium">Th 3, 23 thg 4, 2024</div>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400 ml-1" />
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
