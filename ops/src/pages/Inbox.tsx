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
} from 'lucide-react'
import { api, CareConversation, CareDraft, CareEvent, CareState, CareStats } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useCareScope } from '../lib/scope'
import { FacebookIcon, MessengerIcon } from '../components/BrandIcons'

interface MockConversation {
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

const mockConversationsData: MockConversation[] = [
  {
    id: 'conv_1',
    name: 'Nguyễn Thị Hoa',
    avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=120&auto=format&fit=crop&q=80',
    avatarBg: 'bg-rose-100 text-rose-700',
    message: 'Shop ơi, sản phẩm này còn hàng không ạ?',
    time: '14:28',
    unreadCount: 3,
    hasUnreadDot: true,
    tags: [
      { text: 'Lead nóng', color: 'red' },
      { text: 'Cần hỗ trợ', color: 'amber' },
    ],
    crmTags: [
      { text: 'Lead nóng', color: 'red' },
      { text: 'Quan tâm', color: 'amber' },
      { text: 'Khách mới', color: 'blue' },
    ],
    phone: '0967 123 456',
    fbId: '1000123456789',
    source: 'Messenger',
    firstInteraction: '10/04/2024',
    pageName: 'Page JAVIS Official',
    status: 'lead_hot',
    history: [
      {
        title: 'Lần đầu tương tác',
        desc: 'Khách hàng nhắn tin qua Messenger',
        time: '10/04/2024 14:28',
        dotColor: 'green',
      },
      {
        title: 'Phản hồi gần nhất',
        desc: 'Bạn đã gửi tin nhắn',
        time: '23/04/2024 14:31',
        dotColor: 'blue',
      },
      {
        title: 'Tạo lead',
        desc: 'Tự động từ hội thoại',
        time: '10/04/2024 14:30',
        dotColor: 'gray',
      },
    ],
    messages: [
      {
        id: 'm1',
        sender: 'customer',
        text: 'Shop ơi, sản phẩm này còn hàng không ạ?',
        time: '14:28',
      },
      {
        id: 'm2',
        sender: 'bot',
        text: 'Dạ chào chị Hoa 👋\nSản phẩm hiện vẫn còn hàng ạ. Chị đang quan tâm đến màu và size nào để em tư vấn chi tiết hơn cho mình nhé?',
        time: '14:29',
      },
      {
        id: 'm3',
        sender: 'customer',
        text: 'Mình muốn màu be, size M. Không biết khi nào nhận được hàng ở Hà Nội ạ?',
        time: '14:30',
      },
      {
        id: 'm4',
        sender: 'bot',
        text: 'Dạ với địa chỉ Hà Nội, thời gian giao hàng dự kiến từ 1–2 ngày ạ. Chị có thể đặt hàng ngay hôm nay để được freeship nhé! 🎁',
        time: '14:31',
      },
    ],
  },
  {
    id: 'conv_2',
    name: 'Trần Văn Minh',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=120&auto=format&fit=crop&q=80',
    avatarBg: 'bg-blue-100 text-blue-700',
    message: 'Cảm ơn shop nhé!',
    time: '13:45',
    unreadCount: 1,
    hasUnreadDot: true,
    tags: [
      { text: 'Đã mua', color: 'green' },
      { text: 'VIP', color: 'purple' },
    ],
    phone: '0912 345 678',
    fbId: '1000987654321',
    source: 'Messenger',
    firstInteraction: '08/04/2024',
    pageName: 'Page JAVIS Official',
    status: 'purchased',
    history: [
      {
        title: 'Lần đầu tương tác',
        desc: 'Khách hàng nhắn tin qua Messenger',
        time: '08/04/2024 10:15',
        dotColor: 'green',
      },
      {
        title: 'Hoàn tất đơn hàng',
        desc: 'Đã giao thành công',
        time: '13/04/2024 11:30',
        dotColor: 'blue',
      },
    ],
    messages: [
      {
        id: 'm1',
        sender: 'customer',
        text: 'Đã nhận được hàng đúng mẫu rồi nhé shop!',
        time: '13:40',
      },
      {
        id: 'm2',
        sender: 'customer',
        text: 'Cảm ơn shop nhé!',
        time: '13:45',
      },
      {
        id: 'm3',
        sender: 'bot',
        text: 'Dạ Javis cảm ơn anh Minh nhiều ạ! Chúc anh có trải nghiệm tuyệt vời với sản phẩm ❤️',
        time: '13:46',
      },
    ],
  },
  {
    id: 'conv_3',
    name: 'Lê Quang Huy',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=120&auto=format&fit=crop&q=80',
    avatarBg: 'bg-teal-100 text-teal-700',
    message: 'Khi nào có hàng lại vậy shop?',
    time: '11:20',
    unreadCount: 1,
    hasUnreadDot: true,
    tags: [{ text: 'FAQ', color: 'blue' }],
    phone: '0988 776 655',
    fbId: '1000554433221',
    source: 'Messenger',
    firstInteraction: '12/04/2024',
    pageName: 'Page JAVIS Official',
    status: 'interested',
    history: [
      {
        title: 'Lần đầu tương tác',
        desc: 'Khách hàng hỏi hàng',
        time: '12/04/2024 11:20',
        dotColor: 'green',
      },
    ],
    messages: [
      {
        id: 'm1',
        sender: 'customer',
        text: 'Khi nào có hàng lại vậy shop?',
        time: '11:20',
      },
      {
        id: 'm2',
        sender: 'bot',
        text: 'Dạ đợt hàng mới dự kiến về trong 2 ngày tới ạ. Anh có muốn em lưu số điện thoại để báo ngay khi hàng về không ạ?',
        time: '11:21',
      },
    ],
  },
  {
    id: 'conv_4',
    name: 'Phạm Thị Lan',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=120&auto=format&fit=crop&q=80',
    avatarBg: 'bg-amber-100 text-amber-700',
    message: 'Dạ mình muốn đặt 2 sản phẩm ạ',
    time: '10:37',
    tags: [
      { text: 'Quan tâm', color: 'amber' },
      { text: 'Lead', color: 'red' },
    ],
    phone: '0977 112 233',
    fbId: '1000667788990',
    source: 'Messenger',
    firstInteraction: '15/04/2024',
    pageName: 'Page JAVIS Official',
    status: 'lead_hot',
    history: [
      {
        title: 'Lần đầu tương tác',
        desc: 'Khách hàng nhắn tin đặt hàng',
        time: '15/04/2024 10:37',
        dotColor: 'green',
      },
    ],
    messages: [
      {
        id: 'm1',
        sender: 'customer',
        text: 'Dạ mình muốn đặt 2 sản phẩm ạ',
        time: '10:37',
      },
    ],
  },
  {
    id: 'conv_5',
    name: 'Hoàng Kim',
    avatar: 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=120&auto=format&fit=crop&q=80',
    avatarBg: 'bg-indigo-100 text-indigo-700',
    message: 'Shop có hỗ trợ đổi size không?',
    time: '09:12',
    tags: [{ text: 'Cần hỗ trợ', color: 'amber' }],
    phone: '0933 445 566',
    fbId: '1000332211445',
    source: 'Messenger',
    firstInteraction: '18/04/2024',
    pageName: 'Page JAVIS Official',
    status: 'care_needed',
    history: [
      {
        title: 'Lần đầu tương tác',
        desc: 'Khách hàng hỏi đổi size',
        time: '18/04/2024 09:12',
        dotColor: 'green',
      },
    ],
    messages: [
      {
        id: 'm1',
        sender: 'customer',
        text: 'Shop có hỗ trợ đổi size không?',
        time: '09:12',
      },
    ],
  },
  {
    id: 'conv_6',
    name: 'Đỗ Thu Hà',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=120&auto=format&fit=crop&q=80',
    avatarBg: 'bg-emerald-100 text-emerald-700',
    message: 'Mình đã nhận được hàng rồi ạ',
    time: 'Hôm qua',
    tags: [{ text: 'Đã mua', color: 'green' }],
    phone: '0909 888 777',
    fbId: '1000888999111',
    source: 'Messenger',
    firstInteraction: '19/04/2024',
    pageName: 'Page JAVIS Official',
    status: 'purchased',
    history: [
      {
        title: 'Giao hàng',
        desc: 'Đã nhận hàng thành công',
        time: '21/04/2024 16:00',
        dotColor: 'green',
      },
    ],
    messages: [
      {
        id: 'm1',
        sender: 'customer',
        text: 'Mình đã nhận được hàng rồi ạ',
        time: 'Hôm qua',
      },
    ],
  },
  {
    id: 'conv_7',
    name: 'Nguyễn Anh Tuấn',
    avatar: 'https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=120&auto=format&fit=crop&q=80',
    avatarBg: 'bg-purple-100 text-purple-700',
    message: 'Tư vấn giúp mình với ạ',
    time: 'Hôm qua',
    tags: [{ text: 'Lead', color: 'red' }],
    phone: '0944 556 677',
    fbId: '1000777666555',
    source: 'Messenger',
    firstInteraction: '20/04/2024',
    pageName: 'Page JAVIS Official',
    status: 'interested',
    history: [
      {
        title: 'Tạo lead',
        desc: 'Từ bình luận bài viết',
        time: '20/04/2024 15:30',
        dotColor: 'gray',
      },
    ],
    messages: [
      {
        id: 'm1',
        sender: 'customer',
        text: 'Tư vấn giúp mình với ạ',
        time: 'Hôm qua',
      },
    ],
  },
  {
    id: 'conv_8',
    name: 'Trần Mai Phương',
    avatar: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=120&auto=format&fit=crop&q=80',
    avatarBg: 'bg-rose-100 text-rose-700',
    message: 'Shop ơi cho mình hỏi thêm ạ',
    time: '21/04',
    tags: [{ text: 'FAQ', color: 'blue' }],
    phone: '0922 334 455',
    fbId: '1000444333222',
    source: 'Messenger',
    firstInteraction: '21/04/2024',
    pageName: 'Page JAVIS Official',
    status: 'interested',
    history: [
      {
        title: 'Hỏi thông tin',
        desc: 'Thời gian bảo hành sản phẩm',
        time: '21/04/2024 10:20',
        dotColor: 'blue',
      },
    ],
    messages: [
      {
        id: 'm1',
        sender: 'customer',
        text: 'Shop ơi cho mình hỏi thêm ạ',
        time: '21/04',
      },
    ],
  },
]

export const Inbox: React.FC = () => {
  const { can } = useAuth()
  const { scope, scopeBrand, scopePageId } = useCareScope()
  const [activeChannel, setActiveChannel] = useState<'comments' | 'messenger'>('messenger')
  const [statusFilter, setStatusFilter] = useState<'unread' | 'need_human' | 'done'>('unread')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedConvId, setSelectedConvId] = useState<string>('conv_1')
  const [inputText, setInputText] = useState('')
  const [isTakeover, setIsTakeover] = useState(false)
  const [copySuccess, setCopySuccess] = useState<string | null>(null)
  const [conversationsList, setConversationsList] = useState<MockConversation[]>(mockConversationsData)
  const [noteText, setNoteText] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Real Care state & drafts
  const [careDrafts, setCareDrafts] = useState<CareDraft[]>([])
  const [careStats, setCareStats] = useState<CareStats | null>(null)

