import React, { useState, useEffect } from 'react'
import {
  ShoppingBag,
  Package,
  Truck,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Edit3,
  XCircle,
  Send,
  HelpCircle,
  Copy,
  Check,
  RefreshCw,
  Plus,
  Trash2,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react'
import {
  api,
  OpsOrder,
  OpsOrderItem,
  ExtractOrderResponse,
} from '../lib/api'

interface OrderInboxPanelProps {
  crmId?: string
  threadId?: string
  customerName?: string
  pageId?: string
  messages: Array<{ body: string; sender?: string; kind?: string }>
  onInsertMessageToDraft?: (text: string) => void
  onToast?: (msg: string) => void
}

export const OrderInboxPanel: React.FC<OrderInboxPanelProps> = ({
  crmId,
  threadId,
  customerName,
  pageId,
  messages,
  onInsertMessageToDraft,
  onToast,
}) => {
  const [order, setOrder] = useState<OpsOrder | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [isExtracting, setIsExtracting] = useState<boolean>(false)
  const [isActionPending, setIsActionPending] = useState<boolean>(false)
  const [isEditing, setIsEditing] = useState<boolean>(false)
  const [extractedPreview, setExtractedPreview] = useState<ExtractOrderResponse | null>(null)
  const [copiedTracking, setCopiedTracking] = useState<boolean>(false)

  // Edit form state
  const [editName, setEditName] = useState<string>('')
  const [editPhone, setEditPhone] = useState<string>('')
  const [editAddress, setEditAddress] = useState<string>('')
  const [editCod, setEditCod] = useState<number>(0)
  const [editNotes, setEditNotes] = useState<string>('')
  const [editItems, setEditItems] = useState<OpsOrderItem[]>([])

  const loadOrder = async () => {
    if (!threadId && !crmId) return
    setIsLoading(true)
    try {
      const res = await api.getOrders({
        thread_id: threadId || undefined,
        crm_id: crmId || undefined,
        limit: 1,
      })
      if (res.ok && res.orders && res.orders.length > 0) {
        // Fetch full order detail with items and shipment
        const detailRes = await api.getOrder(res.orders[0].id)
        if (detailRes.ok && detailRes.order) {
          setOrder(detailRes.order)
          populateEditForm(detailRes.order)
        }
      } else {
        setOrder(null)
      }
    } catch {
      // Ignore
    } finally {
      setIsLoading(false)
    }
  }

  const populateEditForm = (o: OpsOrder) => {
    setEditName(o.customer_name || '')
    setEditPhone(o.customer_phone || '')
    setEditAddress(o.shipping_address || '')
    setEditCod(o.cod_amount || o.total_amount || 0)
    setEditNotes(o.customer_notes || '')
    setEditItems(o.items || [])
  }

  useEffect(() => {
    setExtractedPreview(null)
    setIsEditing(false)
    loadOrder()
  }, [threadId, crmId])

  const handleExtractFromThread = async (autoSave: boolean = false) => {
    if (!messages || messages.length === 0) {
      if (onToast) onToast('Chưa có tin nhắn trong hội thoại để trích xuất.')
      return
    }
    setIsExtracting(true)
    try {
      const res = await api.extractOrderFromThread({
        messages,
        customer_name: customerName,
        thread_id: threadId,
        crm_id: crmId,
        page_id: pageId,
        auto_save: autoSave,
      })
      if (res.ok) {
        setExtractedPreview(res)
        if (autoSave && res.saved_order) {
          setOrder(res.saved_order)
          populateEditForm(res.saved_order)
          setExtractedPreview(null)
          if (onToast) onToast('Đã trích xuất và tạo đơn nháp thành công!')
        }
      }
    } catch (err: any) {
      if (onToast) onToast(err?.message || 'Lỗi khi trích xuất đơn hàng bằng AI')
    } finally {
      setIsExtracting(false)
    }
  }

  const handleSaveExtractedPreview = async () => {
    if (!extractedPreview) return
    setIsActionPending(true)
    try {
      const res = await api.createOrder({
        crm_id: crmId,
        thread_id: threadId,
        page_id: pageId,
        customer_name: extractedPreview.customer_name,
        customer_phone: extractedPreview.customer_phone,
        shipping_address: extractedPreview.shipping_address,
        items: extractedPreview.items,
        total_amount: extractedPreview.total_amount,
        cod_amount: extractedPreview.cod_amount,
        ai_confidence: extractedPreview.ai_confidence,
        missing_fields: extractedPreview.missing_fields,
        status: (extractedPreview.status as any) || 'draft',
      })
      if (res.ok && res.order) {
        setOrder(res.order)
        populateEditForm(res.order)
        setExtractedPreview(null)
        if (onToast) onToast('Đã lưu đơn hàng thành công!')
      }
    } catch (err: any) {
      if (onToast) onToast(err?.message || 'Không thể lưu đơn hàng')
    } finally {
      setIsActionPending(false)
    }
  }

  const handleConfirmOrder = async () => {
    if (!order) return
    setIsActionPending(true)
    try {
      const res = await api.confirmOrder(order.id)
      if (res.ok && res.order) {
        setOrder(res.order)
        if (onToast) onToast('Đã xác nhận đơn hàng thành công!')
      }
    } catch (err: any) {
      if (onToast) onToast(err?.message || 'Lỗi khi xác nhận đơn hàng')
    } finally {
      setIsActionPending(false)
    }
  }

  const handleCreateShipment = async () => {
    if (!order) return
    if (!order.customer_phone || !order.shipping_address) {
      if (onToast) onToast('Vui lòng điền đủ Số điện thoại và Địa chỉ giao hàng trước khi tạo vận đơn!')
      return
    }
    setIsActionPending(true)
    try {
      const res = await api.createShipment(order.id, 'ghn')
      if (res.ok && res.order) {
        setOrder(res.order)
        if (onToast) onToast(`Đã tạo vận đơn GHN thành công: ${res.shipment?.tracking_code || ''}`)
      } else {
        if (onToast) onToast(res.error || 'Chưa thể tạo vận đơn GHN. Vui lòng kiểm tra cài đặt token.')
      }
    } catch (err: any) {
      if (onToast) onToast(err?.message || 'Lỗi tạo vận đơn GHN')
    } finally {
      setIsActionPending(false)
    }
  }

  const handleCancelOrder = async () => {
    if (!order) return
    const reason = prompt('Nhập lý do hủy đơn hàng (hoặc để trống):', 'Khách yêu cầu hủy')
    if (reason === null) return
    setIsActionPending(true)
    try {
      const res = await api.cancelOrder(order.id, reason)
      if (res.ok && res.order) {
        setOrder(res.order)
        if (onToast) onToast('Đã hủy đơn hàng thành công!')
      }
    } catch (err: any) {
      if (onToast) onToast(err?.message || 'Lỗi khi hủy đơn hàng')
    } finally {
      setIsActionPending(false)
    }
  }

  const handleSaveEdit = async () => {
    if (!order) return
    setIsActionPending(true)
    try {
      const updates = {
        customer_name: editName,
        customer_phone: editPhone,
        shipping_address: editAddress,
        cod_amount: editCod,
        customer_notes: editNotes,
        items: editItems,
      }
      const res = await api.updateOrder(order.id, updates)
      if (res.ok && res.order) {
        setOrder(res.order)
        setIsEditing(false)
        if (onToast) onToast('Đã cập nhật thông tin đơn hàng!')
      }
    } catch (err: any) {
      if (onToast) onToast(err?.message || 'Lỗi khi lưu đơn hàng')
    } finally {
      setIsActionPending(false)
    }
  }

  const handleAskCustomerForMissing = () => {
    const q = order?.missing_fields?.length
      ? extractedPreview?.followup_question ||
        (order.missing_fields.includes('phone') && order.missing_fields.includes('address')
          ? `Dạ ${order.customer_name || 'anh/chị'} cho em xin số điện thoại và địa chỉ nhận hàng để bên em lên đơn gửi ngay ạ!`
          : order.missing_fields.includes('phone')
          ? `Dạ ${order.customer_name || 'anh/chị'} cho em xin số điện thoại nhận hàng nhé ạ!`
          : `Dạ ${order.customer_name || 'anh/chị'} cho em xin địa chỉ cụ thể để bên em giao tận nơi nhé ạ!`)
      : extractedPreview?.followup_question

    if (q && onInsertMessageToDraft) {
      onInsertMessageToDraft(q)
      if (onToast) onToast('Đã nạp câu hỏi vào ô soạn tin nhắn!')
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedTracking(true)
    setTimeout(() => setCopiedTracking(false), 2000)
  }

  // Trạng thái badge hiển thị
  const getStatusBadge = (status: string) => {
    const map: Record<string, { label: string; color: string; icon: any }> = {
      draft: { label: 'Bản nháp', color: 'bg-slate-100 text-slate-700 border-slate-200', icon: Clock },
      needs_info: { label: 'Cần bổ sung thông tin', color: 'bg-amber-50 text-amber-800 border-amber-300 font-bold', icon: AlertCircle },
      ready_to_confirm: { label: 'Đủ thông tin - Chờ duyệt', color: 'bg-blue-50 text-blue-700 border-blue-200 font-bold', icon: CheckCircle2 },
      confirmed: { label: 'Đã xác nhận chốt đơn', color: 'bg-indigo-50 text-indigo-700 border-indigo-200 font-bold', icon: Package },
      shipment_pending: { label: 'Chờ tạo vận đơn', color: 'bg-purple-50 text-purple-700 border-purple-200', icon: Clock },
      shipment_created: { label: 'Đã tạo vận đơn', color: 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold', icon: Truck },
      picking: { label: 'Đang lấy hàng', color: 'bg-cyan-50 text-cyan-800 border-cyan-200', icon: Truck },
      shipping: { label: 'Đang giao hàng', color: 'bg-blue-50 text-blue-800 border-blue-300 font-bold', icon: Truck },
      delivered: { label: 'Giao thành công', color: 'bg-emerald-100 text-emerald-900 border-emerald-400 font-bold', icon: CheckCircle2 },
      failed: { label: 'Giao thất bại', color: 'bg-rose-50 text-rose-700 border-rose-200', icon: XCircle },
      cancelled: { label: 'Đã hủy đơn', color: 'bg-slate-100 text-slate-500 border-slate-200 line-through', icon: XCircle },
      returned: { label: 'Chuyển hoàn', color: 'bg-orange-50 text-orange-700 border-orange-200', icon: AlertCircle },
    }
    const cur = map[status] || { label: status, color: 'bg-slate-100 text-slate-700 border-slate-200', icon: Clock }
    const Icon = cur.icon
    return (
      <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs border ${cur.color}`}>
        <Icon className="w-3.5 h-3.5" />
        <span>{cur.label}</span>
      </span>
    )
  }

  if (isLoading) {
    return (
      <div className="p-6 text-center text-slate-400 text-xs space-y-2">
        <RefreshCw className="w-5 h-5 animate-spin mx-auto text-blue-600" />
        <span>Đang nạp dữ liệu đơn hàng...</span>
      </div>
    )
  }

  return (
    <div className="space-y-4 text-xs">
      {/* ================= HEADER BAR ================= */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <div className="flex items-center space-x-1.5">
          <ShoppingBag className="w-4 h-4 text-blue-600" />
          <span className="font-bold text-slate-900 text-sm">Đơn Hàng Social</span>
        </div>

        <div className="flex items-center space-x-1.5">
          <button
            type="button"
            onClick={() => handleExtractFromThread(false)}
            disabled={isExtracting}
            title="Dùng AI trích xuất thông tin đơn từ tin nhắn"
            className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold transition-colors cursor-pointer disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isExtracting ? 'animate-spin text-indigo-600' : 'text-indigo-600'}`} />
            <span>{isExtracting ? 'Đang đọc tin...' : 'Trích xuất AI'}</span>
          </button>
        </div>
      </div>

      {/* ================= AI EXTRACTION PREVIEW BANNER ================= */}
      {extractedPreview && (
        <div className="bg-indigo-50/90 border border-indigo-200 rounded-xl p-3.5 space-y-2.5 animate-fade-in shadow-2xs">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5 font-bold text-indigo-950">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span>Kết quả trích xuất từ tin nhắn</span>
            </div>
            <span className="text-[11px] font-mono font-bold bg-white px-2 py-0.5 rounded text-indigo-700 border border-indigo-100">
              Tin cậy: {Math.round(extractedPreview.ai_confidence * 100)}%
            </span>
          </div>

          <div className="space-y-1 text-slate-700 text-xs">
            <div>
              <span className="text-slate-500">Khách:</span>{' '}
              <strong className="text-slate-900">{extractedPreview.customer_name}</strong>
              {extractedPreview.customer_phone ? (
                <span className="ml-2 font-mono text-emerald-700 bg-emerald-50 px-1 rounded">
                  {extractedPreview.customer_phone}
                </span>
              ) : (
                <span className="ml-2 text-rose-600 font-semibold italic">[Thiếu SĐT]</span>
              )}
            </div>
            <div>
              <span className="text-slate-500">Địa chỉ:</span>{' '}
              <span className={extractedPreview.shipping_address ? 'text-slate-800' : 'text-rose-600 italic'}>
                {extractedPreview.shipping_address || '[Thiếu địa chỉ nhận hàng]'}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Sản phẩm:</span>{' '}
              {extractedPreview.items && extractedPreview.items.length > 0 ? (
                <span className="font-semibold text-slate-900">
                  {extractedPreview.items.map((i) => `${i.name} (x${i.quantity})`).join(', ')} —{' '}
                  <span className="text-blue-600 font-bold">{extractedPreview.total_amount.toLocaleString()} đ</span>
                </span>
              ) : (
                <span className="text-rose-600 italic">[Chưa khớp sản phẩm catalog]</span>
              )}
            </div>
          </div>

          {extractedPreview.followup_question && (
            <div className="bg-white/90 p-2 rounded-lg border border-indigo-100 text-[11px] text-slate-600 flex items-start justify-between gap-2">
              <span className="italic leading-relaxed">Gợi ý hỏi khách: "{extractedPreview.followup_question}"</span>
              {onInsertMessageToDraft && (
                <button
                  type="button"
                  onClick={() => onInsertMessageToDraft(extractedPreview.followup_question || '')}
                  className="shrink-0 text-blue-600 font-bold hover:underline"
                >
                  Nạp tin nháp
                </button>
              )}
            </div>
          )}

          <div className="flex items-center justify-end space-x-2 pt-1">
            <button
              type="button"
              onClick={() => setExtractedPreview(null)}
              className="px-2.5 py-1 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-xs cursor-pointer"
            >
              Hủy
            </button>
            <button
              type="button"
              onClick={handleSaveExtractedPreview}
              disabled={isActionPending}
              className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-2xs cursor-pointer disabled:opacity-50"
            >
              {isActionPending ? 'Đang lưu...' : 'Lưu thành đơn hàng'}
            </button>
          </div>
        </div>
      )}

      {/* ================= MAIN ORDER VIEW / EMPTY STATE ================= */}
      {!order && !extractedPreview ? (
        <div className="bg-slate-50 border border-dashed border-slate-200 rounded-2xl p-5 text-center space-y-2.5">
          <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
            <ShoppingBag className="w-5 h-5" />
          </div>
          <div className="font-semibold text-slate-700">Chưa có đơn hàng cho khách này</div>
          <p className="text-[11px] text-slate-400 max-w-xs mx-auto leading-relaxed">
            Hệ thống hỗ trợ AI tự động đọc tin nhắn hội thoại để trích xuất SĐT, địa chỉ và sản phẩm.
          </p>
          <div className="pt-1 flex items-center justify-center space-x-2">
            <button
              type="button"
              onClick={() => handleExtractFromThread(true)}
              disabled={isExtracting}
              className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-colors shadow-sm shadow-emerald-600/20 cursor-pointer flex items-center space-x-1.5"
            >
              <ShoppingBag className="w-3.5 h-3.5" />
              <span>Trích xuất &amp; Tạo đơn ngay</span>
            </button>
          </div>
        </div>
      ) : order && !isEditing ? (
        /* ================= EXISTING ORDER DETAIL CARD ================= */
        <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-2xs space-y-3.5">
          {/* Top Status & Confidence */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="font-mono font-black text-slate-900 text-xs">#{order.id.slice(-6).toUpperCase()}</span>
              {getStatusBadge(order.status)}
            </div>

            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="p-1 text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors"
              title="Chỉnh sửa thông tin đơn"
            >
              <Edit3 className="w-4 h-4" />
            </button>
          </div>

          {/* Missing fields alert */}
          {order.missing_fields && order.missing_fields.length > 0 && order.status !== 'cancelled' && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-2.5 text-xs text-amber-900 space-y-1">
              <div className="flex items-center space-x-1.5 font-bold">
                <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>Cần bổ sung:</span>
                <span className="text-rose-700 font-semibold">
                  {order.missing_fields.map((f) => (f === 'phone' ? 'Số điện thoại' : f === 'address' ? 'Địa chỉ' : 'Sản phẩm')).join(', ')}
                </span>
              </div>
              <p className="text-[11px] text-amber-800 leading-relaxed">
                Đơn hàng chưa đủ điều kiện tạo vận đơn. Nhân viên cần hỏi bổ sung từ khách hàng.
              </p>
            </div>
          )}

          {/* Customer & Delivery Info */}
          <div className="bg-slate-50/80 rounded-xl p-3 border border-slate-100 space-y-1.5 text-slate-700">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-[11px]">Người nhận:</span>
              <span className="font-bold text-slate-900">{order.customer_name || 'Khách hàng'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400 text-[11px]">Số điện thoại:</span>
              <span className={`font-mono font-bold ${order.customer_phone ? 'text-emerald-700' : 'text-rose-600 italic'}`}>
                {order.customer_phone || 'Chưa có SĐT'}
              </span>
            </div>
            <div className="pt-1 border-t border-slate-200/50">
              <span className="text-slate-400 text-[11px] block">Địa chỉ nhận hàng:</span>
              <span className={`block font-medium mt-0.5 ${order.shipping_address ? 'text-slate-800' : 'text-rose-600 italic'}`}>
                {order.shipping_address || 'Chưa có địa chỉ cụ thể'}
              </span>
            </div>
          </div>

          {/* Items Table */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px] font-bold text-slate-500 uppercase tracking-wider">
              <span>Sản phẩm</span>
              <span>Thành tiền</span>
            </div>
            <div className="divide-y divide-slate-100 border border-slate-100 rounded-xl overflow-hidden bg-white">
              {(order.items && order.items.length > 0 ? order.items : []).map((it, idx) => (
                <div key={idx} className="p-2.5 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-900 leading-tight">{it.name}</div>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {it.sku || 'SKU'} · SL: {it.quantity}
                    </span>
                  </div>
                  <div className="font-bold text-slate-800">
                    {(it.total || it.price * it.quantity).toLocaleString()} đ
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pricing summary */}
          <div className="space-y-1 pt-1 border-t border-slate-100 text-xs">
            <div className="flex items-center justify-between text-slate-500">
              <span>Tiền hàng:</span>
              <span className="font-semibold text-slate-800">{order.total_amount?.toLocaleString() || 0} đ</span>
            </div>
            <div className="flex items-center justify-between text-slate-500">
              <span>Cước vận chuyển:</span>
              <span className="font-semibold text-slate-800">
                {order.shipping_fee ? `${order.shipping_fee.toLocaleString()} đ` : 'Miễn phí'}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm font-bold text-slate-900 pt-1 border-t border-slate-200/60">
              <span>Thu hộ COD:</span>
              <span className="text-blue-600 font-black">{order.cod_amount?.toLocaleString() || order.total_amount?.toLocaleString() || 0} đ</span>
            </div>
          </div>

          {/* Active Shipment Tracking Card */}
          {order.shipment && (
            <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-3 space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-1.5 font-bold text-emerald-900 text-xs">
                  <Truck className="w-4 h-4 text-emerald-600" />
                  <span>Vận đơn: {order.shipment.provider.toUpperCase()}</span>
                </div>
                <span className="text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-300">
                  {order.shipment.status}
                </span>
              </div>

              {order.shipment.tracking_code && (
                <div className="flex items-center justify-between bg-white p-1.5 rounded-lg border border-emerald-200/80">
                  <span className="font-mono font-black text-slate-800 tracking-wider text-xs">
                    {order.shipment.tracking_code}
                  </span>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(order.shipment?.tracking_code || '')}
                    className="p-1 text-slate-400 hover:text-emerald-700"
                    title="Sao chép mã vận đơn"
                  >
                    {copiedTracking ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Action buttons */}
          <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center gap-1.5">
            {order.missing_fields && order.missing_fields.length > 0 && (
              <button
                type="button"
                onClick={handleAskCustomerForMissing}
                className="flex-1 py-1.5 px-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white font-semibold text-xs shadow-2xs transition-colors flex items-center justify-center space-x-1 cursor-pointer"
              >
                <HelpCircle className="w-3.5 h-3.5" />
                <span>Hỏi bổ sung</span>
              </button>
            )}

            {['draft', 'needs_info', 'ready_to_confirm'].includes(order.status) && (
              <button
                type="button"
                onClick={handleConfirmOrder}
                disabled={isActionPending}
                className="flex-1 py-1.5 px-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-2xs transition-colors flex items-center justify-center space-x-1 cursor-pointer disabled:opacity-50"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Xác nhận đơn</span>
              </button>
            )}

            {['confirmed', 'shipment_pending'].includes(order.status) && (
              <button
                type="button"
                onClick={handleCreateShipment}
                disabled={isActionPending || !order.customer_phone || !order.shipping_address}
                className="flex-1 py-1.5 px-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-2xs transition-colors flex items-center justify-center space-x-1 cursor-pointer disabled:opacity-50"
              >
                <Truck className="w-3.5 h-3.5" />
                <span>Tạo vận đơn (GHN)</span>
              </button>
            )}

            {!['cancelled', 'delivered'].includes(order.status) && (
              <button
                type="button"
                onClick={handleCancelOrder}
                disabled={isActionPending}
                className="p-1.5 rounded-xl border border-slate-200 text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
                title="Hủy đơn hàng"
              >
                <XCircle className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      ) : isEditing && order ? (
        /* ================= INLINE ORDER EDITOR ================= */
        <div className="bg-white border border-blue-200 rounded-2xl p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="font-bold text-slate-900 text-xs flex items-center space-x-1">
              <Edit3 className="w-3.5 h-3.5 text-blue-600" />
              <span>Chỉnh sửa thông tin đơn hàng</span>
            </span>
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="text-xs text-slate-400 hover:text-slate-700"
            >
              Hủy
            </button>
          </div>

          <div className="space-y-2">
            <div>
              <label className="text-[11px] font-semibold text-slate-500 block mb-0.5">Tên người nhận:</label>
              <input
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-500 block mb-0.5">Số điện thoại:</label>
              <input
                type="text"
                value={editPhone}
                onChange={(e) => setEditPhone(e.target.value)}
                placeholder="09xxx..."
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-500 block mb-0.5">Địa chỉ giao hàng:</label>
              <textarea
                rows={2}
                value={editAddress}
                onChange={(e) => setEditAddress(e.target.value)}
                placeholder="Số nhà, đường, phường/xã, quận/huyện, tỉnh/thành..."
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-500 block mb-0.5">Tiền thu hộ COD (VNĐ):</label>
              <input
                type="number"
                value={editCod}
                onChange={(e) => setEditCod(Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500 font-bold"
              />
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-500 block mb-0.5">Ghi chú giao hàng:</label>
              <input
                type="text"
                value={editNotes}
                onChange={(e) => setEditNotes(e.target.value)}
                placeholder="Cho xem hàng không thử..."
                className="w-full bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsEditing(false)}
              className="px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 text-xs hover:bg-slate-50 cursor-pointer"
            >
              Hủy
            </button>
            <button
              type="button"
              onClick={handleSaveEdit}
              disabled={isActionPending}
              className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-2xs cursor-pointer disabled:opacity-50"
            >
              {isActionPending ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
