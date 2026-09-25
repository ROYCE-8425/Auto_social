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
} from 'lucide-react'
import { api, CareCustomer } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useCareScope } from '../lib/scope'

interface MockCustomer {
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

const mockCustomersList: MockCustomer[] = [
  {
    id: 'c1',
    name: 'Nguyễn Thị Hoa',
    avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=120&auto=format&fit=crop&q=80',
    snippet: 'Sản phẩm này còn...',
    phone: '0967 123 456',
    source: 'Facebook',
    tag: 'Game',
    tagColor: 'blue',
    status: 'Đang tư vấn',
    statusColor: 'blue',
    lastInteraction: '14:28',
    fbId: '1000123456789',
    area: 'Hà Nội',
    createdDate: '10/04/2024 14:28',
    notes: 'Khách quan tâm gói Game, cần tư vấn chi tiết và báo giá.',
    tagsList: ['Game', 'VIP', 'Quan tâm'],
    timeline: [
      {
        type: 'customer',
        title: 'Khách hàng nhắn tin',
        content: 'Sản phẩm này còn hàng không ạ? Mình muốn tư vấn thêm về gói Game.',
      },
      {
        type: 'ai',
        title: 'Javis AI phản hồi',
        content: 'Đã gửi tin nhắn tự động giới thiệu sản phẩm và bảng giá.',
        action: 'Xem nội dung',
      },
      {
        type: 'staff',
        title: 'Nhân viên Trần Văn Minh phản hồi',
        content: 'Tư vấn chi tiết về gói Game, hẹn khách xem thêm ưu đãi.',
      },
      {
        type: 'status',
        title: 'Cập nhật trạng thái',
        content: 'Chuyển từ Khách mới → Đang tư vấn bởi Trần Văn Minh',
      },
      {
        type: 'note',
        title: 'Thêm ghi chú',
        content: 'Khách quan tâm, sẽ follow up lại vào ngày mai.',
      },
    ],
  },
  {
    id: 'c2',
    name: 'Trần Văn Minh',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80',
    snippet: 'Cảm ơn shop nhé!',
    phone: '0903 456 789',
    source: 'Messenger',
    tag: 'VIP',
    tagColor: 'purple',
    status: 'Đã mua',
    statusColor: 'green',
    lastInteraction: '13:46',
    fbId: '1000987654321',
    area: 'TP. Hồ Chí Minh',
    createdDate: '08/04/2024 10:15',
    notes: 'Khách hàng VIP, mua gói trọn năm. Đã hoàn tất thanh toán.',
    tagsList: ['VIP', 'Đã mua', 'Trung thành'],
  },
  {
    id: 'c3',
    name: 'Lê Quang Huy',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80',
    snippet: 'Khi nào có hàng lại v...',
    phone: 'Chưa có',
    source: 'TikTok',
    tag: 'Quan tâm',
    tagColor: 'amber',
    status: 'Lead nóng',
    statusColor: 'rose',
    lastInteraction: '11:20',
    area: 'Đà Nẵng',
    createdDate: '12/04/2024 09:30',
    notes: 'Hỏi về đợt nhập hàng tiếp theo trên TikTok live.',
    tagsList: ['Quan tâm', 'TikTok', 'Lead nóng'],
  },
  {
    id: 'c4',
    name: 'Phạm Thị Lan',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=120&auto=format&fit=crop&q=80',
    snippet: 'Dạ mình tư vấn thêm...',
    phone: '0987 654 321',
    source: 'Facebook',
    tag: 'Tư vấn',
    tagColor: 'blue',
    status: 'Đang tư vấn',
    statusColor: 'blue',
    lastInteraction: '10:37',
    fbId: '1000555666777',
    area: 'Hải Phòng',
    createdDate: '15/04/2024 14:10',
    notes: 'Cần tư vấn đặt mua 2 tài khoản cùng lúc.',
    tagsList: ['Tư vấn', 'Lead', 'Facebook'],
  },
  {
    id: 'c5',
    name: 'Hoàng Kim',
    avatar: 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=120&auto=format&fit=crop&q=80',
    snippet: 'Shop có hỗ trợ đổi tr...',
    phone: 'Chưa có',
    source: 'Website',
    tag: 'Cần hỗ trợ',
    tagColor: 'rose',
    status: 'Khiếu nại',
    statusColor: 'amber',
    lastInteraction: '09:12',
    area: 'Cần Thơ',
    createdDate: '18/04/2024 08:45',
    notes: 'Hỏi chính sách đổi trả hàng sau khi mua.',
    tagsList: ['Cần hỗ trợ', 'Khiếu nại'],
  },
  {
    id: 'c6',
    name: 'Đỗ Thu Hà',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80',
    snippet: 'Mình ở quận nào vạ...',
    phone: '0321 456 789',
    source: 'Messenger',
    tag: 'Game',
    tagColor: 'blue',
    status: 'Đang tư vấn',
    statusColor: 'blue',
    lastInteraction: 'Hôm qua',
    area: 'Hà Nội',
    createdDate: '19/04/2024 16:20',
    notes: 'Hỏi địa chỉ cửa hàng gần nhất để qua trải nghiệm.',
    tagsList: ['Game', 'Messenger'],
  },
  {
    id: 'c7',
    name: 'Nguyễn Anh Tuấn',
    avatar: 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=120&auto=format&fit=crop&q=80',
    snippet: 'Tư vấn gói bên mình...',
    phone: '0868 111 222',
    source: 'TikTok',
    tag: 'Khách cũ',
    tagColor: 'green',
    status: 'Đã mua',
    statusColor: 'green',
    lastInteraction: 'Hôm qua',
    area: 'Bình Dương',
    createdDate: '11/03/2024 11:00',
    notes: 'Khách cũ quay lại gia hạn gói dịch vụ.',
    tagsList: ['Khách cũ', 'Đã mua'],
  },
  {
    id: 'c8',
    name: 'Trần Mai Phương',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=120&auto=format&fit=crop&q=80',
    snippet: 'Cho mình hỏi về chi...',
    phone: '0976 333 888',
    source: 'Facebook',
    tag: 'Quan tâm',
    tagColor: 'amber',
    status: 'Đang tư vấn',
    statusColor: 'blue',
    lastInteraction: '21/04',
    area: 'Hà Nội',
    createdDate: '21/04/2024 15:30',
    notes: 'Hỏi chiết khấu khi mua số lượng lớn.',
    tagsList: ['Quan tâm', 'Tư vấn'],
  },
  {
    id: 'c9',
    name: 'Bùi Văn Nam',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=120&auto=format&fit=crop&q=80',
    snippet: 'Có khuyến mãi khôn...',
    phone: 'Chưa có',
    source: 'Website',
    tag: 'Tiềm năng',
    tagColor: 'purple',
    status: 'Lead nóng',
    statusColor: 'rose',
    lastInteraction: '21/04',
    area: 'Nam Định',
    createdDate: '21/04/2024 10:05',
    notes: 'Khách tìm hiểu voucher giảm giá tuần này.',
    tagsList: ['Tiềm năng', 'Website'],
  },
  {
    id: 'c10',
    name: 'Nguyễn Thị Hương',
    avatar: 'https://images.unsplash.com/photo-1548142813-c348350df52b?w=120&auto=format&fit=crop&q=80',
    snippet: 'Dạ mình nhận được r...',
    phone: '0909 222 333',
    source: 'Messenger',
    tag: 'Khách cũ',
    tagColor: 'green',
    status: 'Đã mua',
    statusColor: 'green',
    lastInteraction: '20/04',
    area: 'Đồng Nai',
    createdDate: '01/04/2024 13:40',
    notes: 'Đã nhận được mã code kích hoạt và xác nhận ok.',
    tagsList: ['Khách cũ', 'Đã mua'],
  },
]

export const Customers: React.FC = () => {
  const { role, can } = useAuth()
  const { scope, scopeBrand, scopePageId } = useCareScope()
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>('c1')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [copySuccess, setCopySuccess] = useState<string | null>(null)

  const selectedCustomer =
    mockCustomersList.find((c) => c.id === selectedCustomerId) || mockCustomersList[0]

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    setCopySuccess(label)
    setTimeout(() => setCopySuccess(null), 2000)
  }

