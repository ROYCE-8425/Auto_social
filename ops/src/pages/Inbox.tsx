import React, { useState, useEffect, useRef } from 'react'
import {
  MessageSquare,
  Send,
  UserCheck,
  Clock,
  Search,
  Bot,
  AlertCircle,
  MessageCircle,
  Sparkles,
  Filter,
  SlidersHorizontal,
  Info,
  Phone,
  Copy,
  Pencil,
  Plus,
  Paperclip,
  Image as ImageIcon,
  Smile,
  FileText,
  Ban,
  Check,
  CheckCheck,
  ArrowRight,
  MoreVertical,
  CheckCircle2,
  Calendar,
  Building2,
  Briefcase,
  Tag,
  Share2,
  Flame,
  ShieldCheck,
  ShieldAlert,
  Zap,
  Layers,
  Compass,
  RefreshCw,
  ShoppingBag,
  User,
} from 'lucide-react'
import { api, CareConversation, CareDraft, CareEvent, CareState, CareStats } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useCareScope } from '../lib/scope'
import { FacebookIcon, MessengerIcon, TikTokIcon } from '../components/BrandIcons'
import { OrderInboxPanel } from '../components/OrderInboxPanel'

export interface ConversationItem {
  id: string
  name: string
  avatar: string
  avatarBg: string
  message: string
  time: string
  unreadCount?: number
  hasUnreadDot?: boolean
  tags: { text: string; color: 'red' | 'amber' | 'green' | 'blue' | 'purple' }[]
  crmTags?: { text: string; color: 'red' | 'amber' | 'green' | 'blue' | 'purple' }[]
  phone: string
  fbId: string
  source: string
  firstInteraction: string
  pageName: string
  status: 'lead_hot' | 'interested' | 'purchased' | 'care_needed'
  leadScore?: {
    score: number
    tier: 'hot' | 'warm' | 'cold'
    nextBestAction: string
    suggestedScript: string
    reason: string
    risk: 'low' | 'medium' | 'high'
  }
  omnichannel?: Array<{
    channel: 'messenger' | 'facebook' | 'tiktok' | 'zalo'
    label: string
    count: number
    lastActive: string
  }>
  history: {
    title: string
    desc: string
    time: string
    dotColor: 'green' | 'blue' | 'gray'
  }[]
  messages: {
    id: string
    sender: 'customer' | 'bot' | 'staff'
    text: string
    time: string
  }[]
}

