import React, { useState, useEffect } from 'react'
import {
  UserCog,
  Plus,
  Trash2,
  Lock,
  CheckCircle2,
  AlertCircle,
  Shield,
  KeyRound,
  UserCheck,
} from 'lucide-react'
import { api, OpsUser } from '../lib/api'
import { useAuth } from '../lib/auth'
import { formatTime } from '../lib/utils'

export const UsersPage: React.FC = () => {
  const { role } = useAuth()
  const [users, setUsers] = useState<OpsUser[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false)

  // New user form state
  const [username, setUsername] = useState<string>('')
  const [password, setPassword] = useState<string>('')
  const [name, setName] = useState<string>('')
  const [userRole, setUserRole] = useState<'staff' | 'manager'>('staff')
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false)

  // Status feedback
  const [feedback, setFeedback] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  const loadUsers = async () => {
    try {
      const res = await api.getUsers()
      setUsers(res.users || [])
    } catch (err: any) {
      setFeedback({ text: err.message || 'Lỗi tải danh sách tài khoản', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (role === 'owner') {
      loadUsers()
    }
  }, [role])

  if (role !== 'owner') {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500">
        <Shield className="w-10 h-10 mx-auto mb-3 text-red-400" />
        <h3 className="font-bold text-slate-800 text-sm">Truy cập bị từ chối</h3>
        <p className="text-xs text-slate-500 mt-1">
          Chỉ có tài khoản Chủ máy (Owner) mới có quyền quản lý tài khoản nhân sự.
        </p>
      </div>
    )
  }

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)
    if (!username.trim() || !password) {
      setFormError('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu')
      return
    }
    if (password.length < 6) {
      setFormError('Mật khẩu tối thiểu 6 ký tự')
      return
    }

    setIsSubmitting(true)
    try {
      await api.createUser({
        username: username.trim(),
        password,
        name: name.trim() || username.trim(),
        role: userRole,
      })
      setFeedback({ text: `Đã tạo tài khoản ${username} thành công!`, type: 'success' })
      setIsModalOpen(false)
      setUsername('')
      setPassword('')
      setName('')
      setUserRole('staff')
      loadUsers()
    } catch (err: any) {
      setFormError(err.message || 'Lỗi tạo tài khoản')
    } finally {
      setIsSubmitting(false)
      setTimeout(() => setFeedback(null), 4000)
    }
  }

  const handleDeleteUser = async (id: string, uname: string) => {
    if (!window.confirm(`Bạn có chắc chắn muốn xoá tài khoản ${uname}?`)) return
    try {
      await api.deleteUser(id)
      setFeedback({ text: `Đã xoá tài khoản ${uname}`, type: 'success' })
      loadUsers()
    } catch (err: any) {
      setFeedback({ text: err.message || 'Lỗi xoá tài khoản', type: 'error' })
    } finally {
      setTimeout(() => setFeedback(null), 4000)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Quản Lý Tài Khoản Nhân Sự</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Cấp quyền tài khoản Nhân viên CSKH (Staff) hoặc Quản lý cơ sở (Manager).
          </p>
        </div>

        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl shadow-md shadow-saoviet-200 transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>Thêm nhân sự mới</span>
        </button>
      </div>

      {feedback && (
        <div
          className={`p-3 rounded-xl text-xs font-semibold flex items-center space-x-2 animate-fade-in ${
            feedback.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {feedback.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{feedback.text}</span>
        </div>
      )}

      {/* Users Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-xs text-slate-600">
          <thead className="bg-slate-50/80 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
            <tr>
              <th className="py-3.5 px-4">Tên hiển thị</th>
              <th className="py-3.5 px-4">Tên đăng nhập</th>
              <th className="py-3.5 px-4">Vai trò (Role)</th>
              <th className="py-3.5 px-4">Trạng thái</th>
              <th className="py-3.5 px-4">Ngày tạo</th>
              <th className="py-3.5 px-4 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-medium">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-50/90 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-900">
                  <div className="flex items-center space-x-2">
                    <div className="w-7 h-7 rounded-full bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-center">
                      {u.name ? u.name.slice(0, 1).toUpperCase() : 'U'}
                    </div>
                    <span>{u.name}</span>
                  </div>
                </td>
                <td className="py-3 px-4 font-mono">{u.username}</td>
                <td className="py-3 px-4">
                  <span
                    className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                      u.role === 'manager'
                        ? 'bg-purple-50 text-purple-700 border-purple-200'
                        : 'bg-blue-50 text-blue-700 border-blue-200'
                    }`}
                  >
                    {u.role === 'manager' ? 'Quản lý' : 'Nhân viên'}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center space-x-1 text-emerald-700 font-bold">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    <span>Đang hoạt động</span>
                  </span>
                </td>
                <td className="py-3 px-4 text-slate-400 text-[11px]">
                  {formatTime(u.created_at)}
                </td>
                <td className="py-3 px-4 text-right">
                  <button
                    onClick={() => handleDeleteUser(u.id, u.username)}
                    className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                    title="Xoá tài khoản"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}

            {users.length === 0 && !loading && (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-400">
                  <UserCog className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                  <span>Chưa có tài khoản phụ nào. Hãy bấm "Thêm nhân sự mới".</span>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Add User Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Cấp tài khoản nhân sự mới</h3>

            {formError && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs font-medium">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateUser} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Tên hiển thị</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Vd: Nguyễn Thị Mai (CSKH)"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Tên đăng nhập *</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  placeholder="mai_cskh"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Mật khẩu ban đầu *</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="Tối thiểu 6 ký tự"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Vai trò & Phân quyền</label>
                <select
                  value={userRole}
                  onChange={(e) => setUserRole(e.target.value as any)}
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500 font-semibold"
                >
                  <option value="staff">Nhân viên CSKH (Duyệt nháp, xem khách, việc)</option>
                  <option value="manager">Quản lý (Gộp CRM, xem xu hướng, quét ngay)</option>
                </select>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
                >
                  Huỷ
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl shadow-md shadow-saoviet-200 disabled:opacity-50"
                >
                  {isSubmitting ? 'Đang tạo...' : 'Tạo tài khoản'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
