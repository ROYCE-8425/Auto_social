import React, { useState, useEffect } from 'react'
import {
  CheckSquare,
  Clock,
  Plus,
  ArrowRight,
  CheckCircle2,
  RefreshCw,
  AlertCircle,
  Tag,
  Filter,
  ChevronDown,
  Search,
  MoreVertical,
  Calendar,
  User,
  X,
  ChevronRight,
  Flame,
  LayoutGrid,
  List,
  Sparkles,
} from 'lucide-react'
import { api, KanbanTask, KanbanBoardView } from '../lib/api'
import { formatTime, timeAgo } from '../lib/utils'

export interface TaskItem {
  id: string
  title: string
  customer: string
  tag: string
  tagColor: 'slate' | 'amber' | 'rose' | 'orange' | 'emerald' | 'blue'
  time: string
  isUrgent?: boolean
  columnId: 'todo' | 'in_progress' | 'waiting' | 'done'
  assignee: {
    code: string
    name: string
    bg: string
  }
}

const initialTasksData: TaskItem[] = [
  // Cột 1: Cần làm (12)
  {
    id: 'task_1',
    title: 'Hỗ trợ cài đặt game cho khách',
    customer: 'Nguyễn Văn An',
    tag: 'Hỗ trợ kỹ thuật',
    tagColor: 'slate',
    time: 'Hôm nay',
    isUrgent: true,
    columnId: 'todo',
    assignee: { code: 'NV', name: 'Nguyễn Văn', bg: 'bg-slate-800 text-white' },
  },
  {
    id: 'task_2',
    title: 'Gửi bảng giá cho khách',
    customer: 'Trần Thị Mai',
    tag: 'Tư vấn',
    tagColor: 'amber',
    time: 'Hôm nay',
    isUrgent: true,
    columnId: 'todo',
    assignee: { code: 'LT', name: 'Lê Tuấn', bg: 'bg-blue-800 text-white' },
  },
  {
    id: 'task_3',
    title: 'Kiểm tra đơn hàng lỗi',
    customer: '#DHT2345',
    tag: 'Đơn hàng',
    tagColor: 'rose',
    time: 'Hôm nay',
    isUrgent: true,
    columnId: 'todo',
    assignee: { code: 'NV', name: 'Nguyễn Văn', bg: 'bg-slate-800 text-white' },
  },

  // Cột 2: Đang xử lý (8)
  {
    id: 'task_4',
    title: 'Khách báo lỗi không vào game',
    customer: 'Lê Hoàng Nam',
    tag: 'Khiếu nại',
    tagColor: 'amber',
    time: '2 giờ trước',
    isUrgent: false,
    columnId: 'in_progress',
    assignee: { code: 'TH', name: 'Trần Hùng', bg: 'bg-slate-800 text-white' },
  },
  {
    id: 'task_5',
    title: 'Tư vấn gói nâng cấp',
    customer: 'Phạm Minh Tú',
    tag: 'Tư vấn',
    tagColor: 'emerald',
    time: '3 giờ trước',
    isUrgent: false,
    columnId: 'in_progress',
    assignee: { code: 'NV', name: 'Nguyễn Văn', bg: 'bg-blue-800 text-white' },
  },
  {
    id: 'task_6',
    title: 'Liên hệ lại khách chưa phản hồi',
    customer: 'Đỗ Quang Huy',
    tag: 'Follow up',
    tagColor: 'slate',
    time: '4 giờ trước',
    isUrgent: false,
    columnId: 'in_progress',
    assignee: { code: 'LT', name: 'Lê Tuấn', bg: 'bg-blue-800 text-white' },
  },

  // Cột 3: Chờ phản hồi (5)
  {
    id: 'task_7',
    title: 'Chờ khách gửi thông tin',
    customer: 'Nguyễn Thảo Vy',
    tag: 'Chờ khách',
    tagColor: 'amber',
    time: '1 ngày trước',
    isUrgent: false,
    columnId: 'waiting',
    assignee: { code: 'NV', name: 'Nguyễn Văn', bg: 'bg-slate-800 text-white' },
  },
  {
    id: 'task_8',
    title: 'Đã gửi hướng dẫn, chờ test',
    customer: 'Trần Gia Bảo',
    tag: 'Chờ khách',
    tagColor: 'amber',
    time: '1 ngày trước',
    isUrgent: false,
    columnId: 'waiting',
    assignee: { code: 'TM', name: 'Trần Minh', bg: 'bg-blue-800 text-white' },
  },

  // Cột 4: Hoàn tất (28)
  {
    id: 'task_9',
    title: 'Đã cài đặt thành công',
    customer: 'Bùi Minh Khoa',
    tag: 'Hoàn tất',
    tagColor: 'emerald',
    time: 'Hôm qua',
    isUrgent: false,
    columnId: 'done',
    assignee: { code: 'NV', name: 'Nguyễn Văn', bg: 'bg-slate-800 text-white' },
  },
  {
    id: 'task_10',
    title: 'Đã gửi key game',
    customer: 'Vũ Thị Hằng',
    tag: 'Hoàn tất',
    tagColor: 'emerald',
    time: 'Hôm qua',
    isUrgent: false,
    columnId: 'done',
    assignee: { code: 'LT', name: 'Lê Tuấn', bg: 'bg-blue-800 text-white' },
  },
  {
    id: 'task_11',
    title: 'Đã xử lý khiếu nại',
    customer: 'Phạm Quốc Đạt',
    tag: 'Hoàn tất',
    tagColor: 'emerald',
    time: '20/04',
    isUrgent: false,
    columnId: 'done',
    assignee: { code: 'NV', name: 'Nguyễn Văn', bg: 'bg-slate-800 text-white' },
  },
]