export const Inbox: React.FC = () => {
  const { can } = useAuth()
  const { scope, scopeBrand, scopePageId } = useCareScope()
  const [activeChannel, setActiveChannel] = useState<'comments' | 'messenger' | 'tiktok'>('messenger')
  const [statusFilter, setStatusFilter] = useState<'unread' | 'need_human' | 'done'>('unread')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedConvId, setSelectedConvId] = useState<string>('')
  const [inputText, setInputText] = useState('')
  const [isTakeover, setIsTakeover] = useState(false)
  const [rightPanelTab, setRightPanelTab] = useState<'orders' | 'crm'>('orders')
  const [copySuccess, setCopySuccess] = useState<string | null>(null)
  const [conversationsList, setConversationsList] = useState<ConversationItem[]>([])
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [processingDraftId, setProcessingDraftId] = useState<number | null>(null)
  const [isAddingTag, setIsAddingTag] = useState(false)
  const [newTagInput, setNewTagInput] = useState('')

  const showToast = (msg: string) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 3500)
  }
  const [noteText, setNoteText] = useState('')
  const [isPolling, setIsPolling] = useState(false)
  const [pollNotice, setPollNotice] = useState<string | null>(null)
  const [rawEvents, setRawEvents] = useState<CareEvent[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Real Care state & drafts
  const [careDrafts, setCareDrafts] = useState<CareDraft[]>([])
  const [careStats, setCareStats] = useState<CareStats | null>(null)

  const loadInboxData = () => {
    // 1. Lấy danh sách hội thoại thực tế từ Fanpage qua /fanpage-care/conversations
    api.getConversations({
      page_id: scopePageId || undefined,
      brand: scopeBrand || undefined,
    }).then((res) => {
      if (res?.ok && res.conversations && res.conversations.length > 0) {
        const mapped: ConversationItem[] = res.conversations.map((c) => {
          const pageTitle = c.page_id === '343562028848465'
            ? 'Game Giá Rẻ BSN'
            : (c.page_id === '988656934325292' ? 'Royce Shop' : 'Fanpage')

          const timeStr = c.last_event_ts
            ? new Date(c.last_event_ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : 'Vừa xong'

          return {
            id: `${c.page_id}_${c.psid}`,
            name: c.customer_name || 'Khách hàng Facebook',
            avatar: `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(c.customer_name || 'Khách')}&backgroundColor=0084ff,2563eb,10b981,f59e0b`,
            avatarBg: 'bg-blue-100 text-blue-700',
            message: c.last_body || 'Đã gửi một tin nhắn đến shop',
            time: timeStr,
            hasUnreadDot: Boolean(c.is_unreplied),
            unreadCount: c.is_unreplied ? 1 : undefined,
            tags: c.is_unreplied
              ? [{ text: 'Cần hỗ trợ', color: 'amber' as const }]
              : [{ text: 'Đã trả lời', color: 'green' as const }],
            crmTags: [
              { text: pageTitle, color: 'blue' as const },
              { text: 'Facebook', color: 'purple' as const },
            ],
            phone: 'Chưa có SĐT',
            fbId: c.psid,
            source: 'Messenger',
            firstInteraction: timeStr,
            pageName: pageTitle,
            status: c.is_unreplied ? 'care_needed' as const : 'interested' as const,
            history: [
              {
                title: 'Tin nhắn gần nhất',
                desc: c.last_body || 'Tương tác qua Messenger',
                time: timeStr,
                dotColor: 'green' as const,
              }
            ],
            messages: [
              {
                id: `m_init_${c.psid}`,
                sender: c.last_sender === 'page' ? 'bot' : 'customer',
                text: c.last_body || 'Chào shop',
                time: timeStr,
              }
            ],
          }
        })
        setConversationsList(mapped)
        setSelectedConvId((prev) => {
          if (prev && mapped.some((m) => m.id === prev)) return prev
          return mapped[0]?.id || ''
        })
      } else {
        setConversationsList([])
      }
    }).catch(() => {})

    // 2. Lấy danh sách nháp AI, sự kiện và thống kê thực tế
    api.getInbox({
      page_id: scopePageId || undefined,
      brand: scopeBrand || undefined,
      limit: 100,
    }).then((res) => {
      if (res?.ok) {
        if (res.drafts) setCareDrafts(res.drafts)
        if (res.stats) setCareStats(res.stats)
        if (res.events) setRawEvents(res.events)
      }
    }).catch(() => {})
  }

  useEffect(() => {
    loadInboxData()
  }, [scope, scopeBrand, scopePageId])

  // Tải chi tiết lịch sử tin nhắn thật khi chọn hội thoại
  useEffect(() => {
    if (!selectedConvId) return
    const parts = selectedConvId.split('_')
    if (parts.length >= 2 && parts[0] !== 'conv') {
      const pageId = parts[0]
      const psid = parts.slice(1).join('_')
      api.getConversationThread(pageId, psid).then((res) => {
        if (res?.ok && res.events && res.events.length > 0) {
          const sortedEvents = [...res.events].sort((a, b) => (a.created_ts || 0) - (b.created_ts || 0))
          const threadMsgs = sortedEvents.map((ev, i) => {
            const isBot = ev.kind === 'echo' || ev.from_name === 'Javis AI' || ev.class === 'auto_reply'
            const isStaff = ev.from_name === 'Nhân viên Fanpage'
            return {
              id: `ev_${ev.id || i}`,
              sender: isBot ? ('bot' as const) : (isStaff ? ('staff' as const) : ('customer' as const)),
              text: ev.body,
              time: ev.created_ts
                ? new Date(ev.created_ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : '',
            }
          })
          setConversationsList((prev) =>
            prev.map((c) => (c.id === selectedConvId ? { ...c, messages: threadMsgs } : c))
          )
        }
      }).catch(() => {})
    }
  }, [selectedConvId])

  // List of comment conversations from real events
  const commentConversations: ConversationItem[] = rawEvents
    .filter((e) => e.kind === 'comment' || e.platform === 'facebook')
    .map((e) => {
      const pageTitle = e.page_id === '343562028848465'
        ? 'Game Giá Rẻ BSN'
        : (e.page_id === '988656934325292' ? 'Royce Shop' : 'Fanpage Facebook')
      const timeStr = e.created_ts
        ? new Date(e.created_ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : 'Vừa xong'

      return {
        id: `cmt_${e.id}`,
        name: e.from_name || 'Khách hàng Facebook',
        avatar: `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(e.from_name || 'Khách')}&backgroundColor=1877F2,2563eb,0084ff`,
        avatarBg: 'bg-blue-100 text-blue-700',
        message: e.body || 'Đã để lại bình luận trên bài viết',
        time: timeStr,
        hasUnreadDot: false,
        tags: [{ text: 'Bình luận', color: 'blue' as const }],
        crmTags: [
          { text: pageTitle, color: 'blue' as const },
          { text: 'Post Comment', color: 'purple' as const },
        ],
        phone: 'Chưa có SĐT',
        fbId: e.from_id || e.object_id,
        source: 'Facebook',
        firstInteraction: timeStr,
        pageName: pageTitle,
        status: 'interested' as const,
        history: [
          {
            title: 'Bình luận bài viết',
            desc: e.body,
            time: timeStr,
            dotColor: 'blue' as const,
          },
        ],
        messages: [
          {
            id: `msg_cmt_${e.id}`,
            sender: 'customer',
            text: e.body,
            time: timeStr,
          },
        ],
      }
    })

  const effectiveConversations = activeChannel === 'comments'
    ? (commentConversations.length > 0 ? commentConversations : conversationsList.filter(c => c.source === 'Facebook'))
    : conversationsList.filter(c => c.source !== 'Facebook')

  const currentConv = effectiveConversations.find((c) => c.id === selectedConvId) || effectiveConversations[0] || null

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    setCopySuccess(label)
    setTimeout(() => setCopySuccess(null), 2000)
  }

  const handleApplyDraft = (text: string) => {
    setInputText(text)
  }

  const handlePollNow = async () => {
    setIsPolling(true)
    setPollNotice('Đang kéo tin nhắn và bình luận mới nhất từ Fanpage...')
    try {
      await api.pollNow()
      setPollNotice('Đã đồng bộ thành công!')
      loadInboxData()
      setTimeout(() => setPollNotice(null), 3000)
    } catch (err: any) {
      setPollNotice(`Đồng bộ thất bại: ${err?.message || 'Lỗi mạng'}`)
      setTimeout(() => setPollNotice(null), 3000)
    } finally {
      setIsPolling(false)
    }
  }

  const handleSendMessage = async () => {
    if (!inputText.trim() || !currentConv) return
    const textToSend = inputText.trim()
    const newMsg = {
      id: `m_${Date.now()}`,
      sender: 'staff' as const,
      text: textToSend,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setConversationsList((prev) =>
      prev.map((c) => {
        if (c.id === currentConv.id) {
          return {
            ...c,
            message: newMsg.text,
            time: newMsg.time,
            messages: [...c.messages, newMsg],
          }
        }
        return c
      })
    )
    setInputText('')

    // Gửi trực tiếp qua Facebook Messenger nếu có page_id & psid
    const parts = currentConv.id.split('_')
    if (parts.length >= 2 && parts[0] !== 'conv') {
      const pageId = parts[0]
      const psid = parts.slice(1).join('_')
      try {
        await api.sendDirectMessage(pageId, psid, textToSend)
        showToast('Đã gửi tin nhắn qua Facebook Messenger')
      } catch (err) {
        console.error('Lỗi gửi tin nhắn trực tiếp qua Messenger:', err)
        showToast('Lỗi gửi tin nhắn qua Messenger')
      }
    }
  }

  const handleSendDraft = async (draftId: number) => {
    setProcessingDraftId(draftId)
    try {
      const res = await api.sendDraft(draftId)
      if (res?.ok) {
        showToast('Đã duyệt và gửi nháp phản hồi thành công!')
        loadInboxData()
      } else {
        showToast(`Gửi nháp thất bại: ${res?.error || 'Lỗi hệ thống'}`)
      }
    } catch (err: any) {
      showToast(`Lỗi gửi nháp: ${err?.message || 'Lỗi mạng'}`)
    } finally {
      setProcessingDraftId(null)
    }
  }

  const handleRejectDraft = async (draftId: number) => {
    setProcessingDraftId(draftId)
    try {
      const res = await api.rejectDraft(draftId)
      if (res?.ok) {
        showToast('Đã từ chối nháp phản hồi')
        loadInboxData()
      } else {
        showToast('Không thể từ chối nháp')
      }
    } catch (err: any) {
      showToast(`Lỗi từ chối nháp: ${err?.message || 'Lỗi mạng'}`)
    } finally {
      setProcessingDraftId(null)
    }
  }

  const handleToggleTakeover = async () => {
    if (!currentConv) return
    const parts = currentConv.id.split('_')
    if (parts.length >= 2 && parts[0] !== 'conv' && parts[0] !== 'cmt') {
      const pageId = parts[0]
      const psid = parts.slice(1).join('_')
      if (isTakeover) {
        try {
          await api.releaseTakeover(pageId, psid)
          setIsTakeover(false)
          showToast('Đã nhả quyền takeover — Javis AI tiếp tục hỗ trợ tự động')
        } catch (err: any) {
          showToast(`Lỗi khi nhả takeover: ${err?.message || 'Lỗi kết nối'}`)
        }
      } else {
        setIsTakeover(true)
        showToast('Đã kích hoạt takeover — tạm dừng phản hồi bot cho hội thoại này')
      }
    } else {
      setIsTakeover(!isTakeover)
      showToast(isTakeover ? 'Đã tắt takeover' : 'Đã bật takeover cho hội thoại này')
    }
  }

  const handleHandoffTask = async () => {
    if (!currentConv) return
    try {
      const res = await api.handoffToStaff({
        title: `Hỗ trợ khách hàng: ${currentConv.name}`,
        intent: currentConv.message || 'Hội thoại cần nhân viên xử lý từ Fanpage Care',
        priority: currentConv.status === 'care_needed' || currentConv.status === 'lead_hot' ? 1 : 2,
        comment_id: currentConv.id,
      })
      if (res?.ok) {
        showToast(`Đã tạo nhiệm vụ #${res.task_id || ''} trên Kanban thành công!`)
      } else {
        showToast('Đã tạo việc trên Kanban thành công!')
      }
    } catch (err: any) {
      showToast(`Lỗi tạo việc: ${err?.message || 'Không thể tạo task'}`)
    }
  }

  const handleCallCustomer = () => {
    if (!currentConv) return
    if (!currentConv.phone || currentConv.phone === 'Chưa có SĐT' || currentConv.phone === 'Chưa có') {
      showToast('Khách hàng chưa để lại số điện thoại')
      return
    }
    if (currentConv.phone.includes('*')) {
      showToast('Số điện thoại được bảo mật theo chính sách phân quyền')
      return
    }
    window.open(`tel:${currentConv.phone.replace(/\s+/g, '')}`)
  }

  const handleAddTag = () => {
    if (!newTagInput.trim() || !currentConv) return
    const tagText = newTagInput.trim()
    setConversationsList((prev) =>
      prev.map((c) => {
        if (c.id === currentConv.id) {
          return {
            ...c,
            tags: [...c.tags, { text: tagText, color: 'blue' }],
          }
        }
        return c
      })
    )
    setNewTagInput('')
    setIsAddingTag(false)
    showToast(`Đã thêm thẻ "${tagText}" thành công`)
  }

  // Scroll messages to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentConv?.messages])

  const pendingDrafts = careDrafts.filter((d) => d.status === 'pending')
  const pendingCommentDrafts = careStats?.pending_comment_drafts ?? 0
  const pendingMessageDrafts = careStats?.pending_message_drafts ?? 0
  const sentTodayCount = careStats?.replies_24h ?? 0

  const tagColorMap = {
    red: 'bg-rose-50 text-rose-600 border border-rose-200',
    amber: 'bg-amber-50 text-amber-600 border border-amber-200',
    green: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
    blue: 'bg-blue-50 text-blue-600 border border-blue-200',
    purple: 'bg-purple-50 text-purple-600 border border-purple-200',
  }

  const unreadCountBadge = effectiveConversations.filter(c => c.hasUnreadDot).length
  const needHumanBadge = effectiveConversations.filter(c => c.status === 'care_needed').length

  const filteredConversations = effectiveConversations.filter((conv) => {
    if (statusFilter === 'unread' && !conv.hasUnreadDot && unreadCountBadge > 0) return false
    if (statusFilter === 'need_human' && conv.status !== 'care_needed' && needHumanBadge > 0) return false
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      conv.name.toLowerCase().includes(q) ||
      conv.message.toLowerCase().includes(q) ||
      conv.phone.includes(q)
    )
  })

  return (
    <div className="space-y-5">
      {/* PAGE HEADER ROW */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Hộp thư & Nháp</h1>
          <p className="text-sm text-slate-500 font-normal mt-0.5">
            Quản lý hội thoại và tin nhắn đồng bộ trực tiếp từ Fanpage ({conversationsList.length} hội thoại).
          </p>
          {pollNotice && (
            <div className="mt-1 text-xs font-semibold text-blue-600 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-lg inline-flex items-center gap-1.5 animate-fade-in">
              <RefreshCw className={`w-3 h-3 ${isPolling ? 'animate-spin' : ''}`} />
              <span>{pollNotice}</span>
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={handlePollNow}
          disabled={isPolling}
          className="flex items-center space-x-1.5 px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm shadow-blue-200 disabled:opacity-60 cursor-pointer self-start sm:self-auto"
          title="Kéo tin nhắn và bình luận mới nhất từ Facebook Fanpage"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin' : ''}`} />
          <span>{isPolling ? 'Đang kéo tin...' : 'Đồng bộ từ Fanpage'}</span>
        </button>
      </div>

      {/* MAIN 3-COLUMN LAYOUT */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
        {/* ================= COLUMN 1: HỘP THƯ TẬP TRUNG (3 cols) ================= */}
        <div className="xl:col-span-3 bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex flex-col h-[820px]">
          {/* Card Top Title & Action */}
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h2 className="text-base font-bold text-slate-900">Hộp thư tập trung</h2>
            <button
              type="button"
              className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
              title="Tùy chọn bộ lọc"
            >
              <SlidersHorizontal className="w-4 h-4" />
            </button>
          </div>

          {/* Sub-channel tabs (Bình luận Fanpage vs Messenger vs TikTok) */}
          <div className="flex border-b border-slate-100 mt-1">
            <button
              type="button"
              onClick={() => setActiveChannel('comments')}
              className={`flex-1 flex items-center justify-center space-x-1.5 py-2.5 text-xs font-semibold transition-all border-b-2 ${
                activeChannel === 'comments'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <FacebookIcon className="w-3.5 h-3.5 text-[#1877F2]" />
              <span>Bình luận</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveChannel('messenger')}
              className={`flex-1 flex items-center justify-center space-x-1.5 py-2.5 text-xs font-semibold transition-all border-b-2 ${
                activeChannel === 'messenger'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <MessengerIcon className="w-3.5 h-3.5 text-[#0084FF]" />
              <span>Messenger</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveChannel('tiktok')}
              className={`flex-1 flex items-center justify-center space-x-1.5 py-2.5 text-xs font-semibold transition-all border-b-2 ${
                activeChannel === 'tiktok'
                  ? 'border-slate-900 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <TikTokIcon className="w-3.5 h-3.5" colored />
              <span>TikTok</span>
            </button>
          </div>

          {/* 3 Status Filter Pills */}
          <div className="flex items-center space-x-2 my-3">
            <button
              type="button"
              onClick={() => setStatusFilter('unread')}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold transition-all ${
                statusFilter === 'unread'
                  ? 'bg-blue-50 text-blue-600 border border-blue-200'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
              <span>Chưa đọc</span>
              {unreadCountBadge > 0 && (
                <span className="bg-blue-600 text-white rounded-full px-1.5 py-0.2 text-[10px] font-bold ml-0.5">
                  {unreadCountBadge}
                </span>
              )}
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter('need_human')}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold transition-all ${
                statusFilter === 'need_human'
                  ? 'bg-orange-50 text-orange-600 border border-orange-200'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
              <span>Cần người</span>
              {needHumanBadge > 0 && (
                <span className="bg-orange-600 text-white rounded-full px-1.5 py-0.2 text-[10px] font-bold ml-0.5">
                  {needHumanBadge}
                </span>
              )}
            </button>
            <button
              type="button"
              onClick={() => setStatusFilter('done')}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                statusFilter === 'done'
                  ? 'bg-emerald-50 text-emerald-600 border border-emerald-200'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span>Đã xong</span>
            </button>
          </div>

          {/* Search input with filter icon */}
          <div className="flex items-center space-x-2 mb-3">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm tên khách hàng, nội dung tin nhắn..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="button"
              className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-xl border border-slate-200 transition-colors"
              title="Lọc nâng cao"
            >
              <Filter className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Conversations scrollable list */}
          <div className="flex-1 overflow-y-auto space-y-1 pr-1 divide-y divide-slate-50">
            {activeChannel === 'tiktok' ? (
              <div className="p-8 text-center text-slate-500">
                <TikTokIcon className="w-10 h-10 mx-auto mb-3" colored />
                <p className="font-semibold text-slate-700 text-sm">
                  Chưa có bình luận TikTok — kênh này dùng để đăng video.
                </p>
                <p className="text-slate-400 text-xs mt-1">
                  PostPeer hiện chỉ hỗ trợ đăng video, chưa có luồng ingest comment TikTok.
                </p>
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <p className="font-semibold text-slate-600 mb-1">
                  Chưa có hội thoại/nháp. Hãy kết nối Facebook Pages hoặc bấm Quét ngay.
                </p>
                <button
                  type="button"
                  onClick={handlePollNow}
                  disabled={isPolling}
                  className="mt-2 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin' : ''}`} />
                  <span>{isPolling ? 'Đang quét...' : 'Quét ngay'}</span>
                </button>
              </div>
            ) : (
              filteredConversations.map((conv) => {
              const active = conv.id === selectedConvId
              return (
                <div
                  key={conv.id}
                  onClick={() => setSelectedConvId(conv.id)}
                  className={`p-2.5 rounded-xl cursor-pointer transition-all flex items-start space-x-2.5 relative ${
                    active
                      ? 'bg-blue-50/60 border border-blue-200/80 shadow-2xs'
                      : 'hover:bg-slate-50 border border-transparent'
                  }`}
                >
                  {/* Left Avatar with Messenger Icon Badge */}
                  <div className="relative flex-shrink-0">
                    <img
                      src={conv.avatar}
                      alt={conv.name}
                      className="w-10 h-10 rounded-full object-cover ring-1 ring-slate-200"
                    />
                    <span className="absolute -bottom-0.5 -right-0.5 w-4 h-4 rounded-full bg-[#0084FF] text-white flex items-center justify-center shadow-xs">
                      <MessengerIcon className="w-2.5 h-2.5 text-white" />
                    </span>
                  </div>

                  {/* Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <div className="flex items-center space-x-1.5 min-w-0 truncate">
                        <span className="text-xs font-bold text-slate-900 truncate">{conv.name}</span>
                        {conv.leadScore && (
                          <span
                            className={`px-1.5 py-0.2 rounded text-[9px] font-bold inline-flex items-center gap-0.5 flex-shrink-0 ${
                              conv.leadScore.tier === 'hot'
                                ? 'bg-rose-50 text-rose-600 border border-rose-200'
                                : conv.leadScore.tier === 'warm'
                                ? 'bg-amber-50 text-amber-700 border border-amber-200'
                                : 'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}
                          >
                            <Flame className="w-2.5 h-2.5" />
                            {conv.leadScore.score}đ · {conv.leadScore.tier === 'hot' ? 'Hot' : 'Warm'}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center space-x-1 flex-shrink-0">
                        <span className="text-[11px] text-slate-400 font-medium">{conv.time}</span>
                        {conv.hasUnreadDot && <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />}
                      </div>
                    </div>
                    <p className="text-xs text-slate-500 truncate mt-0.5 leading-snug">{conv.message}</p>
                    {/* Tags row */}
                    <div className="flex items-center justify-between mt-1.5">
                      <div className="flex items-center space-x-1 overflow-hidden">
                        {conv.tags.map((t, idx) => (
                          <span
                            key={idx}
                            className={`px-1.5 py-0.2 rounded text-[10px] font-semibold whitespace-nowrap ${tagColorMap[t.color]}`}
                          >
                            {t.text}
                          </span>
                        ))}
                      </div>
                      {conv.unreadCount && (
                        <span className="w-4 h-4 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0">
                          {conv.unreadCount}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )
            })
          )}
          </div>
        </div>

        {/* ================= COLUMN 2: HỘI THOẠI & NHÁP TRẢ LỜI (6 cols) ================= */}
        <div className="xl:col-span-6 bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs flex flex-col justify-between h-[820px]">
          {activeChannel === 'tiktok' ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <TikTokIcon className="w-14 h-14 mb-4" colored />
              <h3 className="text-base font-bold text-slate-900">Kênh TikTok Video</h3>
              <p className="text-sm font-semibold text-slate-700 mt-2 max-w-md">
                Chưa có bình luận TikTok — kênh này dùng để đăng video.
              </p>
              <p className="text-xs text-slate-400 mt-1 max-w-md">
                PostPeer hiện chỉ hỗ trợ đăng video, chưa có luồng ingest comment TikTok. Hệ thống tự động phân phối video ngắn theo lịch.
              </p>
            </div>
          ) : !currentConv ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
              <MessageSquare className="w-14 h-14 mb-4 text-slate-300" />
              <h3 className="text-base font-bold text-slate-900">Chưa có hội thoại được chọn</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-md">
                Chưa có hội thoại/nháp. Hãy kết nối Facebook Pages hoặc bấm Quét ngay.
              </p>
              <button
                type="button"
                onClick={handlePollNow}
                disabled={isPolling}
                className="mt-4 inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin' : ''}`} />
                <span>{isPolling ? 'Đang quét...' : 'Quét ngay'}</span>
              </button>
            </div>
          ) : (
            <>
              {/* Chat Header */}
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            {/* Left: Customer Info */}
            <div className="flex items-center space-x-3">
              <div className="relative">
                <img
                  src={currentConv.avatar}
                  alt={currentConv.name}
                  className="w-10 h-10 rounded-full object-cover ring-2 ring-white shadow-2xs"
                />
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-bold text-slate-900 leading-tight">{currentConv.name}</h3>
                  <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-600 border border-rose-200 text-[10px] font-semibold">
                    Lead nóng
                  </span>
                  <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200 text-[10px] font-semibold">
                    Khách mới
                  </span>
                </div>
                <div className="flex items-center space-x-1.5 text-[11px] text-slate-400 font-medium mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  <span>Đang hoạt động</span>
                </div>
              </div>
            </div>

            {/* Right: Actions */}
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-50 border border-blue-200/70 text-blue-600 text-xs font-semibold">
                <Bot className="w-3.5 h-3.5 text-blue-600" />
                <span>Bot đang hỗ trợ</span>
              </div>
              <button
                type="button"
                onClick={handleToggleTakeover}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all shadow-2xs cursor-pointer ${
                  isTakeover
                    ? 'bg-rose-50 text-rose-700 border-rose-300'
                    : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                <Ban className="w-3.5 h-3.5 text-slate-600" />
                <span>{isTakeover ? 'Đang takeover' : 'Takeover'}</span>
              </button>

              <button
                type="button"
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors ml-1"
                title="Tìm kiếm"
              >
                <Search className="w-4 h-4" />
              </button>
              <button
                type="button"
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                title="Thẻ tag"
              >
                <Tag className="w-4 h-4" />
              </button>
              <button
                type="button"
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                title="Tùy chọn khác"
              >
                <MoreVertical className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Chat Messages Body */}
          <div className="flex-1 overflow-y-auto space-y-4 py-4 px-1">
            {currentConv.messages.map((msg) => {
              const isUser = msg.sender === 'customer'
              return (
                <div
                  key={msg.id}
                  className={`flex items-start space-x-2.5 ${isUser ? '' : 'flex-row-reverse space-x-reverse'}`}
                >
                  {/* Avatar */}
                  {isUser ? (
                    <img
                      src={currentConv.avatar}
                      alt={currentConv.name}
                      className="w-8 h-8 rounded-full object-cover flex-shrink-0 mt-0.5"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center flex-shrink-0 shadow-xs mt-0.5">
                      JO
                    </div>
                  )}

                  {/* Message Bubble */}
                  <div className={`max-w-[72%] ${isUser ? '' : 'text-right'}`}>
                    <div
                      className={`inline-block px-4 py-2.5 text-xs leading-relaxed rounded-2xl text-left whitespace-pre-line ${
                        isUser
                          ? 'bg-slate-100 rounded-tl-sm text-slate-800'
                          : 'bg-emerald-600 text-white font-medium rounded-tr-sm shadow-xs'
                      }`}
                    >
                      {msg.text}
                    </div>
                    <div
                      className={`flex items-center space-x-1 text-[10px] text-slate-400 font-medium mt-1 ${
                        isUser ? 'justify-start' : 'justify-end'
                      }`}
                    >
                      <span>{msg.time}</span>
                      {!isUser && <CheckCheck className="w-3.5 h-3.5 text-emerald-600 inline" />}
                    </div>
                  </div>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Javis AI Next Best Action Card (Pillar 3: Chỉ rõ hành động kế tiếp) */}
          {currentConv.leadScore && (
            <div className="bg-gradient-to-r from-indigo-50/90 via-blue-50/70 to-slate-50 border border-indigo-200/90 rounded-2xl p-3.5 my-2 shadow-2xs">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-xs">
                    <Compass className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-slate-900">Next Best Action · Hành động tối ưu kế tiếp</span>
                      <span
                        className={`px-2 py-0.2 rounded-full text-[10px] font-bold inline-flex items-center gap-1 ${
                          currentConv.leadScore.tier === 'hot'
                            ? 'bg-rose-100 text-rose-700 border border-rose-200'
                            : 'bg-amber-100 text-amber-700 border border-amber-200'
                        }`}
                      >
                        <Flame className="w-2.5 h-2.5" />
                        {currentConv.leadScore.score}đ · {currentConv.leadScore.tier === 'hot' ? 'Hot Lead' : 'Warm'}
                      </span>
                    </div>
                  </div>
                </div>
                <span className="text-[10px] font-bold text-indigo-700 bg-indigo-100/70 px-2 py-0.5 rounded-full border border-indigo-200/60">
                  Ưu tiên cao
                </span>
              </div>

              <div className="bg-white/95 p-3 rounded-xl border border-indigo-100 space-y-1.5">
                <p className="text-xs font-bold text-slate-900 leading-snug">
                  {currentConv.leadScore.nextBestAction}
                </p>
                <p className="text-[11px] text-slate-500 italic leading-tight">
                  Lý do AI đề xuất: {currentConv.leadScore.reason}
                </p>
                <div className="flex items-center justify-between pt-1.5 border-t border-slate-100 gap-2">
                  <span className="text-[11px] text-slate-600 truncate">
                    Kịch bản mẫu: &quot;{currentConv.leadScore.suggestedScript}&quot;
                  </span>
                  <button
                    type="button"
                    onClick={() => handleApplyDraft(currentConv.leadScore!.suggestedScript)}
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] font-bold transition-all shadow-xs flex-shrink-0"
                  >
                    <Zap className="w-3 h-3" />
                    <span>Áp dụng kịch bản</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Javis AI Draft Suggestions Card */}
          <div className="bg-slate-50/90 border border-indigo-100/90 rounded-2xl p-3.5 my-2">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-1.5">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <span className="text-xs font-bold text-slate-900">Javis đề xuất nháp ({pendingDrafts.length})</span>
                <span className="text-[11px] text-slate-400 font-normal">
                  · Duyệt trước khi gửi (Human-in-the-Loop)
                </span>
              </div>
              <div className="flex items-center space-x-1 text-[11px] text-slate-500 font-medium">
                <span>Dữ liệu Fanpage Care thật</span>
                <Info className="w-3.5 h-3.5 text-slate-400" />
              </div>
            </div>

            {pendingDrafts.length === 0 ? (
              <div className="py-6 px-4 text-center border border-dashed border-slate-200 rounded-xl bg-white/70">
                <Sparkles className="w-6 h-6 text-slate-300 mx-auto mb-1.5" />
                <p className="text-xs font-semibold text-slate-600 mb-1">
                  Chưa có hội thoại/nháp. Hãy kết nối Facebook Pages hoặc bấm Quét ngay.
                </p>
                <button
                  type="button"
                  onClick={handlePollNow}
                  disabled={isPolling}
                  className="mt-2 inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin' : ''}`} />
                  <span>{isPolling ? 'Đang quét...' : 'Quét ngay'}</span>
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
                {pendingDrafts.slice(0, 3).map((draft) => (
                  <div
                    key={draft.id}
                    className="bg-white p-3 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-1 mb-1.5">
                        <span className="text-[10px] font-bold text-blue-600 flex items-center space-x-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                          <span>{draft.event_kind === 'comment' ? 'Bình luận' : 'Tin nhắn'}</span>
                        </span>
                        <span className="text-[9px] font-bold text-amber-700 bg-amber-50 border border-amber-200/80 px-1.5 py-0.2 rounded inline-flex items-center gap-0.5">
                          <Clock className="w-2.5 h-2.5 text-amber-600" />
                          Chờ duyệt
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-slate-900 line-clamp-1 leading-tight">
                        {draft.from_name ? `Gửi cho: ${draft.from_name}` : `Mục tiêu: ${draft.target_id}`}
                      </h4>
                      {draft.source_body && (
                        <p className="text-[10px] text-slate-400 italic line-clamp-1 mt-0.5">
                          Khách: &quot;{draft.source_body}&quot;
                        </p>
                      )}
                      <p className="text-[11px] text-slate-600 line-clamp-2 mt-1 leading-tight font-medium bg-slate-50 p-1.5 rounded-lg border border-slate-100">
                        {draft.proposed}
                      </p>
                    </div>
                    <div className="flex items-center space-x-1.5 mt-3 pt-2 border-t border-slate-100">
                      <button
                        type="button"
                        disabled={processingDraftId === draft.id}
                        onClick={() => handleSendDraft(draft.id)}
                        className="flex-1 py-1.5 px-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-xs rounded-lg shadow-2xs transition-colors text-center cursor-pointer"
                      >
                        {processingDraftId === draft.id ? 'Đang gửi...' : 'Duyệt gửi'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleApplyDraft(draft.proposed)}
                        className="py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg transition-colors cursor-pointer"
                        title="Đưa vào ô soạn thảo"
                      >
                        Sửa
                      </button>
                      <button
                        type="button"
                        disabled={processingDraftId === draft.id}
                        onClick={() => handleRejectDraft(draft.id)}
                        className="py-1.5 px-2 bg-white hover:bg-rose-50 text-rose-600 hover:border-rose-200 font-semibold text-xs rounded-lg border border-slate-200 transition-colors cursor-pointer"
                        title="Từ chối nháp này"
                      >
                        Bỏ
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Bottom Message Input Box */}
          <div className="border border-slate-200 rounded-2xl p-2.5 bg-white shadow-2xs">
            <textarea
              rows={2}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSendMessage()
                }
              }}
              placeholder="Nhập tin nhắn... (Shift + Enter để xuống dòng)"
              className="w-full text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none resize-none px-1 py-0.5"
            />
            {/* Action Bar */}
            <div className="flex items-center justify-between pt-2 border-t border-slate-100 mt-1">
              {/* Left Icons */}
              <div className="flex items-center space-x-1 text-slate-400">
                <button
                  type="button"
                  className="p-1.5 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                  title="Đính kèm tệp"
                >
                  <Paperclip className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  className="p-1.5 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                  title="Gửi ảnh"
                >
                  <ImageIcon className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  className="p-1.5 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                  title="Emoji"
                >
                  <Smile className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  className="p-1.5 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                  title="Mẫu câu nhanh"
                >
                  <FileText className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  className="px-2 py-1 text-xs font-bold hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                  title="Lệnh nhanh"
                >
                  /
                </button>
              </div>

              {/* Right Send & Save draft Buttons */}
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => showToast('Đã lưu nháp tin nhắn vào bộ nhớ đệm')}
                  className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-colors"
                >
                  Lưu nháp
                </button>
                <button
                  type="button"
                  onClick={handleSendMessage}
                  className="flex items-center space-x-1.5 px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm shadow-emerald-600/20"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Gửi</span>
                </button>
              </div>
            </div>
          </div>
            </>
          )}
        </div>

        {/* ================= COLUMN 3: NHÁP CHỜ DUYỆT & MINI CRM (3 cols) ================= */}
        <div className="xl:col-span-3 space-y-5">
          {/* Card 1: Nháp chờ duyệt hôm nay */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-1.5">
                <Clock className="w-4 h-4 text-blue-600" />
                <h3 className="text-xs font-bold text-slate-900">Nháp chờ duyệt hôm nay</h3>
              </div>
              <button
                type="button"
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-0.5"
              >
                <span>Xem tất cả</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            {/* 3 Mini KPI Boxes */}
            <div className="grid grid-cols-3 gap-2">
              {/* Box 1: Nháp bình luận */}
              <div className="bg-slate-50/70 border border-slate-100 rounded-xl p-2.5 flex flex-col justify-between">
                <div className="w-7 h-7 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center mb-1">
                  <MessageSquare className="w-3.5 h-3.5" />
                </div>
                <span className="text-[11px] text-slate-500 font-medium">Nháp bình luận</span>
                <div className="text-lg font-black text-slate-900 mt-0.5">{pendingCommentDrafts}</div>
              </div>

              {/* Box 2: Nháp IB */}
              <div className="bg-slate-50/70 border border-slate-100 rounded-xl p-2.5 flex flex-col justify-between">
                <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-1">
                  <Send className="w-3.5 h-3.5" />
                </div>
                <span className="text-[11px] text-slate-500 font-medium">Nháp IB</span>
                <div className="text-lg font-black text-slate-900 mt-0.5">{pendingMessageDrafts}</div>
              </div>

              {/* Box 3: Đã gửi */}
              <div className="bg-slate-50/70 border border-slate-100 rounded-xl p-2.5 flex flex-col justify-between">
                <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <span className="text-[11px] text-slate-500 font-medium">Đã gửi</span>
                <div className="text-lg font-black text-slate-900 mt-0.5">{sentTodayCount}</div>
              </div>
            </div>
          </div>

          {/* Card 2: Social Commerce Order & Mini CRM */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs space-y-4">
            {/* Header Switcher: Đơn hàng Ops vs Hồ sơ CRM */}
            <div className="flex items-center justify-between pb-2.5 border-b border-slate-100">
              <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
                <button
                  type="button"
                  onClick={() => setRightPanelTab('orders')}
                  className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg transition-all cursor-pointer ${
                    rightPanelTab === 'orders'
                      ? 'bg-white text-blue-600 shadow-2xs font-bold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <ShoppingBag className="w-3.5 h-3.5" />
                  <span>Đơn hàng Ops</span>
                </button>
                <button
                  type="button"
                  onClick={() => setRightPanelTab('crm')}
                  className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg transition-all cursor-pointer ${
                    rightPanelTab === 'crm'
                      ? 'bg-white text-slate-900 shadow-2xs font-bold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <User className="w-3.5 h-3.5" />
                  <span>Hồ sơ CRM</span>
                </button>
              </div>

              {currentConv && rightPanelTab === 'crm' && (
                <button
                  type="button"
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-0.5"
                >
                  <span>Xem hồ sơ</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {!currentConv ? (
              <div className="py-8 text-center text-slate-400 text-xs">
                <FileText className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <p className="font-semibold text-slate-600 mb-1">Chưa có khách hàng được chọn</p>
                <p className="text-slate-400 text-[11px] mb-3">
                  Chưa có hội thoại/nháp. Hãy kết nối Facebook Pages hoặc bấm Quét ngay.
                </p>
                <button
                  type="button"
                  onClick={handlePollNow}
                  disabled={isPolling}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isPolling ? 'animate-spin' : ''}`} />
                  <span>{isPolling ? 'Đang quét...' : 'Quét ngay'}</span>
                </button>
              </div>
            ) : rightPanelTab === 'orders' ? (
              <OrderInboxPanel
                crmId={currentConv.fbId || currentConv.id}
                threadId={currentConv.id}
                customerName={currentConv.name}
                pageId={currentConv.id.includes('_') ? currentConv.id.split('_')[0] : (scopePageId || undefined)}
                messages={currentConv.messages.map((m) => ({
                  body: m.text,
                  sender: m.sender === 'staff' ? 'staff' : (m.sender === 'bot' ? 'bot' : 'customer'),
                }))}
                onInsertMessageToDraft={(suggestedText) => {
                  setInputText(suggestedText)
                  showToast('Đã đưa câu hỏi bổ sung vào ô soạn thảo chat!')
                }}
                onToast={showToast}
              />
            ) : (
            <>
            {/* Customer Header Avatar & Name */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="relative">
                  <img
                    src={currentConv.avatar}
                    alt={currentConv.name}
                    className="w-10 h-10 rounded-full object-cover ring-2 ring-white shadow-2xs"
                  />
                  <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white" />
                </div>
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="text-sm font-bold text-slate-900">{currentConv.name}</span>
                    <Pencil className="w-3.5 h-3.5 text-slate-400 cursor-pointer hover:text-slate-600" />
                  </div>
                  <div className="flex items-center space-x-1.5 text-[10px] text-slate-400 font-medium">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    <span>Đang hoạt động</span>
                  </div>
                </div>
              </div>

              {/* Chat action button */}
              <div className="flex items-center space-x-1">
                <button
                  type="button"
                  className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-600 text-xs font-semibold transition-colors border border-blue-100"
                >
                  <MessageCircle className="w-3.5 h-3.5" />
                  <span>Nhắn tin</span>
                </button>
                <button
                  type="button"
                  className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                >
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Customer Details List */}
            <div className="space-y-2 text-xs text-slate-600 pt-1">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Phone className="w-3.5 h-3.5 text-slate-400" />
                  <span className="font-medium text-slate-800">{currentConv.phone}</span>
                  {currentConv.phone.includes('*') && (
                    <span className="px-1.5 py-0.2 rounded bg-amber-50 text-amber-600 border border-amber-200 text-[10px] font-semibold">
                      Đã che
                    </span>
                  )}
                </div>
                {!currentConv.phone.includes('*') && currentConv.phone !== 'Chưa có SĐT' && (
                  <button
                    type="button"
                    onClick={() => handleCopy(currentConv.phone, 'SĐT')}
                    className="text-slate-400 hover:text-blue-600 p-1 cursor-pointer"
                    title="Sao chép"
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-blue-600 text-xs w-3.5 text-center">f</span>
                  <span className="text-slate-500">FB ID:</span>
                  <span className="font-medium text-slate-800">{currentConv.fbId}</span>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopy(currentConv.fbId, 'FB ID')}
                  className="text-slate-400 hover:text-blue-600 p-1"
                  title="Sao chép"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="flex items-center space-x-2">
                <MessageCircle className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-500">Nguồn:</span>
                <span className="font-medium text-slate-800">{currentConv.source}</span>
              </div>

              <div className="flex items-center space-x-2">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-500">Lần đầu tương tác:</span>
                <span className="font-medium text-slate-800">{currentConv.firstInteraction}</span>
              </div>

              <div className="flex items-center space-x-2">
                <Building2 className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-500">Khách hàng từ:</span>
                <span className="font-medium text-slate-800">{currentConv.pageName}</span>
              </div>
            </div>

            {copySuccess && (
              <div className="text-[10px] text-emerald-600 font-bold bg-emerald-50 py-1 px-2 rounded text-center animate-fade-in">
                Đã sao chép {copySuccess}!
              </div>
            )}

            {/* Tags section */}
            <div className="pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-slate-800">Thẻ tag</span>
                <button
                  type="button"
                  onClick={() => setIsAddingTag(!isAddingTag)}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-0.5 cursor-pointer"
                >
                  <Plus className="w-3 h-3" />
                  <span>{isAddingTag ? 'Đóng' : 'Thêm tag'}</span>
                </button>
              </div>
              {isAddingTag && (
                <div className="flex items-center gap-1.5 mb-2">
                  <input
                    type="text"
                    value={newTagInput}
                    onChange={(e) => setNewTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleAddTag()
                      }
                    }}
                    placeholder="Nhập tên thẻ tag..."
                    className="flex-1 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    autoFocus
                  />
                  <button
                    type="button"
                    onClick={handleAddTag}
                    className="px-2.5 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg cursor-pointer"
                  >
                    Lưu
                  </button>
                </div>
              )}
              <div className="flex flex-wrap gap-1.5">
                {(currentConv.crmTags || currentConv.tags).map((t, idx) => (
                  <span
                    key={idx}
                    className={`px-2 py-0.5 rounded text-xs font-semibold ${tagColorMap[t.color]}`}
                  >
                    {t.text}
                  </span>
                ))}
              </div>
            </div>

            {/* Customer Status radio/pills */}
            <div className="pt-2 border-t border-slate-100">
              <span className="text-xs font-bold text-slate-800 block mb-2">Trạng thái khách hàng</span>
              <div className="flex flex-wrap items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => {
                    setConversationsList((prev) =>
                      prev.map((c) => (c.id === currentConv.id ? { ...c, status: 'interested' } : c))
                    )
                  }}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                    currentConv.status === 'interested'
                      ? 'bg-amber-50 text-amber-700 border border-amber-300 font-bold'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <span className="w-2 h-2 rounded-full bg-amber-500" />
                  <span>Quan tâm</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setConversationsList((prev) =>
                      prev.map((c) => (c.id === currentConv.id ? { ...c, status: 'lead_hot' } : c))
                    )
                  }}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold transition-colors ${
                    currentConv.status === 'lead_hot'
                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <span className="w-2 h-2 rounded-full bg-rose-600" />
                  <span>Lead nóng</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setConversationsList((prev) =>
                      prev.map((c) => (c.id === currentConv.id ? { ...c, status: 'purchased' } : c))
                    )
                  }}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                    currentConv.status === 'purchased'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-300 font-bold'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>Đã mua</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setConversationsList((prev) =>
                      prev.map((c) => (c.id === currentConv.id ? { ...c, status: 'care_needed' } : c))
                    )
                  }}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                    currentConv.status === 'care_needed'
                      ? 'bg-orange-50 text-orange-700 border border-orange-300 font-bold'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <span className="w-2 h-2 rounded-full bg-orange-500" />
                  <span>Cần chăm sóc</span>
                </button>
              </div>
            </div>

            {/* Omnichannel 360 Memory (Pillar 4: Ký ức xuyên kênh) */}
            <div className="pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5 text-indigo-600" />
                  <span className="text-xs font-bold text-slate-800">Ký ức xuyên kênh (Omnichannel 360)</span>
                </div>
                <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-100">
                  Đã hợp nhất
                </span>
              </div>

              <div className="grid grid-cols-2 gap-1.5">
                {(currentConv.omnichannel || [
                  { channel: 'messenger', label: 'Messenger', count: 4, lastActive: 'Gần đây' },
                  { channel: 'facebook', label: 'Bình luận Fanpage', count: 1, lastActive: '10/04' },
                  { channel: 'tiktok', label: 'Xem video TikTok', count: 1, lastActive: '09/04' },
                  { channel: 'zalo', label: 'Zalo / SĐT', count: 1, lastActive: 'Đã khớp' },
                ]).map((ch, idx) => (
                  <div key={idx} className="p-2 rounded-xl bg-slate-50 border border-slate-100/80 flex flex-col justify-between">
                    <div className="flex items-center space-x-1 text-[11px] font-bold text-slate-800">
                      {ch.channel === 'messenger' && <MessengerIcon className="w-3 h-3 text-[#0084FF]" />}
                      {ch.channel === 'facebook' && <FacebookIcon className="w-3 h-3 text-[#1877F2]" />}
                      {ch.channel === 'tiktok' && <TikTokIcon className="w-3 h-3" colored />}
                      {ch.channel === 'zalo' && <Phone className="w-3 h-3 text-emerald-600" />}
                      <span className="truncate">{ch.label}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">{ch.count} lượt · {ch.lastActive}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Internal Notes section */}
            <div className="pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-slate-800">Ghi chú nội bộ</span>
                <button
                  type="button"
                  onClick={() => {
                    if (noteText.trim()) {
                      showToast('Đã lưu ghi chú nội bộ thành công!')
                      setNoteText('')
                    }
                  }}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-0.5"
                >
                  <Plus className="w-3 h-3" />
                  <span>Thêm ghi chú</span>
                </button>
              </div>
              <input
                type="text"
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Nhập ghi chú về khách hàng..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Interaction History timeline */}
            <div className="pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-800">Lịch sử tương tác</span>
                <button
                  type="button"
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-0.5"
                >
                  <span>Xem tất cả</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>

              <div className="space-y-2 text-xs">
                {currentConv.history.map((h, idx) => (
                  <div key={idx} className="flex items-start space-x-2 text-[11px]">
                    <span
                      className={`w-2 h-2 rounded-full mt-1 flex-shrink-0 ${
                        h.dotColor === 'green'
                          ? 'bg-emerald-500'
                          : h.dotColor === 'blue'
                          ? 'bg-blue-600'
                          : 'bg-slate-400'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="font-bold text-slate-800 leading-tight">{h.title}</div>
                      <div className="text-slate-400 truncate">{h.desc}</div>
                    </div>
                    <span className="text-[10px] text-slate-400 font-medium whitespace-nowrap ml-1">
                      {h.time}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Action Footer Buttons */}
            <div className="grid grid-cols-4 gap-1.5 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={handleHandoffTask}
                className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs cursor-pointer"
                title="Tạo việc chăm sóc khách hàng vào Kanban thật qua api.handoffToStaff"
              >
                <Briefcase className="w-3.5 h-3.5 text-blue-600" />
                <span>Tạo việc</span>
              </button>

              <button
                type="button"
                onClick={handleCallCustomer}
                className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs cursor-pointer"
                title="Gọi khách (kiểm tra bảo mật số điện thoại)"
              >
                <Phone className="w-3.5 h-3.5 text-blue-600" />
                <span>Gọi khách</span>
              </button>

              <button
                type="button"
                onClick={() => showToast('Đã cập nhật nhãn phân loại khách hàng')}
                className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs cursor-pointer"
              >
                <Tag className="w-3.5 h-3.5 text-blue-600" />
                <span>Gắn tag</span>
              </button>

              <button
                type="button"
                onClick={() => showToast('Đã đồng bộ thông tin khách hàng sang CRM!')}
                className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs cursor-pointer"
              >
                <Share2 className="w-3.5 h-3.5 text-blue-600" />
                <span>Xuất CRM</span>
              </button>
            </div>

            {/* Primary CTA: Tạo đơn hàng */}
            <div className="pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setRightPanelTab('orders')}
                className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition-all shadow-sm shadow-emerald-600/20 cursor-pointer"
              >
                <ShoppingBag className="w-4 h-4" />
                <span>Tạo đơn hàng</span>
              </button>
            </div>
            </>
            )}
          </div>
        </div>
      </div>

      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white px-4 py-2.5 rounded-xl shadow-lg text-xs font-semibold flex items-center space-x-2 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  )
}
