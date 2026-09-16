import React, { useState, useEffect } from 'react'
import {
  CheckSquare,
  Clock,
  Plus,
  ArrowRight,
  CheckCircle2,
  Phone,
  User,
  MapPin,
  Calendar,
} from 'lucide-react'
import { api, KanbanTask } from '../lib/api'
import { formatTime, timeAgo } from '../lib/utils'

export const Tasks: React.FC = () => {
  const [tasks, setTasks] = useState<KanbanTask[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false)
  const [newTitle, setNewTitle] = useState<string>('')
  const [newDesc, setNewDesc] = useState<string>('')
  const [newPhone, setNewPhone] = useState<string>('')
  const [newBranch, setNewBranch] = useState<string>('')

  const loadTasks = async () => {
    try {
      const res = await api.getTasks()
      setTasks(res.tasks || [])
    } catch {
      // Fallback
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks()
    const t = setInterval(loadTasks, 20000)
    return () => clearInterval(t)
  }, [])

  const handleUpdateStatus = async (taskId: string, newStatus: 'todo' | 'in_progress' | 'done') => {
    try {
      await api.updateTask(taskId, { status: newStatus })
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
      )
    } catch (err: any) {
      alert(err.message || 'Lỗi cập nhật trạng thái việc')
    }
  }

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTitle.trim()) return
    try {
      await api.createTask({
        title: newTitle.trim(),
        description: newDesc.trim(),
        lead_phone: newPhone.trim(),
        branch: newBranch.trim(),
        status: 'todo',
      })
      setIsAddModalOpen(false)
      setNewTitle('')
      setNewDesc('')
      setNewPhone('')
      setNewBranch('')
      loadTasks()
    } catch (err: any) {
      alert(err.message || 'Lỗi tạo công việc')
    }
  }

  const columns = [
    { id: 'todo', label: 'Cần làm', color: 'bg-amber-50 text-amber-900 border-amber-200' },
    { id: 'in_progress', label: 'Đang xử lý', color: 'bg-blue-50 text-blue-900 border-blue-200' },
    { id: 'done', label: 'Đã hoàn tất', color: 'bg-emerald-50 text-emerald-900 border-emerald-200' },
  ] as const

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Việc Cần Làm (Bảng Vận Hành)</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Các nhiệm vụ chăm sóc lead, gọi lại khách hàng do Javis giao hoặc nhân viên tự tạo.
          </p>
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl shadow-md shadow-saoviet-200 transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Tạo việc mới</span>
        </button>
      </div>

      {/* Kanban 3 Columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {columns.map((col) => {
          const colTasks = tasks.filter((t) => t.status === col.id)
          return (
            <div
              key={col.id}
              className="bg-slate-100/70 rounded-2xl p-4 border border-slate-200/80 flex flex-col h-[calc(100vh-280px)] min-h-[500px]"
            >
              {/* Column Header */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
                <span className="font-bold text-xs text-slate-800 uppercase tracking-wider flex items-center space-x-1.5">
                  <span>{col.label}</span>
                  <span className="px-2 py-0.5 rounded-full bg-white text-slate-700 text-[10px] font-extrabold shadow-2xs">
                    {colTasks.length}
                  </span>
                </span>
              </div>

              {/* Tasks List */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {colTasks.map((task) => (
                  <div
                    key={task.id}
                    className="bg-white rounded-xl p-4 border border-slate-200 shadow-2xs hover:shadow-md transition-all space-y-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="font-bold text-xs text-slate-900 leading-snug">
                        {task.title}
                      </h4>
                      {task.priority && (
                        <span
                          className={`text-[9px] font-bold px-1.5 py-0.2 rounded uppercase ${
                            task.priority === 'high'
                              ? 'bg-red-100 text-red-800'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {task.priority}
                        </span>
                      )}
                    </div>

                    {task.description && (
                      <p className="text-xs text-slate-600 leading-relaxed line-clamp-3">
                        {task.description}
                      </p>
                    )}

                    <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
                      {task.lead_phone && (
                        <span className="flex items-center space-x-1 text-emerald-700 font-bold bg-emerald-50 px-1.5 py-0.5 rounded">
                          <Phone className="w-3 h-3" />
                          <span>{task.lead_phone}</span>
                        </span>
                      )}

                      {task.branch && (
                        <span className="flex items-center space-x-1 text-slate-600">
                          <MapPin className="w-3 h-3 text-saoviet-500" />
                          <span>{task.branch}</span>
                        </span>
                      )}

                      <span className="text-[10px] text-slate-400">
                        {timeAgo(task.created_at)}
                      </span>
                    </div>

                    {/* Move to next stage buttons */}
                    <div className="flex items-center justify-end space-x-1.5 pt-1">
                      {col.id === 'todo' && (
                        <button
                          onClick={() => handleUpdateStatus(task.id, 'in_progress')}
                          className="px-2.5 py-1 text-[11px] font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors cursor-pointer"
                        >
                          Bắt đầu làm
                        </button>
                      )}

                      {col.id === 'in_progress' && (
                        <>
                          <button
                            onClick={() => handleUpdateStatus(task.id, 'todo')}
                            className="px-2 py-1 text-[10px] font-medium text-slate-500 hover:bg-slate-100 rounded-lg"
                          >
                            Quay lại
                          </button>
                          <button
                            onClick={() => handleUpdateStatus(task.id, 'done')}
                            className="px-2.5 py-1 text-[11px] font-bold text-emerald-800 bg-emerald-100 hover:bg-emerald-200 rounded-lg transition-colors cursor-pointer"
                          >
                            Xong việc
                          </button>
                        </>
                      )}

                      {col.id === 'done' && (
                        <button
                          onClick={() => handleUpdateStatus(task.id, 'in_progress')}
                          className="px-2 py-1 text-[10px] font-medium text-slate-400 hover:text-slate-600 rounded-lg"
                        >
                          Mở lại việc
                        </button>
                      )}
                    </div>
                  </div>
                ))}

                {colTasks.length === 0 && (
                  <div className="h-32 flex flex-col items-center justify-center text-slate-400 text-xs italic">
                    <CheckSquare className="w-6 h-6 mb-1 text-slate-300" />
                    <span>Không có việc nào</span>
                  </div>
                )}
              </div>
            </div>
          )
        })}
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

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Số điện thoại khách (nếu có)
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
                  Cơ sở phụ trách
                </label>
                <input
                  type="text"
                  value={newBranch}
                  onChange={(e) => setNewBranch(e.target.value)}
                  placeholder="Vd: Cơ sở Quận 10 / Thủ Đức..."
                  className="w-full p-2.5 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Ghi chú chi tiết
                </label>
                <textarea
                  rows={3}
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="Nội dung chi tiết..."
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
                  className="px-4 py-2 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl shadow-md shadow-saoviet-200"
                >
                  Tạo việc
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
