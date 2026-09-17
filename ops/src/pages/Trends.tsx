import React, { useState, useEffect } from 'react'
import {
  TrendingUp,
  BarChart2,
  PieChart as PieIcon,
  DollarSign,
  Cpu,
  Layers,
  Calendar,
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
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

const COLORS = ['#f97316', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899', '#f59e0b']

export const Trends: React.FC = () => {
  const { role } = useAuth()
  const [usage, setUsage] = useState<any>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [stats, setStats] = useState<any>(null)

  // Derived datasets
  const [branchData, setBranchData] = useState<any[]>([])
  const [intentData, setIntentData] = useState<any[]>([])
  const [dailyActivity, setDailyActivity] = useState<any[]>([])

  useEffect(() => {
    const loadTrends = async () => {
      try {
        const [usageRes, custRes, inboxRes] = await Promise.all([
          api.getUsageSummary().catch(() => null),
          api.getCustomers('', '', 200).catch(() => ({ ok: false, customers: [] })),
          api.getInbox({ limit: 200 }).catch(() => ({ ok: false, events: [], drafts: [], stats: null as any })),
        ])

        if (usageRes) setUsage(usageRes)
        if (inboxRes?.stats) setStats(inboxRes.stats)

        // 1. Group leads by campus (branch)
        const customers = custRes?.customers || []
        const branchCounts: Record<string, number> = {}
        customers.forEach((c: any) => {
          const b = c.campus || 'Chưa gắn cơ sở'
          branchCounts[b] = (branchCounts[b] || 0) + 1
        })
        const branches = Object.entries(branchCounts).map(([name, value]) => ({ name, value }))
        setBranchData(branches)

        // 2. Group comments/messages by intent or classification
        const events = inboxRes?.events || []
        const intentCounts: Record<string, number> = {}
        events.forEach((e: any) => {
          const it = e.faq_intent || e.class || 'Tư vấn chung'
          intentCounts[it] = (intentCounts[it] || 0) + 1
        })
        const intents = Object.entries(intentCounts).map(([name, value]) => ({ name, value }))
        setIntentData(intents)

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
      }
    }

    loadTrends()
  }, [])

  if (role === 'staff') {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500">
        <TrendingUp className="w-10 h-10 mx-auto mb-3 text-slate-300" />
        <h3 className="font-bold text-slate-800 text-sm">Giới hạn quyền truy cập</h3>
        <p className="text-xs text-slate-500 mt-1">
          Trang Xu Hướng & Thống Kê chỉ dành cho tài khoản Quản lý và Chủ máy.
        </p>
      </div>
    )
  }

  // Calculate stats
  const totalTokens = usage?.kpi?.tokens ?? usage?.total_tokens ?? 0
  const costUsd = usage?.kpi?.cost_est ?? usage?.cost_usd ?? 0
  const convRate = stats?.events_24h && stats.events_24h > 0
    ? ((stats.leads_24h / stats.events_24h) * 100).toFixed(1)
    : '0'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Xu Hướng & Báo Cáo Vận Hành</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Số thật từ Care: comment, IB, lead, token. Không vẽ số giả.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs text-slate-500 bg-white px-3 py-1.5 rounded-xl border border-slate-200">
          <Calendar className="w-3.5 h-3.5 text-saoviet-500" />
          <span>Kỳ thống kê: {usage?.period || 'Tháng này'}</span>
        </div>
      </div>

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
  )
}