  // Source badges config
  const sourceIcons = {
    Facebook: { icon: 'f', bg: 'text-blue-600', label: 'Facebook' },
    Messenger: { icon: 'M', bg: 'text-blue-500', label: 'Messenger' },
    TikTok: { icon: '🎵', bg: 'text-slate-900', label: 'TikTok' },
    Website: { icon: '🌐', bg: 'text-purple-600', label: 'Website' },
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
  const filteredCustomers = mockCustomersList.filter((c) => {
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

  return (
    <div className="space-y-5 animate-fade-in">
      {/* ================= HEADER & SEARCH / FILTER TOOLBAR ================= */}
      <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Khách hàng CRM</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Quản lý hồ sơ khách hàng, lead và lịch sử tương tác đa kênh.
          </p>
        </div>

        {/* Controls Toolbar */}
        <div className="flex flex-wrap items-center gap-2">
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

          {/* Brand select */}
          <div className="relative">
            <select className="appearance-none bg-white border border-slate-200 text-slate-700 rounded-xl px-3 py-1.5 pr-7 text-xs font-medium hover:bg-slate-50 shadow-2xs focus:outline-none cursor-pointer">
              <option>Tất cả thương hiệu</option>
              <option>Nhóm Game BSN</option>
              <option>Trung tâm Sao Việt</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Source select */}
          <div className="relative">
            <select className="appearance-none bg-white border border-slate-200 text-slate-700 rounded-xl px-3 py-1.5 pr-7 text-xs font-medium hover:bg-slate-50 shadow-2xs focus:outline-none cursor-pointer">
              <option>Tất cả nguồn</option>
              <option>Facebook</option>
              <option>Messenger</option>
              <option>TikTok</option>
              <option>Website</option>
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Export Excel */}
          <button
            type="button"
            onClick={() => alert('Đang xuất danh sách khách hàng ra Excel...')}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-700 text-xs font-semibold hover:bg-slate-50 shadow-2xs transition-colors"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
            <span>Xuất Excel</span>
          </button>

          {/* + Tạo khách hàng */}
          <button
            type="button"
            onClick={() => alert('Mở form tạo hồ sơ khách hàng mới')}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm shadow-blue-200"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Tạo khách hàng</span>
          </button>
        </div>
      </div>

      {/* ================= 4 KPI CARDS ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {/* Card 1: Tổng khách hàng */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Tổng khách hàng</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">582</div>
            <div className="flex items-center space-x-1 text-[11px] text-emerald-600 font-semibold mt-1">
              <span>↑ 12%</span>
              <span className="text-slate-400 font-normal">so với tháng trước</span>
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
            <div className="text-2xl font-black text-slate-900 mt-0.5">431</div>
            <div className="flex items-center space-x-1 text-[11px] text-emerald-600 font-semibold mt-1">
              <span>↑ 8%</span>
              <span className="text-slate-400 font-normal">so với tháng trước</span>
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
            <div className="text-2xl font-black text-slate-900 mt-0.5">96</div>
            <div className="flex items-center space-x-1 text-[11px] text-emerald-600 font-semibold mt-1">
              <span>↑ 24%</span>
              <span className="text-slate-400 font-normal">so với tháng trước</span>
            </div>
          </div>
          <div className="w-11 h-11 rounded-2xl bg-orange-50 text-orange-600 flex items-center justify-center">
            <MessageCircle className="w-5 h-5" />
          </div>
        </div>

        {/* Card 4: Đã mua */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Đã mua</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">156</div>
            <div className="flex items-center space-x-1 text-[11px] text-emerald-600 font-semibold mt-1">
              <span>↑ 18%</span>
              <span className="text-slate-400 font-normal">so với tháng trước</span>
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
                  {filteredCustomers.map((cust) => {
                    const isSelected = cust.id === selectedCustomer.id
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
                          {cust.phone}
                        </td>
                        <td className="py-2.5 px-2 whitespace-nowrap">
                          <span className="inline-flex items-center space-x-1 text-[11px] text-slate-700">
                            {cust.source === 'Facebook' && <span className="font-bold text-blue-600">f</span>}
                            {cust.source === 'Messenger' && <span className="font-bold text-blue-500">M</span>}
                            {cust.source === 'TikTok' && <span>🎵</span>}
                            {cust.source === 'Website' && <Globe className="w-3 h-3 text-purple-600" />}
                            <span>{cust.source}</span>
                          </span>
                        </td>
                        <td className="py-2.5 px-2 whitespace-nowrap">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${tagColors[cust.tagColor]}`}>
                            {cust.tag}
                          </span>
                        </td>
                        <td className="py-2.5 px-2 whitespace-nowrap">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${statusBadges[cust.status]}`}>
                            {cust.status}
                          </span>
                        </td>
                        <td className="py-2.5 px-2 text-[11px] text-slate-400 whitespace-nowrap">
                          {cust.lastInteraction}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination Footer */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs text-slate-500 mt-2">
            <span>Hiển thị 1 - 10 trong 582 khách hàng</span>
            <div className="flex items-center space-x-1">
              <button type="button" className="p-1 rounded hover:bg-slate-100 text-slate-400">
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <button type="button" className="w-6 h-6 rounded bg-blue-600 text-white font-bold text-xs flex items-center justify-center">
                1
              </button>
              <button type="button" className="w-6 h-6 rounded hover:bg-slate-100 text-xs">
                2
              </button>
              <button type="button" className="w-6 h-6 rounded hover:bg-slate-100 text-xs">
                3
              </button>
              <button type="button" className="w-6 h-6 rounded hover:bg-slate-100 text-xs">
                4
              </button>
              <button type="button" className="w-6 h-6 rounded hover:bg-slate-100 text-xs">
                5
              </button>
              <span className="text-slate-400 px-1">...</span>
              <button type="button" className="w-6 h-6 rounded hover:bg-slate-100 text-xs">
                59
              </button>
              <button type="button" className="p-1 rounded hover:bg-slate-100 text-slate-400">
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* ================= COL 2: HỒ SƠ KHÁCH HÀNG (4 cols) ================= */}
        <div className="xl:col-span-4 bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs space-y-4 min-h-[780px]">
          {/* Header */}
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900">Hồ sơ khách hàng</h3>
            <div className="flex items-center space-x-1.5">
              <button
                type="button"
                className="flex items-center space-x-1 px-2.5 py-1 rounded-lg border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors"
              >
                <Pencil className="w-3 h-3 text-slate-400" />
                <span>Chỉnh sửa</span>
              </button>
              <button type="button" className="p-1 text-slate-400 hover:text-slate-700 rounded-lg">
                <MoreVertical className="w-4 h-4" />
              </button>
            </div>
          </div>

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
                <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-600 border border-rose-200 text-[10px] font-semibold">
                  Lead nóng
                </span>
                <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200 text-[10px] font-semibold">
                  Khách mới
                </span>
              </div>
              <div className="flex items-center space-x-1 text-xs text-slate-400 font-mono mt-0.5">
                <span>ID Facebook: {selectedCustomer.fbId || '1000123456789'}</span>
                <button
                  type="button"
                  onClick={() => handleCopy(selectedCustomer.fbId || '1000123456789', 'FB ID')}
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
              </div>
              <button
                type="button"
                onClick={() => handleCopy(selectedCustomer.phone, 'SĐT')}
                className="text-slate-400 hover:text-blue-600 p-1"
              >
                <Copy className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-slate-400 font-bold w-3.5 text-center">@</span>
              <span className="text-slate-500">Nguồn đến:</span>
              <span className="font-semibold text-slate-900">{selectedCustomer.source}</span>
              <span className="text-blue-600 text-[11px] cursor-pointer hover:underline">
                Xem trang
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <Building2 className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-500">Khu vực:</span>
              <span className="font-semibold text-slate-900">{selectedCustomer.area || 'Hà Nội'}</span>
            </div>

            <div className="flex items-center space-x-2">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-500">Ngày tạo:</span>
              <span className="font-semibold text-slate-900">
                {selectedCustomer.createdDate || '10/04/2024 14:28'}
              </span>
            </div>

            <div className="pt-1">
              <span className="text-slate-500 block mb-0.5">Ghi chú:</span>
              <div className="bg-slate-50 p-2 rounded-xl text-slate-700 leading-relaxed border border-slate-100 text-[11px]">
                {selectedCustomer.notes || 'Khách quan tâm gói Game, cần tư vấn chi tiết và báo giá.'}
              </div>
            </div>

            {/* Tags */}
            <div className="pt-2">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-slate-500 font-medium">Tag khách hàng:</span>
                <button
                  type="button"
                  className="text-blue-600 font-semibold text-[11px] hover:text-blue-700 flex items-center space-x-0.5"
                >
                  <Plus className="w-3 h-3" />
                  <span>Thêm tag</span>
                </button>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {(selectedCustomer.tagsList || ['Game', 'VIP', 'Quan tâm']).map((tg) => (
                  <span
                    key={tg}
                    className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-600 border border-blue-200"
                  >
                    {tg}
                  </span>
                ))}
              </div>
            </div>

            {/* Status Dropdown */}
            <div className="pt-2">
              <span className="text-slate-500 font-medium block mb-1">Trạng thái khách hàng:</span>
              <select className="w-full bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-semibold text-blue-700 focus:outline-none">
                <option>● Đang tư vấn</option>
                <option>● Lead nóng</option>
                <option>● Đã mua</option>
                <option>● Khiếu nại</option>
              </select>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="grid grid-cols-4 gap-1.5 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={() => alert(`Đang gọi đến số ${selectedCustomer.phone}...`)}
              className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-[11px] font-bold shadow-sm transition-colors"
            >
              <Phone className="w-3.5 h-3.5" />
              <span>Gọi khách</span>
            </button>
            <button
              type="button"
              onClick={() => alert('Chuyển sang khung chat với khách...')}
              className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs"
            >
              <MessageCircle className="w-3.5 h-3.5 text-blue-600" />
              <span>Nhắn tin</span>
            </button>
            <button
              type="button"
              onClick={() => alert('Đã tạo việc cần làm trên Kanban!')}
              className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs"
            >
              <CheckSquare className="w-3.5 h-3.5 text-blue-600" />
              <span>Tạo việc</span>
            </button>
            <button
              type="button"
              onClick={() => alert('Gắn tag mới')}
              className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs"
            >
              <Tag className="w-3.5 h-3.5 text-blue-600" />
              <span>Gắn tag</span>
            </button>
          </div>

          {/* Timeline: Lịch sử tương tác */}
          <div className="pt-2 border-t border-slate-100 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-900">Lịch sử tương tác</span>
              <button
                type="button"
                className="text-[11px] font-medium text-slate-500 hover:text-slate-800 flex items-center space-x-0.5"
              >
                <span>Tất cả</span>
                <ChevronDown className="w-3 h-3 text-slate-400" />
              </button>
            </div>

            <div className="space-y-3 relative pl-4 border-l-2 border-slate-100 text-xs">
              {(selectedCustomer.timeline || [
                {
                  type: 'customer',
                  title: 'Khách hàng nhắn tin',
                  content: 'Sản phẩm này còn hàng không ạ? Mình muốn tư vấn thêm về gói Game.',
                },
                {
                  type: 'ai',
                  title: 'Javis AI phản hồi',
                  content: 'Đã gửi tin nhắn tự động giới thiệu sản phẩm và bảng giá.',
                  action: 'Xem nội dung',
                },
                {
                  type: 'staff',
                  title: 'Nhân viên Trần Văn Minh phản hồi',
                  content: 'Tư vấn chi tiết về gói Game, hẹn khách xem thêm ưu đãi.',
                },
                {
                  type: 'status',
                  title: 'Cập nhật trạng thái',
                  content: 'Chuyển từ Khách mới → Đang tư vấn bởi Trần Văn Minh',
                },
                {
                  type: 'note',
                  title: 'Thêm ghi chú',
                  content: 'Khách quan tâm, sẽ follow up lại vào ngày mai.',
                },
              ]).map((event, idx) => (
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
                      {event.action && (
                        <button type="button" className="text-blue-600 hover:underline font-semibold text-[10px]">
                          {event.action}
                        </button>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">
                      {event.content}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
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
                  <span className="text-base font-black text-slate-900 leading-none">582</span>
                  <span className="text-[9px] text-slate-400 font-medium mt-0.5">khách hàng</span>
                </div>
              </div>

              {/* Legend List */}
              <div className="space-y-1 text-[11px] text-slate-600 pl-2">
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                  <span>Đã mua: <strong>156 (26%)</strong></span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
                  <span>Đang tư vấn: <strong>96 (16%)</strong></span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-orange-500 shrink-0" />
                  <span>Lead nóng: <strong>88 (15%)</strong></span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-cyan-500 shrink-0" />
                  <span>Khách mới: <strong>142 (24%)</strong></span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-yellow-500 shrink-0" />
                  <span>Khiếu nại: <strong>36 (6%)</strong></span>
                </div>
                <div className="flex items-center space-x-1.5">
                  <span className="w-2 h-2 rounded-full bg-slate-400 shrink-0" />
                  <span>Khác: <strong>64 (11%)</strong></span>
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
              <div className="flex justify-between gap-3 px-2 pt-2 text-[10px] text-slate-600 font-semibold">
                <span className="flex-1 text-center truncate">f Facebook</span>
                <span className="flex-1 text-center truncate">M Messenger</span>
                <span className="flex-1 text-center truncate">🎵 TikTok</span>
                <span className="flex-1 text-center truncate">🌐 Website</span>
              </div>
            </div>
          </div>

          {/* Card 3: Khách cần follow-up hôm nay (12) */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-900">
                Khách cần follow-up hôm nay (12)
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
              {[
                {
                  name: 'Trần Thị Mai',
                  avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=80&auto=format&fit=crop&q=80',
                  time: '09:00',
                  note: 'Khách đã xem báo giá, cần follow up',
                  tag: 'Lead nóng',
                  tagColor: 'bg-rose-50 text-rose-600 border-rose-200',
                },
                {
                  name: 'Lê Hoàng Nam',
                  avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&auto=format&fit=crop&q=80',
                  time: '10:30',
                  note: 'Hẹn tư vấn qua điện thoại',
                  tag: 'Đang tư vấn',
                  tagColor: 'bg-blue-50 text-blue-600 border-blue-200',
                },
                {
                  name: 'Phạm Minh Tú',
                  avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&auto=format&fit=crop&q=80',
                  time: '14:00',
                  note: 'Chưa phản hồi sau 1 ngày',
                  tag: 'Quan tâm',
                  tagColor: 'bg-amber-50 text-amber-600 border-amber-200',
                },
                {
                  name: 'Hoàng Anh Khoa',
                  avatar: 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=80&auto=format&fit=crop&q=80',
                  time: '15:30',
                  note: 'Gửi thêm thông tin sản phẩm',
                  tag: 'Khách mới',
                  tagColor: 'bg-cyan-50 text-cyan-600 border-cyan-200',
                },
                {
                  name: 'Đặng Thu Trang',
                  avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=80&auto=format&fit=crop&q=80',
                  time: '16:00',
                  note: 'Nhắc lịch hẹn demo',
                  tag: 'Tư vấn',
                  tagColor: 'bg-blue-50 text-blue-600 border-blue-200',
                },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 rounded-xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100"
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
                        <span className="text-[10px] text-slate-400 font-mono">{item.time}</span>
                      </div>
                      <p className="text-[10px] text-slate-400 truncate">{item.note}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5 shrink-0">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${item.tagColor}`}>
                      {item.tag}
                    </span>
                    <button
                      type="button"
                      onClick={() => alert(`Đang kết nối cuộc gọi đến ${item.name}...`)}
                      className="p-1 rounded-lg text-blue-600 hover:bg-blue-50 transition-colors"
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
