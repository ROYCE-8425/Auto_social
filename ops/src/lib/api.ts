// API client for Ops Dashboard
export interface OpsUser {
  id: string
  username: string
  role: 'staff' | 'manager' | 'owner'
  name: string
  enabled?: boolean
  created_at?: number
}

export interface CareState {
  enabled: boolean
  mode: 'suggest' | 'semi' | 'full'
  kill_switch: boolean
  page_name?: string
  page_id?: string
  connected?: boolean
  readonly?: boolean
  stats_24h?: {
    comments?: number
    leads?: number
    drafts_pending?: number
    replied?: number
    handoff?: number
  }
  last_poll_ts?: number
}

export interface InboxItem {
  id: string
  post_id: string
  comment_id: string
  author_id?: string
  author_name: string
  author_pic?: string
  created_time: string | number
  message: string
  intent?: string
  sentiment?: string
  phone?: string
  branch?: string
  confidence?: number
  draft_response?: string
  status: 'pending' | 'sent' | 'rejected' | 'handoff'
  category?: string
  post_summary?: string
}

export interface ConversationItem {
  id: string
  recipient_id: string
  recipient_name: string
  recipient_pic?: string
  last_message: string
  last_message_ts: number
  unread_count?: number
  takeover?: {
    active: boolean
    by?: string
    since?: number
    expires_at?: number
  }
}

export interface CustomerItem {
  id: string
  psid?: string
  name: string
  phone?: string
  branch?: string
  status?: string
  tags?: string[]
  sentiment?: string
  interaction_count?: number
  last_seen_ts?: number
  first_seen_ts?: number
  notes?: string
  history?: Array<{
    type: 'comment' | 'message'
    ts: number
    text: string
    intent?: string
  }>
}

export interface KanbanTask {
  id: string
  title: string
  description?: string
  status: 'todo' | 'in_progress' | 'done'
  assignee?: string
  created_at: number
  priority?: 'low' | 'medium' | 'high'
  lead_phone?: string
  branch?: string
}

export interface AuditLogItem {
  id: string
  ts: number
  actor: string
  action: string
  target?: string
  details?: string
  status?: 'success' | 'warning' | 'error'
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Accept': 'application/json',
      ...((options.body && !(options.body instanceof FormData)) ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  if (res.status === 401) {
    // Tránh loop vô tận nếu đang ở /ops/me
    if (!url.includes('/ops/me') && !url.includes('/ops/auth/login')) {
      window.dispatchEvent(new CustomEvent('ops:unauthorized'))
    }
    throw new Error('Chưa đăng nhập hoặc phiên làm việc đã hết hạn')
  }

  if (res.status === 403) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || 'Bạn không có quyền thực hiện thao tác này')
  }

  if (!res.ok) {
    const text = await res.text()
    let msg = `Lỗi hệ thống (${res.status})`
    try {
      const errJson = JSON.parse(text)
      msg = errJson.error || errJson.message || msg
    } catch {
      if (text.length < 100 && text.trim()) msg = text
    }
    throw new Error(msg)
  }

  return res.json()
}

export const api = {
  // Auth & Session
  getMe: () => request<{ user: OpsUser | null }>('/ops/me'),
  login: (credentials: { username: string; password: string }) =>
    request<{ ok: boolean; user: OpsUser }>('/ops/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),
  logout: () => request<{ ok: boolean }>('/ops/auth/logout', { method: 'POST' }),

  // User Management (Owner only)
  getUsers: () => request<{ users: OpsUser[] }>('/ops/users'),
  createUser: (data: { username: string; password: string; role: string; name?: string }) =>
    request<{ ok: boolean; user: OpsUser }>('/ops/users', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateUser: (id: string, data: Partial<OpsUser & { password?: string }>) =>
    request<{ ok: boolean; user: OpsUser }>(`/ops/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteUser: (id: string) =>
    request<{ ok: boolean }>(`/ops/users/${id}`, { method: 'DELETE' }),

  // Care State & Overview
  getCareState: () => request<CareState>('/fanpage-care/state'),
  pollNow: () => request<{ ok: boolean; count?: number }>('/fanpage-care/poll-now', { method: 'POST' }),

  // Inbox: Comments & Drafts
  getInbox: () => request<{ items: InboxItem[] }>('/fanpage-care/inbox'),
  sendDraft: (commentId: string, customText?: string) =>
    request<{ ok: boolean }>(`/fanpage-care/drafts/${encodeURIComponent(commentId)}/send`, {
      method: 'POST',
      body: JSON.stringify(customText ? { text: customText } : {}),
    }),
  rejectDraft: (commentId: string, reason?: string) =>
    request<{ ok: boolean }>(`/fanpage-care/drafts/${encodeURIComponent(commentId)}/reject`, {
      method: 'POST',
      body: JSON.stringify(reason ? { reason } : {}),
    }),
  handoffToStaff: (commentId: string, note?: string) =>
    request<{ ok: boolean; task_id?: string }>(`/fanpage-care/handoff`, {
      method: 'POST',
      body: JSON.stringify({ comment_id: commentId, note }),
    }),

  // Messenger Conversations
  getConversations: () => request<{ items: ConversationItem[] }>('/fanpage-care/conversations'),
  releaseTakeover: (threadId: string) =>
    request<{ ok: boolean }>('/fanpage-care/conversations/release-takeover', {
      method: 'POST',
      body: JSON.stringify({ thread_id: threadId }),
    }),

  // Customers CRM
  getCustomers: (search?: string) =>
    request<{ customers: CustomerItem[] }>(`/fanpage-care/customers${search ? `?q=${encodeURIComponent(search)}` : ''}`),
  getCustomerDetail: (id: string) =>
    request<{ customer: CustomerItem }>(`/fanpage-care/customers/${encodeURIComponent(id)}`),
  updateCustomer: (id: string, data: Partial<CustomerItem>) =>
    request<{ ok: boolean; customer: CustomerItem }>(`/fanpage-care/customers/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  mergeCustomers: (sourceId: string, targetId: string) =>
    request<{ ok: boolean }>('/fanpage-care/customers/merge', {
      method: 'POST',
      body: JSON.stringify({ source_id: sourceId, target_id: targetId }),
    }),
  deleteCustomer: (id: string) =>
    request<{ ok: boolean }>(`/fanpage-care/customers/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }),

  // Tasks (Kanban)
  getTasks: () => request<{ tasks: KanbanTask[] }>('/kanban'),
  createTask: (task: Partial<KanbanTask>) =>
    request<{ ok: boolean; task: KanbanTask }>('/kanban', {
      method: 'POST',
      body: JSON.stringify(task),
    }),
  updateTask: (id: string, data: Partial<KanbanTask>) =>
    request<{ ok: boolean }>(`/kanban/tasks/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // Trends & Usage (Manager & Owner)
  getUsageSummary: () => request<any>('/usage/summary'),
  
  // System Audit Log (from /inbox)
  getAuditLog: () => request<{ items?: any[] }>('/inbox'),
}
