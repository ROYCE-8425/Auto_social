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
  UserCheck,
  Star,
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
import { api, CareState, CareStats } from '../lib/api'
import { useCareScope } from '../lib/scope'

interface OverviewProps {
  onNavigate: (tab: string) => void
}

// 14-day operational volume chart data matching mockup
const operationalVolumeData = [
  { date: '10/04', cmt: 160, msg: 240 },
  { date: '11/04', cmt: 210, msg: 320 },
  { date: '12/04', cmt: 305, msg: 415 },
  { date: '13/04', cmt: 225, msg: 340 },
  { date: '14/04', cmt: 175, msg: 285 },
  { date: '15/04', cmt: 210, msg: 310 },
  { date: '16/04', cmt: 220, msg: 330 },
  { date: '17/04', cmt: 265, msg: 450 },
  { date: '18/04', cmt: 235, msg: 420 },
  { date: '19/04', cmt: 275, msg: 390 },
  { date: '20/04', cmt: 220, msg: 470 },
  { date: '21/04', cmt: 290, msg: 430 },
  { date: '22/04', cmt: 320, msg: 550 },
  { date: '23/04', cmt: 310, msg: 542 },
]

// Work breakdown donut data matching mockup
const workBreakdownData = [
  { name: 'AI xử lý', value: 78, count: 454, fill: '#10b981' },
  { name: 'Nhân viên xử lý', value: 22, count: 128, fill: '#2563eb' },
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
  'bg-blue-50/60', // 0: Very low
  'bg-blue-100',    // 1: Low
  'bg-blue-300',    // 2: Medium
  'bg-blue-500',    // 3: High
  'bg-blue-700',    // 4: Peak deep blue
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
    <div className="space-y-5">
      {/* ROW 1: 6 KPI METRIC CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3.5">
        {/* Card 1: Bình luận 24h */}
        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] hover:shadow-md transition-shadow relative flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white shadow-sm shadow-blue-200">
              <MessageSquare className="w-4 h-4" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-emerald-600">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>12%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-500 block">Bình luận 24h</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight">{commentsCount}</div>
              <span className="text-[11px] text-slate-400 font-medium">So với hôm qua</span>
            </div>
            <svg className="w-14 h-8 text-blue-500 overflow-visible" viewBox="0 0 50 25" fill="none">
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
        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] hover:shadow-md transition-shadow relative flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-200">
              <Send className="w-4 h-4" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-emerald-600">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>8%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-500 block">Tin nhắn 24h</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight">{inboxesCount}</div>
              <span className="text-[11px] text-slate-400 font-medium">So với hôm qua</span>
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
        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] hover:shadow-md transition-shadow relative flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white shadow-sm shadow-blue-200">
              <Users className="w-4 h-4" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-emerald-600">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>25%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-500 block">Lead mới</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight">{leadsCount}</div>
              <span className="text-[11px] text-slate-400 font-medium">So với hôm qua</span>
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
        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] hover:shadow-md transition-shadow relative flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center justify-center text-white shadow-sm shadow-orange-200">
              <AlertCircle className="w-4 h-4" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-rose-500">
              <TrendingDown className="w-3.5 h-3.5" />
              <span>14%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-500 block">Khách cần hỗ trợ</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight">{needsHumanCount}</div>
              <span className="text-[11px] text-slate-400 font-medium">So với hôm qua</span>
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
        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] hover:shadow-md transition-shadow relative flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center text-white shadow-sm shadow-emerald-200">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-emerald-600">
              <TrendingUp className="w-3.5 h-3.5" />
              <span>6%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-500 block">Tỷ lệ AI xử lý</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight">{aiResolvedRate}%</div>
              <span className="text-[11px] text-slate-400 font-medium">So với hôm qua</span>
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
        <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] hover:shadow-md transition-shadow relative flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white shadow-sm shadow-blue-200">
              <CheckSquare className="w-4 h-4" />
            </div>
            <div className="flex items-center space-x-0.5 text-xs font-bold text-orange-500">
              <TrendingDown className="w-3.5 h-3.5" />
              <span>9%</span>
            </div>
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-500 block">Công việc đang mở</span>
              <div className="text-2xl font-black text-slate-900 tracking-tight">{openTasksCount}</div>
              <span className="text-[11px] text-slate-400 font-medium">So với hôm qua</span>
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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Card A: Tổng quan vận hành */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <BarChart2 className="w-5 h-5 text-blue-600" />
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Tổng quan vận hành</h3>
                <p className="text-xs text-slate-400">Lượt bình luận và tin nhắn trong 14 ngày qua</p>
              </div>
            </div>
            <div className="relative">
              <select className="appearance-none bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold px-2.5 py-1 pr-6 text-slate-700 cursor-pointer focus:outline-none">
                <option>14 ngày qua</option>
                <option>7 ngày qua</option>
                <option>30 ngày qua</option>
              </select>
              <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2 top-2.5 pointer-events-none" />
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
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] flex flex-col justify-between">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <PieIcon className="w-5 h-5 text-blue-600" />
              <div>
                <h3 className="font-bold text-slate-900 text-sm">Phân bổ công việc</h3>
                <p className="text-xs text-slate-400">Tỷ lệ xử lý và kênh tiếp nhận</p>
              </div>
            </div>
            <div className="relative">
              <select className="appearance-none bg-slate-50 border border-slate-200 rounded-lg text-xs font-semibold px-2.5 py-1 pr-6 text-slate-700 cursor-pointer focus:outline-none">
                <option>Hôm nay</option>
                <option>Hôm qua</option>
                <option>Tuần này</option>
              </select>
              <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2 top-2.5 pointer-events-none" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 items-center h-56">
            {/* Donut Chart with Center Text */}
            <div className="h-full relative flex items-center justify-center">
              <ResponsiveContainer width="100%" height="85%">
                <PieChart>
                  <Pie
                    data={workBreakdownData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={68}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {workBreakdownData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute flex flex-col items-center pointer-events-none">
                <span className="text-[10px] text-slate-400 font-semibold">Tổng</span>
                <span className="text-xl font-black text-slate-900 leading-tight">582</span>
                <span className="text-[10px] text-slate-400 font-medium">cuộc hội thoại</span>
              </div>
            </div>

            {/* Right: By Channel Progress Bars */}
            <div className="space-y-3 pl-2 border-l border-slate-100">
              <span className="text-xs font-bold text-slate-700 block">Theo kênh</span>

              {/* Channel 1: Bình luận */}
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                  <span>Bình luận</span>
                  <span>32% (186)</span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-500 rounded-full" style={{ width: '32%' }} />
                </div>
              </div>

              {/* Channel 2: Messenger */}
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                  <span>Messenger</span>
                  <span>48% (279)</span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-blue-600 rounded-full" style={{ width: '48%' }} />
                </div>
              </div>

              {/* Channel 3: CRM / Lead */}
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                  <span>CRM / Lead</span>
                  <span>20% (117)</span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-orange-500 rounded-full" style={{ width: '20%' }} />
                </div>
              </div>
            </div>
          </div>

          {/* Bottom legend */}
          <div className="flex items-center justify-around pt-2 border-t border-slate-100 text-xs font-semibold">
            <span className="flex items-center space-x-1.5 text-emerald-700">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>AI xử lý 78% (454)</span>
            </span>
            <span className="flex items-center space-x-1.5 text-blue-700">
              <span className="w-2 h-2 rounded-full bg-blue-600" />
              <span>Nhân viên xử lý 22% (128)</span>
            </span>
          </div>
        </div>

        {/* Card C: Khung giờ cao điểm (Heatmap Matrix) */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] flex flex-col justify-between">
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
          <div className="flex flex-col justify-between h-56 pt-1">
            <div className="w-full">
              {/* Day Header Row */}
              <div className="grid grid-cols-8 gap-1 mb-1">
                <span className="text-[10px] text-slate-400 font-medium"></span>
                {heatmapDays.map((d) => (
                  <span key={d} className="text-[10px] font-bold text-slate-500 text-center">
                    {d}
                  </span>
                ))}
              </div>

              {/* 8 Time Block Rows */}
              <div className="space-y-1">
                {heatmapHours.map((hour, rIdx) => (
                  <div key={hour} className="grid grid-cols-8 gap-1 items-center">
                    <span className="text-[9px] text-slate-400 font-medium whitespace-nowrap">{hour}</span>
                    {heatmapMatrix[rIdx].map((val, cIdx) => (
                      <div
                        key={`${rIdx}-${cIdx}`}
                        className={`h-4 rounded-[3px] transition-colors ${heatmapBgColors[val]}`}
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
              <span className="w-2 h-2 rounded-full bg-blue-50 border border-blue-200" />
              <span className="w-2 h-2 rounded-full bg-blue-200" />
              <span className="w-2 h-2 rounded-full bg-blue-400" />
              <span className="w-2 h-2 rounded-full bg-blue-600" />
              <span className="w-2 h-2 rounded-full bg-blue-800" />
              <span>Cao</span>
            </div>
          </div>
        </div>
      </div>

      {/* ROW 3: 3 OPERATIONAL CARDS (Mini-Kanban, Hot Leads, Urgent Inbox) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Card 1: Việc cần làm (Mini Kanban) */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] flex flex-col justify-between">
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
            <div className="bg-slate-50/80 rounded-xl p-2 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-blue-700">Cần làm</span>
                  <span className="text-[10px] font-bold bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded-full">8</span>
                </div>
                <div className="space-y-1.5">
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs">
                    <p className="text-[11px] font-semibold text-slate-800 line-clamp-2 leading-tight">
                      Liên hệ lại khách trải nghiệm game
                    </p>
                    <div className="flex items-center justify-between mt-1 text-[9px] text-slate-400 font-medium">
                      <span>#10234</span>
                      <span className="bg-blue-50 text-blue-600 px-1 rounded">NT · 2h trước</span>
                    </div>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs">
                    <p className="text-[11px] font-semibold text-slate-800 line-clamp-2 leading-tight">
                      Kiểm tra khiếu nại nạp thẻ
                    </p>
                    <div className="flex items-center justify-between mt-1 text-[9px] text-slate-400 font-medium">
                      <span>#10221</span>
                      <span className="bg-blue-50 text-blue-600 px-1 rounded">LH · 3h trước</span>
                    </div>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('tasks')}
                className="w-full text-center text-[10px] font-bold text-blue-600 hover:text-blue-700 pt-2 flex items-center justify-center space-x-0.5"
              >
                <Plus className="w-3 h-3" />
                <span>Thêm việc</span>
              </button>
            </div>

            {/* Col 2: Đang xử lý (10) */}
            <div className="bg-slate-50/80 rounded-xl p-2 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-orange-700">Đang xử lý</span>
                  <span className="text-[10px] font-bold bg-orange-100 text-orange-800 px-1.5 py-0.2 rounded-full">10</span>
                </div>
                <div className="space-y-1.5">
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs">
                    <p className="text-[11px] font-semibold text-slate-800 line-clamp-2 leading-tight">
                      Hỗ trợ lỗi đăng nhập trên iOS
                    </p>
                    <div className="flex items-center justify-between mt-1 text-[9px] text-slate-400 font-medium">
                      <span>#10218</span>
                      <span className="bg-orange-50 text-orange-600 px-1 rounded">PT Đang xử lý</span>
                    </div>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs">
                    <p className="text-[11px] font-semibold text-slate-800 line-clamp-2 leading-tight">
                      Tư vấn gói nạp mới
                    </p>
                    <div className="flex items-center justify-between mt-1 text-[9px] text-slate-400 font-medium">
                      <span>#10216</span>
                      <span className="bg-orange-50 text-orange-600 px-1 rounded">ĐT Đang xử lý</span>
                    </div>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('tasks')}
                className="w-full text-center text-[10px] font-bold text-blue-600 hover:text-blue-700 pt-2 flex items-center justify-center space-x-0.5"
              >
                <Plus className="w-3 h-3" />
                <span>Thêm việc</span>
              </button>
            </div>

            {/* Col 3: Chờ phản hồi (6) */}
            <div className="bg-slate-50/80 rounded-xl p-2 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-amber-700">Chờ phản hồi</span>
                  <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded-full">6</span>
                </div>
                <div className="space-y-1.5">
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs">
                    <p className="text-[11px] font-semibold text-slate-800 line-clamp-2 leading-tight">
                      Chờ khách cung cấp thông tin
                    </p>
                    <div className="flex items-center justify-between mt-1 text-[9px] text-slate-400 font-medium">
                      <span>#10209</span>
                      <span className="bg-amber-50 text-amber-600 px-1 rounded">NH · 1h trước</span>
                    </div>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs">
                    <p className="text-[11px] font-semibold text-slate-800 line-clamp-2 leading-tight">
                      Xác nhận thanh toán
                    </p>
                    <div className="flex items-center justify-between mt-1 text-[9px] text-slate-400 font-medium">
                      <span>#10205</span>
                      <span className="bg-amber-50 text-amber-600 px-1 rounded">VT · 2h trước</span>
                    </div>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('tasks')}
                className="w-full text-center text-[10px] font-bold text-blue-600 hover:text-blue-700 pt-2 flex items-center justify-center space-x-0.5"
              >
                <Plus className="w-3 h-3" />
                <span>Thêm việc</span>
              </button>
            </div>

            {/* Col 4: Hoàn tất (4) */}
            <div className="bg-slate-50/80 rounded-xl p-2 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-bold text-emerald-700">Hoàn tất</span>
                  <span className="text-[10px] font-bold bg-emerald-100 text-emerald-800 px-1.5 py-0.2 rounded-full">4</span>
                </div>
                <div className="space-y-1.5">
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs">
                    <p className="text-[11px] font-semibold text-slate-800 line-clamp-2 leading-tight">
                      Đã hỗ trợ thành công
                    </p>
                    <div className="flex items-center justify-between mt-1 text-[9px] text-slate-400 font-medium">
                      <span>#10198</span>
                      <span className="bg-emerald-50 text-emerald-600 px-1 rounded">ML 10:24</span>
                    </div>
                  </div>
                  <div className="bg-white p-2 rounded-lg border border-slate-200/70 shadow-2xs">
                    <p className="text-[11px] font-semibold text-slate-800 line-clamp-2 leading-tight">
                      Đã chuyển team kỹ thuật
                    </p>
                    <div className="flex items-center justify-between mt-1 text-[9px] text-slate-400 font-medium">
                      <span>#10195</span>
                      <span className="bg-emerald-50 text-emerald-600 px-1 rounded">PQ 09:12</span>
                    </div>
                  </div>
                </div>
              </div>
              <button
                onClick={() => onNavigate('tasks')}
                className="w-full text-center text-[10px] font-bold text-blue-600 hover:text-blue-700 pt-2 flex items-center justify-center space-x-0.5"
              >
                <Plus className="w-3 h-3" />
                <span>Thêm việc</span>
              </button>
            </div>
          </div>
        </div>

        {/* Card 2: Khách hàng mới / Lead nổi bật */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] flex flex-col justify-between">
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

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[11px] font-bold text-slate-400 border-b border-slate-100 pb-2">
                  <th className="pb-2 font-bold">Khách hàng</th>
                  <th className="pb-2 font-bold">SĐT</th>
                  <th className="pb-2 font-bold">Nguồn</th>
                  <th className="pb-2 font-bold">Tag</th>
                  <th className="pb-2 font-bold text-right">Thời gian</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 text-xs">
                {/* Row 1 */}
                <tr className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 font-bold text-[10px] flex items-center justify-center">
                      NA
                    </div>
                    <span className="font-bold text-slate-900">Nguyễn Minh Anh</span>
                  </td>
                  <td className="py-2.5 font-medium text-slate-600">0987 123 456</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold text-[10px]">
                      Facebook
                    </span>
                  </td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-cyan-50 text-cyan-700 font-semibold text-[10px]">
                      Quan tâm
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-400">10:24</td>
                </tr>

                {/* Row 2 */}
                <tr className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-700 font-bold text-[10px] flex items-center justify-center">
                      HN
                    </div>
                    <span className="font-bold text-slate-900">Trần Hoàng Nam</span>
                  </td>
                  <td className="py-2.5 font-medium text-slate-600">0321 654 987</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold text-[10px]">
                      Messenger
                    </span>
                  </td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-orange-50 text-orange-700 font-semibold text-[10px]">
                      Nạp thẻ
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-400">09:50</td>
                </tr>

                {/* Row 3 */}
                <tr className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-purple-100 text-purple-700 font-bold text-[10px] flex items-center justify-center">
                      BT
                    </div>
                    <span className="font-bold text-slate-900">Lê Thị Bảo Trân</span>
                  </td>
                  <td className="py-2.5 font-medium text-slate-600">0905 678 321</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-slate-900 text-white font-semibold text-[10px]">
                      TikTok
                    </span>
                  </td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 font-semibold text-[10px]">
                      Tư vấn
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-400">09:12</td>
                </tr>

                {/* Row 4 */}
                <tr className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-700 font-bold text-[10px] flex items-center justify-center">
                      QH
                    </div>
                    <span className="font-bold text-slate-900">Phạm Quốc Huy</span>
                  </td>
                  <td className="py-2.5 font-medium text-slate-600">0869 234 567</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-teal-50 text-teal-700 font-semibold text-[10px]">
                      Website
                    </span>
                  </td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold text-[10px]">
                      Dùng thử
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-400">08:45</td>
                </tr>

                {/* Row 5 */}
                <tr className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-2.5 flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-rose-100 text-rose-700 font-bold text-[10px] flex items-center justify-center">
                      TH
                    </div>
                    <span className="font-bold text-slate-900">Đặng Thu Hà</span>
                  </td>
                  <td className="py-2.5 font-medium text-slate-600">0912 345 678</td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold text-[10px]">
                      Facebook
                    </span>
                  </td>
                  <td className="py-2.5">
                    <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-[10px]">
                      VIP
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-medium text-slate-400">08:20</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Card 3: Hộp thư cần chú ý */}
        <div className="bg-white rounded-2xl p-5 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] flex flex-col justify-between">
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

          {/* List of 5 Urgent Messages */}
          <div className="space-y-2.5">
            {/* Item 1 */}
            <div
              onClick={() => onNavigate('inbox')}
              className="p-2.5 rounded-xl border border-slate-100 hover:bg-slate-50/80 transition-all flex items-center justify-between cursor-pointer"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  MĐ
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 leading-tight">Trần Minh Đức</div>
                  <p className="text-[11px] text-slate-500 truncate">Game bị lỗi đăng nhập, nhờ hỗ trợ gấp...</p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <span className="text-[10px] text-slate-400 block mb-0.5">14:32</span>
                <span className="px-1.5 py-0.2 rounded bg-rose-50 text-rose-700 font-bold text-[10px] border border-rose-200">
                  Ưu tiên
                </span>
              </div>
            </div>

            {/* Item 2 */}
            <div
              onClick={() => onNavigate('inbox')}
              className="p-2.5 rounded-xl border border-slate-100 hover:bg-slate-50/80 transition-all flex items-center justify-between cursor-pointer"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-orange-100 text-orange-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  TH
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 leading-tight">Nguyễn Thị Hoa</div>
                  <p className="text-[11px] text-slate-500 truncate">Cho mình hỏi về gói nạp tháng?...</p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <span className="text-[10px] text-slate-400 block mb-0.5">14:20</span>
                <span className="px-1.5 py-0.2 rounded bg-orange-50 text-orange-700 font-bold text-[10px] border border-orange-200">
                  Cần phản hồi
                </span>
              </div>
            </div>

            {/* Item 3 */}
            <div
              onClick={() => onNavigate('inbox')}
              className="p-2.5 rounded-xl border border-slate-100 hover:bg-slate-50/80 transition-all flex items-center justify-between cursor-pointer"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  AT
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 leading-tight">Phạm Anh Tuấn</div>
                  <p className="text-[11px] text-slate-500 truncate">Khi nào có sự kiện mới vậy ạ?...</p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <span className="text-[10px] text-slate-400 block mb-0.5">13:50</span>
                <span className="px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 font-bold text-[10px] border border-blue-200">
                  Khách VIP
                </span>
              </div>
            </div>

            {/* Item 4 */}
            <div
              onClick={() => onNavigate('inbox')}
              className="p-2.5 rounded-xl border border-slate-100 hover:bg-slate-50/80 transition-all flex items-center justify-between cursor-pointer"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  QB
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 leading-tight">Lê Quốc Bảo</div>
                  <p className="text-[11px] text-slate-500 truncate">Mình đã thanh toán nhưng chưa nhận được...</p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <span className="text-[10px] text-slate-400 block mb-0.5">11:18</span>
                <span className="px-1.5 py-0.2 rounded bg-amber-50 text-amber-700 font-bold text-[10px] border border-amber-200">
                  Cần kiểm tra
                </span>
              </div>
            </div>

            {/* Item 5 */}
            <div
              onClick={() => onNavigate('inbox')}
              className="p-2.5 rounded-xl border border-slate-100 hover:bg-slate-50/80 transition-all flex items-center justify-between cursor-pointer"
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                  MA
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-bold text-slate-900 leading-tight">Trần Mai Anh</div>
                  <p className="text-[11px] text-slate-500 truncate">Tư vấn giúp mình gói phù hợp với newbie...</p>
                </div>
              </div>
              <div className="text-right flex-shrink-0 ml-2">
                <span className="text-[10px] text-slate-400 block mb-0.5">10:05</span>
                <span className="px-1.5 py-0.2 rounded bg-cyan-50 text-cyan-700 font-bold text-[10px] border border-cyan-200">
                  Quan tâm
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ROW 4: BOTTOM AI PERFORMANCE SUMMARY BAR */}
      <div className="bg-white rounded-2xl p-4 border border-slate-100 shadow-[0_4px_16px_rgba(0,0,0,0.03)] flex flex-wrap items-center justify-between gap-4">
        {/* Left: Bot Identity */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-200">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-black text-slate-900 text-sm">Hiệu quả AI</h4>
            <p className="text-xs text-slate-400">Hiệu suất trả lời tự động trong 7 ngày qua</p>
          </div>
        </div>

        {/* 4 Metric Pills */}
        <div className="flex flex-wrap items-center gap-8 text-slate-700">
          {/* Metric 1 */}
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <MessageSquare className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-semibold block">Tỷ lệ trả lời thành công</span>
              <div className="flex items-baseline space-x-1">
                <span className="text-base font-black text-slate-900">78%</span>
                <span className="text-[11px] font-bold text-emerald-600 flex items-center">
                  <TrendingUp className="w-3 h-3 mr-0.5" />
                  6%
                </span>
              </div>
            </div>
          </div>

          {/* Metric 2 */}
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-semibold block">Thời gian phản hồi trung bình</span>
              <div className="flex items-baseline space-x-1">
                <span className="text-base font-black text-slate-900">12 giây</span>
                <span className="text-[11px] font-bold text-emerald-600 flex items-center">
                  <TrendingDown className="w-3 h-3 mr-0.5" />
                  35%
                </span>
              </div>
            </div>
          </div>

          {/* Metric 3 */}
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <UserCheck className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-semibold block">Cần chuyển cho nhân viên</span>
              <div className="flex items-baseline space-x-1">
                <span className="text-base font-black text-slate-900">22%</span>
                <span className="text-[11px] font-bold text-rose-500 flex items-center">
                  <TrendingDown className="w-3 h-3 mr-0.5" />
                  5%
                </span>
              </div>
            </div>
          </div>

          {/* Metric 4 */}
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Star className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-semibold block">Đánh giá hài lòng (từ phản hồi)</span>
              <div className="flex items-baseline space-x-1">
                <span className="text-base font-black text-slate-900">4.6 / 5</span>
                <span className="text-[11px] font-bold text-emerald-600 flex items-center">
                  <TrendingUp className="w-3 h-3 mr-0.5" />
                  0.3
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
