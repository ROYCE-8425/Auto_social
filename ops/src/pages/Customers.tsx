import React, { useState, useEffect } from 'react'
import {
  Users,
  Search,
  Phone,
  Tag,
  Plus,
  ArrowRight,
  MoreVertical,
  CheckCircle2,
  Calendar,
  Building2,
  Share2,
  Pencil,
  Copy,
  ExternalLink,
  MessageCircle,
  FileSpreadsheet,
  Filter,
  ChevronDown,
  Sparkles,
  Bot,
  UserCheck,
  CheckSquare,
  Flame,
  Globe,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  RefreshCw,
} from 'lucide-react'
import { api, CareCustomer, CareCustomerDetail } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useCareScope } from '../lib/scope'
import { FacebookIcon, MessengerIcon, TikTokIcon, PlatformPill } from '../components/BrandIcons'

export interface CustomerItem {
  id: string
  name: string
  avatar: string
  snippet: string
  phone: string
  source: 'Facebook' | 'Messenger' | 'TikTok' | 'Website'
  tag: string
  tagColor: 'blue' | 'purple' | 'amber' | 'rose' | 'green' | 'slate'
  status: 'Đang tư vấn' | 'Đã mua' | 'Lead nóng' | 'Khiếu nại'
  statusColor: 'blue' | 'green' | 'rose' | 'amber'
  lastInteraction: string
  fbId?: string
  area?: string
  createdDate?: string
  notes?: string
  tagsList?: string[]
  timeline?: {
    type: 'customer' | 'ai' | 'staff' | 'status' | 'note'
    title: string
    content: string
    time?: string
    action?: string
  }[]
}

