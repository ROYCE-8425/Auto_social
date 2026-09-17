import React, { useState, useEffect, useRef } from 'react'
import {
  MessageSquare,
  X,
  Send,
  Bot,
  RotateCcw,
  Sparkles,
  ShieldAlert,
  FileText,
  Activity,
  CheckCircle2,
} from 'lucide-react'
import { api, OpsQAResponse } from '../lib/api'
import { useCareScope } from '../lib/scope'

interface ChatMessage {
  id: string
  sender: 'user' | 'assistant'
  text: string
  citations?: string[]
  usedStats?: boolean
  timestamp: number
}

const STORAGE_KEY = 'javis_ops_qa_history_v1'

export const OpsChatBubble: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        return JSON.parse(saved)
      }
    } catch {
      // ignore
    }
    return [
      {
        id: 'welcome',
        sender: 'assistant',
        text: 'Chào bạn! Tôi là trợ lý ca trực Javis Ops. Tôi hỗ trợ tra cứu nhanh số lượng nháp chờ duyệt, thông tin Brand Kit trong scope, hotline cơ sở và hướng dẫn vận hành takeover.',
        citations: ['docs/28-cham-soc-fanpage.md'],
        usedStats: true,
        timestamp: Date.now(),
      },
    ]
  })

  const { scope, scopeBrand, scopePageId, eligiblePages } = useCareScope()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Lưu lịch sử vào localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.slice(-30)))
    } catch {
      // ignore
    }
  }, [messages])

  // Cuộn xuống tin nhắn mới nhất
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  const scopeLabel = React.useMemo(() => {
    if (scope === 'brand') {
      return scopeBrand === 'bsn' ? 'Nhóm Game BSN' : 'Nhóm Đào tạo'
    }
    if (scope === 'page' && scopePageId) {
      const p = eligiblePages.find((item) => (item.page_id || item.id) === scopePageId)
      return p ? p.name : 'Fanpage đã chọn'
    }
    return 'Tất cả trang'
  }, [scope, scopeBrand, scopePageId, eligiblePages])

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend || input).trim()
    if (!text || loading) return

    const userMsg: ChatMessage = {
      id: 'u_' + Date.now(),
      sender: 'user',
      text,
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    const currentScope =
      scope === 'page'
        ? scopePageId
        : scope === 'brand'
        ? scopeBrand
        : 'all'

    try {
      const res: OpsQAResponse = await api.askOpsQA({
        message: text,
        scope: currentScope,
      })

      const botMsg: ChatMessage = {
        id: 'b_' + Date.now(),
        sender: 'assistant',
        text: res.reply || res.error || 'Đã có lỗi xảy ra khi xử lý câu hỏi.',
        citations: res.citations,
        usedStats: res.used_stats,
        timestamp: Date.now(),
      }
      setMessages((prev) => [...prev, botMsg])
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: 'b_err_' + Date.now(),
        sender: 'assistant',
        text: err?.message || 'Không thể kết nối với máy chủ Javis Ops.',
        timestamp: Date.now(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleClearHistory = () => {
    const fresh: ChatMessage[] = [
      {
        id: 'welcome_fresh',
        sender: 'assistant',
        text: `Đã làm mới cuộc trò chuyện. Phạm vi hiện tại: ${scopeLabel}. Bạn cần kiểm tra nháp ca trực hay thông tin nào?`,
        citations: ['docs/28-cham-soc-fanpage.md'],
        usedStats: true,
        timestamp: Date.now(),
      },
    ]
    setMessages(fresh)
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      // ignore
    }
  }

  const quickPrompts = [
    'Hôm nay bao nhiêu nháp comment / IB?',
    'Takeover là gì, bấm nút nào?',
    'Hotline & địa chỉ trong kit này',
    'Khách check ib là ai?',
  ]

  return (
    <>
      {/* Floating Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="fixed bottom-20 md:bottom-6 right-6 z-40 flex items-center space-x-2 px-4 py-2.5 rounded-full bg-gradient-to-r from-saoviet-600 to-saoviet-500 hover:from-saoviet-500 hover:to-saoviet-400 text-white font-bold text-sm shadow-xl shadow-saoviet-500/30 transition-all hover:scale-105 active:scale-95 group cursor-pointer"
        title="Hỏi đáp ca làm việc Javis Ops"
      >
        <div className="relative">
          <Bot className="w-5 h-5 transition-transform group-hover:rotate-12" />
          <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 border-2 border-white rounded-full animate-pulse" />
        </div>
        <span className="tracking-tight">Hỏi Javis</span>
      </button>

      {/* Floating Chat Modal Panel */}
      {isOpen && (
        <div className="fixed bottom-20 md:bottom-20 right-4 sm:right-6 z-50 w-[94vw] sm:w-[390px] h-[540px] max-h-[82vh] bg-white rounded-2xl shadow-2xl border border-slate-200/90 flex flex-col overflow-hidden animate-in slide-in-from-bottom-5 duration-200">
          {/* Header */}
          <div className="bg-slate-900 text-white px-4 py-3 flex items-center justify-between flex-shrink-0 shadow-sm">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-saoviet-500 to-saoviet-400 flex items-center justify-center text-white shadow-md shadow-saoviet-500/20">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center space-x-1.5">
                  <span className="font-bold text-sm leading-none">Hỏi Javis</span>
                  <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-saoviet-500/20 text-saoviet-300 border border-saoviet-400/30">
                    Trợ lý ca
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5 flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                  <span className="truncate max-w-[170px]">{scopeLabel}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-1 text-slate-400">
              <button
                type="button"
                onClick={handleClearHistory}
                title="Làm mới lịch sử chat"
                className="p-1.5 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Đóng"
                className="p-1.5 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* 1-Line Safety Disclaimer Banner */}
          <div className="bg-amber-50 border-b border-amber-200/80 px-3 py-1.5 text-[11px] text-amber-800 flex items-center space-x-1.5 flex-shrink-0">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
            <span className="leading-tight font-medium">
              Chỉ hỏi đáp ca làm. Gửi Facebook: nút trên Hộp thư.
            </span>
          </div>

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-3.5 space-y-3 bg-slate-50/60 text-xs">
            {messages.map((m) => {
              const isUser = m.sender === 'user'
              return (
                <div
                  key={m.id}
                  className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`max-w-[85%] px-3.5 py-2.5 rounded-2xl text-xs leading-relaxed whitespace-pre-line shadow-xs ${
                      isUser
                        ? 'bg-saoviet-600 text-white rounded-br-xs font-medium'
                        : 'bg-white text-slate-800 border border-slate-200/80 rounded-bl-xs'
                    }`}
                  >
                    {m.text}
                  </div>

                  {/* Badges / Citations for Assistant */}
                  {!isUser && (
                    <div className="flex flex-wrap items-center gap-1.5 mt-1.5 px-1">
                      {m.usedStats && (
                        <span className="inline-flex items-center space-x-1 text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded font-medium">
                          <Activity className="w-2.5 h-2.5" />
                          <span>Số liệu 24h</span>
                        </span>
                      )}
                      {m.citations &&
                        m.citations.map((cite, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center space-x-1 text-[10px] text-slate-600 bg-slate-100 border border-slate-200 px-1.5 py-0.5 rounded"
                          >
                            <FileText className="w-2.5 h-2.5 text-slate-400" />
                            <span className="truncate max-w-[130px]">{cite}</span>
                          </span>
                        ))}
                    </div>
                  )}
                </div>
              )
            })}

            {loading && (
              <div className="flex items-center space-x-2 text-slate-500 bg-white border border-slate-200 rounded-2xl rounded-bl-xs px-3.5 py-2.5 max-w-[70%]">
                <div className="flex space-x-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-saoviet-500 animate-bounce" />
                  <div
                    className="w-1.5 h-1.5 rounded-full bg-saoviet-500 animate-bounce"
                    style={{ animationDelay: '0.15s' }}
                  />
                  <div
                    className="w-1.5 h-1.5 rounded-full bg-saoviet-500 animate-bounce"
                    style={{ animationDelay: '0.3s' }}
                  />
                </div>
                <span className="text-[11px] font-medium text-slate-400">
                  Javis đang tra cứu...
                </span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick prompt suggestions */}
          <div className="px-3 py-2 bg-white border-t border-slate-100 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
            {quickPrompts.map((qp, i) => (
              <button
                key={i}
                type="button"
                disabled={loading}
                onClick={() => handleSend(qp)}
                className="text-[11px] whitespace-nowrap px-2.5 py-1 rounded-full bg-slate-100 hover:bg-saoviet-50 hover:text-saoviet-700 text-slate-700 font-medium transition-colors border border-slate-200/60 cursor-pointer flex-shrink-0 disabled:opacity-50"
              >
                {qp}
              </button>
            ))}
          </div>

          {/* Input Area */}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="p-2.5 bg-white border-t border-slate-200 flex items-center space-x-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Nháp BSN hôm nay? Khách check ib là ai?..."
              disabled={loading}
              className="flex-1 bg-slate-100 text-slate-900 placeholder:text-slate-400 text-xs px-3.5 py-2 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500 border border-transparent disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="p-2 rounded-xl bg-saoviet-600 hover:bg-saoviet-500 text-white disabled:opacity-40 transition-colors shadow-sm cursor-pointer"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}
    </>
  )
}