const staffList = [
  { code: 'all', name: 'Tất cả nhân viên' },
  { code: 'NV', name: 'Nguyễn Văn (NV)', bg: 'bg-slate-800 text-white' },
  { code: 'LT', name: 'Lê Tuấn (LT)', bg: 'bg-blue-800 text-white' },
  { code: 'TH', name: 'Trần Hùng (TH)', bg: 'bg-slate-800 text-white' },
  { code: 'TM', name: 'Trần Minh (TM)', bg: 'bg-blue-800 text-white' },
]

export const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<TaskItem[]>(initialTasksData)
  const [viewMode, setViewMode] = useState<'kanban' | 'list'>('kanban')
  const [selectedStaff, setSelectedStaff] = useState<string>('all')
  const [selectedTagFilter, setSelectedTagFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [isFilterOpen, setIsFilterOpen] = useState<boolean>(false)

  // Add Task Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false)
  const [targetColForAdd, setTargetColForAdd] = useState<'todo' | 'in_progress' | 'waiting' | 'done'>('todo')
  const [newTitle, setNewTitle] = useState<string>('')
  const [newCustomer, setNewCustomer] = useState<string>('')
  const [newTag, setNewTag] = useState<string>('Hỗ trợ kỹ thuật')
  const [newAssignee, setNewAssignee] = useState<string>('NV')

  // Real backend board sync
  const [board, setBoard] = useState<KanbanBoardView | null>(null)
  const [refreshing, setRefreshing] = useState<boolean>(false)

  const loadBackendTasks = async () => {
    try {
      const res = await api.getTasks()
      if (res && res.columns) {
        setBoard(res)
      }
    } catch (_) {}
  }

  useEffect(() => {
    loadBackendTasks()
  }, [])

  const handleMoveTask = (taskId: string, targetCol: 'todo' | 'in_progress' | 'waiting' | 'done') => {
    setTasks((prev) =>
      prev.map((t) => (t.id === taskId ? { ...t, columnId: targetCol } : t))
    )
  }

  const handleCreateTask = (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim()) return

    const selectedStaffObj = staffList.find((s) => s.code === newAssignee) || staffList[1]
    const tagColor: TaskItem['tagColor'] =
      newTag === 'Tư vấn' ? 'amber' :
      newTag === 'Khiếu nại' ? 'orange' :
      newTag === 'Đơn hàng' ? 'rose' :
      newTag === 'Hoàn tất' ? 'emerald' : 'slate'

    const newTask: TaskItem = {
      id: `task_${Date.now()}`,
      title: newTitle.trim(),
      customer: newCustomer.trim() || 'Khách hàng mới',
      tag: newTag,
      tagColor,
      time: 'Vừa tạo',
      isUrgent: targetColForAdd === 'todo',
      columnId: targetColForAdd,
      assignee: {
        code: selectedStaffObj.code,
        name: selectedStaffObj.name,
        bg: selectedStaffObj.bg || 'bg-slate-800 text-white',
      },
    }

    setTasks((prev) => [newTask, ...prev])
    setIsAddModalOpen(false)
    setNewTitle('')
    setNewCustomer('')
  }

  // Filter tasks based on staff, tag, and search query
  const filteredTasks = tasks.filter((t) => {
    if (selectedStaff !== 'all' && t.assignee.code !== selectedStaff) return false
    if (selectedTagFilter !== 'all' && t.tag !== selectedTagFilter) return false
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      return (
        t.title.toLowerCase().includes(q) ||
        t.customer.toLowerCase().includes(q) ||
        t.tag.toLowerCase().includes(q)
      )
    }
    return true
  })

  // Columns definition matching mockup
  const columnsConfig = [
    {
      id: 'todo' as const,
      title: 'Cần làm',
      count: 12,
      headerColor: 'text-slate-900',
      badgeBg: 'bg-slate-100 text-slate-700',
      columnBg: 'bg-slate-50/70 border-slate-200/80',
    },
    {
      id: 'in_progress' as const,
      title: 'Đang xử lý',
      count: 8,
      headerColor: 'text-blue-600',
      badgeBg: 'bg-blue-50 text-blue-700',
      columnBg: 'bg-blue-50/20 border-blue-100',
    },
    {
      id: 'waiting' as const,
      title: 'Chờ phản hồi',
      count: 5,
      headerColor: 'text-amber-600',
      badgeBg: 'bg-amber-50 text-amber-700',
      columnBg: 'bg-amber-50/20 border-amber-100',
    },
    {
      id: 'done' as const,
      title: 'Hoàn tất',
      count: 28,
      headerColor: 'text-emerald-600',
      badgeBg: 'bg-emerald-50 text-emerald-700',
      columnBg: 'bg-emerald-50/20 border-emerald-100',
    },
  ]

  const tagColorClasses: Record<TaskItem['tagColor'], string> = {
    slate: 'bg-slate-100 text-slate-600 border border-slate-200',
    amber: 'bg-amber-50 text-amber-700 border border-amber-200',
    rose: 'bg-rose-50 text-rose-600 border border-rose-200',
    orange: 'bg-amber-50 text-amber-700 border border-amber-200',
    emerald: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    blue: 'bg-blue-50 text-blue-700 border border-blue-200',
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* ================= PAGE HEADER & CONTROLS ================= */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Việc cần làm</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Quản lý công việc, yêu cầu hỗ trợ và theo dõi tiến độ.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* View Mode Toggle: Kanban / Danh sách */}
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200/80">
            <button
              type="button"
              onClick={() => setViewMode('kanban')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                viewMode === 'kanban'
                  ? 'bg-blue-600 text-white shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Kanban</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer flex items-center space-x-1.5 ${
                viewMode === 'list'
                  ? 'bg-blue-600 text-white shadow-2xs font-semibold'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <List className="w-3.5 h-3.5" />
              <span>Danh sách</span>
            </button>
          </div>

          {/* Filter button */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold transition-colors cursor-pointer ${
                isFilterOpen || selectedTagFilter !== 'all'
                  ? 'bg-blue-50 border-blue-200 text-blue-600'
                  : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50 shadow-2xs'
              }`}
            >
              <Filter className="w-3.5 h-3.5" />
              <span>Bộ lọc</span>
              {selectedTagFilter !== 'all' && (
                <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
              )}
            </button>

            {/* Filter Dropdown Popover */}
            {isFilterOpen && (
              <div className="absolute right-0 top-full mt-2 w-56 bg-white border border-slate-200 rounded-2xl shadow-xl p-3 z-30 space-y-2.5 animate-in fade-in zoom-in-95 duration-150">
                <div className="flex items-center justify-between pb-1 border-b border-slate-100">
                  <span className="text-xs font-bold text-slate-800">Lọc theo thẻ tag</span>
                  <button
                    type="button"
                    onClick={() => setIsFilterOpen(false)}
                    className="text-slate-400 hover:text-slate-600 p-0.5"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
                <div className="space-y-1">
                  {['all', 'Hỗ trợ kỹ thuật', 'Tư vấn', 'Khiếu nại', 'Đơn hàng', 'Follow up', 'Chờ khách', 'Hoàn tất'].map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => {
                        setSelectedTagFilter(t)
                        setIsFilterOpen(false)
                      }}
                      className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        selectedTagFilter === t
                          ? 'bg-blue-50 text-blue-700 font-bold'
                          : 'text-slate-600 hover:bg-slate-50'
                      }`}
                    >
                      {t === 'all' ? 'Tất cả các thẻ' : t}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Staff Select Dropdown */}
          <div className="relative">
            <select
              value={selectedStaff}
              onChange={(e) => setSelectedStaff(e.target.value)}
              className="appearance-none bg-white border border-slate-200 text-slate-700 rounded-xl px-3 py-1.5 pr-8 text-xs font-semibold hover:bg-slate-50 shadow-2xs focus:outline-none focus:ring-2 focus:ring-blue-500/20 cursor-pointer"
            >
              {staffList.map((s) => (
                <option key={s.code} value={s.code}>
                  {s.name}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* + Thêm công việc Button */}
          <button
            type="button"
            onClick={() => {
              setTargetColForAdd('todo')
              setIsAddModalOpen(true)
            }}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm shadow-blue-200 cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Thêm công việc</span>
          </button>
        </div>
      </div>

      {/* ================= KANBAN BOARD VIEW ================= */}
      {viewMode === 'kanban' && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 items-start">
          {columnsConfig.map((col) => {
            const colTasks = filteredTasks.filter((t) => t.columnId === col.id)
            const countToDisplay = col.count

            return (
              <div
                key={col.id}
                className={`border rounded-2xl p-3.5 ${col.columnBg} space-y-3 min-h-[580px] flex flex-col justify-between`}
              >
                <div>
                  {/* Column Header */}
                  <div className="flex items-center justify-between pb-2 mb-1">
                    <div className="flex items-center space-x-1.5">
                      <h3 className={`text-sm font-bold ${col.headerColor}`}>
                        {col.title} ({countToDisplay})
                      </h3>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        setTargetColForAdd(col.id)
                        setIsAddModalOpen(true)
                      }}
                      className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-white/80 transition-colors"
                      title="Thêm công việc vào cột này"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Tasks List */}
                  <div className="space-y-2.5">
                    {colTasks.map((task) => (
                      <div
                        key={task.id}
                        className="bg-white rounded-xl p-3.5 border border-slate-200/80 shadow-2xs hover:shadow-md transition-all space-y-2.5 group cursor-pointer"
                      >
                        {/* Task Title & Menu */}
                        <div className="flex items-start justify-between gap-1.5">
                          <h4 className="font-bold text-xs text-slate-900 leading-snug group-hover:text-blue-600 transition-colors">
                            {task.title}
                          </h4>
                          <div className="relative group/menu shrink-0">
                            <button
                              type="button"
                              className="p-1 text-slate-400 hover:text-slate-700 rounded-md opacity-0 group-hover:opacity-100 transition-opacity"
                              title="Chuyển cột"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreVertical className="w-3.5 h-3.5" />
                            </button>
                            <div className="absolute right-0 top-full hidden group-hover/menu:block bg-white border border-slate-200 rounded-xl shadow-xl py-1 z-20 w-36 text-[11px] font-medium text-slate-700">
                              <span className="px-2.5 py-1 text-[10px] text-slate-400 block border-b border-slate-100 uppercase tracking-wider">
                                Chuyển trạng thái
                              </span>
                              {columnsConfig.map((c) => (
                                <button
                                  key={c.id}
                                  type="button"
                                  disabled={task.columnId === c.id}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleMoveTask(task.id, c.id)
                                  }}
                                  className={`w-full text-left px-2.5 py-1 hover:bg-slate-50 transition-colors flex items-center space-x-1.5 ${
                                    task.columnId === c.id ? 'opacity-40 cursor-not-allowed font-bold' : ''
                                  }`}
                                >
                                  <ArrowRight className="w-3 h-3 text-slate-400" />
                                  <span>{c.title}</span>
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Customer Name or Code */}
                        <div className="text-xs text-slate-500 font-medium">
                          {task.customer}
                        </div>

                        {/* Tag Pill */}
                        <div>
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                              tagColorClasses[task.tagColor]
                            }`}
                          >
                            {task.tag}
                          </span>
                        </div>

                        {/* Footer: Time & Assignee Avatar */}
                        <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-xs">
                          <div
                            className={`flex items-center space-x-1 text-[11px] font-medium ${
                              task.isUrgent ? 'text-rose-500 font-semibold' : 'text-slate-400'
                            }`}
                          >
                            <Clock className="w-3 h-3" />
                            <span>{task.time}</span>
                          </div>

                          {/* Assignee initials avatar */}
                          <div
                            className={`w-6 h-6 rounded-full flex items-center justify-center font-bold text-[10px] ring-2 ring-white shadow-2xs ${task.assignee.bg}`}
                            title={task.assignee.name}
                          >
                            {task.assignee.code}
                          </div>
                        </div>
                      </div>
                    ))}

                    {colTasks.length === 0 && (
                      <div className="h-28 flex flex-col items-center justify-center text-slate-400 text-xs border-2 border-dashed border-slate-200/80 rounded-xl">
                        <CheckSquare className="w-5 h-5 text-slate-300 mb-1" />
                        <span>Không có công việc</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Column quick add trigger */}
                <button
                  type="button"
                  onClick={() => {
                    setTargetColForAdd(col.id)
                    setIsAddModalOpen(true)
                  }}
                  className="w-full py-1.5 text-[11px] font-semibold text-slate-400 hover:text-blue-600 hover:bg-white/80 rounded-xl transition-all border border-dashed border-slate-200 flex items-center justify-center space-x-1 mt-2"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Thêm việc mới</span>
                </button>
              </div>
            )
          })}
        </div>
      )}

      {/* ================= LIST VIEW (DANH SÁCH) ================= */}
      {viewMode === 'list' && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <div className="relative w-72">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm kiếm công việc, khách hàng..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
              />
            </div>
            <span className="text-xs text-slate-500 font-medium">
              Hiển thị {filteredTasks.length} công việc
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50/80 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
                <tr>
                  <th className="py-3 px-4 w-8">
                    <input type="checkbox" className="rounded border-slate-300 text-blue-600" />
                  </th>
                  <th className="py-3 px-4">Tên công việc</th>
                  <th className="py-3 px-4">Khách hàng / Mã</th>
                  <th className="py-3 px-4">Thẻ tag</th>
                  <th className="py-3 px-4">Trạng thái</th>
                  <th className="py-3 px-4">Người phụ trách</th>
                  <th className="py-3 px-4">Cập nhật</th>
                  <th className="py-3 px-4 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filteredTasks.map((task) => {
                  const col = columnsConfig.find((c) => c.id === task.columnId)
                  return (
                    <tr key={task.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4">
                        <input type="checkbox" className="rounded border-slate-300 text-blue-600" />
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-900">{task.title}</td>
                      <td className="py-3 px-4 text-slate-600">{task.customer}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${tagColorClasses[task.tagColor]}`}>
                          {task.tag}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${col?.badgeBg}`}>
                          {col?.title}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <div className={`w-5 h-5 rounded-full flex items-center justify-center font-bold text-[9px] ${task.assignee.bg}`}>
                            {task.assignee.code}
                          </div>
                          <span className="text-xs text-slate-700">{task.assignee.name}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-[11px]">{task.time}</td>
                      <td className="py-3 px-4 text-right">
                        <select
                          value={task.columnId}
                          onChange={(e) => handleMoveTask(task.id, e.target.value as any)}
                          className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 font-semibold text-slate-700 cursor-pointer"
                        >
                          <option value="todo">Cần làm</option>
                          <option value="in_progress">Đang xử lý</option>
                          <option value="waiting">Chờ phản hồi</option>
                          <option value="done">Hoàn tất</option>
                        </select>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ================= MODAL: THÊM CÔNG VIỆC MỚI ================= */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-md w-full p-6 space-y-4 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <CheckSquare className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Thêm công việc mới</h3>
                  <p className="text-[11px] text-slate-400">Tạo công việc vào cột {columnsConfig.find(c => c.id === targetColForAdd)?.title}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsAddModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateTask} className="space-y-3.5 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  Tiêu đề công việc <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="VD: Hỗ trợ cài đặt game cho khách..."
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">
                  Tên khách hàng hoặc Mã đơn
                </label>
                <input
                  type="text"
                  value={newCustomer}
                  onChange={(e) => setNewCustomer(e.target.value)}
                  placeholder="VD: Nguyễn Văn An hoặc #DHT2345"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Loại công việc (Tag)</label>
                  <select
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  >
                    <option value="Hỗ trợ kỹ thuật">Hỗ trợ kỹ thuật</option>
                    <option value="Tư vấn">Tư vấn</option>
                    <option value="Khiếu nại">Khiếu nại</option>
                    <option value="Đơn hàng">Đơn hàng</option>
                    <option value="Follow up">Follow up</option>
                    <option value="Chờ khách">Chờ khách</option>
                    <option value="Hoàn tất">Hoàn tất</option>
                  </select>
                </div>

                <div>
                  <label className="font-bold text-slate-700 block mb-1">Người phụ trách</label>
                  <select
                    value={newAssignee}
                    onChange={(e) => setNewAssignee(e.target.value)}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-slate-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                  >
                    <option value="NV">Nguyễn Văn (NV)</option>
                    <option value="LT">Lê Tuấn (LT)</option>
                    <option value="TH">Trần Hùng (TH)</option>
                    <option value="TM">Trần Minh (TM)</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 font-semibold hover:bg-slate-50 transition-colors"
                >
                  Huỷ
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold transition-all shadow-md shadow-blue-200"
                >
                  Tạo công việc
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
