import React, { useState, useEffect } from 'react'
import {
  Users,
  Search,
  Eye,
  EyeOff,
  Trash2,
  GitMerge,
  Clock,
  Phone,
  MapPin,
  MessageCircle,
  Tag,
  AlertCircle,
  CheckCircle2,
  X,
  FileText,
} from 'lucide-react'
import { api, CustomerItem } from '../lib/api'
import { useAuth } from '../lib/auth'
import { maskPhone, formatTime, timeAgo } from '../lib/utils'

export const Customers: React.FC = () => {
  const { role, can } = useAuth()
  const [customers, setCustomers] = useState<CustomerItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [unmaskAll, setUnmaskAll] = useState<boolean>(false)

  // Drawer state
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerItem | null>(null)
  const [customerNotes, setCustomerNotes] = useState<string>('')
  const [isSavingNotes, setIsSavingNotes] = useState<boolean>(false)

  // Merge modal state
  const [mergeModalOpen, setMergeModalOpen] = useState<boolean>(false)
  const [targetCustomerId, setTargetCustomerId] = useState<string>('')
  const [isMerging, setIsMerging] = useState<boolean>(false)

  // Action status message
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  const loadCustomers = async () => {
    try {
      const res = await api.getCustomers(searchQuery)
      setCustomers(res.customers || [])
    } catch (err: any) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCustomers()
  }, [searchQuery])

  const handleSelectCustomer = async (cust: CustomerItem) => {
    setSelectedCustomer(cust)
    setCustomerNotes(cust.notes || '')
    // Fetch full detail if available
    try {
      const res = await api.getCustomerDetail(cust.id)
      if (res.customer) {
        setSelectedCustomer(res.customer)
        setCustomerNotes(res.customer.notes || '')
      }
    } catch {
      // Use existing record
    }
  }

  const handleSaveNotes = async () => {
    if (!selectedCustomer) return
    setIsSavingNotes(true)
    try {
      await api.updateCustomer(selectedCustomer.id, { notes: customerNotes })
      setSelectedCustomer({ ...selectedCustomer, notes: customerNotes })
      setStatusMsg({ text: 'Đã lưu ghi chú thành công', type: 'success' })
      loadCustomers()
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Lỗi lưu ghi chú', type: 'error' })
    } finally {
      setIsSavingNotes(false)
      setTimeout(() => setStatusMsg(null), 3000)
    }
  }

  const handleDeleteCustomer = async (id: string) => {
    if (!can('delete_crm')) return
    if (!window.confirm('Bạn có chắc chắn muốn xoá khách hàng này khỏi danh sách CRM?')) return

    try {
      await api.deleteCustomer(id)
      setStatusMsg({ text: 'Đã xoá hồ sơ khách hàng', type: 'success' })
      if (selectedCustomer?.id === id) {
        setSelectedCustomer(null)
      }
      loadCustomers()
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Lỗi xoá khách hàng', type: 'error' })
    } finally {
      setTimeout(() => setStatusMsg(null), 3000)
    }
  }

  const handleConfirmMerge = async () => {
    if (!selectedCustomer || !targetCustomerId) return
    setIsMerging(true)
    try {
      await api.mergeCustomers(selectedCustomer.id, targetCustomerId)
      setStatusMsg({ text: 'Đã gộp hai hồ sơ khách hàng thành công', type: 'success' })
      setMergeModalOpen(false)
      setSelectedCustomer(null)
      loadCustomers()
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Lỗi gộp hồ sơ', type: 'error' })
    } finally {
      setIsMerging(false)
      setTimeout(() => setStatusMsg(null), 3000)
    }
  }

  const canViewFullPhone = role === 'manager' || role === 'owner'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Khách Hàng (Sao Việt CRM)</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Danh sách khách hàng tiềm năng đã để lại SĐT hoặc tương tác với Fanpage.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {canViewFullPhone && (
            <button
              onClick={() => setUnmaskAll(!unmaskAll)}
              className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors"
            >
              {unmaskAll ? <EyeOff className="w-3.5 h-3.5 text-slate-500" /> : <Eye className="w-3.5 h-3.5 text-slate-500" />}
              <span>{unmaskAll ? 'Che SĐT' : 'Hiện đầy đủ SĐT'}</span>
            </button>
          )}

          <div className="relative w-64">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm tên, SĐT, cơ sở..."
              className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-saoviet-500"
            />
          </div>
        </div>
      </div>

      {statusMsg && (
        <div
          className={`p-3 rounded-xl text-xs font-semibold flex items-center space-x-2 animate-fade-in ${
            statusMsg.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {statusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* CRM Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-50/80 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
              <tr>
                <th className="py-3.5 px-4">Họ và tên</th>
                <th className="py-3.5 px-4">Số điện thoại</th>
                <th className="py-3.5 px-4">Cơ sở quan tâm</th>
                <th className="py-3.5 px-4">Tâm trạng / Ý định</th>
                <th className="py-3.5 px-4">Số tương tác</th>
                <th className="py-3.5 px-4">Lần cuối</th>
                <th className="py-3.5 px-4 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {customers.map((cust) => (
                <tr
                  key={cust.id}
                  onClick={() => handleSelectCustomer(cust)}
                  className="hover:bg-slate-50/90 transition-colors cursor-pointer"
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2.5">
                      <div className="w-7 h-7 rounded-full bg-saoviet-100 text-saoviet-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                        {cust.name ? cust.name.slice(0, 1).toUpperCase() : 'K'}
                      </div>
                      <span className="font-bold text-slate-900">{cust.name}</span>
                    </div>
                  </td>

                  <td className="py-3 px-4 font-mono">
                    {cust.phone ? (
                      <span className="bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded font-bold border border-emerald-100">
                        {maskPhone(cust.phone, unmaskAll && canViewFullPhone)}
                      </span>
                    ) : (
                      <span className="text-slate-400">Chưa có</span>
                    )}
                  </td>

                  <td className="py-3 px-4">
                    {cust.branch ? (
                      <span className="inline-flex items-center space-x-1 text-slate-700">
                        <MapPin className="w-3 h-3 text-saoviet-500" />
                        <span>{cust.branch}</span>
                      </span>
                    ) : (
                      <span className="text-slate-400">—</span>
                    )}
                  </td>

                  <td className="py-3 px-4">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        cust.sentiment === 'positive'
                          ? 'bg-emerald-100 text-emerald-800'
                          : cust.sentiment === 'negative'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {cust.status || cust.sentiment || 'Quan tâm học phí'}
                    </span>
                  </td>

                  <td className="py-3 px-4">
                    <span className="font-bold text-slate-800">{cust.interaction_count || 1}</span> lượt
                  </td>

                  <td className="py-3 px-4 text-slate-400 text-[11px]">
                    {timeAgo(cust.last_seen_ts)}
                  </td>

                  <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end space-x-1">
                      <button
                        onClick={() => handleSelectCustomer(cust)}
                        className="px-2.5 py-1 text-xs font-semibold text-saoviet-700 hover:bg-saoviet-50 rounded-lg transition-colors"
                      >
                        Chi tiết
                      </button>

                      {can('delete_crm') && (
                        <button
                          onClick={() => handleDeleteCustomer(cust.id)}
                          title="Xoá hồ sơ (Quản lý)"
                          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}

              {customers.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <Users className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                    <span>Không tìm thấy hồ sơ khách hàng nào</span>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Customer Detail Drawer */}
      {selectedCustomer && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={() => setSelectedCustomer(null)}
          />

          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col">
              {/* Drawer Header */}
              <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-saoviet-500 text-white font-bold flex items-center justify-center text-sm shadow-sm">
                    {selectedCustomer.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <h2 className="font-bold text-slate-900 text-base leading-tight">
                      {selectedCustomer.name}
                    </h2>
                    <p className="text-xs text-slate-500">ID: {selectedCustomer.id}</p>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedCustomer(null)}
                  className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-200/50 rounded-full"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Body */}
              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                {/* Contact Information Box */}
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 flex items-center space-x-1.5">
                      <Phone className="w-3.5 h-3.5 text-slate-400" />
                      <span>Số điện thoại:</span>
                    </span>
                    <span className="font-bold font-mono text-slate-900">
                      {maskPhone(selectedCustomer.phone, canViewFullPhone)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 flex items-center space-x-1.5">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span>Cơ sở đăng ký:</span>
                    </span>
                    <span className="font-semibold text-slate-800">
                      {selectedCustomer.branch || 'Chưa chọn'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 flex items-center space-x-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>Tương tác gần nhất:</span>
                    </span>
                    <span className="text-slate-700">
                      {selectedCustomer.last_seen_ts ? formatTime(selectedCustomer.last_seen_ts) : '—'}
                    </span>
                  </div>
                </div>

                {/* Staff Internal Notes */}
                <div className="space-y-2">
                  <label className="block text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                    <FileText className="w-4 h-4 text-saoviet-500" />
                    <span>Ghi chú của tư vấn viên</span>
                  </label>
                  <textarea
                    rows={4}
                    value={customerNotes}
                    onChange={(e) => setCustomerNotes(e.target.value)}
                    placeholder="Nhập tình trạng tư vấn, lịch hẹn kiểm tra trình độ, nhu cầu học..."
                    className="w-full p-3 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                  />
                  <div className="flex justify-end">
                    <button
                      onClick={handleSaveNotes}
                      disabled={isSavingNotes}
                      className="px-3 py-1.5 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-lg shadow-sm transition-all disabled:opacity-50"
                    >
                      {isSavingNotes ? 'Đang lưu...' : 'Lưu ghi chú'}
                    </button>
                  </div>
                </div>

                {/* Timeline of interactions */}
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                    <MessageCircle className="w-4 h-4 text-blue-500" />
                    <span>Lịch sử tương tác</span>
                  </h3>

                  <div className="space-y-2">
                    {selectedCustomer.history && selectedCustomer.history.length > 0 ? (
                      selectedCustomer.history.map((h, i) => (
                        <div key={i} className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs space-y-1">
                          <div className="flex items-center justify-between text-[10px] text-slate-400">
                            <span className="font-semibold capitalize text-slate-700">{h.type}</span>
                            <span>{formatTime(h.ts)}</span>
                          </div>
                          <p className="text-slate-800">"{h.text}"</p>
                          {h.intent && (
                            <span className="inline-block text-[9px] bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded font-medium">
                              {h.intent}
                            </span>
                          )}
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-slate-400 italic">Chưa có lịch sử lưu trữ chi tiết</p>
                    )}
                  </div>
                </div>

                {/* Manager / Owner Actions: Merge / Delete */}
                {can('merge_crm') && (
                  <div className="pt-4 border-t border-slate-200 space-y-2">
                    <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                      Thao tác Quản lý
                    </span>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setMergeModalOpen(true)}
                        className="flex-1 flex items-center justify-center space-x-1.5 py-2 px-3 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
                      >
                        <GitMerge className="w-3.5 h-3.5 text-slate-500" />
                        <span>Gộp hồ sơ trùng</span>
                      </button>

                      <button
                        onClick={() => handleDeleteCustomer(selectedCustomer.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-xl transition-colors"
                        title="Xoá hồ sơ này"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Merge Modal */}
      {mergeModalOpen && selectedCustomer && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900">Gộp hồ sơ khách hàng trùng lặp</h3>
            <p className="text-xs text-slate-500">
              Chuyển toàn bộ lịch sử và ghi chú của <b>{selectedCustomer.name}</b> vào một hồ sơ chính khác.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Chọn hồ sơ nhận dữ liệu
              </label>
              <select
                value={targetCustomerId}
                onChange={(e) => setTargetCustomerId(e.target.value)}
                className="w-full p-2.5 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
              >
                <option value="">-- Chọn khách hàng mục tiêu --</option>
                {customers
                  .filter((c) => c.id !== selectedCustomer.id)
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({maskPhone(c.phone, true)}) - {c.id}
                    </option>
                  ))}
              </select>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                onClick={() => setMergeModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl"
              >
                Huỷ
              </button>
              <button
                onClick={handleConfirmMerge}
                disabled={!targetCustomerId || isMerging}
                className="px-4 py-2 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl disabled:opacity-50"
              >
                {isMerging ? 'Đang gộp...' : 'Xác nhận gộp hồ sơ'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
