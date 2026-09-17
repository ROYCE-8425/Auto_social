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
  Tag,
  AlertCircle,
  CheckCircle2,
  X,
  FileText,
  UserCheck,
  BookOpen,
} from 'lucide-react'
import { api, CareCustomer, CareCustomerDetail } from '../lib/api'
import { useAuth } from '../lib/auth'
import { maskPhone, formatTime, timeAgo } from '../lib/utils'

export const Customers: React.FC = () => {
  const { role, can } = useAuth()
  const [customers, setCustomers] = useState<CareCustomer[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [unmaskAll, setUnmaskAll] = useState<boolean>(false)

  // Drawer state
  const [selectedCustomer, setSelectedCustomer] = useState<CareCustomer | null>(null)
  const [customerDetail, setCustomerDetail] = useState<CareCustomerDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState<boolean>(false)

  // Merge modal state
  const [mergeModalOpen, setMergeModalOpen] = useState<boolean>(false)
  const [targetCustomerId, setTargetCustomerId] = useState<string>('')
  const [isMerging, setIsMerging] = useState<boolean>(false)

  // Quick handoff state
  const [isHandoffing, setIsHandoffing] = useState<boolean>(false)

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

  const handleSelectCustomer = async (cust: CareCustomer) => {
    setSelectedCustomer(cust)
    setCustomerDetail(null)
    setDetailLoading(true)
    try {
      const detail = await api.getCustomerDetail(cust.crm_id)
      setCustomerDetail(detail)
    } catch (err: any) {
      console.error(err)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleDeleteCustomer = async (crmId: string) => {
    if (!can('delete_crm')) return
    if (!window.confirm('Bạn có chắc chắn muốn xoá khách hàng này khỏi danh sách CRM?')) return

    try {
      await api.deleteCustomer(crmId)
      setStatusMsg({ text: 'Đã xoá hồ sơ khách hàng', type: 'success' })
      if (selectedCustomer?.crm_id === crmId) {
        setSelectedCustomer(null)
        setCustomerDetail(null)
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
      await api.mergeCustomers(selectedCustomer.crm_id, targetCustomerId)
      setStatusMsg({ text: 'Đã gộp hai hồ sơ khách hàng thành công', type: 'success' })
      setMergeModalOpen(false)
      setSelectedCustomer(null)
      setCustomerDetail(null)
      loadCustomers()
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Lỗi gộp hồ sơ', type: 'error' })
    } finally {
      setIsMerging(false)
      setTimeout(() => setStatusMsg(null), 3000)
    }
  }

  const handleCreateHandoffTask = async (cust: CareCustomer) => {
    setIsHandoffing(true)
    const phone = cust.phones?.[0] || 'Chưa có'
    try {
      await api.handoffToStaff({
        title: `Gọi lại tư vấn khách ${cust.name}`,
        intent: `Khách quan tâm: ${cust.course_interest || 'Khoá học'} tại ${cust.campus || 'cơ sở'}. SĐT: ${phone}`,
        priority: 2,
      })
      setStatusMsg({ text: 'Đã tạo việc gọi lại vào bảng Kanban!', type: 'success' })
    } catch (err: any) {
      setStatusMsg({ text: err.message || 'Lỗi tạo việc', type: 'error' })
    } finally {
      setIsHandoffing(false)
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
                <th className="py-3.5 px-4">Khoá học / Thẻ</th>
                <th className="py-3.5 px-4">Cập nhật lần cuối</th>
                <th className="py-3.5 px-4 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {customers.map((cust) => {
                const primaryPhone = cust.phones?.[0]
                return (
                  <tr
                    key={cust.crm_id}
                    onClick={() => handleSelectCustomer(cust)}
                    className="hover:bg-slate-50/90 transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2.5">
                        <div className="w-7 h-7 rounded-full bg-saoviet-100 text-saoviet-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                          {cust.name ? cust.name.slice(0, 1).toUpperCase() : 'K'}
                        </div>
                        <div>
                          <span className="font-bold text-slate-900 block">{cust.name || 'Ẩn danh'}</span>
                          <span className="text-[10px] text-slate-400 font-mono">{cust.crm_id}</span>
                        </div>
                      </div>
                    </td>

                    <td className="py-3 px-4 font-mono">
                      {primaryPhone ? (
                        <span className="bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded font-bold border border-emerald-100">
                          {maskPhone(primaryPhone, unmaskAll && canViewFullPhone)}
                        </span>
                      ) : (
                        <span className="text-slate-400">Chưa có</span>
                      )}
                    </td>

                    <td className="py-3 px-4">
                      {cust.campus ? (
                        <span className="inline-flex items-center space-x-1 text-slate-700">
                          <MapPin className="w-3 h-3 text-saoviet-500" />
                          <span>{cust.campus}</span>
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex flex-wrap items-center gap-1">
                        {cust.course_interest && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-100">
                            {cust.course_interest}
                          </span>
                        )}
                        {(cust.tags || []).map((t, i) => (
                          <span key={i} className="px-1.5 py-0.2 rounded text-[9px] bg-slate-100 text-slate-600">
                            #{t}
                          </span>
                        ))}
                        {!cust.course_interest && (!cust.tags || cust.tags.length === 0) && (
                          <span className="text-slate-400">—</span>
                        )}
                      </div>
                    </td>

                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {cust.updated_ts ? timeAgo(cust.updated_ts) : '—'}
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
                            onClick={() => handleDeleteCustomer(cust.crm_id)}
                            title="Xoá hồ sơ (Quản lý)"
                            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}

              {customers.length === 0 && !loading && (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
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
            onClick={() => {
              setSelectedCustomer(null)
              setCustomerDetail(null)
            }}
          />

          <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
            <div className="w-screen max-w-md bg-white shadow-2xl flex flex-col">
              {/* Drawer Header */}
              <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-full bg-saoviet-500 text-white font-bold flex items-center justify-center text-sm shadow-sm">
                    {selectedCustomer.name ? selectedCustomer.name.slice(0, 2).toUpperCase() : 'KH'}
                  </div>
                  <div>
                    <h2 className="font-bold text-slate-900 text-base leading-tight">
                      {selectedCustomer.name || 'Ẩn danh'}
                    </h2>
                    <p className="text-xs text-slate-500 font-mono">CRM ID: {selectedCustomer.crm_id}</p>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setSelectedCustomer(null)
                    setCustomerDetail(null)
                  }}
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
                    <div className="text-right">
                      {(selectedCustomer.phones && selectedCustomer.phones.length > 0) ? (
                        selectedCustomer.phones.map((p, i) => (
                          <div key={i} className="font-bold font-mono text-slate-900">
                            {maskPhone(p, canViewFullPhone)}
                          </div>
                        ))
                      ) : (
                        <span className="text-slate-400">Chưa có</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 flex items-center space-x-1.5">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span>Cơ sở quan tâm:</span>
                    </span>
                    <span className="font-semibold text-slate-800">
                      {selectedCustomer.campus || 'Chưa chọn'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 flex items-center space-x-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                      <span>Khoá học quan tâm:</span>
                    </span>
                    <span className="font-semibold text-slate-800">
                      {selectedCustomer.course_interest || 'Chưa rõ'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 flex items-center space-x-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>Cập nhật lần cuối:</span>
                    </span>
                    <span className="text-slate-700">
                      {selectedCustomer.updated_ts ? formatTime(selectedCustomer.updated_ts) : '—'}
                    </span>
                  </div>
                </div>

                {customerDetail?.behavior && (
                  <div className="space-y-2 p-3 rounded-xl border border-emerald-100 bg-emerald-50/50">
                    <span className="text-xs font-bold text-slate-900 block">Hành vi (Javis)</span>
                    <p className="text-xs text-slate-700">
                      Giai đoạn: <b>{customerDetail.behavior.stage}</b>
                      {' · '}{customerDetail.behavior.message_count || 0} tin nhắn
                      {' · '}{customerDetail.behavior.comment_count || 0} bình luận
                    </p>
                    {customerDetail.behavior.last_body && (
                      <p className="text-xs text-slate-600">Mới nhất: “{customerDetail.behavior.last_body}”</p>
                    )}
                    {customerDetail.behavior.by_class && (
                      <p className="text-[11px] text-slate-500">
                        {Object.entries(customerDetail.behavior.by_class).map(([k, v]) => `${k}: ${v}`).join(' · ')}
                      </p>
                    )}
                  </div>
                )}

                {/* Linked Identities */}
                {customerDetail?.identities && customerDetail.identities.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-xs font-bold text-slate-900 block">Định danh liên kết</span>
                    <div className="space-y-1">
                      {customerDetail.identities.map((id, idx) => (
                        <div key={idx} className="p-2 bg-slate-50 rounded-lg text-xs flex items-center justify-between border border-slate-100 font-mono">
                          <span className="text-slate-500">{id.kind}:</span>
                          <span className="text-slate-800">{id.ext_id}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Markdown Notes & Timeline from Vault */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900 flex items-center space-x-1.5">
                      <FileText className="w-4 h-4 text-saoviet-500" />
                      <span>Lịch sử & Ghi chú hồ sơ (Vault CRM)</span>
                    </span>
                  </div>
                  <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs text-slate-800 leading-relaxed font-mono whitespace-pre-wrap max-h-60 overflow-y-auto">
                    {detailLoading ? 'Đang tải hồ sơ...' : (customerDetail?.markdown || 'Chưa có tệp ghi chú chi tiết trong vault.')}
                  </div>
                </div>

                {/* Quick Handoff Action */}
                <div className="pt-2">
                  <button
                    onClick={() => handleCreateHandoffTask(selectedCustomer)}
                    disabled={isHandoffing}
                    className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-saoviet-500 hover:bg-saoviet-600 text-white font-bold text-xs rounded-xl shadow-md transition-all cursor-pointer disabled:opacity-50"
                  >
                    <UserCheck className="w-4 h-4" />
                    <span>{isHandoffing ? 'Đang tạo việc...' : 'Tạo việc gọi lại (Giao Kanban)'}</span>
                  </button>
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

                      {can('delete_crm') && (
                        <button
                          onClick={() => handleDeleteCustomer(selectedCustomer.crm_id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-xl transition-colors"
                          title="Xoá hồ sơ này"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
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
              Gộp hồ sơ <b>{selectedCustomer.name}</b> ({selectedCustomer.crm_id}) vào một hồ sơ chính khác.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Chọn hồ sơ mục tiêu (nhận gộp)
              </label>
              <select
                value={targetCustomerId}
                onChange={(e) => setTargetCustomerId(e.target.value)}
                className="w-full p-2.5 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
              >
                <option value="">-- Chọn khách hàng mục tiêu --</option>
                {customers
                  .filter((c) => c.crm_id !== selectedCustomer.crm_id)
                  .map((c) => (
                    <option key={c.crm_id} value={c.crm_id}>
                      {c.name} ({maskPhone(c.phones?.[0] || '', true)}) - {c.crm_id}
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

