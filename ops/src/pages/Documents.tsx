import React, { useState, useEffect, useMemo, useRef } from 'react'
import {
  FolderLock,
  Search,
  Plus,
  Filter,
  FileText,
  BookOpen,
  ShieldCheck,
  Receipt,
  FileSpreadsheet,
  Briefcase,
  Users,
  Megaphone,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileCheck,
  Eye,
  Download,
  Trash2,
  X,
  Upload,
  RefreshCw,
  ExternalLink,
  History,
  FileUp,
  Tag,
  Calendar,
  Lock,
  ChevronRight,
  Link2,
  FileSignature,
  FileClock,
  Sparkles,
  Check,
  AlertCircle
} from 'lucide-react'
import {
  api,
  CompanyDocument,
  DocumentStats,
  DocumentCategory,
  DocumentApprovalStatus,
  DocumentVersion,
  DocumentActivity
} from '../lib/api'

// Helper format file size
const formatBytes = (bytes: number, decimals = 1) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}

// Helper format date
const formatDate = (dateStrOrTs?: string | number | null) => {
  if (!dateStrOrTs) return 'Chưa có'
  try {
    if (typeof dateStrOrTs === 'number') {
      const d = new Date(dateStrOrTs > 1e11 ? dateStrOrTs : dateStrOrTs * 1000)
      return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })
    }
    const d = new Date(dateStrOrTs)
    return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })
  } catch (_) {
    return String(dateStrOrTs)
  }
}

// Category metadata
const CATEGORY_MAP: Record<DocumentCategory, { label: string; icon: React.FC<{ className?: string }>; color: string; bg: string }> = {
  contract: { label: 'Hợp đồng', icon: FileText, color: 'text-blue-600', bg: 'bg-blue-50 border-blue-200' },
  sop: { label: 'Quy trình SOP', icon: BookOpen, color: 'text-emerald-600', bg: 'bg-emerald-50 border-emerald-200' },
  policy: { label: 'Chính sách', icon: ShieldCheck, color: 'text-indigo-600', bg: 'bg-indigo-50 border-indigo-200' },
  invoice: { label: 'Hóa đơn / Chứng từ', icon: Receipt, color: 'text-amber-600', bg: 'bg-amber-50 border-amber-200' },
  template: { label: 'Biểu mẫu chuẩn', icon: FileSpreadsheet, color: 'text-purple-600', bg: 'bg-purple-50 border-purple-200' },
  legal: { label: 'Pháp lý', icon: Briefcase, color: 'text-rose-600', bg: 'bg-rose-50 border-rose-200' },
  hr: { label: 'Nhân sự', icon: Users, color: 'text-cyan-600', bg: 'bg-cyan-50 border-cyan-200' },
  marketing: { label: 'Marketing & Brand', icon: Megaphone, color: 'text-pink-600', bg: 'bg-pink-50 border-pink-200' },
}

// Status metadata
const STATUS_MAP: Record<DocumentApprovalStatus, { label: string; badge: string; icon: React.FC<{ className?: string }> }> = {
  approved: { label: 'Đã duyệt', badge: 'bg-emerald-100 text-emerald-800 border-emerald-200', icon: CheckCircle2 },
  signed: { label: 'Đã ký', badge: 'bg-blue-100 text-blue-800 border-blue-200', icon: FileSignature },
  pending: { label: 'Chờ duyệt', badge: 'bg-amber-100 text-amber-800 border-amber-200', icon: Clock },
  draft: { label: 'Dự thảo', badge: 'bg-slate-100 text-slate-700 border-slate-200', icon: FileText },
  rejected: { label: 'Từ chối', badge: 'bg-rose-100 text-rose-800 border-rose-200', icon: AlertCircle },
  expired: { label: 'Hết hạn', badge: 'bg-red-100 text-red-800 border-red-200', icon: AlertTriangle },
}