  useEffect(() => {
    let mounted = true
    api.getInbox({ limit: 40 })
      .then((res) => {
        if (mounted && res) {
          if (res.drafts) setCareDrafts(res.drafts)
          if (res.stats) setCareStats(res.stats)
        }
      })
      .catch(() => {})
    return () => {
      mounted = false
    }
  }, [scope, scopeBrand, scopePageId])

  const currentConv = conversationsList.find((c) => c.id === selectedConvId) || conversationsList[0]

  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    setCopySuccess(label)
    setTimeout(() => setCopySuccess(null), 2000)
  }

  const handleApplyDraft = (text: string) => {
    setInputText(text)
  }

  const handleSendMessage = () => {
    if (!inputText.trim()) return
    const newMsg = {
      id: `m_${Date.now()}`,
      sender: 'staff' as const,
      text: inputText.trim(),
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
  }

  // Scroll messages to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentConv?.messages])

  const pendingCommentDrafts = careStats?.pending_comment_drafts || 5
  const pendingMessageDrafts = careStats?.pending_message_drafts || 12
  const sentTodayCount = careStats?.replies_24h || 24

  const tagColorMap = {
    red: 'bg-rose-50 text-rose-600 border border-rose-200',
    amber: 'bg-amber-50 text-amber-600 border border-amber-200',
    green: 'bg-emerald-50 text-emerald-600 border border-emerald-200',
    blue: 'bg-blue-50 text-blue-600 border border-blue-200',
    purple: 'bg-purple-50 text-purple-600 border border-purple-200',
  }

  const filteredConversations = conversationsList.filter((conv) => {
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
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">Hộp thư & Nháp</h1>
        <p className="text-sm text-slate-500 font-normal mt-0.5">
          Quản lý hội thoại, xử lý tin nhắn và soạn nháp với sự hỗ trợ của Javis AI.
        </p>
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

          {/* Sub-channel tabs (Bình luận Fanpage vs Messenger) */}
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
              <span>Bình luận Fanpage</span>
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
              <span className="bg-blue-600 text-white rounded-full px-1.5 py-0.2 text-[10px] font-bold ml-0.5">
                12
              </span>
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
              <span className="bg-slate-200 text-slate-700 rounded-full px-1.5 py-0.2 text-[10px] font-bold ml-0.5">
                8
              </span>
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
            {filteredConversations.map((conv) => {
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
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 truncate">{conv.name}</span>
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
            })}
          </div>
        </div>

        {/* ================= COLUMN 2: HỘI THOẠI & NHÁP TRẢ LỜI (6 cols) ================= */}
        <div className="xl:col-span-6 bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs flex flex-col justify-between h-[820px]">
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
                onClick={() => setIsTakeover(!isTakeover)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all shadow-2xs ${
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
                      className={`inline-block px-4 py-2.5 text-xs text-slate-800 leading-relaxed rounded-2xl text-left whitespace-pre-line ${
                        isUser
                          ? 'bg-slate-100 rounded-tl-sm'
                          : 'bg-blue-100/70 border border-blue-200/50 rounded-tr-sm'
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
                      {!isUser && <CheckCheck className="w-3.5 h-3.5 text-blue-600 inline" />}
                    </div>
                  </div>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>

          {/* Javis AI Draft Suggestions Card */}
          <div className="bg-slate-50/90 border border-indigo-100/90 rounded-2xl p-3.5 my-2">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-1.5">
                <Sparkles className="w-4 h-4 text-purple-600" />
                <span className="text-xs font-bold text-slate-900">Javis đề xuất nháp</span>
                <span className="text-[11px] text-slate-400 font-normal">
                  · Dựa trên nội dung hội thoại và thông tin sản phẩm
                </span>
              </div>
              <div className="flex items-center space-x-1 text-[11px] text-slate-500 font-medium">
                <span>Độ chính xác cao từ AI</span>
                <Info className="w-3.5 h-3.5 text-slate-400" />
              </div>
            </div>

            {/* 3 Side-by-side Draft Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
              {/* Draft 1 */}
              <div className="bg-white p-3 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-bold text-emerald-600 flex items-center space-x-1 mb-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    <span>96% phù hợp</span>
                  </span>
                  <h4 className="text-xs font-bold text-slate-900 line-clamp-1 leading-tight">
                    Xác nhận đơn hàng + thông tin giao hàng
                  </h4>
                  <p className="text-[11px] text-slate-500 line-clamp-2 mt-1 leading-tight">
                    Dạ em đã ghi nhận thông tin của chị... Em sẽ tạo đơn ngay và gửi chị...
                  </p>
                </div>
                <div className="flex items-center space-x-1.5 mt-3 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() =>
                      handleApplyDraft(
                        'Dạ em đã ghi nhận thông tin của chị Hoa (Màu be, size M). Em sẽ tạo đơn ngay và gửi chị xác nhận nhé!'
                      )
                    }
                    className="flex-1 py-1.5 px-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg shadow-2xs transition-colors text-center"
                  >
                    Dùng nháp
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      handleApplyDraft(
                        'Dạ em đã ghi nhận thông tin của chị Hoa (Màu be, size M). Chị cho em xin số điện thoại và địa chỉ nhận hàng cụ thể ở Hà Nội để em tạo đơn nhé ạ!'
                      )
                    }
                    className="py-1.5 px-2.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-lg border border-slate-200 transition-colors"
                  >
                    Chỉnh sửa
                  </button>
                </div>
              </div>

              {/* Draft 2 */}
              <div className="bg-white p-3 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-bold text-teal-600 flex items-center space-x-1 mb-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                    <span>89% phù hợp</span>
                  </span>
                  <h4 className="text-xs font-bold text-slate-900 line-clamp-1 leading-tight">
                    Tư vấn thêm sản phẩm liên quan
                  </h4>
                  <p className="text-[11px] text-slate-500 line-clamp-2 mt-1 leading-tight">
                    Ngoài sản phẩm này, bên em còn có... Chị có thể tham khảo thêm ạ...
                  </p>
                </div>
                <div className="flex items-center space-x-1.5 mt-3 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() =>
                      handleApplyDraft(
                        'Ngoài sản phẩm này, bên em còn có mẫu áo khoác cùng bộ phối rất hợp với màu be ạ. Chị có muốn em gửi hình tham khảo thêm không ạ?'
                      )
                    }
                    className="flex-1 py-1.5 px-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg shadow-2xs transition-colors text-center"
                  >
                    Dùng nháp
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      handleApplyDraft(
                        'Bên em đang có chương trình mua kèm phụ kiện giảm thêm 15% đó ạ!'
                      )
                    }
                    className="py-1.5 px-2.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-lg border border-slate-200 transition-colors"
                  >
                    Chỉnh sửa
                  </button>
                </div>
              </div>

              {/* Draft 3 */}
              <div className="bg-white p-3 rounded-xl border border-slate-200/80 shadow-2xs flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-bold text-blue-600 flex items-center space-x-1 mb-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                    <span>78% phù hợp</span>
                  </span>
                  <h4 className="text-xs font-bold text-slate-900 line-clamp-1 leading-tight">
                    Chăm sóc sau bán hàng
                  </h4>
                  <p className="text-[11px] text-slate-500 line-clamp-2 mt-1 leading-tight">
                    Cảm ơn chị đã quan tâm đến sản phẩm... Nếu cần hỗ trợ thêm chị cứ nhắn...
                  </p>
                </div>
                <div className="flex items-center space-x-1.5 mt-3 pt-2 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() =>
                      handleApplyDraft(
                        'Cảm ơn chị đã quan tâm đến sản phẩm bên em! Nếu cần hỗ trợ thêm thông tin gì về size số chị cứ nhắn em nhé ❤️'
                      )
                    }
                    className="flex-1 py-1.5 px-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-lg shadow-2xs transition-colors text-center"
                  >
                    Dùng nháp
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      handleApplyDraft(
                        'Dạ chúc chị một ngày tốt lành ạ!'
                      )
                    }
                    className="py-1.5 px-2.5 bg-white hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-lg border border-slate-200 transition-colors"
                  >
                    Chỉnh sửa
                  </button>
                </div>
              </div>
            </div>
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
                  onClick={() => alert('Đã lưu nháp tin nhắn thành công')}
                  className="px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition-colors"
                >
                  Lưu nháp
                </button>
                <button
                  type="button"
                  onClick={handleSendMessage}
                  className="flex items-center space-x-1.5 px-4 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-sm shadow-blue-500/20"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Gửi</span>
                </button>
              </div>
            </div>
          </div>
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

          {/* Card 2: Mini CRM */}
          <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900">Mini CRM</h3>
              <button
                type="button"
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-0.5"
              >
                <span>Xem hồ sơ đầy đủ</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

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
                </div>
                <button
                  type="button"
                  onClick={() => handleCopy(currentConv.phone, 'SĐT')}
                  className="text-slate-400 hover:text-blue-600 p-1"
                  title="Sao chép"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
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
                  onClick={() => {
                    const newTag = prompt('Nhập tên tag mới:')
                    if (newTag?.trim()) {
                      setConversationsList((prev) =>
                        prev.map((c) => {
                          if (c.id === currentConv.id) {
                            return {
                              ...c,
                              tags: [...c.tags, { text: newTag.trim(), color: 'blue' }],
                            }
                          }
                          return c
                        })
                      )
                    }
                  }}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center space-x-0.5"
                >
                  <Plus className="w-3 h-3" />
                  <span>Thêm tag</span>
                </button>
              </div>
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

            {/* Internal Notes section */}
            <div className="pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-bold text-slate-800">Ghi chú nội bộ</span>
                <button
                  type="button"
                  onClick={() => {
                    if (noteText.trim()) {
                      alert('Đã lưu ghi chú nội bộ!')
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
                onClick={() => alert('Đã tạo việc trên Kanban!')}
                className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs"
              >
                <Briefcase className="w-3.5 h-3.5 text-blue-600" />
                <span>Tạo việc</span>
              </button>

              <button
                type="button"
                onClick={() => window.open(`tel:${currentConv.phone}`)}
                className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs"
              >
                <Phone className="w-3.5 h-3.5 text-blue-600" />
                <span>Gọi khách</span>
              </button>

              <button
                type="button"
                onClick={() => alert('Chọn tag để gắn')}
                className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs"
              >
                <Tag className="w-3.5 h-3.5 text-blue-600" />
                <span>Gắn tag</span>
              </button>

              <button
                type="button"
                onClick={() => alert('Đã đồng bộ sang CRM!')}
                className="flex items-center justify-center space-x-1 py-2 px-1 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-[11px] font-semibold transition-colors shadow-2xs"
              >
                <Share2 className="w-3.5 h-3.5 text-blue-600" />
                <span>Xuất CRM</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