export const Customers: React.FC = () => {
  const { role, can } = useAuth()
  const { scope, scopeBrand, scopePageId } = useCareScope()
  const [customersList, setCustomersList] = useState<CustomerItem[]>([])
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [copySuccess, setCopySuccess] = useState<string | null>(null)
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'info' | 'error' } | null>(null)

  const showToast = (text: string, type: 'success' | 'info' | 'error' = 'info') => {
    setToastMessage({ text, type })
    setTimeout(() => setToastMessage(null), 3000)
  }

  const [loading, setLoading] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [pollNotice, setPollNotice] = useState<string | null>(null)
  const [customerDetail, setCustomerDetail] = useState<CareCustomerDetail | null>(null)
  const [showMergeModal, setShowMergeModal] = useState(false)
  const [secondaryCrmId, setSecondaryCrmId] = useState('')
  const [isMerging, setIsMerging] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [isAddingTag, setIsAddingTag] = useState(false)
  const [newTagInput, setNewTagInput] = useState('')

  const loadCustomers = () => {
    setLoading(true)
    api.getCustomers({ brand: scopeBrand || undefined, page_id: scopePageId || undefined, limit: 100 })
      .then((res) => {
        if (res?.ok && res.customers && res.customers.length > 0) {
          const mapped: CustomerItem[] = res.customers.map((c) => {
            const hasPhone = c.phones && c.phones.length > 0
            const isLead = c.tags?.includes('lead') || c.tags?.includes('hot')
            const isBought = c.tags?.includes('bought') || c.tags?.includes('paid')
            const status: 'Lead nóng' | 'Đang tư vấn' | 'Đã mua' | 'Khiếu nại' = isLead
              ? 'Lead nóng'
              : (isBought ? 'Đã mua' : 'Đang tư vấn')
            const statusColor: 'rose' | 'green' | 'blue' | 'amber' = isLead
              ? 'rose'
              : (isBought ? 'green' : 'blue')
            const tag = c.tags?.[0] ? (c.tags[0] === 'lead' ? 'Lead nóng' : c.tags[0].toUpperCase()) : 'Fanpage'
            const tagColor: 'rose' | 'green' | 'blue' | 'purple' | 'amber' | 'slate' = isLead ? 'rose' : 'blue'

            return {
              id: c.crm_id,
              name: c.name,
              avatar: `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(c.name)}&backgroundColor=2563eb,10b981,f59e0b,f43f5e`,
              snippet: c.course_interest || `Khách hàng từ ${c.campus || 'Fanpage'}`,
              phone: hasPhone ? c.phones[0] : 'Chưa có SĐT',
              source: 'Messenger',
              tag,
              tagColor,
              status,
              statusColor,
              lastInteraction: new Date(c.updated_ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              fbId: c.crm_id.replace('c_', '1000'),
              area: c.campus || 'Game Giá Rẻ BSN',
              createdDate: new Date(c.updated_ts * 1000).toLocaleDateString('vi-VN'),
              notes: c.course_interest ? `Quan tâm: ${c.course_interest}` : `Đồng bộ từ Fanpage ${c.campus || 'Game Giá Rẻ BSN'}`,
              tagsList: c.tags || ['Fanpage'],
              timeline: [
                {
                  type: 'customer',
                  title: 'Tương tác Fanpage',
                  content: `Khách hàng tương tác qua kênh Messenger/Facebook của ${c.campus || 'Fanpage'}`,
                },
                {
                  type: 'ai',
                  title: 'Javis AI tự động ghi nhận',
                  content: 'Đã lưu trữ hồ sơ CRM và đồng bộ trạng thái hội thoại.',
                },
              ],
            }
          })
          setCustomersList(mapped)
          setSelectedCustomerId((prev) => (mapped.some((m) => m.id === prev) ? prev : mapped[0]?.id || ''))
        } else {
          setCustomersList([])
          setSelectedCustomerId('')
        }
      })
      .catch((err: any) => {
        showToast(err?.message || 'Không thể tải danh sách khách hàng', 'error')
        setCustomersList([])
        setSelectedCustomerId('')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadCustomers()
  }, [scopeBrand, scopePageId])

  useEffect(() => {
    if (selectedCustomerId && selectedCustomerId.startsWith('c_')) {
      api.getCustomerDetail(selectedCustomerId).then((res: any) => {
        if (res?.ok) {
          setCustomerDetail(res)
        }
      }).catch(() => {})
    } else {
      setCustomerDetail(null)
    }
    setConfirmDelete(false)
    setShowMergeModal(false)
  }, [selectedCustomerId])

  const handlePollNow = async () => {
    setIsPolling(true)
    setPollNotice('Đang kéo khách hàng & tương tác mới nhất từ Fanpage...')
    try {
      await api.pollNow()
      setPollNotice('Đã đồng bộ thành công!')
      loadCustomers()
      setTimeout(() => setPollNotice(null), 3000)
    } catch (err: any) {
      setPollNotice(`Đồng bộ thất bại: ${err?.message || 'Lỗi mạng'}`)
      setTimeout(() => setPollNotice(null), 3000)
    } finally {
      setIsPolling(false)
    }
  }

  const handleBackfill = async () => {
    setIsPolling(true)
    setPollNotice('Đang tổng hợp hồ sơ CRM từ tất cả sự kiện Fanpage...')
    try {
      const res = await api.backfillCustomers()
      setPollNotice(`Đã cập nhật ${res.customers_created || 0} hồ sơ khách hàng mới!`)
      loadCustomers()
      setTimeout(() => setPollNotice(null), 3000)
    } catch (err: any) {
      setPollNotice(`Backfill lỗi: ${err?.message || 'Lỗi mạng'}`)
      setTimeout(() => setPollNotice(null), 3000)
    } finally {
      setIsPolling(false)
    }
  }

  const handleExportCSV = () => {
    const headers = ['ID', 'Tên khách hàng', 'SĐT', 'Khu vực / Fanpage', 'Nguồn', 'Trạng thái', 'Tag', 'Lần cuối']
    const rows = filteredCustomers.map((c) => [
      c.id,
      `"${c.name}"`,
      `"${c.phone}"`,
      `"${c.area || ''}"`,
      c.source,
      c.status,
      `"${c.tagsList?.join(', ') || ''}"`,
      c.lastInteraction,
    ])
    const csvContent = '\uFEFF' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `khach_hang_crm_${new Date().toISOString().slice(0, 10)}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const selectedCustomer: CustomerItem | null =
    customersList.find((c) => c.id === selectedCustomerId) || customersList[0] || null

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    setCopySuccess(label)
    setTimeout(() => setCopySuccess(null), 2000)
  }

  const handleMergeCustomers = async () => {
    if (!selectedCustomer || !secondaryCrmId.trim()) return
    if (secondaryCrmId.trim() === selectedCustomer.id) {
      showToast('Không thể gộp khách hàng với chính mình', 'error')
      return
    }
    setIsMerging(true)
    try {
      const res = await api.mergeCustomers(selectedCustomer.id, secondaryCrmId.trim())
      if (res?.ok) {
        showToast(`Đã gộp hồ sơ ${secondaryCrmId.trim()} vào ${selectedCustomer.name} thành công!`, 'success')
        setShowMergeModal(false)
        setSecondaryCrmId('')
        loadCustomers()
      } else {
        showToast('Gộp hồ sơ không thành công', 'error')
      }
    } catch (err: any) {
      showToast(`Lỗi gộp hồ sơ: ${err?.message || 'Lỗi mạng'}`, 'error')
    } finally {
      setIsMerging(false)
    }
  }

  const handleCreateCustomerTask = async () => {
    if (!selectedCustomer) return
    try {
      const res = await api.handoffToStaff({
        title: `Chăm sóc khách hàng CRM: ${selectedCustomer.name}`,
        intent: selectedCustomer.notes || selectedCustomer.snippet || 'Theo dõi và chăm sóc khách hàng',
        priority: selectedCustomer.status === 'Lead nóng' ? 1 : 2,
        comment_id: selectedCustomer.id,
      })
      if (res?.ok) {
        showToast(`Đã tạo nhiệm vụ #${res.task_id || ''} trên Kanban thành công!`, 'success')
      } else {
        showToast(`Đã tạo nhiệm vụ chăm sóc cho ${selectedCustomer.name} trên Kanban`, 'success')
      }
    } catch (err: any) {
      showToast(`Lỗi tạo việc: ${err?.message || 'Lỗi mạng'}`, 'error')
    }
  }

  const handleCallCustomer = (phone: string, name: string) => {
    if (!phone || phone === 'Chưa có SĐT' || phone === 'Chưa có') {
      showToast(`Khách hàng ${name} chưa để lại số điện thoại`, 'info')
      return
    }
    if (phone.includes('*')) {
      showToast('Số điện thoại đang được bảo vệ quyền riêng tư theo phân quyền.', 'info')
      return
    }
    window.location.href = `tel:${phone.replace(/\s+/g, '')}`
  }

  const handleAddTag = () => {
    if (!newTagInput.trim() || !selectedCustomer) return
    const tagText = newTagInput.trim()
    setCustomersList((prev) =>
      prev.map((c) => {
        if (c.id === selectedCustomer.id) {
          const updatedTags = [...(c.tagsList || []), tagText]
          return { ...c, tagsList: updatedTags }
        }
        return c
      })
    )
    setNewTagInput('')
    setIsAddingTag(false)
    showToast(`Đã thêm tag "${tagText}" cho ${selectedCustomer.name}`, 'success')
  }


  // Source badges config
  const sourceIcons = {
    Facebook: { icon: <FacebookIcon className="w-3.5 h-3.5 text-[#1877F2]" />, label: 'Facebook' },
    Messenger: { icon: <MessengerIcon className="w-3.5 h-3.5 text-[#0084FF]" />, label: 'Messenger' },
    TikTok: { icon: <TikTokIcon className="w-3.5 h-3.5" colored />, label: 'TikTok' },
    Website: { icon: <Globe className="w-3.5 h-3.5 text-purple-600" />, label: 'Website' },
  }

  const tagColors = {
    blue: 'bg-blue-50 text-blue-600 border border-blue-200',
    purple: 'bg-purple-50 text-purple-600 border border-purple-200',
    amber: 'bg-amber-50 text-amber-600 border border-amber-200',
    rose: 'bg-rose-50 text-rose-600 border border-rose-200',
    green: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
    slate: 'bg-slate-50 text-slate-600 border border-slate-200',
  }

  const statusBadges = {
    'Đang tư vấn': 'bg-blue-50 text-blue-700 border border-blue-200',
    'Đã mua': 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    'Lead nóng': 'bg-rose-50 text-rose-700 border border-rose-200',
    'Khiếu nại': 'bg-amber-50 text-amber-700 border border-amber-200',
  }

  // Filter customers
  const filteredCustomers = customersList.filter((c) => {
    if (statusFilter !== 'all' && c.status !== statusFilter) return false
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      return (
        c.name.toLowerCase().includes(q) ||
        c.phone.toLowerCase().includes(q) ||
        (c.fbId && c.fbId.includes(q))
      )
    }
    return true
  })

  // Real KPIs calculations
  const totalCustomersCount = customersList.length
  const leadsWithPhoneCount = customersList.filter((c) => c.phone && c.phone !== 'Chưa có SĐT').length
  const consultingCount = customersList.filter((c) => c.status === 'Đang tư vấn').length
  const boughtCount = customersList.filter((c) => c.status === 'Đã mua' || c.status === 'Lead nóng').length

  return (
    <div className="space-y-5 animate-fade-in">
      {/* ================= HEADER & SEARCH / FILTER TOOLBAR ================= */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Khách hàng CRM</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Quản lý hồ sơ khách hàng thật đồng bộ trực tiếp từ Fanpage ({totalCustomersCount} khách hàng).
          </p>
          {pollNotice && (
            <div className="mt-1 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-lg inline-flex items-center gap-1.5 animate-fade-in">
              <RefreshCw className={`w-3 h-3 ${isPolling ? 'animate-spin' : ''}`} />
              <span>{pollNotice}</span>
            </div>
          )}
        </div>

        {/* Controls Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Sync Fanpage Button */}
          <button
            type="button"
            onClick={handlePollNow}
            disabled={isPolling}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm shadow-blue-200 disabled:opacity-60 cursor-pointer"
            title="Đồng bộ khách hàng và tin nhắn mới nhất trực tiếp từ Facebook Fanpage"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin' : ''}`} />
            <span>{isPolling ? 'Đang kéo...' : 'Đồng bộ Fanpage'}</span>
          </button>

          {/* Backfill CRM Button */}
          <button
            type="button"
            onClick={handleBackfill}
            disabled={isPolling}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-xs font-semibold transition-all shadow-2xs disabled:opacity-60 cursor-pointer"
            title="Quét lại toàn bộ lịch sử tin nhắn & bình luận để cập nhật hồ sơ CRM"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Tổng hợp CRM</span>
          </button>
        </div>
      </div>

      {toastMessage && (
        <div className={`p-3 rounded-xl text-xs font-semibold flex items-center justify-between animate-fade-in ${
          toastMessage.type === 'error'
            ? 'bg-rose-50 text-rose-700 border border-rose-200'
            : toastMessage.type === 'success'
            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            : 'bg-blue-50 text-blue-700 border border-blue-200'
        }`}>
          <span>{toastMessage.text}</span>
          <button type="button" onClick={() => setToastMessage(null)} className="text-slate-400 hover:text-slate-600 ml-2 cursor-pointer font-bold">×</button>
        </div>
      )}

      {/* Toolbar filters */}
      <div className="flex flex-wrap items-center justify-between gap-3">


          {/* Search box */}
          <div className="relative w-64 sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm theo tên, SĐT, Facebook ID..."
              className="w-full bg-white border border-slate-200 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-2xs"
            />
          </div>

          {/* Quick filter pills */}
          <div className="flex items-center space-x-1 bg-white p-1 rounded-xl border border-slate-200 shadow-2xs text-xs">
            {[
              { id: 'all', label: 'Tất cả' },
              { id: 'Lead nóng', label: 'Lead nóng' },
              { id: 'Đang tư vấn', label: 'Đang tư vấn' },
              { id: 'Đã mua', label: 'Đã mua' },
              { id: 'Khiếu nại', label: 'Khiếu nại' },
            ].map((st) => (
              <button
                key={st.id}
                type="button"
                onClick={() => setStatusFilter(st.id)}
                className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                  statusFilter === st.id
                    ? 'bg-blue-600 text-white font-bold shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>

          {/* Export Excel / CSV */}
          <button
            type="button"
            onClick={handleExportCSV}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-700 text-xs font-semibold hover:bg-slate-50 shadow-2xs transition-colors cursor-pointer"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
            <span>Xuất CSV</span>
          </button>
        </div>

      {/* ================= 4 KPI CARDS ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {/* Card 1: Tổng khách hàng */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Tổng khách hàng</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">{totalCustomersCount}</div>
            <div className="flex items-center space-x-1 text-[11px] text-emerald-600 font-semibold mt-1">
              <span>Đồng bộ từ Fanpage</span>
            </div>
          </div>
          <div className="w-11 h-11 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Users className="w-5 h-5" />
          </div>
        </div>

        {/* Card 2: Lead có SĐT */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Lead có SĐT</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">{leadsWithPhoneCount}</div>
            <div className="flex items-center space-x-1 text-[11px] text-emerald-600 font-semibold mt-1">
              <span>Đã thu thập SĐT</span>
            </div>
          </div>
          <div className="w-11 h-11 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Phone className="w-5 h-5" />
          </div>
        </div>

        {/* Card 3: Đang tư vấn */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Đang tư vấn</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">{consultingCount}</div>
            <div className="flex items-center space-x-1 text-[11px] text-orange-600 font-semibold mt-1">
              <span>Hội thoại đang mở</span>
            </div>
          </div>
          <div className="w-11 h-11 rounded-2xl bg-orange-50 text-orange-600 flex items-center justify-center">
            <MessageCircle className="w-5 h-5" />
          </div>
        </div>

        {/* Card 4: Lead nóng / Đã mua */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Lead nóng & Đã mua</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">{boughtCount}</div>
            <div className="flex items-center space-x-1 text-[11px] text-teal-600 font-semibold mt-1">
              <span>Cần chăm sóc chốt đơn</span>
            </div>
          </div>
          <div className="w-11 h-11 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* ================= 3-COLUMN MAIN LAYOUT ================= */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
        {/* ================= COL 1: DANH SÁCH KHÁCH HÀNG (5 cols) ================= */}
        <div className="xl:col-span-5 bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex flex-col justify-between min-h-[780px]">
          <div>
            {/* Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <h3 className="text-sm font-bold text-slate-900">
                Danh sách khách hàng ({filteredCustomers.length})
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  className="flex items-center space-x-1 text-xs text-slate-600 hover:text-slate-900 px-2 py-1 rounded-lg border border-slate-200"
                >
                  <span>Mới nhất</span>
                  <ChevronDown className="w-3 h-3 text-slate-400" />
                </button>
                <button
                  type="button"
                  className="flex items-center space-x-1 text-xs text-slate-600 hover:text-slate-900 px-2.5 py-1 rounded-lg border border-slate-200"
                >
                  <Filter className="w-3 h-3 text-slate-400" />
                  <span>Bộ lọc</span>
                </button>
              </div>
            </div>

            {/* Customers Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="text-[11px] text-slate-400 font-bold border-b border-slate-100">
                  <tr>
                    <th className="py-2 px-1 w-6">
                      <input type="checkbox" className="rounded border-slate-300 text-blue-600" />
                    </th>
                    <th className="py-2 px-2">Khách hàng</th>
                    <th className="py-2 px-2">SĐT</th>
                    <th className="py-2 px-2">Nguồn</th>
                    <th className="py-2 px-2">Tag</th>
                    <th className="py-2 px-2">Trạng thái</th>
                    <th className="py-2 px-2">Lần cuối</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {filteredCustomers.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-12 text-center text-slate-400">
                        <Users className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                        <p className="font-semibold text-slate-600 mb-1">
                          Chưa có hội thoại/nháp. Hãy kết nối Facebook Pages hoặc bấm Quét ngay.
                        </p>
                        <button
                          type="button"
                          onClick={handlePollNow}
                          disabled={isPolling}
                          className="mt-2 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
                        >
                          <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin' : ''}`} />
                          <span>{isPolling ? 'Đang quét...' : 'Quét ngay'}</span>
                        </button>
                      </td>
                    </tr>
                  ) : (
                    filteredCustomers.map((cust) => {
                      const isSelected = cust.id === selectedCustomer?.id
                      return (
                        <tr
                          key={cust.id}
                          onClick={() => setSelectedCustomerId(cust.id)}
                          className={`cursor-pointer transition-colors ${
                            isSelected
                              ? 'bg-blue-50/80 font-semibold'
                              : 'hover:bg-slate-50/80'
                          }`}
                        >
                          <td className="py-2.5 px-1" onClick={(e) => e.stopPropagation()}>
                            <input type="checkbox" className="rounded border-slate-300 text-blue-600" />
                          </td>
                          <td className="py-2.5 px-2">
                            <div className="flex items-center space-x-2">
                              <img
                                src={cust.avatar}
                                alt={cust.name}
                                className="w-7 h-7 rounded-full object-cover ring-1 ring-slate-200 shrink-0"
                              />
                              <div className="truncate max-w-[110px]">
                                <div className="font-bold text-slate-900 truncate leading-tight">
                                  {cust.name}
                                </div>
                                <div className="text-[10px] text-slate-400 truncate">
                                  {cust.snippet}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="py-2.5 px-2 text-slate-700 whitespace-nowrap text-[11px]">
                            <span>{cust.phone}</span>
                            {cust.phone?.includes('*') && (
                              <span className="ml-1 px-1 py-0.2 rounded bg-amber-50 text-amber-600 text-[9px] font-semibold border border-amber-100">
                                Che
                              </span>
                            )}
                          </td>
                          <td className="py-2.5 px-2 whitespace-nowrap">
                            <span className="inline-flex items-center space-x-1.5 text-[11px] font-medium text-slate-700">
                              {cust.source === 'Facebook' && <FacebookIcon className="w-3.5 h-3.5 text-[#1877F2]" />}
                              {cust.source === 'Messenger' && <MessengerIcon className="w-3.5 h-3.5 text-[#0084FF]" />}
                              {cust.source === 'TikTok' && <TikTokIcon className="w-3.5 h-3.5" colored />}
                              {cust.source === 'Website' && <Globe className="w-3.5 h-3.5 text-purple-600" />}
                              <span>{cust.source}</span>
                            </span>
                          </td>
                          <td className="py-2.5 px-2 whitespace-nowrap">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${tagColors[cust.tagColor]}`}>
                              {cust.tag}
                            </span>
                          </td>
                          <td className="py-2.5 px-2 whitespace-nowrap">
                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${statusBadges[cust.status] || 'bg-slate-50 text-slate-700 border border-slate-200'}`}>
                              {cust.status}
                            </span>
                          </td>
                          <td className="py-2.5 px-2 text-[11px] text-slate-400 whitespace-nowrap">
                            {cust.lastInteraction}
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs text-slate-500 mt-2">
            <span>Hiển thị {filteredCustomers.length > 0 ? 1 : 0} - {filteredCustomers.length} trong {customersList.length} khách hàng</span>
            <div className="flex items-center space-x-1">
              <button type="button" className="p-1 rounded hover:bg-slate-100 text-slate-400">
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <button type="button" className="w-6 h-6 rounded bg-blue-600 text-white font-bold text-xs flex items-center justify-center">
                1
              </button>
              <button type="button" className="p-1 rounded hover:bg-slate-100 text-slate-400">
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* ================= COL 2: HỒ SƠ KHÁCH HÀNG (4 cols) ================= */}
        <div className="xl:col-span-4 bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs space-y-4 min-h-[780px]">
          {!selectedCustomer ? (
            <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-center p-6 text-slate-400">
              <Users className="w-12 h-12 text-slate-300 mb-3" />
              <h4 className="text-sm font-bold text-slate-700">Chưa có khách hàng</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-xs">
                Chưa có hội thoại/nháp. Hãy kết nối Facebook Pages hoặc bấm Quét ngay.
              </p>
              <button
                type="button"
                onClick={handlePollNow}
                disabled={isPolling}
                className="mt-4 inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin' : ''}`} />
                <span>{isPolling ? 'Đang quét...' : 'Quét ngay'}</span>
              </button>
            </div>
          ) : (
            <>
              {/* Header */}
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <h3 className="text-sm font-bold text-slate-900">Hồ sơ khách hàng</h3>
                <div className="flex items-center space-x-1.5">
                  {can('merge_crm') && (
                    <button
                      type="button"
                      onClick={() => setShowMergeModal(!showMergeModal)}
                      className="flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-indigo-200 text-indigo-700 text-xs font-semibold hover:bg-indigo-50 transition-colors cursor-pointer"
                      title="Gộp hồ sơ khách hàng trùng lặp qua api.mergeCustomers"
                    >
                      <Share2 className="w-3 h-3 text-indigo-500" />
                      <span>{showMergeModal ? 'Đóng' : 'Gộp hồ sơ'}</span>
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => showToast(`Đang mở chỉnh sửa hồ sơ ${selectedCustomer.name}`, 'info')}
                    className="flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors cursor-pointer"
                  >
                    <Pencil className="w-3 h-3 text-slate-400" />
                    <span>Chỉnh sửa</span>
                  </button>
                  {can('delete_crm') && (
                    confirmDelete ? (
                      <div className="flex items-center space-x-1">
                        <button
                          type="button"
                          onClick={() => {
                            api.deleteCustomer(selectedCustomer.id)
                              .then(() => {
                                showToast(`Đã xóa khách hàng ${selectedCustomer.name}`, 'success')
                                setConfirmDelete(false)
                                loadCustomers()
                              })
                              .catch((err) => showToast(err?.message || 'Lỗi khi xóa', 'error'))
                          }}
                          className="px-2 py-1 rounded-lg bg-rose-600 text-white text-xs font-semibold hover:bg-rose-700 transition-colors cursor-pointer"
                        >
                          Xác nhận
                        </button>
                        <button
                          type="button"
                          onClick={() => setConfirmDelete(false)}
                          className="px-2 py-1 rounded-lg border border-slate-200 text-slate-600 text-xs font-semibold hover:bg-slate-50 transition-colors cursor-pointer"
                        >
                          Hủy
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={() => setConfirmDelete(true)}
                        className="px-2 py-1 rounded-lg border border-rose-200 text-rose-600 text-xs font-semibold hover:bg-rose-50 transition-colors cursor-pointer"
                        title="Xóa khách hàng"
                      >
                        Xóa
                      </button>
                    )
                  )}
                </div>
              </div>

              {/* Merge Drawer / Form */}
              {showMergeModal && (
                <div className="p-3 bg-indigo-50/70 border border-indigo-200 rounded-xl space-y-2 animate-fade-in">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-900">Gộp hồ sơ vào {selectedCustomer.name}</span>
                    <button
                      type="button"
                      onClick={() => setShowMergeModal(false)}
                      className="text-slate-400 hover:text-slate-600 text-xs font-bold cursor-pointer"
                    >
                      ×
                    </button>
                  </div>
                  <p className="text-[11px] text-indigo-700 leading-snug">
                    Nhập mã CRM phụ (Secondary CRM ID) cần gộp vào khách hàng chính này. Toàn bộ định danh và lịch sử sẽ được chuyển sang {selectedCustomer.id}.
                  </p>
                  <div className="flex items-center gap-1.5">
                    <input
                      type="text"
                      value={secondaryCrmId}
                      onChange={(e) => setSecondaryCrmId(e.target.value)}
                      placeholder="Nhập CRM ID phụ (ví dụ: c_123456)..."
                      className="flex-1 bg-white border border-indigo-200 rounded-lg px-2.5 py-1 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                    <button
                      type="button"
                      disabled={isMerging || !secondaryCrmId.trim()}
                      onClick={handleMergeCustomers}
                      className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer whitespace-nowrap"
                    >
                      {isMerging ? 'Đang gộp...' : 'Gộp ngay'}
                    </button>
                  </div>
                </div>
              )}

              {/* Customer Avatar & Hero */}
              <div className="flex items-center space-x-3">
                <img
                  src={selectedCustomer.avatar}
                  alt={selectedCustomer.name}
                  className="w-12 h-12 rounded-full object-cover ring-2 ring-white shadow-2xs"
                />
                <div>
                  <div className="flex items-center space-x-1.5">
                    <h4 className="text-base font-bold text-slate-900 leading-tight">
                      {selectedCustomer.name}
                    </h4>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                      selectedCustomer.status === 'Lead nóng'
                        ? 'bg-rose-50 text-rose-600 border-rose-200'
                        : selectedCustomer.status === 'Đã mua'
                        ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                        : 'bg-blue-50 text-blue-600 border-blue-200'
                    }`}>
                      {selectedCustomer.status}
                    </span>
                  </div>
                  <div className="flex items-center space-x-1 text-xs text-slate-400 font-mono mt-0.5">
                    <span>ID: {selectedCustomer.id}</span>
                    <button
                      type="button"
                      onClick={() => handleCopy(selectedCustomer.id, 'ID')}
                      className="hover:text-blue-600 p-0.5"
                    >
                      <Copy className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Customer Detail Fields */}
              <div className="space-y-2 text-xs text-slate-600 pt-1 border-t border-slate-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span className="text-slate-500">SĐT:</span>
                    <span className="font-semibold text-slate-900">{selectedCustomer.phone}</span>
                    {selectedCustomer.phone?.includes('*') && (
                      <span className="px-1.5 py-0.2 rounded bg-amber-50 text-amber-600 border border-amber-200 text-[10px] font-semibold">
                        Đã che
                      </span>
                    )}
                  </div>
                  {selectedCustomer.phone && selectedCustomer.phone !== 'Chưa có SĐT' && !selectedCustomer.phone.includes('*') && (
                    <button
                      type="button"
                      onClick={() => handleCopy(selectedCustomer.phone, 'SĐT')}
                      className="text-slate-400 hover:text-blue-600 p-1 cursor-pointer"
                      title="Sao chép SĐT"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-slate-400 font-bold w-3.5 text-center">@</span>
                  <span className="text-slate-500">Nguồn đến:</span>
                  <span className="font-semibold text-slate-900">{selectedCustomer.source}</span>
                </div>

                <div className="flex items-center space-x-2">
                  <Building2 className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-slate-500">Khu vực / Page:</span>
                  <span className="font-semibold text-slate-900">{selectedCustomer.area || 'Fanpage'}</span>
                </div>

                <div className="flex items-center space-x-2">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-slate-500">Ngày cập nhật:</span>
                  <span className="font-semibold text-slate-900">
                    {selectedCustomer.createdDate || 'Hôm nay'}
                  </span>
                </div>

                <div className="pt-1">
                  <span className="text-slate-500 block mb-0.5">Ghi chú & Quan tâm:</span>
                  <div className="bg-slate-50 p-2 rounded-xl text-slate-700 leading-relaxed border border-slate-100 text-[11px]">
                    {selectedCustomer.notes || 'Khách hàng quan tâm dịch vụ trên Fanpage.'}
                  </div>
                </div>

                {/* Real Care Customer Details: Behavior & Identities & Markdown */}
                {customerDetail?.behavior && (
                  <div className="pt-2 border-t border-slate-100">
                    <span className="text-slate-500 font-medium block mb-1 text-[11px]">Hành vi tương tác (Fanpage Care):</span>
                    <div className="grid grid-cols-2 gap-1.5 text-[11px]">
                      <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                        <span className="text-slate-400 block text-[10px]">Giai đoạn</span>
                        <span className="font-bold text-slate-800 capitalize">{customerDetail.behavior.stage || 'Lead'}</span>
                      </div>
                      <div className="bg-slate-50 p-2 rounded-xl border border-slate-100">
                        <span className="text-slate-400 block text-[10px]">Tương tác</span>
                        <span className="font-bold text-slate-800">
                          {customerDetail.behavior.message_count || 0} tin nhắn · {customerDetail.behavior.comment_count || 0} bình luận
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {customerDetail?.identities && customerDetail.identities.length > 0 && (
                  <div className="pt-2 border-t border-slate-100">
                    <span className="text-slate-500 font-medium block mb-1.5 text-[11px]">Định danh liên kết ({customerDetail.identities.length}):</span>
                    <div className="space-y-1">
                      {customerDetail.identities.map((idObj: any, i: number) => (
                        <div key={i} className="flex items-center justify-between text-[11px] bg-slate-50 px-2 py-1 rounded-lg border border-slate-100">
                          <span className="font-mono text-slate-600 truncate max-w-[180px]">
                            {idObj.kind}: {idObj.ext_id}
                          </span>
                          <span className="text-[10px] text-slate-400">Page {idObj.page_id}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {customerDetail?.markdown && (
                  <div className="pt-2 border-t border-slate-100">
                    <span className="text-slate-500 font-medium block mb-1 text-[11px]">Hồ sơ Vault Markdown:</span>
                    <div className="bg-slate-50 p-2 rounded-xl border border-slate-100 text-[10px] font-mono text-slate-700 whitespace-pre-wrap max-h-32 overflow-y-auto">
                      {customerDetail.markdown}
                    </div>
                  </div>
                )}

                {/* Tags */}
                <div className="pt-2">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-slate-500 font-medium">Tag khách hàng:</span>
                    <button
                      type="button"
                      onClick={() => setIsAddingTag(!isAddingTag)}
                      className="text-blue-600 font-semibold text-[11px] hover:text-blue-700 flex items-center space-x-0.5 cursor-pointer"
                    >
                      <Plus className="w-3 h-3" />
                      <span>{isAddingTag ? 'Đóng' : 'Thêm tag'}</span>
                    </button>
                  </div>
                  {isAddingTag && (
                    <div className="flex items-center gap-1.5 mb-2">
                      <input
                        type="text"
                        value={newTagInput}
                        onChange={(e) => setNewTagInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            handleAddTag()
                          }
                        }}
                        placeholder="Nhập tên tag mới..."
                        className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        autoFocus
                      />
                      <button
                        type="button"
                        onClick={handleAddTag}
                        className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg cursor-pointer"
                      >
                        Lưu
                      </button>
                    </div>
                  )}
                  <div className="flex flex-wrap gap-1.5">
                    {(selectedCustomer.tagsList || ['Fanpage']).map((tg) => (
                      <span
                        key={tg}
                        className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-600 border border-blue-200"
                      >
                        {tg}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Quick Action Buttons */}
              <div className="grid grid-cols-4 gap-1.5 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => handleCallCustomer(selectedCustomer.phone, selectedCustomer.name)}
                  className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-bold shadow-sm transition-colors cursor-pointer"
                  title="Gọi khách (kiểm tra bảo mật SĐT)"
                >
                  <Phone className="w-3.5 h-3.5" />
                  <span>Gọi khách</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    window.location.hash = 'inbox'
                  }}
                  className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs cursor-pointer"
                  title="Mở tin nhắn hội thoại tại Inbox"
                >
                  <MessageCircle className="w-3.5 h-3.5 text-blue-600" />
                  <span>Nhắn tin</span>
                </button>
                <button
                  type="button"
                  onClick={handleCreateCustomerTask}
                  className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs cursor-pointer"
                  title="Tạo việc chăm sóc khách hàng vào Kanban qua api.handoffToStaff"
                >
                  <CheckSquare className="w-3.5 h-3.5 text-blue-600" />
                  <span>Tạo việc</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsAddingTag(true)}
                  className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs cursor-pointer"
                  title="Gắn tag phân loại khách hàng"
                >
                  <Tag className="w-3.5 h-3.5 text-blue-600" />
                  <span>Gắn tag</span>
                </button>
              </div>

              {/* Timeline: Lịch sử tương tác */}
              <div className="pt-2 border-t border-slate-100 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">Lịch sử tương tác</span>
                  <span className="text-[11px] font-medium text-slate-400">
                    Thời gian thực
                  </span>
                </div>

                <div className="space-y-3 relative pl-4 border-l-2 border-slate-100 text-xs">
                  {(selectedCustomer.timeline && selectedCustomer.timeline.length > 0) ? (
                    selectedCustomer.timeline.map((event, idx) => (
                      <div key={idx} className="relative group">
                        <span
                          className={`absolute -left-[21px] top-0.5 w-3 h-3 rounded-full ring-4 ring-white ${
                            event.type === 'customer'
                              ? 'bg-blue-500'
                              : event.type === 'ai'
                              ? 'bg-purple-500'
                              : event.type === 'staff'
                              ? 'bg-emerald-500'
                              : event.type === 'status'
                              ? 'bg-teal-500'
                              : 'bg-amber-500'
                          }`}
                        />
                        <div>
                          <div className="flex items-center justify-between font-bold text-slate-800 text-[11px]">
                            <span>{event.title}</span>
                          </div>
                          <p className="text-slate-600 text-[11px] mt-0.5 leading-relaxed">{event.content}</p>
                          {event.time && (
                            <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">{event.time}</span>
                          )}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-slate-400 text-xs py-2 italic">
                      Chưa có lịch sử tương tác ghi nhận.
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>


        {/* ================= COL 3: ANALYTICS & FOLLOW-UP (3 cols) ================= */}
        <div className="xl:col-span-3 space-y-4">
          {/* Card 1: Phân nhóm khách hàng (Donut Chart) */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900">Phân nhóm khách hàng</h3>
              <button
                type="button"
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-0.5"
              >
                <span>Xem chi tiết</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="flex items-center justify-between pt-1">
              {/* SVG Donut Chart */}
              <div className="relative w-28 h-28 flex items-center justify-center shrink-0">
                <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                  {/* Background track */}
                  <circle cx="18" cy="18" r="14" fill="none" stroke="#f1f5f9" strokeWidth="4" />
                  {/* Segment 1: Đã mua (26%) -> 26% of 88 = 22.88 */}
                  <circle
                    cx="18"
                    cy="18"
                    r="14"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="4"
                    strokeDasharray="22.88 88"
                    strokeDashoffset="0"
                  />
                  {/* Segment 2: Đang tư vấn (16%) -> 14.08 */}
                  <circle
                    cx="18"
                    cy="18"
                    r="14"
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="4"
                    strokeDasharray="14.08 88"
                    strokeDashoffset="-22.88"
                  />
                  {/* Segment 3: Lead nóng (15%) -> 13.2 */}
                  <circle
                    cx="18"
                    cy="18"
                    r="14"
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="4"
                    strokeDasharray="13.2 88"
                    strokeDashoffset="-36.96"
                  />
                  {/* Segment 4: Khách mới (24%) -> 21.12 */}
                  <circle
                    cx="18"
                    cy="18"
                    r="14"
                    fill="none"
                    stroke="#06b6d4"
                    strokeWidth="4"
                    strokeDasharray="21.12 88"
                    strokeDashoffset="-50.16"
                  />
                  {/* Segment 5: Khiếu nại (6%) -> 5.28 */}
                  <circle
                    cx="18"
                    cy="18"
                    r="14"
                    fill="none"
                    stroke="#eab308"
                    strokeWidth="4"
                    strokeDasharray="5.28 88"
                    strokeDashoffset="-71.28"
                  />
                  {/* Segment 6: Khác (11%) -> 9.68 */}
                  <circle
                    cx="18"
                    cy="18"
                    r="14"
                    fill="none"
                    stroke="#94a3b8"
                    strokeWidth="4"
                    strokeDasharray="9.68 88"
                    strokeDashoffset="-76.56"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-base font-black text-slate-900 leading-none">{totalCustomersCount}</span>
                  <span className="text-[9px] text-slate-400 font-medium mt-0.5">khách hàng</span>
                </div>
              </div>

              {/* Legend List */}
              <div className="space-y-1 text-[11px] text-slate-600 pl-2">
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-orange-500 shrink-0" />
                  <span>Lead nóng: <strong>{boughtCount} ({totalCustomersCount ? Math.round((boughtCount / totalCustomersCount) * 100) : 0}%)</strong></span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
                  <span>Đang tư vấn: <strong>{consultingCount} ({totalCustomersCount ? Math.round((consultingCount / totalCustomersCount) * 100) : 0}%)</strong></span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                  <span>Có SĐT: <strong>{leadsWithPhoneCount} ({totalCustomersCount ? Math.round((leadsWithPhoneCount / totalCustomersCount) * 100) : 0}%)</strong></span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-slate-400 shrink-0" />
                  <span>Khác: <strong>{Math.max(0, totalCustomersCount - boughtCount - consultingCount)}</strong></span>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Nguồn khách hàng (Bar Chart) */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900">Nguồn khách hàng</h3>
              <button
                type="button"
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-0.5"
              >
                <span>Xem chi tiết</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            {/* Vertical Bar Chart */}
            <div className="pt-2">
              <div className="h-32 flex items-end justify-between gap-3 px-2 border-b border-slate-200 pb-1">
                {/* Facebook: 238 (max ~ 300) -> 80% */}
                <div className="flex-1 flex flex-col items-center gap-1 group">
                  <span className="text-[10px] font-bold text-slate-700 group-hover:text-blue-600">238</span>
                  <div className="w-full bg-blue-600 rounded-t-lg transition-all group-hover:bg-blue-700 h-24" />
                </div>
                {/* Messenger: 142 -> 48% */}
                <div className="flex-1 flex flex-col items-center gap-1 group">
                  <span className="text-[10px] font-bold text-slate-700 group-hover:text-blue-500">142</span>
                  <div className="w-full bg-blue-500 rounded-t-lg transition-all group-hover:bg-blue-600 h-16" />
                </div>
                {/* TikTok: 126 -> 42% */}
                <div className="flex-1 flex flex-col items-center gap-1 group">
                  <span className="text-[10px] font-bold text-slate-700 group-hover:text-rose-600">126</span>
                  <div className="w-full bg-rose-500 rounded-t-lg transition-all group-hover:bg-rose-600 h-14" />
                </div>
                {/* Website: 54 -> 18% */}
                <div className="flex-1 flex flex-col items-center gap-1 group">
                  <span className="text-[10px] font-bold text-slate-700 group-hover:text-purple-600">54</span>
                  <div className="w-full bg-purple-500 rounded-t-lg transition-all group-hover:bg-purple-600 h-7" />
                </div>
              </div>

              {/* Labels */}
              <div className="flex justify-between gap-2 px-1 pt-2 text-[10px] text-slate-600 font-semibold">
                <span className="flex-1 flex items-center justify-center space-x-1 truncate">
                  <FacebookIcon className="w-3 h-3 text-[#1877F2]" />
                  <span>Facebook</span>
                </span>
                <span className="flex-1 flex items-center justify-center space-x-1 truncate">
                  <MessengerIcon className="w-3 h-3 text-[#0084FF]" />
                  <span>Messenger</span>
                </span>
                <span className="flex-1 flex items-center justify-center space-x-1 truncate">
                  <TikTokIcon className="w-3 h-3" colored />
                  <span>TikTok</span>
                </span>
                <span className="flex-1 flex items-center justify-center space-x-1 truncate">
                  <Globe className="w-3 h-3 text-purple-600" />
                  <span>Website</span>
                </span>
              </div>
            </div>
          </div>

          {/* Card 3: Khách cần follow-up hôm nay */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900">
                Khách cần follow-up ({customersList.length})
              </h3>
              <button
                type="button"
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-0.5"
              >
                <span>Xem tất cả</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-2.5">
              {customersList.slice(0, 5).map((item) => (
                <div
                  key={item.id}
                  onClick={() => setSelectedCustomerId(item.id)}
                  className="flex items-center justify-between p-2 rounded-xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100 cursor-pointer"
                >
                  <div className="flex items-center space-x-2">
                    <img
                      src={item.avatar}
                      alt={item.name}
                      className="w-8 h-8 rounded-full object-cover shrink-0 ring-1 ring-slate-200"
                    />
                    <div className="truncate max-w-[130px]">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-xs font-bold text-slate-900 truncate">
                          {item.name}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">{item.lastInteraction || 'Hôm nay'}</span>
                      </div>
                      <p className="text-[10px] text-slate-400 truncate">{item.snippet || 'Quan tâm tự vấn'}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5 shrink-0">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${tagColors[item.tagColor] || tagColors.blue}`}>
                      {item.tag}
                    </span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleCallCustomer(item.phone, item.name)
                      }}
                      className="p-1 rounded-lg text-blue-600 hover:bg-blue-50 transition-colors cursor-pointer"
                      title="Gọi khách"
                    >
                      <Phone className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
