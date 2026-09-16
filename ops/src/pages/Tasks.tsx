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
  Flame,
} from 'lucide-react'
import { api, KanbanTask, KanbanBoardView } from '../lib/api'
import { formatTime, timeAgo } from '../lib/utils'

export const Tasks: React.FC = () => {
  const [board, setBoard] = useState<KanbanBoardView | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [refreshing, setRefreshing] = useState<boolean>(false)
  const [actionError, setActionError] = useState<string | null>(null)

  // Add Task Modal State
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false)
  const [newTitle, setNewTitle] = useState<string>('')
  const [newIntent, setNewIntent] = useState<string>('')
  const [newPriority, setNewPriority] = useState<number>(2)
  const [newPhone, setNewPhone] = useState<string>('')
  const [newCampus, setNewCampus] = useState<string>('')
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)

  const loadTasks = async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true)
    try {
      const res = await api.getTasks()
      setBoard(res)
      setActionError(null)
    } catch (err: any) {
      setActionError(err.message || 'Lỗi tải bảng công việc')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadTasks()
    const t = setInterval(() => loadTasks(false), 20000)
    return () => clearInterval(t)
  }, [])

  const handleMove = async (taskId: string, targetStatus: string) => {
    try {
      await api.moveTask(taskId, targetStatus)
      await loadTasks(false)
    } catch (err: any) {
      alert(err.message || `Lỗi chuyển trạng thái sang ${targetStatus}`)
    }
  }

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim()) return
    setIsSubmitting(true)
    try {
      const intentParts: string[] = []
      if (newPhone.trim()) intentParts.push(`SĐT: ${newPhone.trim()}`)
      if (newCampus.trim()) intentParts.push(`Cơ sở: ${newCampus.trim()}`)
      if (newIntent.trim()) intentParts.push(newIntent.trim())

      await api.createTask({
        title: newTitle.trim(),
        intent: intentParts.join(' | ') || newTitle.trim(),
        priority: newPriority,
      })

      setIsAddModalOpen(false)
      setNewTitle('')
      setNewIntent('')
      setNewPhone('')
      setNewCampus('')
      setNewPriority(2)
      await loadTasks(false)
    } catch (err: any) {
      alert(err.message || 'Lỗi tạo nhiệm vụ')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Aggregate backend columns into 3 operator-friendly boards
  const columns = board?.columns || {}
  const queueTasks = [
    ...(columns.triage || []),
    ...(columns.todo || []),
    ...(columns.ready || []),
  ]
  const activeTasks = [
    ...(columns.running || []),
    ...(columns.review || []),
    ...(columns.blocked || []),
  ]
  const historyTasks = [
    ...(columns.done || []),
    ...(columns.cancelled || []),
  ]

  const statusLabel = (status: string) => {
    switch (status) {
      case 'triage': return { text: 'Tiếp nhận', color: 'bg-indigo-50 text-indigo-700 border-indigo-200' }
      case 'todo': return { text: 'Cần làm', color: 'bg-amber-50 text-amber-700 border-amber-200' }
      case 'ready': return { text: 'Sẵn sàng', color: 'bg-blue-50 text-blue-700 border-blue-200' }
      case 'running': return { text: 'Đang chạy', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
      case 'review': return { text: 'Chờ duyệt', color: 'bg-purple-50 text-purple-700 border-purple-200' }
      case 'blocked': return { text: 'Bị chặn', color: 'bg-red-50 text-red-700 border-red-200' }
      case 'done': return { text: 'Hoàn tất', color: 'bg-teal-50 text-teal-700 border-teal-200' }
      case 'cancelled': return { text: 'Đã huỷ', color: 'bg-slate-100 text-slate-500 border-slate-200' }
      default: return { text: status, color: 'bg-slate-100 text-slate-600 border-slate-200' }
    }
  }

  const priorityBadge = (p: number) => {
    if (p <= 1) {
      return (
        <span className="flex items-center space-x-1 text-[10px] font-bold text-red-700 bg-red-50 px-2 py-0.5 rounded-full border border-red-200">
          <Flame className="w-3 h-3 text-red-500" />
          <span>P1 Gấp</span>
        </span>
      )
    }
    if (p === 2) {
      return (
        <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
          P2 Bình thường
        </span>
      )
    }
    return (
      <span className="text-[10px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
        P3 Thấp
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Nhiệm Vụ Vận Hành (Kanban)</h1>
            {board?.running && (
              <span className="px-2 py-0.5 text-[10px] font-bold text-emerald-700 bg-emerald-100 rounded-full animate-pulse">
                Dispatcher Running
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Bảng theo dõi các tác vụ chăm sóc lead, gọi lại học viên và công việc tự động của Javis.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => loadTasks(true)}
            disabled={refreshing}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
            title="Làm mới bảng việc"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl shadow-md shadow-saoviet-200 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Tạo việc mới</span>
          </button>
        </div>
      </div>

      {actionError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Board Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 1. Hàng đợi (Queue) */}
        <div className="bg-slate-100/70 rounded-2xl p-4 border border-slate-200/80 flex flex-col h-[calc(100vh-280px)] min-h-[500px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
            <span className="font-bold text-xs text-slate-800 uppercase tracking-wider flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400 inline-block" />
              <span>Chờ xử lý</span>
              <span className="px-2 py-0.5 rounded-full bg-white text-slate-700 text-[10px] font-extrabold shadow-2xs">
                {queueTasks.length}
              </span>
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            {queueTasks.map((task) => {
              const st = statusLabel(task.status)
              return (
                <div
                  key={task.id}
                  className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs hover:shadow-md transition-all space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-bold text-xs text-slate-900 leading-snug">
                      {task.title}
                    </h4>
                    {priorityBadge(task.priority)}
                  </div>

                  {task.intent && task.intent !== task.title && (
                    <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-2 rounded-lg border border-slate-100">
                      {task.intent}
                    </p>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-400">
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${st.color}`}>
                      {st.text}
                    </span>
                    <span className="text-[10px]">{timeAgo(task.created_at)}</span>
                  </div>

                  <div className="flex items-center justify-end space-x-1.5 pt-1">
                    <button
                      onClick={() => handleMove(task.id, 'running')}
                      className="px-3 py-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm transition-colors cursor-pointer flex items-center space-x-1"
                    >
                      <span>Bắt đầu làm</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              )
            })}

            {queueTasks.length === 0 && (
              <div className="h-32 flex flex-col items-center justify-center text-slate-400 text-xs italic">
                <CheckSquare className="w-6 h-6 mb-1 text-slate-300" />
                <span>Không có việc chờ</span>
              </div>
            )}
          </div>
        </div>

        {/* 2. Đang xử lý (Active) */}
        <div className="bg-slate-100/70 rounded-2xl p-4 border border-slate-200/80 flex flex-col h-[calc(100vh-280px)] min-h-[500px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
            <span className="font-bold text-xs text-slate-800 uppercase tracking-wider flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block animate-ping" />
              <span>Đang xử lý</span>
              <span className="px-2 py-0.5 rounded-full bg-white text-slate-700 text-[10px] font-extrabold shadow-2xs">
                {activeTasks.length}
              </span>
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            {activeTasks.map((task) => {
              const st = statusLabel(task.status)
              return (
                <div
                  key={task.id}
                  className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs hover:shadow-md transition-all space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-bold text-xs text-slate-900 leading-snug">
                      {task.title}
                    </h4>
                    {priorityBadge(task.priority)}
                  </div>

                  {task.intent && task.intent !== task.title && (
                    <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-2 rounded-lg border border-slate-100">
                      {task.intent}
                    </p>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-400">
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${st.color}`}>
                      {st.text}
                    </span>
                    <span className="text-[10px]">{timeAgo(task.created_at)}</span>
                  </div>

                  <div className="flex items-center justify-end space-x-2 pt-1">
                    <button
                      onClick={() => handleMove(task.id, 'todo')}
                      className="px-2 py-1 text-[11px] font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
                    >
                      Trả về chờ
                    </button>
                    <button
                      onClick={() => handleMove(task.id, 'done')}
                      className="px-3 py-1.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-colors cursor-pointer flex items-center space-x-1"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Xong việc</span>
                    </button>
                  </div>
                </div>
              )
            })}

            {activeTasks.length === 0 && (
              <div className="h-32 flex flex-col items-center justify-center text-slate-400 text-xs italic">
                <CheckSquare className="w-6 h-6 mb-1 text-slate-300" />
                <span>Không có việc đang xử lý</span>
              </div>
            )}
          </div>
        </div>

        {/* 3. Lịch sử / Hoàn tất (Done & Cancelled) */}
        <div className="bg-slate-100/70 rounded-2xl p-4 border border-slate-200/80 flex flex-col h-[calc(100vh-280px)] min-h-[500px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
            <span className="font-bold text-xs text-slate-800 uppercase tracking-wider flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
              <span>Đã hoàn tất / Lưu trữ</span>
              <span className="px-2 py-0.5 rounded-full bg-white text-slate-700 text-[10px] font-extrabold shadow-2xs">
                {historyTasks.length}
              </span>
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            {historyTasks.map((task) => {
              const st = statusLabel(task.status)
              return (
                <div
                  key={task.id}
                  className="bg-white/80 rounded-xl p-4 border border-slate-200 shadow-2xs opacity-85 hover:opacity-100 transition-all space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="font-bold text-xs text-slate-700 leading-snug line-through">
                      {task.title}
                    </h4>
                    {priorityBadge(task.priority)}
                  </div>

                  {task.intent && task.intent !== task.title && (
                    <p className="text-xs text-slate-500 leading-relaxed">
                      {task.intent}
                    </p>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-[11px] text-slate-400">
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${st.color}`}>
                      {st.text}
                    </span>
                    <span className="text-[10px]">{timeAgo(task.updated_at || task.created_at)}</span>
                  </div>

                  <div className="flex items-center justify-end pt-1">
                    <button
                      onClick={() => handleMove(task.id, 'todo')}
                      className="px-2.5 py-1 text-[11px] font-medium text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                    >
                      Mở lại việc
                    </button>
                  </div>
                </div>
              )
            })}

            {historyTasks.length === 0 && (
              <div className="h-32 flex flex-col items-center justify-center text-slate-400 text-xs italic">
                <CheckSquare className="w-6 h-6 mb-1 text-slate-300" />
                <span>Chưa có việc hoàn tất</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Task Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Tạo việc mới cần làm</h3>

            <form onSubmit={handleCreateTask} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Tiêu đề công việc *
                </label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                  placeholder="Vd: Gọi lại khách Nguyễn Văn A tư vấn khoá TOEIC..."
                  className="w-full p-2.5 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Số điện thoại
                  </label>
                  <input
                    type="text"
                    value={newPhone}
                    onChange={(e) => setNewPhone(e.target.value)}
                    placeholder="0901234567"
                    className="w-full p-2.5 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Mức ưu tiên
                  </label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(Number(e.target.value))}
                    className="w-full p-2.5 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                  >
                    <option value={1}>P1 - Gấp / Khẩn</option>
                    <option value={2}>P2 - Bình thường</option>
                    <option value={3}>P3 - Thấp</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Cơ sở phụ trách
                </label>
                <input
                  type="text"
                  value={newCampus}
                  onChange={(e) => setNewCampus(e.target.value)}
                  placeholder="Vd: Quận 10 / Thủ Đức..."
                  className="w-full p-2.5 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Mô tả / Ý định chi tiết
                </label>
                <textarea
                  rows={3}
                  value={newIntent}
                  onChange={(e) => setNewIntent(e.target.value)}
                  placeholder="Ghi chú chi tiết yêu cầu khách hàng..."
                  className="w-full p-2.5 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                />
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Huỷ
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl shadow-md shadow-saoviet-200 transition-all cursor-pointer disabled:opacity-50"
                >
                  {isSubmitting ? 'Đang tạo...' : 'Tạo việc'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
