import React, { useState, useEffect } from 'react'
import {
  MessageSquare,
  Send,
  XCircle,
  UserCheck,
  CheckCircle2,
  Clock,
  RotateCcw,
  Search,
  Filter,
  Bot,
  AlertCircle,
  Edit3,
} from 'lucide-react'
import { api, InboxItem, ConversationItem } from '../lib/api'
import { formatTime, timeAgo } from '../lib/utils'

export const Inbox: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'comments' | 'messenger'>('comments')
  const [inboxItems, setInboxItems] = useState<InboxItem[]>([])
  const [conversations, setConversations] = useState<ConversationItem[]>([])
  const [filterStatus, setFilterStatus] = useState<string>('pending')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [actionMsg, setActionMsg] = useState<{ id: string; msg: string; type: 'success' | 'error' } | null>(null)

  // Edit draft state
  const [editingDraftId, setEditingDraftId] = useState<string | null>(null)
  const [editedText, setEditedText] = useState<string>('')

  // Handoff note modal state
  const [handoffModalItem, setHandoffModalItem] = useState<InboxItem | null>(null)
  const [handoffNote, setHandoffNote] = useState<string>('')

  const loadData = async () => {
    try {
      const [inboxRes, convRes] = await Promise.all([
        api.getInbox().catch(() => ({ items: [] })),
        api.getConversations().catch(() => ({ items: [] })),
      ])
      setInboxItems(inboxRes.items || [])
      setConversations(convRes.items || [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 15000)
    return () => clearInterval(interval)
  }, [])

  const handleSendDraft = async (item: InboxItem) => {
    const commentId = item.comment_id || item.id
    setActionLoading(commentId)
    try {
      const text = editingDraftId === commentId ? editedText : item.draft_response
      await api.sendDraft(commentId, text)
      setActionMsg({ id: commentId, msg: 'Đã gửi phản hồi thành công!', type: 'success' })
      setEditingDraftId(null)
      loadData()
    } catch (err: any) {
      setActionMsg({ id: commentId, msg: err.message || 'Lỗi gửi phản hồi', type: 'error' })
    } finally {
      setActionLoading(null)
      setTimeout(() => setActionMsg(null), 4000)
    }
  }

  const handleRejectDraft = async (item: InboxItem) => {
    const commentId = item.comment_id || item.id
    setActionLoading(commentId)
    try {
      await api.rejectDraft(commentId)
      setActionMsg({ id: commentId, msg: 'Đã bỏ qua nháp này', type: 'success' })
      loadData()
    } catch (err: any) {
      setActionMsg({ id: commentId, msg: err.message || 'Lỗi bỏ qua', type: 'error' })
    } finally {
      setActionLoading(null)
      setTimeout(() => setActionMsg(null), 4000)
    }
  }

  const handleConfirmHandoff = async () => {
    if (!handoffModalItem) return
    const commentId = handoffModalItem.comment_id || handoffModalItem.id
    setActionLoading(commentId)
    try {
      await api.handoffToStaff(commentId, handoffNote.trim())
      setActionMsg({ id: commentId, msg: 'Đã tạo việc và giao nhân viên hỗ trợ!', type: 'success' })
      setHandoffModalItem(null)
      setHandoffNote('')
      loadData()
    } catch (err: any) {
      setActionMsg({ id: commentId, msg: err.message || 'Lỗi tạo việc', type: 'error' })
    } finally {
      setActionLoading(null)
      setTimeout(() => setActionMsg(null), 4000)
    }
  }

  const handleReleaseTakeover = async (threadId: string) => {
    setActionLoading(threadId)
    try {
      await api.releaseTakeover(threadId)
      setActionMsg({ id: threadId, msg: 'Javis đã nhận lại cuộc trò chuyện', type: 'success' })
      loadData()
    } catch (err: any) {
      setActionMsg({ id: threadId, msg: err.message || 'Lỗi nhận lại', type: 'error' })
    } finally {
      setActionLoading(null)
      setTimeout(() => setActionMsg(null), 4000)
    }
  }

  const filteredComments = inboxItems.filter((item) => {
    if (filterStatus !== 'all' && item.status !== filterStatus) return false
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      const matchAuthor = item.author_name?.toLowerCase().includes(q)
      const matchMsg = item.message?.toLowerCase().includes(q)
      const matchDraft = item.draft_response?.toLowerCase().includes(q)
      const matchPhone = item.phone?.includes(q)
      return matchAuthor || matchMsg || matchDraft || matchPhone
    }
    return true
  })

  return (
    <div className="space-y-6">
      {/* Top Header with Tab Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Hộp thư & Duyệt câu trả lời</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Duyệt nháp Javis tự động tạo hoặc theo dõi cuộc trò chuyện Messenger với khách.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-slate-200/80 p-1 rounded-xl w-fit">
          <button
            onClick={() => setActiveSubTab('comments')}
            className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeSubTab === 'comments'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <MessageSquare className="w-4 h-4 text-saoviet-500" />
            <span>Bình luận Fanpage ({inboxItems.length})</span>
          </button>
          <button
            onClick={() => setActiveSubTab('messenger')}
            className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeSubTab === 'messenger'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Bot className="w-4 h-4 text-blue-500" />
            <span>Tin nhắn Messenger ({conversations.length})</span>
          </button>
        </div>
      </div>

      {/* SUB-TAB 1: COMMENTS & DRAFTS */}
      {activeSubTab === 'comments' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-3">
            <div className="flex items-center space-x-1.5 overflow-x-auto w-full md:w-auto">
              {[
                { id: 'pending', label: 'Chờ duyệt', count: inboxItems.filter((i) => i.status === 'pending').length },
                { id: 'sent', label: 'Đã gửi', count: inboxItems.filter((i) => i.status === 'sent').length },
                { id: 'handoff', label: 'Cần người hỗ trợ', count: inboxItems.filter((i) => i.status === 'handoff').length },
                { id: 'all', label: 'Tất cả', count: inboxItems.length },
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setFilterStatus(f.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                    filterStatus === f.id
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {f.label} ({f.count})
                </button>
              ))}
            </div>

            <div className="relative w-full md:w-72">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm người gửi, SĐT, nội dung..."
                className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-saoviet-500"
              />
            </div>
          </div>

          {/* Comments List */}
          <div className="space-y-4">
            {filteredComments.map((item) => {
              const commentId = item.comment_id || item.id
              const isEditing = editingDraftId === commentId
              const msg = actionMsg?.id === commentId ? actionMsg : null
              const isBusy = actionLoading === commentId

              return (
                <div
                  key={commentId}
                  className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-slate-300 transition-all space-y-4"
                >
                  {/* Status Banner / Feedback */}
                  {msg && (
                    <div
                      className={`p-2.5 rounded-xl text-xs font-medium flex items-center space-x-2 ${
                        msg.type === 'success' ? 'bg-emerald-50 text-emerald-800' : 'bg-red-50 text-red-800'
                      }`}
                    >
                      {msg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                      <span>{msg.msg}</span>
                    </div>
                  )}

                  {/* Comment Metadata */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-10 h-10 rounded-full bg-slate-100 border border-slate-200 text-slate-700 font-bold text-sm flex items-center justify-center flex-shrink-0">
                        {item.author_name ? item.author_name.slice(0, 2).toUpperCase() : 'KH'}
                      </div>
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-bold text-sm text-slate-900">{item.author_name}</span>
                          {item.phone && (
                            <span className="text-[11px] px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 font-bold border border-emerald-200">
                              SĐT: {item.phone}
                            </span>
                          )}
                          {item.intent && (
                            <span className="text-[11px] px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 font-medium border border-blue-100">
                              Mục đích: {item.intent}
                            </span>
                          )}
                          {item.branch && (
                            <span className="text-[11px] px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 font-medium border border-purple-100">
                              Cơ sở: {item.branch}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {formatTime(item.created_time)} • ID: {commentId.slice(0, 14)}...
                        </p>
                      </div>
                    </div>

                    <span
                      className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                        item.status === 'pending'
                          ? 'bg-amber-100 text-amber-800'
                          : item.status === 'sent'
                          ? 'bg-emerald-100 text-emerald-800'
                          : item.status === 'handoff'
                          ? 'bg-rose-100 text-rose-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {item.status === 'pending'
                        ? 'Chờ duyệt'
                        : item.status === 'sent'
                        ? 'Đã gửi'
                        : item.status === 'handoff'
                        ? 'Đã giao người'
                        : 'Đã bỏ'}
                    </span>
                  </div>

                  {/* Customer's comment body */}
                  <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100 text-xs text-slate-800 leading-relaxed font-normal">
                    <span className="font-bold text-slate-900 block mb-1">Khách bình luận:</span>
                    "{item.message}"
                  </div>

                  {/* Javis draft response */}
                  {item.draft_response && (
                    <div className="p-4 bg-saoviet-50/70 border border-saoviet-200/80 rounded-xl space-y-2">
                      <div className="flex items-center justify-between text-xs font-bold text-saoviet-800">
                        <div className="flex items-center space-x-1.5">
                          <Bot className="w-4 h-4 text-saoviet-600" />
                          <span>Câu trả lời Javis soạn sẵn</span>
                        </div>
                        {item.status === 'pending' && !isEditing && (
                          <button
                            onClick={() => {
                              setEditingDraftId(commentId)
                              setEditedText(item.draft_response || '')
                            }}
                            className="text-saoviet-600 hover:text-saoviet-700 flex items-center space-x-1 text-[11px] font-semibold"
                          >
                            <Edit3 className="w-3 h-3" />
                            <span>Chỉnh sửa câu trả lời</span>
                          </button>
                        )}
                      </div>

                      {isEditing ? (
                        <div className="space-y-2">
                          <textarea
                            rows={3}
                            value={editedText}
                            onChange={(e) => setEditedText(e.target.value)}
                            className="w-full p-2.5 text-xs text-slate-900 bg-white border border-saoviet-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                          />
                          <div className="flex items-center justify-end space-x-2">
                            <button
                              onClick={() => setEditingDraftId(null)}
                              className="px-3 py-1 text-xs text-slate-600 hover:bg-slate-200/70 rounded-md"
                            >
                              Huỷ sửa
                            </button>
                            <button
                              onClick={() => setEditingDraftId(null)}
                              className="px-3 py-1 text-xs bg-saoviet-500 text-white font-bold rounded-md"
                            >
                              Lưu nháp
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-slate-800 leading-relaxed italic">
                          "{item.draft_response}"
                        </p>
                      )}
                    </div>
                  )}

                  {/* Actions for staff/manager */}
                  {item.status === 'pending' && (
                    <div className="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-slate-100">
                      <button
                        onClick={() => handleRejectDraft(item)}
                        disabled={isBusy}
                        className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-600 hover:text-red-700 hover:bg-red-50 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                      >
                        <XCircle className="w-4 h-4 text-slate-400 hover:text-red-500" />
                        <span>Bỏ qua</span>
                      </button>

                      <button
                        onClick={() => {
                          setHandoffModalItem(item)
                          setHandoffNote(`Khách ${item.author_name} hỏi: ${item.message.slice(0, 100)}`)
                        }}
                        disabled={isBusy}
                        className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                      >
                        <UserCheck className="w-4 h-4 text-slate-500" />
                        <span>Tạo việc giao người</span>
                      </button>

                      <button
                        onClick={() => handleSendDraft(item)}
                        disabled={isBusy}
                        className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl shadow-md shadow-saoviet-200 transition-all cursor-pointer disabled:opacity-50"
                      >
                        <Send className="w-4 h-4" />
                        <span>{isBusy ? 'Đang gửi...' : 'Gửi phản hồi'}</span>
                      </button>
                    </div>
                  )}
                </div>
              )
            })}

            {filteredComments.length === 0 && (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400 text-xs">
                <MessageSquare className="w-10 h-10 mx-auto mb-3 text-slate-300" />
                <p className="font-semibold text-slate-600">Không có bình luận nào phù hợp</p>
                <p className="text-slate-400 mt-1">Hãy thử đổi trạng thái lọc hoặc xoá từ khoá tìm kiếm</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SUB-TAB 2: MESSENGER CONVERSATIONS & TAKEOVER */}
      {activeSubTab === 'messenger' && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 text-xs text-blue-900 flex items-start space-x-3">
            <Bot className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block mb-0.5">Cơ chế nhường quyền tự động (Takeover 4 giờ):</span>
              Khi nhân viên mở Meta Business Suite hoặc điện thoại để nhắn tin trực tiếp với khách, Javis sẽ tự động tạm lùi lại trong 4 tiếng để tránh trả lời trùng lặp. Khi tư vấn xong, nhân viên có thể bấm nút <b>"Javis nhận lại"</b> để kích hoạt trả lời tự động trở lại ngay lập tức.
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {conversations.map((conv) => {
              const isTakeover = conv.takeover?.active
              const isBusy = actionLoading === conv.id

              return (
                <div
                  key={conv.id}
                  className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between space-y-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-11 h-11 rounded-full bg-blue-100 text-blue-800 font-bold text-sm flex items-center justify-center">
                        {conv.recipient_name ? conv.recipient_name.slice(0, 2).toUpperCase() : 'FB'}
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm">{conv.recipient_name}</h3>
                        <p className="text-[11px] text-slate-400">{timeAgo(conv.last_message_ts)}</p>
                      </div>
                    </div>

                    {isTakeover ? (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                        Nhân viên đang trực
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                        Javis quản lý
                      </span>
                    )}
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-700">
                    <span className="font-semibold text-slate-900 block mb-0.5">Tin nhắn gần nhất:</span>
                    "{conv.last_message || 'Chưa có nội dung'}"
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                    <div className="text-[11px] text-slate-500">
                      {isTakeover && conv.takeover?.expires_at ? (
                        <span>Hết hạn takeover: {formatTime(conv.takeover.expires_at)}</span>
                      ) : (
                        <span>Tự động giải đáp 24/7</span>
                      )}
                    </div>

                    {isTakeover && (
                      <button
                        onClick={() => handleReleaseTakeover(conv.id)}
                        disabled={isBusy}
                        className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-bold text-saoviet-700 bg-saoviet-50 hover:bg-saoviet-100 border border-saoviet-200 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
                      >
                        <RotateCcw className={`w-3.5 h-3.5 ${isBusy ? 'animate-spin' : ''}`} />
                        <span>Javis nhận lại</span>
                      </button>
                    )}
                  </div>
                </div>
              )
            })}

            {conversations.length === 0 && (
              <div className="col-span-2 bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400 text-xs">
                <Bot className="w-10 h-10 mx-auto mb-3 text-slate-300" />
                <p className="font-semibold text-slate-600">Chưa có cuộc trò chuyện Messenger nào</p>
                <p className="text-slate-400 mt-1">Khi khách gửi tin nhắn vào Fanpage, dữ liệu sẽ hiển thị ở đây</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal: Handoff Note */}
      {handoffModalItem && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <h3 className="text-base font-bold text-slate-900">Tạo việc giao nhân viên hỗ trợ</h3>
            <p className="text-xs text-slate-500">
              Việc này sẽ chuyển bình luận của <b>{handoffModalItem.author_name}</b> vào Bảng Việc Cần Làm để tư vấn viên phụ trách theo dõi.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Ghi chú công việc</label>
              <textarea
                rows={3}
                value={handoffNote}
                onChange={(e) => setHandoffNote(e.target.value)}
                placeholder="Nhập ghi chú cho nhân viên (vd: Khách cần tư vấn khoá TOEIC cấp tốc)..."
                className="w-full p-3 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
              />
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                onClick={() => setHandoffModalItem(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
              >
                Huỷ bỏ
              </button>
              <button
                onClick={handleConfirmHandoff}
                className="px-4 py-2 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl shadow-md shadow-saoviet-200 transition-all cursor-pointer"
              >
                Xác nhận tạo việc
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
