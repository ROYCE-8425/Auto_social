import React, { useState, useEffect } from 'react'
import {
  ShoppingBag,
  Package,
  Truck,
  CheckCircle2,
  Clock,
  Search,
  Filter,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  AlertCircle,
  Copy,
  Check,
  XCircle,
  Phone,
  User,
  MapPin,
  Calendar,
  ShieldCheck,
  Plus,
} from 'lucide-react'
import { api, OpsOrder, OpsOrderItem, OpsShipment } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useCareScope } from '../lib/scope'

export const OrdersPage: React.FC = () => {
  const { role, can } = useAuth()
  const { scopePageId, scopeBrand } = useCareScope()
  const [orders, setOrders] = useState<OpsOrder[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedOrder, setSelectedOrder] = useState<OpsOrder | null>(null)
  const [isActionPending, setIsActionPending] = useState<boolean>(false)
  const [copiedTracking, setCopiedTracking] = useState<string | null>(null)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 3500)
  }

  const loadOrders = async () => {
    setIsLoading(true)
    try {
      const res = await api.getOrders({
        page_id: scopePageId || undefined,
        limit: 100,
      })
      if (res?.ok && res.orders) {
        setOrders(res.orders)
        if (selectedOrder) {
          const updated = res.orders.find((o) => o.id === selectedOrder.id)
          if (updated) setSelectedOrder(updated)
        }
      }
    } catch (err: any) {
      showToast(err?.message || 'Không thể tải danh sách đơn hàng')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadOrders()
  }, [scopePageId, scopeBrand])

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    setCopiedTracking(text)
    showToast(`Đã sao chép ${label}`)
    setTimeout(() => setCopiedTracking(null), 2500)
  }

  const handleConfirmOrder = async (orderId: string) => {
    setIsActionPending(true)
    try {
      const res = await api.confirmOrder(orderId)
      if (res.ok) {
        showToast('Đã xác nhận đơn hàng thành công!')
        loadOrders()
      } else {
        showToast('Không thể xác nhận đơn hàng')
      }
    } catch (err: any) {
      showToast(err?.message || 'Lỗi khi xác nhận đơn')
    } finally {
      setIsActionPending(false)
    }
  }

  const handleCreateShipment = async (orderId: string) => {
    setIsActionPending(true)
    try {
      const res = await api.createShipment(orderId, 'ghn')
      if (res.ok) {
        showToast(`Đã tạo vận đơn GHN thành công! Mã: ${res.shipment?.tracking_code || ''}`)
        loadOrders()
      } else {
        showToast(res.error || 'Chưa thể tạo vận đơn GHN')
      }
    } catch (err: any) {
      showToast(err?.message || 'Lỗi khi đẩy vận đơn GHN')
    } finally {
      setIsActionPending(false)
    }
  }

  const handleSyncShipment = async (orderId: string) => {
    setIsActionPending(true)
    try {
      const res = await api.syncShipmentStatus(orderId)
      if (res.ok) {
        const status = res.shipment?.status || res.tracking?.status || 'đã cập nhật'
        showToast(`Đã check GHN: ${status}`)
        loadOrders()
      } else {
        showToast(res.error || 'Chưa thể kiểm tra trạng thái GHN')
      }
    } catch (err: any) {
      showToast(err?.message || 'Lỗi khi kiểm tra trạng thái GHN')
    } finally {
      setIsActionPending(false)
    }
  }

  const handleCancelOrder = async (orderId: string) => {
    const reason = prompt('Nhập lý do hủy đơn (hoặc để trống):', 'Khách đổi ý')
    if (reason === null) return
    setIsActionPending(true)
    try {
      const res = await api.cancelOrder(orderId, reason)
      if (res.ok) {
        showToast('Đã hủy đơn hàng!')
        loadOrders()
      }
    } catch (err: any) {
      showToast(err?.message || 'Lỗi khi hủy đơn')
    } finally {
      setIsActionPending(false)
    }
  }

  // Filtered orders
  const filteredOrders = orders.filter((o) => {
    if (statusFilter !== 'all' && o.status !== statusFilter) return false
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      const name = (o.customer_name || '').toLowerCase()
      const phone = (o.customer_phone || '').toLowerCase()
      const id = (o.id || '').toLowerCase()
      const tracking = (o.shipment?.tracking_code || '').toLowerCase()
      return name.includes(q) || phone.includes(q) || id.includes(q) || tracking.includes(q)
    }
    return true
  })

  // KPI Calculations
  const totalOrders = orders.length
  const pendingConfirmCount = orders.filter((o) => o.status === 'draft' || o.status === 'ready_to_confirm' || o.status === 'needs_info').length
  const shippingCount = orders.filter((o) => o.status === 'shipment_created' || o.status === 'shipping').length
  const totalRevenue = orders
    .filter((o) => o.status !== 'cancelled')
    .reduce((sum, o) => sum + (o.cod_amount || o.total_amount || 0), 0)

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'confirmed':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 inline-flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-blue-600" />
            Đã xác nhận
          </span>
        )
      case 'shipment_created':
      case 'shipping':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-700 border border-purple-200 inline-flex items-center gap-1">
            <Truck className="w-3 h-3 text-purple-600" />
            Đang giao GHN
          </span>
        )
      case 'delivered':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 inline-flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            Hoàn tất
          </span>
        )
      case 'cancelled':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 inline-flex items-center gap-1">
            <XCircle className="w-3 h-3 text-rose-600" />
            Đã hủy
          </span>
        )
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 inline-flex items-center gap-1">
            <Clock className="w-3 h-3 text-amber-600" />
            Chờ xác nhận
          </span>
        )
    }
  }

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* ================= HEADER ================= */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-600 via-teal-600 to-cyan-600 flex items-center justify-center text-white shadow-md shadow-emerald-500/20">
            <ShoppingBag className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Quản Lý Đơn Hàng &amp; Vận Chuyển
              </h1>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200 uppercase font-mono">
                {orders.length} Đơn
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Theo dõi toàn bộ đơn hàng chốt từ Messenger/Fanpage, tiến độ đẩy vận đơn GHN và doanh thu COD.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5 self-start md:self-auto">
          <button
            type="button"
            onClick={loadOrders}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
            title="Tải lại danh sách"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Làm mới</span>
          </button>
        </div>
      </div>

      {/* ================= 4 KPI STATS ================= */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex items-center space-x-3.5">
          <div className="w-11 h-11 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <ShoppingBag className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Tổng số đơn</p>
            <p className="text-xl font-black text-slate-900 mt-0.5">{totalOrders}</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex items-center space-x-3.5">
          <div className="w-11 h-11 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Chờ xác nhận</p>
            <p className="text-xl font-black text-amber-600 mt-0.5">{pendingConfirmCount}</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex items-center space-x-3.5">
          <div className="w-11 h-11 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <Truck className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Đang giao GHN</p>
            <p className="text-xl font-black text-purple-600 mt-0.5">{shippingCount}</p>
          </div>
        </div>

        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex items-center space-x-3.5">
          <div className="w-11 h-11 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Package className="w-5 h-5" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500">Doanh thu COD</p>
            <p className="text-lg font-black text-emerald-600 mt-0.5">
              {totalRevenue.toLocaleString()} đ
            </p>
          </div>
        </div>
      </div>

      {/* ================= SEARCH & STATUS FILTER ================= */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Status Filter Tabs */}
        <div className="flex items-center space-x-1 overflow-x-auto pb-1 md:pb-0">
          {[
            { id: 'all', label: 'Tất cả' },
            { id: 'draft', label: 'Chờ xác nhận' },
            { id: 'confirmed', label: 'Đã xác nhận' },
            { id: 'shipment_created', label: 'Đang giao GHN' },
            { id: 'delivered', label: 'Hoàn tất' },
            { id: 'cancelled', label: 'Đã hủy' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                statusFilter === tab.id
                  ? 'bg-slate-900 text-white shadow-2xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <div className="relative min-w-[260px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo tên, SĐT, mã đơn, mã GHN..."
            className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
      </div>

      {/* ================= ORDERS TABLE / EMPTY STATE ================= */}
      <div className="bg-white border border-slate-200/80 rounded-2xl shadow-2xs overflow-hidden">
        {isLoading ? (
          <div className="py-16 text-center text-slate-400 text-xs">
            <RefreshCw className="w-6 h-6 animate-spin text-emerald-600 mx-auto mb-2" />
            <span>Đang nạp danh sách đơn hàng...</span>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="py-16 text-center text-slate-400 text-xs space-y-2">
            <ShoppingBag className="w-10 h-10 text-slate-300 mx-auto mb-1" />
            <p className="font-semibold text-slate-700 text-sm">Chưa có đơn hàng nào</p>
            <p className="text-slate-400 max-w-sm mx-auto">
              Khi khách hàng nhắn tin chốt đơn trên Fanpage Messenger, Javis Sales Automation sẽ tự động nhận diện và tạo đơn tại đây.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">Mã đơn</th>
                  <th className="py-3 px-4">Khách hàng</th>
                  <th className="py-3 px-4">Sản phẩm</th>
                  <th className="py-3 px-4 text-right">Tổng tiền / COD</th>
                  <th className="py-3 px-4">Trạng thái</th>
                  <th className="py-3 px-4">Vận chuyển GHN</th>
                  <th className="py-3 px-4 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredOrders.map((order) => {
                  const tracking = order.shipment?.tracking_code
                  return (
                    <tr
                      key={order.id}
                      onClick={() => setSelectedOrder(order)}
                      className={`hover:bg-slate-50/70 transition-colors cursor-pointer ${
                        selectedOrder?.id === order.id ? 'bg-emerald-50/40' : ''
                      }`}
                    >
                      {/* Mã đơn */}
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">
                        #{order.id.slice(-6).toUpperCase()}
                      </td>

                      {/* Khách hàng */}
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-900">{order.customer_name || 'Khách lẻ'}</div>
                        <div className="text-[11px] text-slate-500 font-mono flex items-center gap-1 mt-0.5">
                          <Phone className="w-3 h-3 text-slate-400" />
                          <span>{order.customer_phone || 'Chưa có SĐT'}</span>
                        </div>
                      </td>

                      {/* Sản phẩm */}
                      <td className="py-3 px-4 max-w-xs">
                        {order.items && order.items.length > 0 ? (
                          <div className="space-y-0.5">
                            {order.items.slice(0, 2).map((it, idx) => (
                              <div key={idx} className="truncate text-slate-800 font-medium">
                                • {it.name} <span className="text-slate-400 font-bold">(x{it.quantity})</span>
                              </div>
                            ))}
                            {order.items.length > 2 && (
                              <div className="text-[10px] text-slate-400 italic">
                                +{order.items.length - 2} sản phẩm khác
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">Không có sản phẩm</span>
                        )}
                      </td>

                      {/* Tiền / COD */}
                      <td className="py-3 px-4 text-right">
                        <div className="font-black text-slate-900">
                          {(order.cod_amount || order.total_amount || 0).toLocaleString()} đ
                        </div>
                        {order.shipping_fee ? (
                          <div className="text-[10px] text-slate-400">
                            Ship: +{order.shipping_fee.toLocaleString()} đ
                          </div>
                        ) : null}
                      </td>

                      {/* Trạng thái */}
                      <td className="py-3 px-4">
                        {getStatusBadge(order.status)}
                      </td>

                      {/* GHN Tracking */}
                      <td className="py-3 px-4">
                        {tracking ? (
                          <div className="flex items-center space-x-1.5">
                            <span className="font-mono font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-[11px]">
                              {tracking}
                            </span>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleCopy(tracking, 'Mã vận đơn')
                              }}
                              className="text-slate-400 hover:text-emerald-600 p-1 cursor-pointer"
                              title="Sao chép mã vận đơn"
                            >
                              {copiedTracking === tracking ? (
                                <Check className="w-3.5 h-3.5 text-emerald-600" />
                              ) : (
                                <Copy className="w-3.5 h-3.5" />
                              )}
                            </button>
                            <a
                              href={`https://donhang.ghn.vn/?order_code=${tracking}`}
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="text-slate-400 hover:text-blue-600 p-1"
                              title="Tra cứu trên GHN"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleSyncShipment(order.id)
                              }}
                              disabled={isActionPending}
                              className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-cyan-50 text-cyan-700 border border-cyan-200 hover:bg-cyan-100 font-semibold text-[10px] transition-colors disabled:opacity-60 cursor-pointer"
                              title="Check trạng thái mới nhất từ GHN"
                            >
                              <RefreshCw className={`w-3 h-3 ${isActionPending ? 'animate-spin' : ''}`} />
                              <span>Check</span>
                            </button>
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">Chưa tạo đơn GHN</span>
                        )}
                      </td>

                      {/* Thao tác */}
                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end space-x-1.5">
                          {order.status === 'draft' && (
                            <button
                              type="button"
                              onClick={() => handleConfirmOrder(order.id)}
                              disabled={isActionPending}
                              className="px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-[11px] transition-colors cursor-pointer"
                            >
                              Xác nhận
                            </button>
                          )}
                          {order.status === 'confirmed' && !tracking && (
                            <button
                              type="button"
                              onClick={() => handleCreateShipment(order.id)}
                              disabled={isActionPending}
                              className="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-[11px] transition-colors cursor-pointer inline-flex items-center gap-1"
                            >
                              <Truck className="w-3 h-3" />
                              <span>Đẩy GHN</span>
                            </button>
                          )}
                          {order.status !== 'cancelled' && order.status !== 'delivered' && (
                            <button
                              type="button"
                              onClick={() => handleCancelOrder(order.id)}
                              disabled={isActionPending}
                              className="p-1 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                              title="Hủy đơn"
                            >
                              <XCircle className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ================= ORDER DETAIL MODAL ================= */}
      {selectedOrder && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto space-y-5 animate-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <ShoppingBag className="w-5 h-5 text-emerald-600" />
                <h3 className="text-base font-bold text-slate-900">
                  Chi tiết đơn hàng #{selectedOrder.id.slice(-6).toUpperCase()}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedOrder(null)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-lg hover:bg-slate-100"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            {/* Customer & Shipping Info */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Khách hàng:</span>
                <span className="font-bold text-slate-900">{selectedOrder.customer_name || 'Khách lẻ'}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Số điện thoại:</span>
                <span className="font-mono font-bold text-slate-900">{selectedOrder.customer_phone || 'Chưa có'}</span>
              </div>
              <div className="flex items-start justify-between gap-4">
                <span className="text-slate-500 shrink-0">Địa chỉ giao:</span>
                <span className="font-medium text-slate-900 text-right">{selectedOrder.shipping_address || 'Chưa có địa chỉ'}</span>
              </div>
              {selectedOrder.customer_notes && (
                <div className="flex items-start justify-between gap-4 pt-1 border-t border-slate-200/60">
                  <span className="text-slate-500 shrink-0">Ghi chú:</span>
                  <span className="italic text-slate-700 text-right">{selectedOrder.customer_notes}</span>
                </div>
              )}
            </div>

            {/* Products Table in Modal */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Danh sách sản phẩm</h4>
              <div className="border border-slate-200 rounded-xl overflow-hidden text-xs">
                <table className="w-full text-left">
                  <thead className="bg-slate-50 text-slate-500 font-bold border-b border-slate-200">
                    <tr>
                      <th className="py-2 px-3">Tên sản phẩm</th>
                      <th className="py-2 px-3 text-center">SL</th>
                      <th className="py-2 px-3 text-right">Đơn giá</th>
                      <th className="py-2 px-3 text-right">Thành tiền</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(selectedOrder.items || []).map((it, idx) => (
                      <tr key={idx}>
                        <td className="py-2.5 px-3 font-medium text-slate-900">{it.name}</td>
                        <td className="py-2.5 px-3 text-center font-bold text-slate-700">{it.quantity}</td>
                        <td className="py-2.5 px-3 text-right text-slate-600">{it.price.toLocaleString()} đ</td>
                        <td className="py-2.5 px-3 text-right font-bold text-slate-900">
                          {(it.price * it.quantity).toLocaleString()} đ
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-slate-50 font-bold border-t border-slate-200">
                    <tr>
                      <td colSpan={3} className="py-2 px-3 text-right text-slate-600">Tổng tiền COD:</td>
                      <td className="py-2 px-3 text-right text-emerald-600 font-black text-sm">
                        {(selectedOrder.cod_amount || selectedOrder.total_amount || 0).toLocaleString()} đ
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end space-x-2.5 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedOrder(null)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50"
              >
                Đóng
              </button>
              {selectedOrder.status === 'confirmed' && !selectedOrder.shipment?.tracking_code && (
                <button
                  type="button"
                  onClick={() => handleCreateShipment(selectedOrder.id)}
                  disabled={isActionPending}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm shadow-emerald-600/20"
                >
                  Tạo đơn GHN ngay
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Floating Toast */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white px-4 py-2.5 rounded-xl shadow-lg text-xs font-semibold flex items-center space-x-2 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  )
}