export const DocumentsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'library' | 'action_needed' | 'templates'>('library')
  const [documents, setDocuments] = useState<CompanyDocument[]>([])
  const [templates, setTemplates] = useState<CompanyDocument[]>([])
  const [stats, setStats] = useState<DocumentStats | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [search, setSearch] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [departmentFilter, setDepartmentFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [actionNeededSubtab, setActionNeededSubtab] = useState<'all' | 'pending' | 'expiring' | 'unsigned'>('all')

  // Modals & Drawers
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false)
  const [uploadPreset, setUploadPreset] = useState<{ title?: string; category?: DocumentCategory; template_type?: string } | null>(null)
  const [newVersionDoc, setNewVersionDoc] = useState<CompanyDocument | null>(null)

  // Load Data
  const loadData = async () => {
    setLoading(true)
    try {
      const [docsRes, statsRes, tmplRes] = await Promise.all([
        api.getDocuments({ limit: 100 }),
        api.getDocumentStats(),
        api.getDocumentTemplates(),
      ])
      if (docsRes?.documents) setDocuments(docsRes.documents)
      if (statsRes?.stats) setStats(statsRes.stats)
      if (tmplRes?.templates) setTemplates(tmplRes.templates)
    } catch (err) {
      console.error('Lỗi khi tải kho tài liệu:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Filtered Documents for Library
  const filteredLibrary = useMemo(() => {
    return documents.filter((doc) => {
      if (categoryFilter !== 'all' && doc.category !== categoryFilter) return false
      if (departmentFilter !== 'all' && doc.department !== departmentFilter) return false
      if (statusFilter !== 'all' && doc.approval_status !== statusFilter) return false
      if (search.trim()) {
        const q = search.toLowerCase()
        const matchTitle = (doc.title || '').toLowerCase().includes(q)
        const matchCode = (doc.code || '').toLowerCase().includes(q)
        const matchOwner = (doc.owner || '').toLowerCase().includes(q)
        const matchFile = (doc.filename || '').toLowerCase().includes(q)
        const matchTags = (doc.tags || []).some((t) => t.toLowerCase().includes(q))
        if (!matchTitle && !matchCode && !matchOwner && !matchFile && !matchTags) return false
      }
      return true
    })
  }, [documents, categoryFilter, departmentFilter, statusFilter, search])

  // Documents needing action
  const actionNeededDocs = useMemo(() => {
    return documents.filter((doc) => {
      const isPending = doc.approval_status === 'pending'
      const isExpiring = Boolean(doc.is_expiring_soon || doc.is_expired)
      const isUnsigned = doc.category === 'contract' && doc.approval_status !== 'signed' && doc.approval_status !== 'rejected'

      if (actionNeededSubtab === 'pending') return isPending
      if (actionNeededSubtab === 'expiring') return isExpiring
      if (actionNeededSubtab === 'unsigned') return isUnsigned
      return isPending || isExpiring || isUnsigned
    })
  }, [documents, actionNeededSubtab])

  const departments = useMemo(() => {
    const set = new Set<string>()
    documents.forEach((d) => {
      if (d.department) set.add(d.department)
    })
    return Array.from(set)
  }, [documents])

  return (
    <div className="space-y-6 pb-16 animate-fade-in text-slate-800">
      {/* 1. Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100 shadow-2xs">
              <FolderLock className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                Kho Tài Liệu Doanh Nghiệp
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold border border-slate-200">
                  Document Vault
                </span>
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Lưu trữ file thật, quản lý phiên bản, kiểm soát hạn hợp đồng và cấp phát tri thức cho AI Assistant
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            onClick={loadData}
            title="Tải lại dữ liệu"
            disabled={loading}
            className="p-2.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl border border-slate-200/80 transition-colors shadow-2xs disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-emerald-600' : ''}`} />
          </button>

          <button
            onClick={() => {
              setUploadPreset(null)
              setIsUploadOpen(true)
            }}
            className="flex items-center space-x-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-semibold text-sm transition-all shadow-xs hover:shadow-md cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Tải lên tài liệu</span>
          </button>
        </div>
      </div>

      {/* 2. Stat Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Docs */}
        <div className="bg-white p-4.5 rounded-2xl border border-slate-200/80 shadow-2xs flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-slate-500">Tổng tài liệu lưu trữ</p>
            <p className="text-2xl font-black text-slate-900 mt-1">{stats?.total ?? documents.length}</p>
            <p className="text-[11px] text-slate-400 mt-0.5">Trong {stats?.categories_count || 8} danh mục chuẩn</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
            <FolderLock className="w-5 h-5" />
          </div>
        </div>

        {/* Pending Approval */}
        <div
          onClick={() => {
            setActiveTab('action_needed')
            setActionNeededSubtab('pending')
          }}
          className="bg-white p-4.5 rounded-2xl border border-amber-200/80 shadow-2xs flex items-center justify-between cursor-pointer hover:border-amber-400 transition-all group"
        >
          <div>
            <p className="text-xs font-semibold text-amber-600 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              Chờ phê duyệt
            </p>
            <p className="text-2xl font-black text-amber-700 mt-1">{stats?.pending_approval ?? 0}</p>
            <p className="text-[11px] text-amber-500 mt-0.5 group-hover:underline">Bấm để duyệt ngay &rarr;</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center group-hover:scale-105 transition-transform">
            <FileClock className="w-5 h-5" />
          </div>
        </div>

        {/* Expiring Soon */}
        <div
          onClick={() => {
            setActiveTab('action_needed')
            setActionNeededSubtab('expiring')
          }}
          className="bg-white p-4.5 rounded-2xl border border-rose-200/80 shadow-2xs flex items-center justify-between cursor-pointer hover:border-rose-400 transition-all group"
        >
          <div>
            <p className="text-xs font-semibold text-rose-600 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              Sắp hết hạn (30 ngày)
            </p>
            <p className="text-2xl font-black text-rose-700 mt-1">{stats?.expiring_soon ?? 0}</p>
            <p className="text-[11px] text-rose-500 mt-0.5 group-hover:underline">Cần gia hạn hợp đồng &rarr;</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-rose-50 text-rose-600 border border-rose-200 flex items-center justify-center group-hover:scale-105 transition-transform">
            <Calendar className="w-5 h-5" />
          </div>
        </div>

        {/* Unsigned / Missing Signature */}
        <div
          onClick={() => {
            setActiveTab('action_needed')
            setActionNeededSubtab('unsigned')
          }}
          className="bg-white p-4.5 rounded-2xl border border-blue-200/80 shadow-2xs flex items-center justify-between cursor-pointer hover:border-blue-400 transition-all group"
        >
          <div>
            <p className="text-xs font-semibold text-blue-600 flex items-center gap-1.5">
              <FileSignature className="w-3.5 h-3.5" />
              Chờ ký & Đóng dấu
            </p>
            <p className="text-2xl font-black text-blue-700 mt-1">{stats?.missing_signature ?? 0}</p>
            <p className="text-[11px] text-blue-500 mt-0.5 group-hover:underline">Ký số trực tiếp &rarr;</p>
          </div>
          <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 border border-blue-200 flex items-center justify-center group-hover:scale-105 transition-transform">
            <FileCheck className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* 3. Navigation Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab('library')}
          className={`pb-3 px-5 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === 'library'
              ? 'border-emerald-600 text-emerald-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FolderLock className="w-4 h-4" />
          Thư viện tài liệu
          <span className="px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-600">
            {documents.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('action_needed')}
          className={`pb-3 px-5 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === 'action_needed'
              ? 'border-emerald-600 text-emerald-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <AlertCircle className="w-4 h-4 text-amber-500" />
          Tài liệu cần xử lý
          {Boolean(stats && (stats.pending_approval + stats.expiring_soon + stats.missing_signature > 0)) && (
            <span className="px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-800 font-bold border border-amber-200">
              {stats!.pending_approval + stats!.expiring_soon + stats!.missing_signature}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('templates')}
          className={`pb-3 px-5 text-sm font-semibold border-b-2 transition-all flex items-center gap-2 cursor-pointer ${
            activeTab === 'templates'
              ? 'border-emerald-600 text-emerald-600 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FileSpreadsheet className="w-4 h-4 text-purple-600" />
          Mẫu tài liệu chuẩn
          <span className="px-2 py-0.5 rounded-full text-xs bg-purple-50 text-purple-700 font-medium">
            {templates.length}
          </span>
        </button>
      </div>

      {/* 4. Tab Content: Library */}
      {activeTab === 'library' && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
            <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
              {/* Search Bar */}
              <div className="relative w-full md:w-96">
                <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Tìm tài liệu theo tên, mã số, người phụ trách..."
                  className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-emerald-500 focus:bg-white transition-colors"
                />
                {search && (
                  <button
                    onClick={() => setSearch('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Department & Status Selectors */}
              <div className="flex items-center gap-2 w-full md:w-auto">
                <select
                  value={departmentFilter}
                  onChange={(e) => setDepartmentFilter(e.target.value)}
                  className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-700 focus:outline-none focus:border-emerald-500"
                >
                  <option value="all">Tất cả phòng ban</option>
                  {departments.map((dept) => (
                    <option key={dept} value={dept}>
                      {dept}
                    </option>
                  ))}
                </select>

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="text-xs bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-700 focus:outline-none focus:border-emerald-500"
                >
                  <option value="all">Tất cả trạng thái</option>
                  <option value="approved">Đã duyệt</option>
                  <option value="signed">Đã ký</option>
                  <option value="pending">Chờ duyệt</option>
                  <option value="draft">Dự thảo</option>
                  <option value="expired">Hết hạn</option>
                </select>
              </div>
            </div>

            {/* Category Chips Bar */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none pt-1">
              <button
                onClick={() => setCategoryFilter('all')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold shrink-0 transition-all cursor-pointer ${
                  categoryFilter === 'all'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                Tất cả ({documents.length})
              </button>
              {(Object.keys(CATEGORY_MAP) as DocumentCategory[]).map((cat) => {
                const meta = CATEGORY_MAP[cat]
                const count = stats?.by_category?.[cat] || documents.filter((d) => d.category === cat).length
                const active = categoryFilter === cat
                const Icon = meta.icon
                return (
                  <button
                    key={cat}
                    onClick={() => setCategoryFilter(cat)}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium shrink-0 transition-all cursor-pointer ${
                      active
                        ? 'bg-emerald-600 text-white font-bold shadow-xs'
                        : 'bg-white border border-slate-200/90 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${active ? 'text-white' : meta.color}`} />
                    <span>{meta.label}</span>
                    <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${active ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-500'}`}>
                      {count}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Documents Table / Grid */}
          {loading ? (
            <div className="bg-white p-12 rounded-2xl border border-slate-200/80 text-center">
              <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-700">Đang nạp danh sách tài liệu...</p>
            </div>
          ) : filteredLibrary.length === 0 ? (
            <div className="bg-white p-12 rounded-2xl border border-slate-200/80 text-center">
              <FolderLock className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800">Không tìm thấy tài liệu phù hợp</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                Không có tài liệu nào khớp với bộ lọc hiện tại. Thử chọn lại phòng ban hoặc tải lên tài liệu mới.
              </p>
              <button
                onClick={() => {
                  setCategoryFilter('all')
                  setDepartmentFilter('all')
                  setStatusFilter('all')
                  setSearch('')
                }}
                className="mt-4 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors"
              >
                Xóa tất cả bộ lọc
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/75 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                      <th className="py-3.5 px-4">Tài liệu & Mã số</th>
                      <th className="py-3.5 px-3">Phân loại</th>
                      <th className="py-3.5 px-3">Phòng ban / Phụ trách</th>
                      <th className="py-3.5 px-3">Phiên bản</th>
                      <th className="py-3.5 px-3">Trạng thái</th>
                      <th className="py-3.5 px-3">Hạn hiệu lực</th>
                      <th className="py-3.5 px-3">Liên kết nghiệp vụ</th>
                      <th className="py-3.5 px-4 text-right">Thao tác</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-xs">
                    {filteredLibrary.map((doc) => {
                      const catMeta = CATEGORY_MAP[doc.category] || CATEGORY_MAP.contract
                      const statusMeta = STATUS_MAP[doc.approval_status] || STATUS_MAP.draft
                      const CatIcon = catMeta.icon
                      const StatusIcon = statusMeta.icon

                      return (
                        <tr
                          key={doc.id}
                          className="hover:bg-slate-50/80 transition-colors group cursor-pointer"
                          onClick={() => setSelectedDocId(doc.id)}
                        >
                          {/* Title & Filename */}
                          <td className="py-3 px-4">
                            <div className="flex items-start space-x-3">
                              <div className={`p-2 rounded-xl shrink-0 border ${catMeta.bg} ${catMeta.color} mt-0.5`}>
                                <CatIcon className="w-4 h-4" />
                              </div>
                              <div className="min-w-0 max-w-sm">
                                <p className="font-bold text-slate-900 group-hover:text-emerald-700 transition-colors truncate">
                                  {doc.title}
                                </p>
                                <div className="flex items-center space-x-2 mt-0.5 text-[11px] text-slate-500">
                                  <span className="font-mono bg-slate-100 px-1.5 py-0.2 rounded text-slate-600 font-semibold">
                                    {doc.code}
                                  </span>
                                  <span>&bull;</span>
                                  <span className="truncate">{doc.filename}</span>
                                  <span>&bull;</span>
                                  <span>{formatBytes(doc.file_size)}</span>
                                </div>
                              </div>
                            </div>
                          </td>

                          {/* Category */}
                          <td className="py-3 px-3">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-lg text-[11px] font-semibold border ${catMeta.bg} ${catMeta.color}`}>
                              {catMeta.label}
                            </span>
                          </td>

                          {/* Dept & Owner */}
                          <td className="py-3 px-3">
                            <p className="font-medium text-slate-800">{doc.department || 'Nội bộ'}</p>
                            <p className="text-[11px] text-slate-400">{doc.owner || 'Chưa gán'}</p>
                          </td>

                          {/* Version */}
                          <td className="py-3 px-3">
                            <span className="font-mono text-xs px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md font-semibold border border-slate-200">
                              v{doc.version}
                            </span>
                          </td>

                          {/* Status */}
                          <td className="py-3 px-3">
                            <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${statusMeta.badge}`}>
                              <StatusIcon className="w-3 h-3" />
                              <span>{statusMeta.label}</span>
                            </span>
                          </td>

                          {/* Expiry Date */}
                          <td className="py-3 px-3">
                            {doc.expiry_date ? (
                              <div>
                                <p className={`font-medium ${doc.is_expiring_soon ? 'text-rose-600 font-bold' : 'text-slate-700'}`}>
                                  {formatDate(doc.expiry_date)}
                                </p>
                                {doc.is_expiring_soon && (
                                  <span className="inline-block text-[10px] text-rose-600 font-bold bg-rose-50 px-1.5 py-0.2 rounded border border-rose-200 mt-0.5">
                                    Sắp hết hạn
                                  </span>
                                )}
                              </div>
                            ) : (
                              <span className="text-slate-400 text-[11px]">Vô thời hạn</span>
                            )}
                          </td>

                          {/* Linked Entity */}
                          <td className="py-3 px-3">
                            {doc.linked_entity_type && doc.linked_entity_id ? (
                              <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                                <Link2 className="w-3 h-3 text-slate-400" />
                                <span className="capitalize">{doc.linked_entity_type}:</span>
                                <span className="font-mono font-semibold">{doc.linked_entity_id}</span>
                              </span>
                            ) : (
                              <span className="text-slate-400 text-[11px]">-</span>
                            )}
                          </td>

                          {/* Actions */}
                          <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-end space-x-1">
                              <a
                                href={api.getDocumentFileUrl(doc.id, false)}
                                target="_blank"
                                rel="noreferrer"
                                title="Xem trực tiếp trong tab mới"
                                className="p-1.5 text-slate-500 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors"
                              >
                                <Eye className="w-4 h-4" />
                              </a>
                              <a
                                href={api.getDocumentFileUrl(doc.id, true)}
                                download={doc.filename}
                                title="Tải file thật về máy"
                                className="p-1.5 text-slate-500 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
                              >
                                <Download className="w-4 h-4" />
                              </a>
                              <button
                                onClick={() => setSelectedDocId(doc.id)}
                                title="Chi tiết & Lịch sử"
                                className="p-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                              >
                                <ChevronRight className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 5. Tab Content: Action Needed */}
      {activeTab === 'action_needed' && (
        <div className="space-y-4">
          {/* Sub-filter chips */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActionNeededSubtab('all')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold cursor-pointer ${
                actionNeededSubtab === 'all'
                  ? 'bg-slate-900 text-white'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              Tất cả cần xử lý
            </button>
            <button
              onClick={() => setActionNeededSubtab('pending')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer ${
                actionNeededSubtab === 'pending'
                  ? 'bg-amber-600 text-white'
                  : 'bg-white border border-amber-200 text-amber-700 hover:bg-amber-50'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              Chờ phê duyệt ({stats?.pending_approval || 0})
            </button>
            <button
              onClick={() => setActionNeededSubtab('expiring')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer ${
                actionNeededSubtab === 'expiring'
                  ? 'bg-rose-600 text-white'
                  : 'bg-white border border-rose-200 text-rose-700 hover:bg-rose-50'
              }`}
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              Sắp hết hạn trong 30 ngày ({stats?.expiring_soon || 0})
            </button>
            <button
              onClick={() => setActionNeededSubtab('unsigned')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 cursor-pointer ${
                actionNeededSubtab === 'unsigned'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-blue-200 text-blue-700 hover:bg-blue-50'
              }`}
            >
              <FileSignature className="w-3.5 h-3.5" />
              Chờ ký & đóng dấu ({stats?.missing_signature || 0})
            </button>
          </div>

          {/* Action List */}
          {actionNeededDocs.length === 0 ? (
            <div className="bg-white p-12 rounded-2xl border border-slate-200/80 text-center">
              <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800">Tuyệt vời! Không có tài liệu nào tồn đọng</h3>
              <p className="text-xs text-slate-500 mt-1">
                Tất cả hợp đồng, chính sách và SOP đều đã được phê duyệt và đang có hiệu lực an toàn.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {actionNeededDocs.map((doc) => {
                const catMeta = CATEGORY_MAP[doc.category] || CATEGORY_MAP.contract
                const isPending = doc.approval_status === 'pending'
                const isExpiring = Boolean(doc.is_expiring_soon || doc.is_expired)
                const isUnsigned = doc.category === 'contract' && doc.approval_status !== 'signed'

                return (
                  <div
                    key={doc.id}
                    className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs hover:border-slate-300 transition-all flex flex-col justify-between space-y-4"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center space-x-2">
                          <span className={`p-2 rounded-xl border ${catMeta.bg} ${catMeta.color}`}>
                            {React.createElement(catMeta.icon, { className: 'w-4 h-4' })}
                          </span>
                          <div>
                            <span className="font-mono text-[11px] font-bold text-slate-500">{doc.code}</span>
                            <span className="text-[11px] text-slate-400"> &bull; v{doc.version}</span>
                          </div>
                        </div>

                        {/* Badges */}
                        <div className="flex items-center gap-1.5">
                          {isPending && (
                            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                              Chờ duyệt
                            </span>
                          )}
                          {isExpiring && (
                            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                              Sắp hết hạn ({formatDate(doc.expiry_date)})
                            </span>
                          )}
                          {isUnsigned && !isPending && (
                            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                              Chờ ký số
                            </span>
                          )}
                        </div>
                      </div>

                      <h4 className="font-bold text-slate-900 mt-3 text-sm leading-snug">{doc.title}</h4>
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                        {doc.description || `File: ${doc.filename} (${formatBytes(doc.file_size)}) · Phụ trách: ${doc.owner}`}
                      </p>

                      <div className="flex items-center gap-3 mt-3 text-[11px] text-slate-500 border-t border-slate-100 pt-2.5">
                        <span>Phòng: <strong className="text-slate-700">{doc.department}</strong></span>
                        <span>&bull;</span>
                        <span>Người tạo: <strong className="text-slate-700">{doc.owner}</strong></span>
                      </div>
                    </div>

                    {/* Quick action buttons */}
                    <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                      <button
                        onClick={() => setSelectedDocId(doc.id)}
                        className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1 cursor-pointer"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Xem chi tiết & File
                      </button>

                      <div className="flex items-center space-x-2">
                        {isPending && (
                          <button
                            onClick={async () => {
                              try {
                                await api.approveDocument(doc.id, 'approve', 'Phê duyệt nhanh từ màn Cần xử lý')
                                await loadData()
                              } catch (e: any) {
                                alert(e.message || 'Lỗi phê duyệt')
                              }
                            }}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1"
                          >
                            <Check className="w-3.5 h-3.5" />
                            Duyệt ngay
                          </button>
                        )}

                        {isUnsigned && !isPending && (
                          <button
                            onClick={async () => {
                              const signer = prompt('Nhập tên người ký đại diện công ty:', 'Ban Giám Đốc')
                              if (!signer) return
                              try {
                                await api.signDocument(doc.id, signer, 'Ký duyệt số trên hệ thống')
                                await loadData()
                              } catch (e: any) {
                                alert(e.message || 'Lỗi ký tài liệu')
                              }
                            }}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1"
                          >
                            <FileSignature className="w-3.5 h-3.5" />
                            Ký số
                          </button>
                        )}

                        <a
                          href={api.getDocumentFileUrl(doc.id, true)}
                          download={doc.filename}
                          className="p-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                          title="Tải file thật về máy"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* 6. Tab Content: Templates */}
      {activeTab === 'templates' && (
        <div className="space-y-4">
          <div className="bg-gradient-to-r from-purple-900/90 to-indigo-900/90 text-white p-6 rounded-2xl shadow-sm">
            <div className="flex items-center space-x-3 mb-2">
              <Sparkles className="w-5 h-5 text-purple-300" />
              <h3 className="font-bold text-base">Thư viện Biểu mẫu Tiêu chuẩn (Corporate Templates)</h3>
            </div>
            <p className="text-xs text-purple-200 max-w-2xl leading-relaxed">
              Các biểu mẫu hợp đồng kinh tế, báo giá, biên bản bàn giao, thỏa thuận bảo mật NDA và chính sách đã được luật sư và ban giám đốc chuẩn hóa. Nhân viên có thể tải file hoặc tạo tài liệu mới từ mẫu này chỉ với 1 click.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templates.map((tmpl) => {
              const catMeta = CATEGORY_MAP[tmpl.category] || CATEGORY_MAP.template

              return (
                <div
                  key={tmpl.id}
                  className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs hover:border-purple-300 hover:shadow-md transition-all flex flex-col justify-between space-y-4 group"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className={`p-2 rounded-xl border ${catMeta.bg} ${catMeta.color}`}>
                        {React.createElement(catMeta.icon, { className: 'w-4 h-4' })}
                      </span>
                      <span className="font-mono text-[11px] font-semibold text-slate-400">
                        {tmpl.code}
                      </span>
                    </div>

                    <h4 className="font-bold text-slate-900 mt-3 text-sm group-hover:text-purple-700 transition-colors">
                      {tmpl.title}
                    </h4>
                    <p className="text-xs text-slate-500 mt-1 line-clamp-3">
                      {tmpl.description || `File biểu mẫu gốc: ${tmpl.filename} (${formatBytes(tmpl.file_size)})`}
                    </p>

                    <div className="flex items-center space-x-2 mt-3 text-[11px] text-slate-500">
                      <span className="bg-purple-50 text-purple-700 px-2 py-0.5 rounded font-semibold border border-purple-100">
                        {tmpl.template_type || 'Biểu mẫu'}
                      </span>
                      <span>&bull;</span>
                      <span>v{tmpl.version}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between border-t border-slate-100 pt-3">
                    <a
                      href={api.getDocumentFileUrl(tmpl.id, true)}
                      download={tmpl.filename}
                      className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5"
                    >
                      <Download className="w-3.5 h-3.5" />
                      Tải file mẫu
                    </a>

                    <button
                      onClick={() => {
                        setUploadPreset({
                          title: `${tmpl.title} - [Tên khách hàng / Đối tác]`,
                          category: tmpl.category,
                          template_type: tmpl.template_type || undefined,
                        })
                        setIsUploadOpen(true)
                      }}
                      className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center gap-1"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      Sử dụng mẫu này
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 7. Document Detail Drawer */}
      {selectedDocId && (
        <DocumentDetailDrawer
          documentId={selectedDocId}
          onClose={() => setSelectedDocId(null)}
          onReload={loadData}
          onOpenNewVersion={(doc) => {
            setNewVersionDoc(doc)
          }}
        />
      )}

      {/* 8. Upload Modal */}
      {isUploadOpen && (
        <UploadDocumentModal
          preset={uploadPreset}
          departments={departments}
          onClose={() => {
            setIsUploadOpen(false)
            setUploadPreset(null)
          }}
          onSuccess={() => {
            setIsUploadOpen(false)
            setUploadPreset(null)
            loadData()
          }}
        />
      )}

      {/* 9. Upload New Version Modal */}
      {newVersionDoc && (
        <UploadNewVersionModal
          document={newVersionDoc}
          onClose={() => setNewVersionDoc(null)}
          onSuccess={() => {
            setNewVersionDoc(null)
            loadData()
          }}
        />
      )}
    </div>
  )
}

// ============================================================
// Drawer: Chi tiết tài liệu, Preview, Metadata, Version & Audit
// ============================================================
interface DocumentDetailDrawerProps {
  documentId: string
  onClose: () => void
  onReload: () => void
  onOpenNewVersion: (doc: CompanyDocument) => void
}

const DocumentDetailDrawer: React.FC<DocumentDetailDrawerProps> = ({
  documentId,
  onClose,
  onReload,
  onOpenNewVersion,
}) => {
  const [doc, setDoc] = useState<CompanyDocument | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [activeTab, setActiveTab] = useState<'preview' | 'metadata' | 'versions' | 'audit'>('preview')
  const [actionLoading, setActionLoading] = useState<boolean>(false)

  const loadDetail = async () => {
    setLoading(true)
    try {
      const res = await api.getDocument(documentId)
      if (res?.document) setDoc(res.document)
    } catch (err) {
      console.error('Lỗi khi nạp chi tiết tài liệu:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDetail()
  }, [documentId])

  if (!doc && loading) {
    return (
      <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex justify-end">
        <div className="w-full max-w-2xl bg-white h-full p-8 flex items-center justify-center">
          <RefreshCw className="w-8 h-8 text-emerald-600 animate-spin" />
        </div>
      </div>
    )
  }

  if (!doc) return null

  const catMeta = CATEGORY_MAP[doc.category] || CATEGORY_MAP.contract
  const statusMeta = STATUS_MAP[doc.approval_status] || STATUS_MAP.draft
  const isPdf = doc.mime_type === 'application/pdf' || doc.filename.toLowerCase().endsWith('.pdf')

  const handleApprove = async (action: 'approve' | 'reject') => {
    const notes = prompt(`Ghi chú khi ${action === 'approve' ? 'phê duyệt' : 'từ chối'}:`, '')
    setActionLoading(true)
    try {
      await api.approveDocument(doc.id, action, notes || undefined)
      await loadDetail()
      onReload()
    } catch (err: any) {
      alert(err.message || 'Lỗi thao tác duyệt')
    } finally {
      setActionLoading(false)
    }
  }

  const handleSign = async () => {
    const signer = prompt('Nhập họ tên người ký đại diện:', doc.owner || 'Ban Giám Đốc')
    if (!signer) return
    setActionLoading(true)
    try {
      await api.signDocument(doc.id, signer, 'Ký duyệt số trên hệ thống Document Vault')
      await loadDetail()
      onReload()
    } catch (err: any) {
      alert(err.message || 'Lỗi khi ký tài liệu')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Bạn có chắc chắn muốn xóa vĩnh viễn tài liệu "${doc.title}"?`)) return
    setActionLoading(true)
    try {
      await api.deleteDocument(doc.id)
      onReload()
      onClose()
    } catch (err: any) {
      alert(err.message || 'Lỗi khi xóa tài liệu')
      setActionLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex justify-end animate-fade-in">
      <div className="w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col justify-between overflow-hidden">
        {/* Drawer Header */}
        <div className="p-5 border-b border-slate-200 flex items-start justify-between bg-slate-50/50">
          <div className="flex items-start space-x-3 min-w-0 pr-4">
            <span className={`p-2.5 rounded-xl border ${catMeta.bg} ${catMeta.color} shrink-0 mt-0.5`}>
              {React.createElement(catMeta.icon, { className: 'w-5 h-5' })}
            </span>
            <div className="min-w-0">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xs font-bold text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                  {doc.code}
                </span>
                <span className="text-xs text-slate-500 font-semibold">&bull; v{doc.version}</span>
                <span className={`inline-flex items-center px-2 py-0.2 rounded-full text-[10px] font-bold border ${statusMeta.badge}`}>
                  {statusMeta.label}
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-900 mt-1 truncate">{doc.title}</h2>
              <p className="text-xs text-slate-500 truncate mt-0.5">
                {doc.filename} &bull; {formatBytes(doc.file_size)}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-xl transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Tabs */}
        <div className="flex border-b border-slate-200 px-5 pt-2 bg-white">
          <button
            onClick={() => setActiveTab('preview')}
            className={`pb-2.5 px-4 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
              activeTab === 'preview'
                ? 'border-emerald-600 text-emerald-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Xem trước File
          </button>
          <button
            onClick={() => setActiveTab('metadata')}
            className={`pb-2.5 px-4 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
              activeTab === 'metadata'
                ? 'border-emerald-600 text-emerald-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Thông tin & Phân quyền
          </button>
          <button
            onClick={() => setActiveTab('versions')}
            className={`pb-2.5 px-4 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
              activeTab === 'versions'
                ? 'border-emerald-600 text-emerald-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Lịch sử phiên bản ({doc.versions?.length || 1})
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`pb-2.5 px-4 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
              activeTab === 'audit'
                ? 'border-emerald-600 text-emerald-600 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Nhật ký ({doc.activities?.length || 0})
          </button>
        </div>

        {/* Drawer Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Tab 1: Preview */}
          {activeTab === 'preview' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                <div className="flex items-center space-x-2 text-xs text-slate-700">
                  <FileText className="w-4 h-4 text-emerald-600" />
                  <span className="font-semibold truncate max-w-xs">{doc.filename}</span>
                  <span className="text-slate-400">({formatBytes(doc.file_size)})</span>
                </div>

                <div className="flex items-center space-x-2">
                  <a
                    href={api.getDocumentFileUrl(doc.id, false)}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-semibold shadow-2xs transition-colors"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Mở tab mới</span>
                  </a>

                  <a
                    href={api.getDocumentFileUrl(doc.id, true)}
                    download={doc.filename}
                    className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Tải về</span>
                  </a>
                </div>
              </div>

              {/* PDF Preview Iframe */}
              {isPdf ? (
                <div className="border border-slate-200 rounded-xl overflow-hidden shadow-inner bg-slate-100 h-[480px]">
                  <iframe
                    src={api.getDocumentFileUrl(doc.id, false)}
                    className="w-full h-full border-none"
                    title={doc.title}
                  />
                </div>
              ) : (
                <div className="p-12 text-center border-2 border-dashed border-slate-200 rounded-2xl bg-slate-50">
                  <FileText className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                  <h4 className="font-bold text-slate-800 text-sm">Xem trước định dạng này trong tab mới</h4>
                  <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                    File kiểu <code>{doc.mime_type || 'tài liệu'}</code> được lưu thật trong máy chủ. Bấm mở tab mới hoặc tải về để đọc.
                  </p>
                  <a
                    href={api.getDocumentFileUrl(doc.id, false)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center space-x-2 mt-4 px-4 py-2 bg-emerald-600 text-white text-xs font-bold rounded-xl shadow-xs hover:bg-emerald-700 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>Mở xem file thật</span>
                  </a>
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Metadata */}
          {activeTab === 'metadata' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block mb-0.5">Phân loại tài liệu</span>
                  <span className="font-bold text-slate-800">{catMeta.label}</span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block mb-0.5">Phòng ban quản lý</span>
                  <span className="font-bold text-slate-800">{doc.department}</span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block mb-0.5">Người phụ trách</span>
                  <span className="font-bold text-slate-800">{doc.owner}</span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block mb-0.5">Quyền truy cập</span>
                  <span className="font-bold text-slate-800 capitalize flex items-center gap-1">
                    <Lock className="w-3 h-3 text-slate-400" />
                    {doc.permission_level || 'Nội bộ'}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block mb-0.5">Ngày hết hạn</span>
                  <span className={`font-bold ${doc.is_expiring_soon ? 'text-rose-600' : 'text-slate-800'}`}>
                    {doc.expiry_date ? formatDate(doc.expiry_date) : 'Không thời hạn'}
                  </span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                  <span className="text-slate-400 block mb-0.5">Đối tượng gắn kết</span>
                  <span className="font-bold text-slate-800">
                    {doc.linked_entity_type ? `${doc.linked_entity_type}: ${doc.linked_entity_id}` : 'Không gắn kết'}
                  </span>
                </div>
              </div>

              {/* Description */}
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                <span className="text-xs text-slate-400 block mb-1 font-medium">Mô tả / Tóm tắt nội dung</span>
                <p className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">
                  {doc.description || 'Chưa có mô tả bổ sung cho tài liệu này.'}
                </p>
              </div>

              {/* Tags */}
              {doc.tags && doc.tags.length > 0 && (
                <div>
                  <span className="text-xs text-slate-400 block mb-1.5 font-medium">Nhãn / Tags</span>
                  <div className="flex flex-wrap gap-1.5">
                    {doc.tags.map((tag) => (
                      <span key={tag} className="text-[11px] bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded-full border border-slate-200 font-medium">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* File details */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1 font-mono text-slate-600">
                <p>Đường dẫn: {doc.file_path}</p>
                <p>Ngày tạo: {formatDate(doc.created_at)} &bull; Cập nhật: {formatDate(doc.updated_at)}</p>
              </div>
            </div>
          )}

          {/* Tab 3: Version History */}
          {activeTab === 'versions' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-xs text-slate-500">Mỗi khi tài liệu được cập nhật, bản cũ được bảo toàn để tra cứu.</p>
                <button
                  onClick={() => onOpenNewVersion(doc)}
                  className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-xl text-xs font-bold border border-emerald-200 transition-colors cursor-pointer"
                >
                  <FileUp className="w-3.5 h-3.5" />
                  <span>Tải phiên bản mới</span>
                </button>
              </div>

              <div className="space-y-3">
                {/* Current Version */}
                <div className="p-3.5 rounded-xl border-2 border-emerald-200 bg-emerald-50/40 relative">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold bg-emerald-600 text-white px-2 py-0.5 rounded">
                        v{doc.version}
                      </span>
                      <span className="text-xs font-bold text-slate-800">Phiên bản hiện hành</span>
                    </div>
                    <span className="text-[11px] text-slate-500">{formatDate(doc.updated_at)}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-2">
                    File: <strong className="font-mono">{doc.filename}</strong> ({formatBytes(doc.file_size)})
                  </p>
                  <p className="text-[11px] text-slate-400 mt-1">Cập nhật bởi: {doc.owner}</p>
                </div>

                {/* Past versions */}
                {doc.versions?.map((ver) => (
                  <div key={ver.id} className="p-3.5 rounded-xl border border-slate-200 bg-white">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200">
                          v{ver.version}
                        </span>
                        <span className="text-xs text-slate-600 font-medium">Bản lưu trữ</span>
                      </div>
                      <span className="text-[11px] text-slate-400">{formatDate(ver.created_at)}</span>
                    </div>
                    <p className="text-xs text-slate-600 mt-2 font-mono">
                      {ver.filename} ({formatBytes(ver.file_size)})
                    </p>
                    {ver.notes && <p className="text-[11px] text-slate-500 mt-1 italic">"{ver.notes}"</p>}
                    <p className="text-[11px] text-slate-400 mt-1">Người tải lên: {ver.uploaded_by}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 4: Audit Activity Log */}
          {activeTab === 'audit' && (
            <div className="space-y-3">
              <p className="text-xs text-slate-500">Mọi hành vi tải file, phê duyệt hoặc sửa đổi đều được ghi vết bảo mật.</p>
              <div className="relative border-l-2 border-slate-200 ml-3 pl-4 space-y-4">
                {(doc.activities || []).map((act) => (
                  <div key={act.id} className="relative">
                    <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-white" />
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-xs text-slate-800">{act.action}</span>
                        <span className="text-[11px] text-slate-400">&bull; {formatDate(act.created_at)}</span>
                      </div>
                      <p className="text-xs text-slate-600 mt-0.5">{act.details || 'Không có chi tiết'}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5 font-medium">Bởi: {act.actor}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Drawer Footer Actions */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <button
            onClick={handleDelete}
            disabled={actionLoading}
            className="text-xs font-semibold text-rose-600 hover:text-rose-800 flex items-center gap-1.5 p-2 rounded-xl hover:bg-rose-50 transition-colors cursor-pointer"
          >
            <Trash2 className="w-4 h-4" />
            <span>Xóa tài liệu</span>
          </button>

          <div className="flex items-center space-x-2">
            {doc.approval_status === 'pending' && (
              <>
                <button
                  onClick={() => handleApprove('reject')}
                  disabled={actionLoading}
                  className="px-3 py-2 bg-white border border-rose-300 text-rose-700 hover:bg-rose-50 rounded-xl text-xs font-bold transition-all cursor-pointer shadow-2xs"
                >
                  Từ chối
                </button>
                <button
                  onClick={() => handleApprove('approve')}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all cursor-pointer shadow-xs flex items-center gap-1.5"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>Phê duyệt</span>
                </button>
              </>
            )}

            {doc.category === 'contract' && doc.approval_status !== 'signed' && doc.approval_status !== 'rejected' && (
              <button
                onClick={handleSign}
                disabled={actionLoading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all cursor-pointer shadow-xs flex items-center gap-1.5"
              >
                <FileSignature className="w-3.5 h-3.5" />
                <span>Ký số văn bản</span>
              </button>
            )}

            <button
              onClick={() => onOpenNewVersion(doc)}
              className="px-3.5 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5"
            >
              <FileUp className="w-3.5 h-3.5" />
              <span>Bản mới</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================================
// Modal: Tải lên tài liệu mới (File thật + Metadata)
// ============================================================
interface UploadDocumentModalProps {
  preset: { title?: string; category?: DocumentCategory; template_type?: string } | null
  departments: string[]
  onClose: () => void
  onSuccess: () => void
}

const UploadDocumentModal: React.FC<UploadDocumentModalProps> = ({
  preset,
  departments,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null)
  const [title, setTitle] = useState<string>(preset?.title || '')
  const [code, setCode] = useState<string>('')
  const [category, setCategory] = useState<DocumentCategory>(preset?.category || 'contract')
  const [department, setDepartment] = useState<string>(departments[0] || 'Kinh doanh & Bán hàng')
  const [owner, setOwner] = useState<string>('Nguyễn Văn Quản')
  const [version, setVersion] = useState<string>('1.0')
  const [approvalStatus, setApprovalStatus] = useState<DocumentApprovalStatus>('approved')
  const [expiryDate, setExpiryDate] = useState<string>('')
  const [permissionLevel, setPermissionLevel] = useState<string>('internal')
  const [linkedType, setLinkedType] = useState<string>('')
  const [linkedId, setLinkedId] = useState<string>('')
  const [isTemplate, setIsTemplate] = useState<boolean>(Boolean(preset?.template_type))
  const [templateType, setTemplateType] = useState<string>(preset?.template_type || '')
  const [description, setDescription] = useState<string>('')
  const [tags, setTags] = useState<string>('')
  const [submitting, setSubmitting] = useState<boolean>(false)
  const [dragActive, setDragActive] = useState<boolean>(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0])
    }
  }

  const handleFileSelected = (selectedFile: File) => {
    setFile(selectedFile)
    if (!title) {
      const cleanName = selectedFile.name.replace(/\.[^/.]+$/, '')
      setTitle(cleanName)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      alert('Vui lòng chọn một file thật để lưu vào kho tài liệu.')
      return
    }
    if (!title.trim()) {
      alert('Vui lòng nhập tiêu đề tài liệu.')
      return
    }

    setSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', title.trim())
      if (code.trim()) formData.append('code', code.trim())
      formData.append('category', category)
      formData.append('department', department)
      formData.append('owner', owner.trim())
      formData.append('version', version.trim() || '1.0')
      formData.append('approval_status', approvalStatus)
      if (expiryDate) formData.append('expiry_date', expiryDate)
      formData.append('permission_level', permissionLevel)
      if (linkedType) formData.append('linked_entity_type', linkedType)
      if (linkedId) formData.append('linked_entity_id', linkedId)
      formData.append('is_template', String(isTemplate))
      if (templateType) formData.append('template_type', templateType)
      if (description) formData.append('description', description)
      if (tags) formData.append('tags', tags)

      await api.uploadDocument(formData)
      onSuccess()
    } catch (err: any) {
      alert(err.message || 'Lỗi khi tải tài liệu lên')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white w-full max-w-2xl rounded-2xl shadow-2xl border border-slate-200 overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-xl border border-emerald-100">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base">Tải lên tài liệu vào Kho công ty</h3>
              <p className="text-xs text-slate-500">File được lưu vật lý an toàn và đồng bộ metadata vào hệ thống</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-slate-700 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* File Drag & Drop Zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
              dragActive
                ? 'border-emerald-500 bg-emerald-50/50'
                : file
                ? 'border-emerald-300 bg-emerald-50/20'
                : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) handleFileSelected(e.target.files[0])
              }}
              className="hidden"
            />
            {file ? (
              <div className="flex items-center justify-center space-x-3 text-emerald-800">
                <FileCheck className="w-8 h-8 text-emerald-600" />
                <div className="text-left">
                  <p className="font-bold text-sm truncate max-w-sm">{file.name}</p>
                  <p className="text-xs text-emerald-600">{formatBytes(file.size)} &bull; Bấm để đổi file khác</p>
                </div>
              </div>
            ) : (
              <div>
                <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <p className="text-xs font-bold text-slate-700">Kéo thả file vào đây hoặc bấm để duyệt từ máy tính</p>
                <p className="text-[11px] text-slate-400 mt-1">Hỗ trợ PDF, DOCX, XLSX, hình ảnh, văn bản quy chuẩn</p>
              </div>
            )}
          </div>

          {/* Title & Code */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-2">
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Tiêu đề tài liệu <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="VD: Hợp đồng triển khai dịch vụ Auto_Social 2026"
                className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none font-medium"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Mã tài liệu (Tùy chọn)</label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Tự động sinh nếu để trống"
                className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none font-mono"
              />
            </div>
          </div>

          {/* Category & Department */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Phân loại tài liệu</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as DocumentCategory)}
                className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none"
              >
                {(Object.keys(CATEGORY_MAP) as DocumentCategory[]).map((cat) => (
                  <option key={cat} value={cat}>
                    {CATEGORY_MAP[cat].label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Phòng ban quản lý</label>
              <select
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none"
              >
                <option value="Ban Giám đốc">Ban Giám đốc</option>
                <option value="Kinh doanh & Bán hàng">Kinh doanh & Bán hàng</option>
                <option value="Marketing">Marketing</option>
                <option value="Nhân sự">Nhân sự</option>
                <option value="Tài chính">Tài chính</option>
                <option value="Kỹ thuật & Vận hành">Kỹ thuật & Vận hành</option>
              </select>
            </div>
          </div>

          {/* Owner, Version, Status */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Người phụ trách</label>
              <input
                type="text"
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Phiên bản</label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="1.0"
                className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Trạng thái duyệt</label>
              <select
                value={approvalStatus}
                onChange={(e) => setApprovalStatus(e.target.value as DocumentApprovalStatus)}
                className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none"
              >
                <option value="approved">Đã duyệt</option>
                <option value="pending">Chờ duyệt</option>
                <option value="draft">Dự thảo</option>
                <option value="signed">Đã ký</option>
              </select>
            </div>
          </div>

          {/* Expiry Date & Permission */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Ngày hết hạn (Nếu có)</label>
              <input
                type="date"
                value={expiryDate}
                onChange={(e) => setExpiryDate(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Phân quyền bảo mật</label>
              <select
                value={permissionLevel}
                onChange={(e) => setPermissionLevel(e.target.value)}
                className="w-full text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none"
              >
                <option value="internal">Nội bộ công ty (Internal)</option>
                <option value="confidential">Bảo mật cao (Confidential)</option>
                <option value="restricted">Chỉ ban giám đốc (Restricted)</option>
                <option value="public">Công khai (Public)</option>
              </select>
            </div>
          </div>

          {/* Linked Entity */}
          <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Gắn với đối tượng nghiệp vụ</label>
              <select
                value={linkedType}
                onChange={(e) => setLinkedType(e.target.value)}
                className="w-full text-xs px-3.5 py-2 bg-white border border-slate-200 rounded-xl focus:border-emerald-500 focus:outline-none"
              >
                <option value="">Không gắn</option>
                <option value="customer">Khách hàng CRM</option>
                <option value="order">Đơn hàng (Order)</option>
                <option value="task">Nhiệm vụ Kanban</option>
                <option value="staff">Nhân viên (Staff)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Mã đối tượng (ID / SĐT / Mã đơn)</label>
              <input
                type="text"
                value={linkedId}
                onChange={(e) => setLinkedId(e.target.value)}
                placeholder="VD: ord_20261001 hoặc crm_0988..."
                disabled={!linkedType}
                className="w-full text-xs px-3.5 py-2 bg-white border border-slate-200 rounded-xl focus:border-emerald-500 focus:outline-none font-mono disabled:opacity-50"
              />
            </div>
          </div>

          {/* Template Toggle */}
          <div className="flex items-center justify-between p-3 bg-purple-50/50 rounded-xl border border-purple-100">
            <div>
              <p className="text-xs font-bold text-purple-900">Đặt làm Biểu mẫu Tiêu chuẩn (Template)</p>
              <p className="text-[11px] text-purple-600">Cho phép các nhân viên khác sử dụng để tạo hợp đồng/chứng từ mới</p>
            </div>
            <input
              type="checkbox"
              checked={isTemplate}
              onChange={(e) => setIsTemplate(e.target.checked)}
              className="w-4 h-4 text-purple-600 rounded focus:ring-purple-500"
            />
          </div>

          {/* Description & Tags */}
          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Mô tả / Tóm tắt nội dung</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Tóm tắt ngắn về phạm vi, điều khoản chính hoặc lưu ý khi dùng tài liệu này..."
              className="w-full text-xs px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Thẻ phân loại (Tags, phân cách bằng dấu phẩy)</label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="VD: hop-dong, khach-hang, 2026, quang-cao"
              className="w-full text-xs px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:border-emerald-500 focus:outline-none"
            />
          </div>
        </form>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-end space-x-2.5">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 text-xs font-bold text-slate-600 hover:text-slate-900 rounded-xl"
          >
            Hủy
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || !file}
            className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {submitting ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Đang lưu file...</span>
              </>
            ) : (
              <>
                <Upload className="w-3.5 h-3.5" />
                <span>Lưu vào Kho tài liệu</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// ============================================================
// Modal: Tải lên phiên bản mới (New Version)
// ============================================================
interface UploadNewVersionModalProps {
  document: CompanyDocument
  onClose: () => void
  onSuccess: () => void
}

const UploadNewVersionModal: React.FC<UploadNewVersionModalProps> = ({
  document,
  onClose,
  onSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null)
  const [version, setVersion] = useState<string>('')
  const [notes, setNotes] = useState<string>('')
  const [submitting, setSubmitting] = useState<boolean>(false)

  useEffect(() => {
    // Propose next version number
    try {
      const parts = document.version.split('.')
      if (parts.length >= 2) {
        const minor = parseInt(parts[1]) || 0
        setVersion(`${parts[0]}.${minor + 1}`)
      } else {
        setVersion(`${document.version}.1`)
      }
    } catch (_) {
      setVersion('1.1')
    }
  }, [document])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      alert('Vui lòng chọn file mới.')
      return
    }

    setSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('version', version.trim() || '1.1')
      if (notes) formData.append('notes', notes.trim())

      await api.addDocumentVersion(document.id, formData)
      onSuccess()
    } catch (err: any) {
      alert(err.message || 'Lỗi khi cập nhật phiên bản')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-2">
            <FileUp className="w-4 h-4 text-emerald-600" />
            <h3 className="font-bold text-slate-800 text-sm">Cập nhật phiên bản mới</h3>
          </div>
          <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-700">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs">
            <p className="font-bold text-slate-800">{document.title}</p>
            <p className="text-slate-500 font-mono mt-0.5">Bản hiện tại: v{document.version}</p>
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">File phiên bản mới</label>
            <input
              type="file"
              required
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) setFile(e.target.files[0])
              }}
              className="text-xs w-full text-slate-600"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Số hiệu phiên bản mới</label>
            <input
              type="text"
              required
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white font-mono"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">Ghi chú thay đổi (Changelog)</label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="VD: Cập nhật điều khoản thanh toán 2026..."
              className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl focus:bg-white"
            />
          </div>

          <div className="flex items-center justify-end space-x-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-3 py-1.5 text-xs text-slate-600 font-bold"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={submitting || !file}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-xs cursor-pointer disabled:opacity-50"
            >
              {submitting ? 'Đang lưu...' : 'Lưu phiên bản mới'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
