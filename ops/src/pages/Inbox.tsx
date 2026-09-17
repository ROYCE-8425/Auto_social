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
  Bot,
  AlertCircle,
  MessageCircle,
  X,
  ExternalLink,
  Sparkles,
} from 'lucide-react'
import { api, CareConversation, CareDraft, CareEvent, CareState, CareStats } from '../lib/api'
import { useAuth } from '../lib/auth'
import { useCareScope } from '../lib/scope'
import { formatTime, timeAgo } from '../lib/utils'

export const Inbox: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<'comments' | 'messenger'>(() => {
    if (typeof window !== 'undefined' && window.location.hash.includes('tab=messenger')) {
      return 'messenger'
    }
    return 'comments'
  })
  const { can } = useAuth()
  const { scope, scopeBrand, scopePageId, eligiblePages: globalPages } = useCareScope()
  const [platformFilter, setPlatformFilter] = useState<'all' | 'facebook' | 'tiktok'>('all')
  const [pageFilter, setPageFilter] = useState<string>('')
  const [eligiblePages, setEligiblePages] = useState<NonNullable<CareState['eligible_pages']>>([])
  const [isPolling, setIsPolling] = useState(false)
  const [pollHint, setPollHint] = useState<string | null>(null)
  const [events, setEvents] = useState<CareEvent[]>([])
  const [drafts, setDrafts] = useState<CareDraft[]>([])
  const [stats, setStats] = useState<CareStats | null>(null)
  const [conversations, setConversations] = useState<CareConversation[]>([])
  const [filterView, setFilterView] = useState<'pending' | 'events'>('pending')
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(true)
  const [actionLoading, setActionLoading] = useState<string | number | null>(null)
  const [actionMsg, setActionMsg] = useState<{ id: string | number; msg: string; type: 'success' | 'error' } | null>(null)

  // Sync activeSubTab when URL hash changes (e.g. from Overview links)
  useEffect(() => {
    const handleHash = () => {
      if (window.location.hash.includes('tab=messenger')) {
        setActiveSubTab('messenger')
      } else if (window.location.hash.includes('tab=comments')) {
        setActiveSubTab('comments')
      }
    }
    window.addEventListener('hashchange', handleHash)
    return () => window.removeEventListener('hashchange', handleHash)
  }, [])

  // Sync pageFilter when Scope changes from the global ScopeBar
  useEffect(() => {
    if (scope === 'page' && scopePageId) {
      setPageFilter(scopePageId)
    } else if (scope === 'all' || scope === 'brand') {
      setPageFilter('')
    }
  }, [scope, scopePageId])

  // Chat conversation modal state
  const [selectedConv, setSelectedConv] = useState<CareConversation | null>(null)
  const [threadEvents, setThreadEvents] = useState<CareEvent[]>([])
  const [threadLoading, setThreadLoading] = useState<boolean>(false)
  const [directMsgText, setDirectMsgText] = useState<string>('')
  const [sendingDirectMsg, setSendingDirectMsg] = useState<boolean>(false)

  // Handoff note modal state
  const [handoffModalOpen, setHandoffModalOpen] = useState<boolean>(false)
  const [handoffTitle, setHandoffTitle] = useState<string>('')
  const [handoffIntent, setHandoffIntent] = useState<string>('')
  const [handoffCommentId, setHandoffCommentId] = useState<string>('')

  const getPageInfo = (pid?: string) => {
    const pages = eligiblePages.length ? eligiblePages : globalPages
    return pages.find((p) => (p.page_id || p.id) === pid)
  }

  const renderPlatformChip = (platform?: string) => {
    const p = (platform || 'facebook').toLowerCase()
    if (p === 'tiktok') {
      return (
        <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-slate-900 text-white tracking-wide">
          TikTok
        </span>
      )
    }
    if (p === 'messenger') {
      return (
        <span className="text-[10px] px-2 py-0.5 rounded font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
          Messenger
        </span>
      )
    }
    return (
      <span className="text-[10px] px-2 py-0.5 rounded font-medium bg-blue-50 text-blue-700 border border-blue-200">
        Facebook
      </span>
    )
  }

  const loadData = async (filter = platformFilter, pageId = pageFilter, subTab = activeSubTab) => {
    try {
      const effectivePageId = pageId || (scope === 'page' ? scopePageId : undefined)
      const effectiveBrand = (!effectivePageId && scope === 'brand') ? scopeBrand : undefined

      if (subTab === 'comments') {
        const [inboxRes, stateRes] = await Promise.all([
          api.getInbox({
            limit: 80,
            kind: 'comment',
            platform: filter === 'all' ? undefined : filter,
            page_id: effectivePageId || undefined,
            brand: effectiveBrand || undefined,
          }).catch(() => null),
          api.getCareState().catch(() => null),
        ])
        if (inboxRes) {
          setEvents(inboxRes.events || [])
          setDrafts(inboxRes.drafts || [])
          if (inboxRes.stats) setStats(inboxRes.stats)
        }
        if (stateRes?.eligible_pages) {
          setEligiblePages(stateRes.eligible_pages)
        }
      } else {
        const [inboxRes, convRes, stateRes] = await Promise.all([
          api.getInbox({
            limit: 80,
            kind: 'message',
            platform: filter === 'all' ? undefined : filter,
            page_id: effectivePageId || undefined,
            brand: effectiveBrand || undefined,
          }).catch(() => null),
          api.getConversations({
            page_id: effectivePageId || undefined,
            brand: effectiveBrand || undefined,
          }).catch(() => null),
          api.getCareState().catch(() => null),
        ])
        if (inboxRes) {
          setEvents(inboxRes.events || [])
          setDrafts(inboxRes.drafts || [])
          if (inboxRes.stats) setStats(inboxRes.stats)
        }
        if (convRes) {
          setConversations(convRes.conversations || [])
        }
        if (stateRes?.eligible_pages) {
          setEligiblePages(stateRes.eligible_pages)
        }
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData(platformFilter, pageFilter, activeSubTab)
    const interval = setInterval(() => loadData(platformFilter, pageFilter, activeSubTab), 15000)
    return () => clearInterval(interval)
  }, [platformFilter, pageFilter, scope, scopeBrand, scopePageId, activeSubTab])

  const handlePollPage = async () => {
    if (!can('poll_now') || isPolling) return
    setIsPolling(true)
    setPollHint(null)
    try {
      const effectivePageId = pageFilter || (scope === 'page' ? scopePageId : undefined)
      const res = await api.pollNow(effectivePageId || undefined)
      const r = res.result || {}
      const err = (r.page_errors && r.page_errors[0]?.error) || r.reason
      setPollHint(
        r.status === 'skipped'
          ? `Bỏ qua: ${r.reason || 'disabled'}`
          : `Đã quét ${r.events_ingested ?? 0} comment mới · ${r.drafts_created ?? 0} nháp` +
            (err ? ` · ${String(err).slice(0, 120)}` : ''),
      )
      await loadData(platformFilter, pageFilter)
    } catch (err: any) {
      setPollHint(err.message || 'Lỗi quét')
    } finally {
      setIsPolling(false)
      setTimeout(() => setPollHint(null), 8000)
    }
  }

  const handleSendDraft = async (draft: CareDraft) => {
    setActionLoading(draft.id)
    try {
      const res = await api.sendDraft(draft.id)
      if (res.ok) {
        setActionMsg({ id: draft.id, msg: 'Đã gửi phản hồi ra Facebook thành công!', type: 'success' })
      } else {
        setActionMsg({ id: draft.id, msg: res.error || 'Lỗi gửi phản hồi', type: 'error' })
      }
      loadData()
    } catch (err: any) {
      setActionMsg({ id: draft.id, msg: err.message || 'Lỗi gửi phản hồi', type: 'error' })
    } finally {
      setActionLoading(null)
      setTimeout(() => setActionMsg(null), 4000)
    }
  }

  const handleRejectDraft = async (draft: CareDraft) => {
    setActionLoading(draft.id)
    try {
      await api.rejectDraft(draft.id)
      setActionMsg({ id: draft.id, msg: 'Đã bỏ qua nháp này', type: 'success' })
      loadData()
    } catch (err: any) {
      setActionMsg({ id: draft.id, msg: err.message || 'Lỗi bỏ qua', type: 'error' })
    } finally {
      setActionLoading(null)
      setTimeout(() => setActionMsg(null), 4000)
    }
  }

  const handleOpenHandoff = (title: string, intent: string, commentId: string) => {
    setHandoffTitle(title)
    setHandoffIntent(intent)
    setHandoffCommentId(commentId)
    setHandoffModalOpen(true)
  }

  const handleConfirmHandoff = async () => {
    if (!handoffTitle.trim() || !handoffIntent.trim()) {
      alert('Vui lòng nhập tiêu đề và nội dung công việc')
      return
    }
    setActionLoading('handoff')
    try {
      await api.handoffToStaff({
        title: handoffTitle.trim(),
        intent: handoffIntent.trim(),
        priority: 2,
        comment_id: handoffCommentId,
      })
      setActionMsg({
        id: handoffCommentId || 'handoff',
        msg: 'Đã tạo việc và chuyển vào bảng Kanban thành công!',
        type: 'success',
      })
      setHandoffModalOpen(false)
      loadData()
    } catch (err: any) {
      alert(err.message || 'Lỗi tạo việc bàn giao')
    } finally {
      setActionLoading(null)
      setTimeout(() => setActionMsg(null), 4000)
    }
  }

  const handleReleaseTakeover = async (pageId: string, psid: string) => {
    const key = `${pageId}_${psid}`
    setActionLoading(key)
    try {
      await api.releaseTakeover(pageId, psid)
      setActionMsg({ id: key, msg: 'Javis đã nhận lại cuộc trò chuyện!', type: 'success' })
      loadData()
    } catch (err: any) {
      setActionMsg({ id: key, msg: err.message || 'Lỗi nhận lại', type: 'error' })
    } finally {
      setActionLoading(null)
      setTimeout(() => setActionMsg(null), 4000)
    }
  }

  const handleOpenConversation = async (conv: CareConversation) => {
    setSelectedConv(conv)
    setThreadLoading(true)
    setDirectMsgText('')
    try {
      const res = await api.getConversationThread(conv.page_id, conv.psid)
      if (res.ok) {
        setThreadEvents(res.events || [])
      }
    } catch (e) {
      console.error('Error fetching thread:', e)
    } finally {
      setThreadLoading(false)
    }
  }

  const handleSendDirectMessage = async () => {
    if (!selectedConv || !directMsgText.trim() || sendingDirectMsg) return
    setSendingDirectMsg(true)
    try {
      const res = await api.sendDirectMessage(selectedConv.page_id, selectedConv.psid, directMsgText.trim())
      if (res.ok) {
        const newEv: CareEvent = {
          id: Date.now(),
          kind: 'echo',
          platform: 'messenger',
          page_id: selectedConv.page_id,
          object_id: `msg_${Date.now()}`,
          thread_id: selectedConv.psid,
          from_id: selectedConv.page_id,
          from_name: 'Nhân viên Fanpage',
          body: directMsgText.trim(),
          class: 'manual_reply',
          created_ts: Date.now() / 1000,
        }
        setThreadEvents((prev) => [...prev, newEv])
        setDirectMsgText('')
        await loadData(platformFilter, pageFilter)
      } else {
        alert(res.error || 'Lỗi gửi tin nhắn')
      }
    } catch (err: any) {
      alert(err.message || 'Lỗi gửi tin nhắn')
    } finally {
      setSendingDirectMsg(false)
    }
  }

  // Strict separation: no heuristics, driven 100% by API kind and activeSubTab
  const pendingDrafts = drafts.filter((d) => d.status === 'pending')
  const commentDrafts = activeSubTab === 'comments' ? pendingDrafts : []
  const messengerDrafts = activeSubTab === 'messenger' ? pendingDrafts : []

  const commentEvents = activeSubTab === 'comments' ? events : []
  const messengerEvents = activeSubTab === 'messenger' ? events : []

  const filteredCommentDrafts = commentDrafts.filter((draft) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    const ev = events.find((e) => e.id === draft.event_id || e.object_id === draft.target_id)
    return (
      draft.proposed?.toLowerCase().includes(q) ||
      (draft.from_name || ev?.from_name)?.toLowerCase().includes(q) ||
      (draft.source_body || ev?.body)?.toLowerCase().includes(q) ||
      draft.target_id?.includes(q)
    )
  })

  const filteredCommentEvents = commentEvents.filter((e) => {
    if (!searchQuery.trim()) return true
    const q = searchQuery.toLowerCase()
    return (
      e.from_name?.toLowerCase().includes(q) ||
      e.body?.toLowerCase().includes(q) ||
      e.object_id?.includes(q) ||
      e.class?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-6">
      {/* Top Header with Tab Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Hộp Thư & Duyệt Câu Trả Lời</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Duyệt nháp Javis tự động tạo hoặc theo dõi cuộc trò chuyện Messenger với khách.
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-slate-200/80 p-1 rounded-xl w-fit">
          <button
            onClick={() => {
              setActiveSubTab('comments')
              window.location.hash = 'inbox?tab=comments'
            }}
            className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeSubTab === 'comments'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <MessageSquare className="w-4 h-4 text-saoviet-500" />
            <span>Bình luận bài viết ({stats?.pending_comment_drafts ?? (activeSubTab === 'comments' ? commentDrafts.length : 0)} chờ duyệt)</span>
          </button>
          <button
            onClick={() => {
              setActiveSubTab('messenger')
              window.location.hash = 'inbox?tab=messenger'
            }}
            className={`flex items-center space-x-2 px-4 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeSubTab === 'messenger'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Bot className="w-4 h-4 text-blue-500" />
            <span>Tin nhắn IB ({conversations.length}{(stats?.pending_message_drafts || messengerDrafts.length) > 0 ? ` · ${stats?.pending_message_drafts ?? messengerDrafts.length} gợi ý` : ''})</span>
          </button>
        </div>
      </div>

      {/* SUB-TAB 1: COMMENTS & DRAFTS */}
      {activeSubTab === 'comments' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-3">
            <div className="flex items-center space-x-3 overflow-x-auto w-full md:w-auto">
              <div className="flex items-center space-x-1.5">
                <button
                  onClick={() => setFilterView('pending')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                    filterView === 'pending'
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  Nháp chờ duyệt ({commentDrafts.length})
                </button>
                <button
                  onClick={() => setFilterView('events')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                    filterView === 'events'
                      ? 'bg-slate-900 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  Tất cả sự kiện bình luận ({commentEvents.length})
                </button>
              </div>

              {/* Platform selector */}
              <div className="flex items-center space-x-1 border-l border-slate-200 pl-3">
                <span className="text-[11px] font-medium text-slate-400 mr-1">Kênh:</span>
                {(['all', 'facebook', 'tiktok'] as const).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPlatformFilter(p)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
                      platformFilter === p
                        ? p === 'tiktok'
                          ? 'bg-slate-900 text-white shadow-sm'
                          : p === 'facebook'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-slate-700 text-white shadow-sm'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {p === 'all' ? 'Tất cả' : p === 'facebook' ? 'Facebook' : 'TikTok'}
                  </button>
                ))}
              </div>

              <select
                value={pageFilter}
                onChange={(e) => setPageFilter(e.target.value)}
                className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-slate-50 border border-slate-200 text-slate-700 max-w-[220px]"
              >
                <option value="">Mọi Fanpage</option>
                {eligiblePages.map((p) => (
                  <option key={p.page_id || p.id} value={p.page_id || p.id}>
                    {p.name} {p.brand === 'bsn' ? '(BSN)' : ''}
                  </option>
                ))}
              </select>

              {can('poll_now') && (
                <button
                  type="button"
                  onClick={handlePollPage}
                  disabled={isPolling}
                  className="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-50 whitespace-nowrap flex-shrink-0"
                >
                  {isPolling ? 'Đang kéo…' : 'Kéo comment'}
                </button>
              )}
            </div>
            {pollHint && <p className="text-xs text-slate-500">{pollHint}</p>}

            <div className="relative w-full md:w-72">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm người gửi, nội dung, ID..."
                className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-saoviet-500"
              />
            </div>
          </div>

          {/* DRAFTS PENDING VIEW */}
          {filterView === 'pending' && (
            <div className="space-y-4">
              {filteredCommentDrafts.map((draft) => {
                const ev = events.find((e) => e.id === draft.event_id || e.object_id === draft.target_id)
                const isBusy = actionLoading === draft.id
                const msg = actionMsg?.id === draft.id ? actionMsg : null
                const customerName = draft.from_name || ev?.from_name || 'Khách hàng'
                const commentText = draft.source_body || ev?.body
                const pageInfo = getPageInfo(draft.page_id)

                return (
                  <div
                    key={draft.id}
                    className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-slate-300 transition-all space-y-4"
                  >
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

                    {/* Metadata Header */}
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start space-x-3">
                        <div className="w-10 h-10 rounded-full bg-amber-100 text-amber-800 font-bold text-sm flex items-center justify-center flex-shrink-0">
                          {customerName ? customerName.slice(0, 2).toUpperCase() : 'KH'}
                        </div>
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-bold text-sm text-slate-900">{customerName}</span>
                            {renderPlatformChip((draft.event_platform === 'tiktok' || ev?.platform === 'tiktok') ? 'tiktok' : 'facebook')}
                            {draft.class && (
                              <span className="text-[11px] px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 font-medium border border-blue-100">
                                Phân loại: {draft.class}
                              </span>
                            )}
                            <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-medium flex items-center space-x-1">
                              <span className="text-slate-400">Trang:</span>
                              <span className="font-semibold text-slate-800">{pageInfo?.name || draft.page_id}</span>
                              {pageInfo?.brand && (
                                <span
                                  className={`text-[9px] px-1 py-0.2 rounded font-bold ${
                                    pageInfo.brand === 'bsn'
                                      ? 'bg-purple-100 text-purple-700'
                                      : 'bg-saoviet-100 text-saoviet-700'
                                  }`}
                                >
                                  {pageInfo.brand === 'bsn' ? 'BSN' : 'Sao Việt'}
                                </span>
                              )}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">
                            {formatTime(draft.created_ts)} • Target: {draft.target_id.slice(0, 16)}...
                          </p>
                        </div>
                      </div>

                      <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-amber-100 text-amber-800">
                        Chờ duyệt
                      </span>
                    </div>

                    {/* Customer's Comment */}
                    {commentText && (
                      <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100 text-xs text-slate-800 leading-relaxed font-normal">
                        <span className="font-bold text-slate-900 block mb-1">
                          Khách bình luận ({customerName}):
                        </span>
                        "{commentText}"
                      </div>
                    )}

                    {/* Javis Draft Response */}
                    <div className="p-4 bg-saoviet-50/70 border border-saoviet-200/80 rounded-xl space-y-2">
                      <div className="flex items-center space-x-1.5 text-xs font-bold text-saoviet-800">
                        <Bot className="w-4 h-4 text-saoviet-600" />
                        <span>Câu trả lời Javis soạn sẵn</span>
                      </div>
                      <p className="text-xs text-slate-800 leading-relaxed italic">
                        "{draft.proposed}"
                      </p>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex flex-wrap items-center justify-end gap-2 pt-2 border-t border-slate-100">
                      <button
                        onClick={() => handleRejectDraft(draft)}
                        disabled={isBusy}
                        className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-600 hover:text-red-700 hover:bg-red-50 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                      >
                        <XCircle className="w-4 h-4 text-slate-400 hover:text-red-500" />
                        <span>Bỏ qua</span>
                      </button>

                      <button
                        onClick={() =>
                          handleOpenHandoff(
                            `Tư vấn khách ${customerName}`,
                            commentText || draft.proposed,
                            draft.target_id
                          )
                        }
                        disabled={isBusy}
                        className="flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                      >
                        <UserCheck className="w-4 h-4 text-slate-500" />
                        <span>Tạo việc giao người</span>
                      </button>

                      <button
                        onClick={() => handleSendDraft(draft)}
                        disabled={isBusy}
                        className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl shadow-md shadow-saoviet-200 transition-all cursor-pointer disabled:opacity-50"
                      >
                        <Send className="w-4 h-4" />
                        <span>{isBusy ? 'Đang gửi...' : 'Gửi phản hồi'}</span>
                      </button>
                    </div>
                  </div>
                )
              })}

              {filteredCommentDrafts.length === 0 && (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400 text-xs">
                  <CheckCircle2 className="w-10 h-10 mx-auto mb-3 text-emerald-400" />
                  {platformFilter === 'tiktok' ? (
                    <>
                      <p className="font-semibold text-slate-700 text-sm">Chưa có bình luận TikTok — kênh này dùng để đăng video.</p>
                      <p className="text-slate-400 mt-1">PostPeer hiện chỉ hỗ trợ đăng video, chưa có luồng ingest comment TikTok.</p>
                    </>
                  ) : (
                    <>
                      <p className="font-semibold text-slate-600 text-sm">Chưa có comment trên bài.</p>
                      <p className="text-slate-400 mt-1">Khi có bình luận bài viết mới cần phản hồi, Javis sẽ chuẩn bị nháp tại đây</p>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ALL EVENTS VIEW */}
          {filterView === 'events' && (
            <div className="space-y-4">
              {filteredCommentEvents.map((item) => (
                <div
                  key={item.id}
                  className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-slate-300 transition-all space-y-3"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center flex-shrink-0">
                        {item.from_name ? item.from_name.slice(0, 2).toUpperCase() : 'KH'}
                      </div>
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-bold text-sm text-slate-900">{item.from_name || 'Khách hàng'}</span>
                          {renderPlatformChip(item.platform || 'facebook')}
                          <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 capitalize">
                            {item.kind}
                          </span>
                          {item.class && (
                            <span
                              className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                                item.class === 'lead'
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : 'bg-blue-50 text-blue-700'
                              }`}
                            >
                              {item.class}
                            </span>
                          )}
                          {item.faq_intent && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-purple-50 text-purple-700">
                              {item.faq_intent}
                            </span>
                          )}
                          {(() => {
                            const p = getPageInfo(item.page_id)
                            return p?.name ? (
                              <span className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-medium">
                                {p.name} {p.brand === 'bsn' ? '(BSN)' : ''}
                              </span>
                            ) : null
                          })()}
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {formatTime(item.created_ts)} • ID: {item.object_id}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={() =>
                        handleOpenHandoff(
                          `Tư vấn khách ${item.from_name || 'Fanpage'}`,
                          item.body,
                          item.object_id
                        )
                      }
                      className="px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer"
                    >
                      Tạo việc
                    </button>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-800 leading-relaxed">
                    "{item.body}"
                  </div>
                </div>
              ))}

              {filteredCommentEvents.length === 0 && (
                <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400 text-xs">
                  <MessageSquare className="w-10 h-10 mx-auto mb-3 text-slate-300" />
                  {platformFilter === 'tiktok' ? (
                    <>
                      <p className="font-semibold text-slate-700 text-sm">Chưa có bình luận TikTok — kênh này dùng để đăng video.</p>
                      <p className="text-slate-400 mt-1">PostPeer hiện chỉ hỗ trợ đăng video, chưa có luồng ingest comment TikTok.</p>
                    </>
                  ) : (
                    <>
                      <p className="font-semibold text-slate-600">Chưa có comment trên bài.</p>
                      <p className="text-slate-400 mt-1">Các bình luận và tương tác mới sẽ xuất hiện tại đây</p>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 2: MESSENGER CONVERSATIONS & TAKEOVER */}
      {activeSubTab === 'messenger' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            {can('poll_now') && (
              <button
                type="button"
                onClick={async () => {
                  if (isPolling) return
                  setIsPolling(true)
                  setPollHint(null)
                  try {
                    const res = await api.pollNow(pageFilter || undefined, 'messenger')
                    const r = res.result || {}
                    setPollHint(
                      `Hộp thư IB: ${r.messages_ingested ?? 0} tin mới · ${r.drafts_created ?? 0} nháp` +
                        (r.page_errors?.[0]?.error ? ` · ${String(r.page_errors[0].error).slice(0, 100)}` : ''),
                    )
                    await loadData(platformFilter, pageFilter)
                  } catch (err: any) {
                    setPollHint(err.message || 'Lỗi kéo inbox')
                  } finally {
                    setIsPolling(false)
                    setTimeout(() => setPollHint(null), 8000)
                  }
                }}
                disabled={isPolling}
                className="px-3 py-1.5 rounded-lg text-xs font-bold bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 whitespace-nowrap flex-shrink-0"
              >
                {isPolling ? 'Đang kéo hộp thư…' : 'Kéo hộp thư IB'}
              </button>
            )}
            {pollHint && <span className="text-xs text-slate-500">{pollHint}</span>}
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-2xl p-4 text-xs text-blue-900 flex items-start space-x-3">
            <Bot className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block mb-0.5">Cơ chế nhường quyền tự động (Takeover 4 giờ):</span>
              Khi nhân viên mở Meta Business Suite hoặc điện thoại để nhắn tin trực tiếp với khách, Javis sẽ tự động tạm lùi lại trong 4 tiếng để tránh trả lời trùng lặp. Khi tư vấn xong, nhân viên có thể bấm nút <b>"Javis nhận lại"</b> để kích hoạt trả lời tự động trở lại ngay lập tức.
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {conversations.map((conv) => {
              const key = `${conv.page_id}_${conv.psid}`
              const isTakeover = Boolean(conv.takeover_until && conv.takeover_until > Date.now() / 1000)
              const in24hWindow = Boolean(conv.last_user_ts && (Date.now() / 1000 - conv.last_user_ts) < 86400)
              const isBusy = actionLoading === key
              const msg = actionMsg?.id === key ? actionMsg : null

              return (
                <div
                  key={key}
                  className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between space-y-4"
                >
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

                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-11 h-11 rounded-full bg-blue-600 text-white font-bold text-base flex items-center justify-center shadow-sm">
                        {conv.customer_name ? conv.customer_name.trim().charAt(0).toUpperCase() : <MessageCircle className="w-5 h-5 text-white" />}
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm">
                          {conv.customer_name || `Khách Messenger ${conv.psid.slice(-4)}`}
                        </h3>
                        {(() => {
                          const p = getPageInfo(conv.page_id)
                          return (
                            <div className="flex items-center space-x-1.5 text-[11px] text-slate-500 mt-0.5">
                              <span>Trang: <strong className="text-slate-700">{p?.name || conv.page_id}</strong></span>
                              {p?.brand && (
                                <span
                                  className={`text-[9px] px-1 py-0.2 rounded font-bold ${
                                    p.brand === 'bsn'
                                      ? 'bg-purple-100 text-purple-700'
                                      : 'bg-saoviet-100 text-saoviet-700'
                                  }`}
                                >
                                  {p.brand === 'bsn' ? 'BSN' : 'Sao Việt'}
                                </span>
                              )}
                              <span>· PSID: {conv.psid.slice(-6)}</span>
                            </div>
                          )
                        })()}
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

                  {conv.last_body && (
                    <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-800 leading-relaxed">
                      <span className="text-[10px] font-bold uppercase text-slate-400 mr-2">Tin mới</span>
                      {conv.last_class && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 mr-2">{conv.last_class}</span>
                      )}
                      “{conv.last_body}”
                    </div>
                  )}

                  <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-700 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Khách nhắn lần cuối:</span>
                      <span className="font-semibold text-slate-800">
                        {conv.last_user_ts ? formatTime(conv.last_user_ts) : 'Chưa có'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Trang gửi lần cuối:</span>
                      <span className="font-semibold text-slate-800">
                        {conv.last_page_ts ? formatTime(conv.last_page_ts) : 'Chưa có'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500">Cửa sổ phản hồi:</span>
                      <span className={`font-semibold ${in24hWindow ? 'text-emerald-700' : 'text-slate-500'}`}>
                        {in24hWindow ? 'Trong 24 giờ' : 'Hết 24 giờ'}
                      </span>
                    </div>
                  </div>

                  {/* Javis suggested reply for this conversation if any */}
                  {(() => {
                    const draftForConv = messengerDrafts.find(
                      (d) => d.target_id === conv.psid || d.from_id === conv.psid
                    )
                    if (!draftForConv) return null
                    const isBusyDraft = actionLoading === draftForConv.id
                    return (
                      <div className="p-3.5 bg-gradient-to-r from-blue-50/80 to-indigo-50/80 border border-blue-200/90 rounded-xl space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-1.5 text-xs font-bold text-blue-900">
                            <Sparkles className="w-4 h-4 text-blue-600 animate-pulse" />
                            <span>Gợi ý phản hồi từ Javis</span>
                          </div>
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                            Chờ duyệt
                          </span>
                        </div>
                        <p className="text-xs text-slate-800 italic leading-relaxed">
                          "{draftForConv.proposed}"
                        </p>
                        <div className="flex items-center justify-end space-x-2 pt-1.5 border-t border-blue-200/60">
                          <button
                            onClick={() => handleRejectDraft(draftForConv)}
                            disabled={isBusyDraft}
                            className="px-2.5 py-1 text-[11px] font-medium text-slate-500 hover:text-red-600 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
                          >
                            Bỏ qua
                          </button>
                          <button
                            onClick={() => handleSendDraft(draftForConv)}
                            disabled={isBusyDraft}
                            className="flex items-center space-x-1 px-3 py-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-2xs transition-all cursor-pointer disabled:opacity-50"
                          >
                            <Send className="w-3 h-3" />
                            <span>{isBusyDraft ? 'Đang gửi…' : 'Duyệt & Gửi tin nhắn'}</span>
                          </button>
                        </div>
                      </div>
                    )
                  })()}

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between gap-2">
                    <button
                      onClick={() => handleOpenConversation(conv)}
                      className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition-colors cursor-pointer"
                    >
                      <MessageCircle className="w-3.5 h-3.5" />
                      <span>Xem chat & Trả lời</span>
                    </button>

                    <div className="flex items-center space-x-2">
                      {isTakeover && (
                        <button
                          onClick={() => handleReleaseTakeover(conv.page_id, conv.psid)}
                          disabled={isBusy}
                          className="flex items-center space-x-1.5 px-3 py-1.5 text-xs font-bold text-saoviet-700 bg-saoviet-50 hover:bg-saoviet-100 border border-saoviet-200 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
                        >
                          <RotateCcw className={`w-3.5 h-3.5 ${isBusy ? 'animate-spin' : ''}`} />
                          <span>Javis nhận lại</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}

            {conversations.length === 0 && (
              <div className="col-span-2 bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400 text-xs">
                <Bot className="w-10 h-10 mx-auto mb-3 text-slate-300" />
                <p className="font-semibold text-slate-700 text-sm">Chưa có tin nhắn hộp thư. Bấm Kéo hộp thư IB.</p>
                <p className="text-slate-500 mt-2 max-w-md mx-auto leading-relaxed">
                  Tab này là <b>tin nhắn IB</b> qua Facebook Messenger / Business Suite.
                  Bình luận dưới bài viết nằm ở tab <b>Bình luận bài viết</b> — hoàn toàn riêng biệt.
                  Bấm nút <b>Kéo hộp thư IB</b> ở trên để đồng bộ tin nhắn mới nhất từ Meta.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal: Handoff Note */}
      {handoffModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <h3 className="text-base font-bold text-slate-900">Tạo việc giao nhân viên hỗ trợ</h3>
            <p className="text-xs text-slate-500">
              Chuyển yêu cầu vào Bảng Việc Cần Làm (Kanban) của Javis để tư vấn viên chăm sóc tiếp.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Tiêu đề việc *</label>
                <input
                  type="text"
                  value={handoffTitle}
                  onChange={(e) => setHandoffTitle(e.target.value)}
                  placeholder="Vd: Tư vấn khoá TOEIC cho khách..."
                  className="w-full p-2.5 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Nội dung / Yêu cầu chi tiết *</label>
                <textarea
                  rows={3}
                  value={handoffIntent}
                  onChange={(e) => setHandoffIntent(e.target.value)}
                  placeholder="Nội dung khách trao đổi hoặc yêu cầu gọi lại..."
                  className="w-full p-2.5 text-xs text-slate-900 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-saoviet-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                onClick={() => setHandoffModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
              >
                Huỷ bỏ
              </button>
              <button
                onClick={handleConfirmHandoff}
                disabled={actionLoading === 'handoff'}
                className="px-4 py-2 text-xs font-bold text-white bg-saoviet-500 hover:bg-saoviet-600 rounded-xl shadow-md shadow-saoviet-200 transition-all cursor-pointer disabled:opacity-50"
              >
                {actionLoading === 'handoff' ? 'Đang tạo việc...' : 'Xác nhận tạo việc'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Messenger Chat & Direct Reply */}
      {selectedConv && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full h-[620px] shadow-2xl border border-slate-200 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Header */}
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/80">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-full bg-blue-600 text-white font-bold text-base flex items-center justify-center shadow-sm">
                  {selectedConv.customer_name ? selectedConv.customer_name.trim().charAt(0).toUpperCase() : <MessageCircle className="w-5 h-5 text-white" />}
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-base font-bold text-slate-900">
                      {selectedConv.customer_name || `Khách Messenger ${selectedConv.psid.slice(-4)}`}
                    </h3>
                    {Boolean(selectedConv.takeover_until && selectedConv.takeover_until > Date.now() / 1000) ? (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                        Takeover nhân viên
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                        Javis quản lý
                      </span>
                    )}
                  </div>
                  {(() => {
                    const p = getPageInfo(selectedConv.page_id)
                    return (
                      <div className="flex items-center space-x-1.5 text-[11px] text-slate-500">
                        <span>Trang: <strong className="text-slate-700">{p?.name || selectedConv.page_id}</strong></span>
                        {p?.brand && (
                          <span
                            className={`text-[9px] px-1 py-0.2 rounded font-bold ${
                              p.brand === 'bsn'
                                ? 'bg-purple-100 text-purple-700'
                                : 'bg-saoviet-100 text-saoviet-700'
                            }`}
                          >
                            {p.brand === 'bsn' ? 'BSN' : 'Sao Việt'}
                          </span>
                        )}
                        <span>· PSID: {selectedConv.psid}</span>
                      </div>
                    )
                  })()}
                </div>
              </div>

              <button
                onClick={() => setSelectedConv(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Chat Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/50">
              {threadLoading ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-400 text-xs">
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-2" />
                  <span>Đang tải lịch sử tin nhắn...</span>
                </div>
              ) : threadEvents.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-slate-400 text-xs text-center">
                  <Bot className="w-8 h-8 text-slate-300 mb-2" />
                  <p className="font-semibold text-slate-600">Chưa có bản ghi tin nhắn chi tiết trong hệ thống</p>
                  <p className="text-[11px] text-slate-400 mt-1 max-w-sm">
                    Bấm "Kéo hộp thư IB (Business)" để đồng bộ toàn bộ tin nhắn từ Facebook hoặc nhập tin nhắn bên dưới để phản hồi trực tiếp cho khách.
                  </p>
                </div>
              ) : (
                threadEvents.map((ev) => {
                  const isPage = ev.kind === 'echo' || ev.from_id === selectedConv.page_id || ev.from_name === 'Nhân viên Fanpage'
                  return (
                    <div
                      key={ev.id || ev.object_id}
                      className={`flex flex-col ${isPage ? 'items-end' : 'items-start'}`}
                    >
                      <div className="flex items-center space-x-1 mb-1 text-[10px] text-slate-400">
                        <span>{isPage ? 'Trang (Nhân viên / Javis)' : (ev.from_name || selectedConv.customer_name || 'Khách')}</span>
                        <span>·</span>
                        <span>{formatTime(ev.created_ts)}</span>
                      </div>
                      <div
                        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-xs shadow-sm ${
                          isPage
                            ? 'bg-blue-600 text-white rounded-br-xs'
                            : 'bg-white text-slate-800 border border-slate-200 rounded-bl-xs'
                        }`}
                      >
                        <p className="whitespace-pre-wrap leading-relaxed">{ev.body}</p>
                      </div>
                    </div>
                  )
                })
              )}
            </div>

            {/* Suggested Draft Banner inside Modal */}
            {(() => {
              const activeModalDraft = messengerDrafts.find(
                (d) => d.target_id === selectedConv.psid || d.from_id === selectedConv.psid
              )
              if (!activeModalDraft) return null
              const isBusyModal = actionLoading === activeModalDraft.id
              return (
                <div className="px-4 py-2.5 bg-gradient-to-r from-blue-50 to-indigo-50 border-t border-blue-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                  <div className="flex items-start space-x-2 flex-1 min-w-0">
                    <Sparkles className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <div className="text-[11px] font-bold text-blue-900 flex items-center gap-1.5">
                        <span>Gợi ý phản hồi từ Javis</span>
                        <span className="text-[10px] font-normal text-blue-600">(soạn theo Brand Kit)</span>
                      </div>
                      <p className="text-xs text-slate-800 line-clamp-2 italic mt-0.5">
                        "{activeModalDraft.proposed}"
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 flex-shrink-0 self-end sm:self-center">
                    <button
                      type="button"
                      onClick={() => setDirectMsgText(activeModalDraft.proposed)}
                      className="px-2.5 py-1 text-xs font-semibold text-blue-700 bg-white hover:bg-blue-50 border border-blue-200 rounded-lg shadow-2xs transition-colors cursor-pointer"
                    >
                      Điền vào ô chat
                    </button>
                    <button
                      type="button"
                      onClick={async () => {
                        await handleSendDraft(activeModalDraft)
                        if (selectedConv) {
                          handleOpenConversation(selectedConv)
                        }
                      }}
                      disabled={isBusyModal}
                      className="px-3 py-1 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
                    >
                      {isBusyModal ? 'Đang gửi…' : 'Gửi ngay'}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRejectDraft(activeModalDraft)}
                      disabled={isBusyModal}
                      className="p-1 text-slate-400 hover:text-red-500 rounded-lg transition-colors cursor-pointer"
                      title="Bỏ qua gợi ý này"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )
            })()}

            {/* Footer Input */}
            <div className="p-3 border-t border-slate-200 bg-white space-y-2">
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  value={directMsgText}
                  onChange={(e) => setDirectMsgText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSendDirectMessage()
                    }
                  }}
                  placeholder={`Nhắn tin cho ${selectedConv.customer_name || 'khách hàng'} (Enter để gửi)...`}
                  className="flex-1 px-3.5 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="button"
                  onClick={handleSendDirectMessage}
                  disabled={!directMsgText.trim() || sendingDirectMsg}
                  className="flex items-center space-x-1.5 px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-xl shadow-sm transition-all cursor-pointer"
                >
                  <Send className={`w-3.5 h-3.5 ${sendingDirectMsg ? 'animate-pulse' : ''}`} />
                  <span>{sendingDirectMsg ? 'Đang gửi…' : 'Gửi Messenger'}</span>
                </button>
              </div>
              <p className="text-[10px] text-slate-400">
                Tin nhắn gửi trực tiếp qua Facebook Messenger Graph API · Tự động ghi nhận lịch sử vào Javis Care.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

