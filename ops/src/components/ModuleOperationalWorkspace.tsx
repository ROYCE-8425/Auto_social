import React, { useState, useEffect } from 'react'
import {
  X,
  Plus,
  Search,
  Filter,
  Users,
  FileText,
  BookOpen,
  BarChart3,
  Kanban,
  DollarSign,
  Calendar,
  Layers,
  CheckCircle2,
  Clock,
  AlertCircle,
  FolderGit2,
  Trash2,
  Edit,
  ExternalLink,
  MessageSquare,
  Paperclip,
  History,
  Send,
  Loader2,
  ArrowRight,
  ShieldCheck,
  Check,
  ChevronRight,
  FileCheck,
  Tag,
  Phone,
  Mail,
  UserCheck,
  RefreshCw,
} from 'lucide-react'
import {
  api,
  BusinessModule,
  ModuleRecord,
  ModuleActivity,
  ModuleComment,
  ModuleAttachment,
} from '../lib/api'

interface ModuleOperationalWorkspaceProps {
  module: BusinessModule
  isOpen: boolean
  onClose: () => void
  onModuleUpdated?: () => void
  onNavigate?: (tab: string) => void
}

export const ModuleOperationalWorkspace: React.FC<ModuleOperationalWorkspaceProps> = ({
  module,
  isOpen,
  onClose,
  onModuleUpdated,
  onNavigate,
}) => {
  const [records, setRecords] = useState<ModuleRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [selectedPriority, setSelectedPriority] = useState<string>('all')
  const [activeTab, setActiveTab] = useState<'records' | 'scope'>('records')

  // Chi tiết hồ sơ đang chọn
  const [selectedRecord, setSelectedRecord] = useState<ModuleRecord | null>(null)
  const [recordDetailLoading, setRecordDetailLoading] = useState(false)

  // Bình luận & Đính kèm
  const [newComment, setNewComment] = useState('')
  const [commentSubmitting, setCommentSubmitting] = useState(false)
  const [newAttName, setNewAttName] = useState('')
  const [newAttUrl, setNewAttUrl] = useState('')
  const [attSubmitting, setAttSubmitting] = useState(false)
  const [isAddingAttachment, setIsAddingAttachment] = useState(false)

  // Modal tạo hồ sơ mới
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [createSubmitting, setCreateSubmitting] = useState(false)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    status: 'new',
    priority: 'normal',
    owner_id: '',
    due_at: '',
    payload: {} as Record<string, any>,
  })

  // Khởi tạo form theo từng phân hệ
  const resetFormForModule = () => {
    const defaultStatus = module.workflows && module.workflows.length > 0 ? module.workflows[0].id : 'new'
    if (module.code === 'recruitment') {
      setFormData({
        title: '',
        description: '',
        status: defaultStatus,
        priority: 'high',
        owner_id: '',
        due_at: '',
        payload: {
          candidate_name: '',
          position: 'Lập trình viên / Kỹ thuật',
          phone: '',
          email: '',
          cv_link: '',
          interview_date: '',
          interviewer: '',
          notes: '',
        },
      })
    } else if (module.code === 'contract') {
      setFormData({
        title: '',
        description: '',
        status: defaultStatus,
        priority: 'normal',
        owner_id: '',
        due_at: '',
        payload: {
          contract_number: `HD-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
          party_a: 'Công ty TNHH Royce Shop',
          party_b: '',
          contract_value: 50000000,
          contract_type: 'Hợp đồng dịch vụ',
          signer: '',
          sign_date: new Date().toISOString().split('T')[0],
          expire_date: '',
          file_url: '',
        },
      })
    } else if (module.code === 'sop') {
      setFormData({
        title: '',
        description: '',
        status: defaultStatus,
        priority: 'normal',
        owner_id: '',
        due_at: '',
        payload: {
          sop_code: `SOP-OPS-${Math.floor(10 + Math.random() * 90)}`,
          version: 'v1.0',
          department: 'Chăm sóc khách hàng & Vận hành',
          author: '',
          approver: '',
          content_markdown: '',
        },
      })
    } else if (module.code === 'kpi') {
      setFormData({
        title: '',
        description: '',
        status: defaultStatus,
        priority: 'normal',
        owner_id: '',
        due_at: '',
        payload: {
          kpi_code: `KPI-${Math.floor(100 + Math.random() * 900)}`,
          period: `Tháng ${new Date().getMonth() + 1}/${new Date().getFullYear()}`,
          department: 'Kinh doanh & Bán lẻ',
          target_value: '100.000.000',
          actual_value: '0',
          unit: 'VND',
        },
      })
    } else if (module.code === 'finance') {
      setFormData({
        title: '',
        description: '',
        status: defaultStatus,
        priority: 'normal',
        owner_id: '',
        due_at: '',
        payload: {
          entry_type: 'Chi phí',
          amount: 5000000,
          requester: '',
          approver: '',
          payment_method: 'Chuyển khoản ngân hàng',
          invoice_url: '',
        },
      })
    } else if (module.code === 'calendar') {
      setFormData({
        title: '',
        description: '',
        status: defaultStatus,
        priority: 'normal',
        owner_id: '',
        due_at: '',
        payload: {
          event_type: 'Họp điều hành',
          start_time: '',
          location: 'Phòng họp trực tuyến Google Meet',
          participants: '',
        },
      })
    } else {
      setFormData({
        title: '',
        description: '',
        status: defaultStatus,
        priority: 'normal',
        owner_id: '',
        due_at: '',
        payload: {},
      })
    }
  }

  // Tải danh sách hồ sơ từ API
  const fetchRecords = async () => {
    setLoading(true)
    try {
      const res = await api.getModuleRecords(module.code, {
        status: selectedStatus === 'all' ? undefined : selectedStatus,
        priority: selectedPriority === 'all' ? undefined : selectedPriority,
        search: search.trim() || undefined,
      })
      if (res && res.ok && Array.isArray(res.records)) {
        setRecords(res.records)
      }
    } catch (err) {
      console.error('Lỗi tải danh sách hồ sơ module:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen) {
      fetchRecords()
      resetFormForModule()
    }
  }, [isOpen, module.code, selectedStatus, selectedPriority])

  // Lấy chi tiết hồ sơ khi người dùng bấm xem
  const loadRecordDetail = async (id: string) => {
    setRecordDetailLoading(true)
    try {
      const res = await api.getModuleRecord(module.code, id)
      if (res && res.ok && res.record) {
        setSelectedRecord(res.record)
      }
    } catch (err) {
      console.error('Lỗi tải chi tiết hồ sơ:', err)
    } finally {
      setRecordDetailLoading(false)
    }
  }

  // Chuyển đổi trạng thái hồ sơ nhanh
  const handleTransitionStatus = async (newStatus: string) => {
    if (!selectedRecord) return
    try {
      const res = await api.updateModuleRecord(module.code, selectedRecord.id, {
        status: newStatus,
      })
      if (res && res.ok && res.record) {
        setSelectedRecord(res.record)
        fetchRecords()
        if (onModuleUpdated) onModuleUpdated()
      }
    } catch (err) {
      alert('Không thể cập nhật trạng thái: ' + err)
    }
  }

  // Thêm bình luận
  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedRecord || !newComment.trim()) return
    setCommentSubmitting(true)
    try {
      const res = await api.addModuleComment(module.code, selectedRecord.id, newComment.trim())
      if (res && res.ok) {
        setNewComment('')
        loadRecordDetail(selectedRecord.id)
      }
    } catch (err) {
      alert('Lỗi thêm bình luận: ' + err)
    } finally {
      setCommentSubmitting(false)
    }
  }

  // Thêm tệp đính kèm
  const handleAddAttachment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedRecord || !newAttName.trim() || !newAttUrl.trim()) return
    setAttSubmitting(true)
    try {
      const res = await api.addModuleAttachment(module.code, selectedRecord.id, {
        file_name: newAttName.trim(),
        file_url: newAttUrl.trim(),
      })
      if (res && res.ok) {
        setNewAttName('')
        setNewAttUrl('')
        setIsAddingAttachment(false)
        loadRecordDetail(selectedRecord.id)
      }
    } catch (err) {
      alert('Lỗi thêm tệp đính kèm: ' + err)
    } finally {
      setAttSubmitting(false)
    }
  }

  // Xóa hồ sơ
  const handleDeleteRecord = async (id: string) => {
    if (!confirm('Bạn có chắc chắn muốn xóa hồ sơ này? Hành động này không thể hoàn tác.')) return
    try {
      const res = await api.deleteModuleRecord(module.code, id)
      if (res && res.ok) {
        if (selectedRecord?.id === id) {
          setSelectedRecord(null)
        }
        fetchRecords()
        if (onModuleUpdated) onModuleUpdated()
      }
    } catch (err) {
      alert('Lỗi xóa hồ sơ: ' + err)
    }
  }

  // Xử lý tạo mới hồ sơ
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim()) {
      alert('Vui lòng nhập tiêu đề hồ sơ')
      return
    }
    setCreateSubmitting(true)
    try {
      const res = await api.createModuleRecord(module.code, {
        title: formData.title.trim(),
        description: formData.description.trim(),
        status: formData.status,
        priority: formData.priority,
        owner_id: formData.owner_id.trim(),
        due_at: formData.due_at || null,
        payload: formData.payload,
      })
      if (res && res.ok && res.record) {
        setIsCreateModalOpen(false)
        resetFormForModule()
        fetchRecords()
        if (onModuleUpdated) onModuleUpdated()
        loadRecordDetail(res.record.id)
      }
    } catch (err) {
      alert('Lỗi tạo hồ sơ: ' + err)
    } finally {
      setCreateSubmitting(false)
    }
  }

  // Chọn icon tương ứng
  const getIcon = () => {
    switch (module.code) {
      case 'recruitment':
        return Users
      case 'contract':
        return FileText
      case 'sop':
        return BookOpen
      case 'kpi':
        return BarChart3
      case 'projects':
        return Kanban
      case 'finance':
        return DollarSign
      case 'calendar':
        return Calendar
      default:
        return Layers
    }
  }
  const ModuleIcon = getIcon()

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
      <div className="w-full max-w-5xl bg-white h-full shadow-2xl flex flex-col transform transition-transform duration-300 ease-out border-l border-slate-200">
        {/* ================= HEADER PHÂN HỆ ================= */}
        <div className="px-6 py-4 border-b border-slate-200/90 bg-white flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3.5">
            <div className={`w-11 h-11 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shrink-0 border border-blue-200/50 shadow-2xs`}>
              <ModuleIcon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h2 className="text-base font-bold text-slate-900">{module.name}</h2>
                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border inline-flex items-center space-x-1.5 ${
                  records.length > 0
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-blue-50 text-blue-700 border-blue-200'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${records.length > 0 ? 'bg-emerald-500 animate-pulse' : 'bg-blue-500'}`} />
                  <span>{records.length > 0 ? `Đang hoạt động (${records.length} hồ sơ)` : 'Đã kết nối vận hành'}</span>
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{module.description}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={fetchRecords}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-all cursor-pointer"
              title="Làm mới dữ liệu"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              type="button"
              onClick={() => {
                resetFormForModule()
                setIsCreateModalOpen(true)
              }}
              className="px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs flex items-center space-x-1.5 transition-all cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Tạo hồ sơ mới</span>
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-all cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* ================= TABS & FILTER BAR ================= */}
        <div className="px-6 py-2.5 bg-slate-50/80 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div className="flex items-center space-x-1 bg-slate-200/70 p-0.5 rounded-xl">
            <button
              type="button"
              onClick={() => setActiveTab('records')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                activeTab === 'records'
                  ? 'bg-white text-slate-900 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Danh sách hồ sơ ({records.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('scope')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                activeTab === 'scope'
                  ? 'bg-white text-slate-900 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Định chuẩn quy trình &amp; Phân vai
            </button>
          </div>

          {activeTab === 'records' && (
            <div className="flex items-center space-x-2 grow sm:grow-0">
              {/* Search */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchRecords()}
                  placeholder="Tìm kiếm hồ sơ..."
                  className="pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs w-48 sm:w-56 focus:outline-hidden focus:ring-1 focus:ring-blue-500"
                />
              </div>

              {/* Status Filter */}
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="px-2.5 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-700 cursor-pointer focus:outline-hidden"
              >
                <option value="all">Tất cả trạng thái</option>
                {module.workflows?.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.label}
                  </option>
                ))}
              </select>

              {/* Priority Filter */}
              <select
                value={selectedPriority}
                onChange={(e) => setSelectedPriority(e.target.value)}
                className="px-2.5 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-700 cursor-pointer focus:outline-hidden"
              >
                <option value="all">Mọi ưu tiên</option>
                <option value="urgent">Khẩn cấp</option>
                <option value="high">Cao</option>
                <option value="normal">Bình thường</option>
                <option value="low">Thấp</option>
              </select>
            </div>
          )}
        </div>

        {/* ================= BODY CONTENT ================= */}
        <div className="flex-1 overflow-hidden flex">
          {activeTab === 'scope' ? (
            /* Tab: Định chuẩn quy trình nghiệp vụ */
            <div className="flex-1 p-6 overflow-y-auto space-y-6">
              <div className="bg-slate-50 border border-slate-200/90 rounded-2xl p-5 space-y-4">
                <div className="space-y-1.5">
                  <div className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                    <BookOpen className="w-4 h-4 text-blue-600" />
                    <span>Phạm vi định chuẩn nghiệp vụ:</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed pl-6">
                    {module.description} Hệ thống hỗ trợ lưu trữ hồ sơ, quản trị luồng xử lý theo các bước quy định, đảm bảo tính minh bạch và truy vết lịch sử hoạt động.
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-200/70 space-y-1.5">
                  <div className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>Quy trình chuyển đổi trạng thái (Workflow):</span>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 pl-6 pt-1">
                    {module.workflows?.map((wf, idx) => (
                      <React.Fragment key={wf.id}>
                        <div className="px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-800 shadow-2xs flex items-center space-x-1.5">
                          <span className="w-2 h-2 rounded-full bg-blue-500" />
                          <span>{wf.label}</span>
                        </div>
                        {idx < (module.workflows?.length || 0) - 1 && (
                          <ChevronRight className="w-3.5 h-3.5 text-slate-300" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              </div>

              <div className="border border-slate-200 rounded-2xl p-5 bg-white space-y-3">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Trạng thái kết nối dữ liệu:
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
                    <div className="text-xs text-slate-500">Tổng số hồ sơ</div>
                    <div className="text-lg font-bold text-slate-900 mt-0.5">{records.length}</div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
                    <div className="text-xs text-slate-500">Cơ chế lưu trữ</div>
                    <div className="text-xs font-bold text-emerald-600 mt-1">SQLite chuẩn hóa (WAL)</div>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
                    <div className="text-xs text-slate-500">Vết kiểm toán (Audit)</div>
                    <div className="text-xs font-bold text-blue-600 mt-1">Ghi nhận tự động 100%</div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Tab: Danh sách hồ sơ thật & Drawer chi tiết */
            <div className="flex-1 flex overflow-hidden">
              {/* Cột danh sách hồ sơ */}
              <div className={`overflow-y-auto p-6 space-y-3 transition-all ${
                selectedRecord ? 'w-1/2 border-r border-slate-200 hidden lg:block' : 'w-full'
              }`}>
                {loading ? (
                  <div className="py-20 text-center space-y-3">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto" />
                    <p className="text-xs text-slate-500">Đang tải danh sách hồ sơ...</p>
                  </div>
                ) : records.length === 0 ? (
                  /* ================= EMPTY STATE ================= */
                  <div className="py-16 text-center border-2 border-dashed border-slate-200 rounded-3xl p-8 space-y-4 bg-slate-50/50">
                    <div className="w-14 h-14 rounded-3xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto border border-blue-100 shadow-xs">
                      <ModuleIcon className="w-7 h-7" />
                    </div>
                    <div className="space-y-1">
                      <h3 className="font-bold text-slate-800 text-sm">Chưa có hồ sơ nào trong phân hệ</h3>
                      <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                        Phân hệ đã được kết nối cơ sở dữ liệu thật. Bạn có thể bắt đầu tạo hồ sơ đầu tiên hoặc nhận dữ liệu tự động từ các luồng tự động hóa.
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        resetFormForModule()
                        setIsCreateModalOpen(true)
                      }}
                      className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs inline-flex items-center space-x-1.5 transition-all cursor-pointer"
                    >
                      <Plus className="w-4 h-4" />
                      <span>Tạo hồ sơ đầu tiên</span>
                    </button>
                  </div>
                ) : (
                  /* Danh sách thẻ hồ sơ */
                  <div className="space-y-2.5">
                    {records.map((rec) => {
                      const isSelected = selectedRecord?.id === rec.id
                      const workflow = module.workflows?.find((w) => w.id === rec.status)
                      return (
                        <div
                          key={rec.id}
                          onClick={() => loadRecordDetail(rec.id)}
                          className={`p-4 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between space-y-2.5 ${
                            isSelected
                              ? 'bg-blue-50/40 border-blue-500/80 shadow-xs ring-1 ring-blue-500/30'
                              : 'bg-white border-slate-200/90 hover:border-slate-300 hover:shadow-xs'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="space-y-1 grow">
                              <div className="flex items-center space-x-2">
                                <span className="font-bold text-xs text-slate-900 hover:text-blue-600 transition-colors">
                                  {rec.title}
                                </span>
                                {rec.priority === 'urgent' && (
                                  <span className="px-1.5 py-0.5 rounded-md bg-rose-50 text-rose-600 text-[10px] font-bold border border-rose-200">
                                    Khẩn cấp
                                  </span>
                                )}
                              </div>
                              {rec.description && (
                                <p className="text-[11px] text-slate-500 line-clamp-2 leading-relaxed">
                                  {rec.description}
                                </p>
                              )}
                            </div>

                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold shrink-0 border ${
                              rec.status === 'passed' || rec.status === 'signed' || rec.status === 'published' || rec.status === 'completed' || rec.status === 'paid'
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : rec.status === 'interviewing' || rec.status === 'reviewing' || rec.status === 'in_progress'
                                ? 'bg-purple-50 text-purple-700 border-purple-200'
                                : rec.status === 'rejected' || rec.status === 'expired' || rec.status === 'behind'
                                ? 'bg-rose-50 text-rose-700 border-rose-200'
                                : 'bg-slate-100 text-slate-700 border-slate-200'
                            }`}>
                              {workflow?.label || rec.status}
                            </span>
                          </div>

                          {/* Quick attributes preview */}
                          {rec.payload && Object.keys(rec.payload).length > 0 && (
                            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-500 pt-1 border-t border-slate-100">
                              {rec.payload.phone && (
                                <span className="inline-flex items-center space-x-1">
                                  <Phone className="w-3 h-3 text-slate-400" />
                                  <span>{rec.payload.phone}</span>
                                </span>
                              )}
                              {rec.payload.position && (
                                <span className="inline-flex items-center space-x-1">
                                  <UserCheck className="w-3 h-3 text-slate-400" />
                                  <span>{rec.payload.position}</span>
                                </span>
                              )}
                              {rec.payload.contract_number && (
                                <span className="inline-flex items-center space-x-1">
                                  <FileText className="w-3 h-3 text-slate-400" />
                                  <span>{rec.payload.contract_number}</span>
                                </span>
                              )}
                              {rec.payload.sop_code && (
                                <span className="inline-flex items-center space-x-1">
                                  <BookOpen className="w-3 h-3 text-slate-400" />
                                  <span>{rec.payload.sop_code}</span>
                                </span>
                              )}
                              {rec.payload.contract_value && (
                                <span className="font-semibold text-slate-700">
                                  {Number(rec.payload.contract_value).toLocaleString('vi-VN')} đ
                                </span>
                              )}
                            </div>
                          )}

                          <div className="flex items-center justify-between pt-1 text-[11px] text-slate-400">
                            <span className="truncate max-w-[150px]">
                              {rec.owner_id ? `Phụ trách: ${rec.owner_id}` : 'Chưa gán'}
                            </span>
                            <span className="text-[10px]">
                              {new Date(rec.created_at * 1000).toLocaleDateString('vi-VN')}
                            </span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* Cột chi tiết một hồ sơ (Detail Pane) */}
              {selectedRecord ? (
                <div className="w-full lg:w-1/2 overflow-y-auto p-6 space-y-6 bg-slate-50/30">
                  {recordDetailLoading ? (
                    <div className="py-20 text-center space-y-2">
                      <Loader2 className="w-6 h-6 animate-spin text-blue-600 mx-auto" />
                      <p className="text-xs text-slate-500">Đang tải chi tiết hồ sơ...</p>
                    </div>
                  ) : (
                    <>
                      {/* Record Top Bar */}
                      <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-200">
                        <div className="space-y-1">
                          <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                            Mã: {selectedRecord.id}
                          </span>
                          <h3 className="font-bold text-slate-900 text-base">{selectedRecord.title}</h3>
                        </div>
                        <div className="flex items-center space-x-1">
                          <button
                            type="button"
                            onClick={() => handleDeleteRecord(selectedRecord.id)}
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                            title="Xóa hồ sơ này"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => setSelectedRecord(null)}
                            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg transition-colors cursor-pointer lg:hidden"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      {/* Trạng thái Workflow & Nút chuyển bước */}
                      <div className="bg-white border border-slate-200/90 rounded-2xl p-4 space-y-2.5">
                        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                          Chuyển bước quy trình:
                        </div>
                        <div className="flex flex-wrap items-center gap-1.5">
                          {module.workflows?.map((wf) => {
                            const isCurrent = selectedRecord.status === wf.id
                            return (
                              <button
                                key={wf.id}
                                type="button"
                                onClick={() => handleTransitionStatus(wf.id)}
                                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1 ${
                                  isCurrent
                                    ? 'bg-blue-600 text-white shadow-xs'
                                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                }`}
                              >
                                {isCurrent && <Check className="w-3 h-3" />}
                                <span>{wf.label}</span>
                              </button>
                            )
                          })}
                        </div>
                      </div>

                      {/* Chi tiết Payload theo phân hệ */}
                      <div className="bg-white border border-slate-200/90 rounded-2xl p-4 space-y-3">
                        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                          Thông tin chi tiết hồ sơ:
                        </div>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <span className="text-slate-400 text-[11px]">Người phụ trách:</span>
                            <div className="font-semibold text-slate-800">{selectedRecord.owner_id || 'Chưa gán'}</div>
                          </div>
                          <div>
                            <span className="text-slate-400 text-[11px]">Độ ưu tiên:</span>
                            <div className="font-semibold text-slate-800 capitalize">{selectedRecord.priority}</div>
                          </div>
                          <div>
                            <span className="text-slate-400 text-[11px]">Ngày tạo:</span>
                            <div className="font-semibold text-slate-800">
                              {new Date(selectedRecord.created_at * 1000).toLocaleString('vi-VN')}
                            </div>
                          </div>
                          <div>
                            <span className="text-slate-400 text-[11px]">Nguồn phát sinh:</span>
                            <div className="font-semibold text-slate-800 capitalize">{selectedRecord.source || 'Thủ công'}</div>
                          </div>
                        </div>

                        {selectedRecord.description && (
                          <div className="pt-2 border-t border-slate-100">
                            <span className="text-slate-400 text-[11px]">Mô tả / Ghi chú:</span>
                            <p className="text-xs text-slate-700 mt-0.5 leading-relaxed">
                              {selectedRecord.description}
                            </p>
                          </div>
                        )}

                        {/* Các trường động trong payload */}
                        {selectedRecord.payload && Object.keys(selectedRecord.payload).length > 0 && (
                          <div className="pt-2 border-t border-slate-100 space-y-2">
                            <div className="text-[11px] font-bold text-slate-600">Dữ liệu phân hệ mở rộng:</div>
                            <div className="bg-slate-50/80 rounded-xl p-3 space-y-1.5 text-xs">
                              {Object.entries(selectedRecord.payload).map(([k, v]) => (
                                <div key={k} className="flex justify-between items-start gap-2">
                                  <span className="text-slate-400 text-[11px] font-mono">{k}:</span>
                                  {typeof v === 'string' && (v.startsWith('http://') || v.startsWith('https://')) ? (
                                    <a
                                      href={v}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="font-medium text-blue-600 hover:underline flex items-center space-x-1"
                                    >
                                      <span className="truncate max-w-[200px]">{v}</span>
                                      <ExternalLink className="w-3 h-3 shrink-0" />
                                    </a>
                                  ) : (
                                    <span className="font-medium text-slate-800 text-right">
                                      {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                                    </span>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Tệp đính kèm & Tài liệu liên kết */}
                      <div className="bg-white border border-slate-200/90 rounded-2xl p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                            <Paperclip className="w-3.5 h-3.5 text-slate-500" />
                            <span>Tài liệu &amp; Tệp đính kèm ({selectedRecord.attachments?.length || 0}):</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => setIsAddingAttachment(!isAddingAttachment)}
                            className="text-xs text-blue-600 font-semibold hover:underline flex items-center space-x-1 cursor-pointer"
                          >
                            <Plus className="w-3 h-3" />
                            <span>Đính kèm link/file</span>
                          </button>
                        </div>

                        {/* Form thêm đính kèm */}
                        {isAddingAttachment && (
                          <form onSubmit={handleAddAttachment} className="p-3 bg-slate-50 rounded-xl space-y-2 border border-slate-200">
                            <input
                              type="text"
                              value={newAttName}
                              onChange={(e) => setNewAttName(e.target.value)}
                              placeholder="Tên tệp (vd: CV_Ung_Vien.pdf)"
                              className="w-full px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-hidden"
                              required
                            />
                            <input
                              type="text"
                              value={newAttUrl}
                              onChange={(e) => setNewAttUrl(e.target.value)}
                              placeholder="Đường dẫn URL / Link Drive (https://...)"
                              className="w-full px-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-hidden"
                              required
                            />
                            <div className="flex justify-end space-x-2">
                              <button
                                type="button"
                                onClick={() => setIsAddingAttachment(false)}
                                className="px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-200 rounded-lg"
                              >
                                Hủy
                              </button>
                              <button
                                type="submit"
                                disabled={attSubmitting}
                                className="px-3 py-1 text-xs bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50"
                              >
                                {attSubmitting ? 'Đang lưu...' : 'Thêm tệp'}
                              </button>
                            </div>
                          </form>
                        )}

                        {selectedRecord.attachments && selectedRecord.attachments.length > 0 ? (
                          <div className="space-y-1.5">
                            {selectedRecord.attachments.map((att) => (
                              <div
                                key={att.id}
                                className="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-200/80 text-xs hover:bg-slate-100 transition-colors"
                              >
                                <div className="flex items-center space-x-2 truncate">
                                  <FileText className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                                  <span className="font-semibold text-slate-800 truncate">{att.file_name}</span>
                                </div>
                                <a
                                  href={att.file_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-blue-600 hover:text-blue-800 font-medium flex items-center space-x-1 shrink-0 ml-2"
                                >
                                  <span>Mở</span>
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-slate-400 italic">Chưa có tệp đính kèm nào.</p>
                        )}
                      </div>

                      {/* Trao đổi & Bình luận nội bộ */}
                      <div className="bg-white border border-slate-200/90 rounded-2xl p-4 space-y-3">
                        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                          <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
                          <span>Trao đổi &amp; Ghi chú ({selectedRecord.comments?.length || 0}):</span>
                        </div>

                        {selectedRecord.comments && selectedRecord.comments.length > 0 && (
                          <div className="space-y-2.5 max-h-48 overflow-y-auto pr-1">
                            {selectedRecord.comments.map((cmt) => (
                              <div key={cmt.id} className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 text-xs space-y-1">
                                <div className="flex items-center justify-between text-[10px] text-slate-400">
                                  <span className="font-bold text-slate-700">{cmt.actor_id}</span>
                                  <span>{new Date(cmt.created_at * 1000).toLocaleString('vi-VN')}</span>
                                </div>
                                <p className="text-slate-800 leading-relaxed">{cmt.content}</p>
                              </div>
                            ))}
                          </div>
                        )}

                        <form onSubmit={handleAddComment} className="flex items-center space-x-2 pt-1">
                          <input
                            type="text"
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            placeholder="Nhập ghi chú thảo luận..."
                            className="flex-1 px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-hidden focus:bg-white focus:ring-1 focus:ring-blue-500"
                          />
                          <button
                            type="submit"
                            disabled={commentSubmitting || !newComment.trim()}
                            className="p-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-40 transition-all cursor-pointer"
                          >
                            <Send className="w-3.5 h-3.5" />
                          </button>
                        </form>
                      </div>

                      {/* Vết kiểm toán (Activity Timeline) */}
                      <div className="bg-white border border-slate-200/90 rounded-2xl p-4 space-y-3">
                        <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                          <History className="w-3.5 h-3.5 text-slate-500" />
                          <span>Nhật ký vết kiểm toán (Audit Trail):</span>
                        </div>

                        <div className="space-y-3 pl-2 border-l-2 border-slate-100 max-h-48 overflow-y-auto">
                          {selectedRecord.activities?.map((act) => (
                            <div key={act.id} className="relative pl-3 text-xs space-y-0.5">
                              <span className="absolute -left-[19px] top-1 w-2 h-2 rounded-full bg-blue-500 ring-2 ring-white" />
                              <div className="flex items-center justify-between text-[10px] text-slate-400">
                                <span className="font-semibold text-slate-600">{act.actor_id}</span>
                                <span>{new Date(act.created_at * 1000).toLocaleTimeString('vi-VN')}</span>
                              </div>
                              <p className="text-slate-800 font-medium">
                                {act.action === 'created'
                                  ? 'Đã tạo mới hồ sơ này'
                                  : act.action === 'status_changed'
                                  ? `Đã đổi trạng thái từ "${act.before?.status}" sang "${act.after?.status}"`
                                  : act.action === 'comment_added'
                                  ? 'Đã thêm một bình luận'
                                  : act.action === 'attachment_added'
                                  ? `Đã đính kèm tệp "${act.after?.file_name || 'tài liệu'}"`
                                  : 'Đã cập nhật thông tin hồ sơ'}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {/* ================= MODAL TẠO HỒ SƠ MỚI ================= */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-60 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Plus className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Tạo hồ sơ {module.name}</h3>
                  <p className="text-[11px] text-slate-400">Nhập thông tin nghiệp vụ thực tế</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(false)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-3.5">
              {/* Tiêu đề chung */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Tiêu đề hồ sơ <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder={
                    module.code === 'recruitment'
                      ? 'Vd: Nguyễn Văn A - Lập trình viên React'
                      : module.code === 'contract'
                      ? 'Vd: Hợp đồng cung cấp giải pháp Marketing - Cty ABC'
                      : module.code === 'sop'
                      ? 'Vd: Quy trình tiếp nhận và xử lý khiếu nại khách hàng'
                      : 'Tiêu đề hồ sơ nghiệp vụ'
                  }
                  className="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-hidden focus:ring-1 focus:ring-blue-500 font-medium"
                  required
                />
              </div>

              {/* Form riêng theo từng phân hệ */}
              {module.code === 'recruitment' && (
                <div className="space-y-2.5 p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 text-xs">
                  <div className="font-bold text-slate-800 text-[11px] uppercase tracking-wider">
                    Thông tin ứng viên &amp; Tuyển dụng:
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Vị trí tuyển dụng:</label>
                      <input
                        type="text"
                        value={formData.payload.position || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, position: e.target.value },
                          })
                        }
                        placeholder="Vd: Nhân viên Sale, CSKH..."
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Số điện thoại:</label>
                      <input
                        type="text"
                        value={formData.payload.phone || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, phone: e.target.value },
                          })
                        }
                        placeholder="0912345678"
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[11px] text-slate-600 block mb-0.5">Link CV / Portfolio:</label>
                    <input
                      type="text"
                      value={formData.payload.cv_link || ''}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          payload: { ...formData.payload, cv_link: e.target.value },
                        })
                      }
                      placeholder="https://drive.google.com/..."
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Người phỏng vấn:</label>
                      <input
                        type="text"
                        value={formData.payload.interviewer || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, interviewer: e.target.value },
                          })
                        }
                        placeholder="HR_Mai / Tech_Nam"
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Lịch hẹn phỏng vấn:</label>
                      <input
                        type="datetime-local"
                        value={formData.payload.interview_date || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, interview_date: e.target.value },
                          })
                        }
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                  </div>
                </div>
              )}

              {module.code === 'contract' && (
                <div className="space-y-2.5 p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 text-xs">
                  <div className="font-bold text-slate-800 text-[11px] uppercase tracking-wider">
                    Thông tin hợp đồng &amp; Pháp lý:
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Số hiệu HĐ:</label>
                      <input
                        type="text"
                        value={formData.payload.contract_number || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, contract_number: e.target.value },
                          })
                        }
                        placeholder="HD-2026-001"
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Giá trị hợp đồng (VND):</label>
                      <input
                        type="number"
                        value={formData.payload.contract_value || 0}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, contract_value: Number(e.target.value) },
                          })
                        }
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Bên A (Chủ thể):</label>
                      <input
                        type="text"
                        value={formData.payload.party_a || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, party_a: e.target.value },
                          })
                        }
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Bên B (Đối tác/Khách):</label>
                      <input
                        type="text"
                        value={formData.payload.party_b || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, party_b: e.target.value },
                          })
                        }
                        placeholder="Tên doanh nghiệp / cá nhân"
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Ngày ký kết:</label>
                      <input
                        type="date"
                        value={formData.payload.sign_date || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, sign_date: e.target.value },
                          })
                        }
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Ngày hết hạn:</label>
                      <input
                        type="date"
                        value={formData.payload.expire_date || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, expire_date: e.target.value },
                          })
                        }
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                  </div>
                </div>
              )}

              {module.code === 'sop' && (
                <div className="space-y-2.5 p-3.5 bg-slate-50 rounded-2xl border border-slate-200/80 text-xs">
                  <div className="font-bold text-slate-800 text-[11px] uppercase tracking-wider">
                    Quy chuẩn SOP nội bộ:
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Mã SOP:</label>
                      <input
                        type="text"
                        value={formData.payload.sop_code || ''}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, sop_code: e.target.value },
                          })
                        }
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-mono"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] text-slate-600 block mb-0.5">Phiên bản:</label>
                      <input
                        type="text"
                        value={formData.payload.version || 'v1.0'}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            payload: { ...formData.payload, version: e.target.value },
                          })
                        }
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-mono"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[11px] text-slate-600 block mb-0.5">Phòng ban áp dụng:</label>
                    <input
                      type="text"
                      value={formData.payload.department || ''}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          payload: { ...formData.payload, department: e.target.value },
                        })
                      }
                      placeholder="Chăm sóc khách hàng & Bán lẻ"
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] text-slate-600 block mb-0.5">Nội dung quy trình (Markdown):</label>
                    <textarea
                      rows={3}
                      value={formData.payload.content_markdown || ''}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          payload: { ...formData.payload, content_markdown: e.target.value },
                        })
                      }
                      placeholder="Mô tả các bước thực hiện..."
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-mono"
                    />
                  </div>
                </div>
              )}

              {/* Trạng thái ban đầu & Phụ trách */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Trạng thái ban đầu:</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-hidden"
                  >
                    {module.workflows?.map((w) => (
                      <option key={w.id} value={w.id}>
                        {w.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Mức độ ưu tiên:</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-hidden"
                  >
                    <option value="urgent">Khẩn cấp</option>
                    <option value="high">Cao</option>
                    <option value="normal">Bình thường</option>
                    <option value="low">Thấp</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Người phụ trách:</label>
                <input
                  type="text"
                  value={formData.owner_id}
                  onChange={(e) => setFormData({ ...formData, owner_id: e.target.value })}
                  placeholder="Vd: Nguyễn Thị Mai"
                  className="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-hidden"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Mô tả tóm tắt:</label>
                <textarea
                  rows={2}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Ghi chú ngắn về hồ sơ..."
                  className="w-full px-3 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-hidden"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={createSubmitting}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs shadow-xs transition-all disabled:opacity-50 flex items-center space-x-1.5"
                >
                  {createSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
                  <span>Lưu hồ sơ mới</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
