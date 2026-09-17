// API client for Ops Dashboard - Aligned 1-to-1 with Javis Backend

export interface OpsUser {
  id: string
  username: string
  role: 'staff' | 'manager' | 'owner'
  name: string
  enabled?: boolean
  created_at?: number
}

export interface CareStats {
  total_events: number
  events_24h: number
  leads_24h: number
  human_needed_24h: number
  replies_24h: number
  spam_hidden_24h: number
  pending_drafts: number
  pending_comment_drafts?: number
  pending_message_drafts?: number
  total_customers: number
}

export interface CareFeatures {
  poll_comments?: boolean
  poll_messenger?: boolean
  auto_reply_comments?: boolean
  auto_reply_messenger?: boolean
  hide_spam?: boolean
  crm?: boolean
  drafts?: boolean
  [key: string]: boolean | undefined
}

export interface CarePageSettings {
  enabled?: boolean
  mode?: 'suggest' | 'semi' | 'auto' | 'full' | string
  brand?: string
  features?: Partial<CareFeatures>
}

export interface CareConfig {
  enabled?: boolean
  mode?: 'suggest' | 'semi' | 'auto' | 'full' | string
  scope?: 'all' | 'brand' | 'page'
  scope_brand?: 'bsn' | 'saoviet' | string
  scope_page_id?: string
  features?: CareFeatures
  pages?: Record<string, CarePageSettings>
  kill_switch?: boolean
  quiet_hours?: string
  poll_interval_min?: number
  app_secret?: string
  webhook_verify_token?: string
  [key: string]: any
}

export interface CareState {
  ok: boolean
  config: CareConfig
  stats: CareStats
  eligible_pages?: Array<{ page_id: string; id?: string; name: string; kit_file?: string; brand?: string }>
  connection_perm?: 'readonly' | 'full'
  facebook_connected?: boolean
  facebook_label?: string
  is_quiet?: boolean
  poller_running?: boolean
}

export interface CareEvent {
  id: number
  kind: 'comment' | 'message' | 'echo' | 'action'
  platform?: 'facebook' | 'tiktok' | 'messenger'
  page_id: string
  object_id: string
  thread_id?: string | null
  from_id?: string | null
  from_name?: string | null
  body: string
  class?: string | null
  faq_intent?: string | null
  created_ts: number
  ingested_ts?: number
}

export interface CareDraft {
  id: number
  event_id?: number | null
  page_id: string
  target_id: string
  proposed: string
  class?: string | null
  status: 'pending' | 'approved' | 'rejected' | 'sent' | 'expired'
  created_ts: number
  event_kind?: 'comment' | 'message'
  event_platform?: string
  from_name?: string
  from_id?: string
  source_body?: string
  event_created_ts?: number
}

export interface CareConversation {
  page_id: string
  psid: string
  customer_name?: string
  last_user_ts?: number
  last_page_ts?: number
  takeover_until?: number
  last_body?: string
  last_class?: string
  last_event_ts?: number
  last_kind?: string
  last_sender?: 'customer' | 'page' | string
  is_unreplied?: boolean
  waiting_since?: number
  latest_activity_ts?: number
  pending_draft?: {
    id: number
    proposed: string
    created_ts?: number
  } | null
}

export interface CareCustomer {
  crm_id: string
  name: string
  phones: string[]
  tags: string[]
  brand?: string
  course_interest?: string
  campus?: string
  page_ids?: string[]
  md_path?: string
  updated_ts: number
}

export interface CareIdentity {
  kind: string
  page_id: string
  ext_id: string
  crm_id: string
}

export interface CareCustomerDetail {
  ok: boolean
  customer: CareCustomer
  identities: CareIdentity[]
  markdown: string
  behavior?: {
    stage?: string
    message_count?: number
    comment_count?: number
    by_platform?: Record<string, number>
    by_class?: Record<string, number>
    last_intent?: string | null
    last_body?: string
    last_ts?: number
    campus?: string
    course_interest?: string
  }
}

export interface KanbanTask {
  id: string
  brain_root?: string
  title: string
  normalized_title?: string
  intent?: string
  route?: string
  capability?: string
  execution_mode?: string
  priority: number
  status: 'triage' | 'todo' | 'ready' | 'running' | 'review' | 'blocked' | 'done' | 'cancelled' | 'archived'
  needs_approval?: boolean
  block_kind?: string
  block_reason?: string
  created_by?: string
  chat_id?: string
  idempotency_key?: string
  created_at: number
  updated_at: number
  metadata?: Record<string, any>
  artifacts?: any[]
  deps?: string[]
}

export interface KanbanBoardView {
  schema: number
  brain_root: string
  orchestration: string
  dispatcher?: {
    running: boolean
    max_workers: number
    active_workers: number
    workers?: any[]
  }
  columns: {
    triage?: KanbanTask[]
    todo?: KanbanTask[]
    ready?: KanbanTask[]
    running?: KanbanTask[]
    review?: KanbanTask[]
    blocked?: KanbanTask[]
    done?: KanbanTask[]
    cancelled?: KanbanTask[]
    [key: string]: KanbanTask[] | undefined
  }
  counts: Record<string, number>
  completed_24h: number
  running: boolean
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const isFormData = options.body instanceof FormData
  const res = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...((options.body && !isFormData) ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })

  if (res.status === 401) {
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
      msg = errJson.detail || errJson.error || errJson.message || msg
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
  saveCareSettings: (patch: Partial<CareConfig>) =>
    request<{ ok: boolean; config?: CareConfig; error?: string }>('/fanpage-care/settings', {
      method: 'POST',
      body: JSON.stringify(patch),
    }),
  getCareStats: (params?: { page_id?: string; brand?: string }) => {
    const query = new URLSearchParams()
    if (params?.page_id) query.set('page_id', params.page_id)
    if (params?.brand) query.set('brand', params.brand)
    const qs = query.toString()
    return request<{ ok: boolean; stats: CareStats }>(`/fanpage-care/stats${qs ? `?${qs}` : ''}`)
  },
  pollNow: (pageId?: string, channel?: 'comments' | 'messenger' | 'both') =>
    request<{ ok: boolean; result?: any }>('/fanpage-care/poll-now', {
      method: 'POST',
      body: JSON.stringify({
        ...(pageId ? { page_id: pageId } : {}),
        ...(channel ? { channel } : {}),
      }),
    }),

  // Inbox: Comments & Drafts
  getInbox: (params?: {
    page_id?: string
    brand?: string
    class_name?: string
    platform?: string
    kind?: 'comment' | 'message'
    limit?: number
    offset?: number
  }) => {
    const query = new URLSearchParams()
    if (params?.page_id) query.set('page_id', params.page_id)
    if (params?.brand) query.set('brand', params.brand)
    if (params?.class_name) query.set('class_name', params.class_name)
    if (params?.platform) query.set('platform', params.platform)
    if (params?.kind) query.set('kind', params.kind)
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const qs = query.toString()
    return request<{
      ok: boolean
      events: CareEvent[]
      drafts: CareDraft[]
      stats: CareStats
    }>(`/fanpage-care/inbox${qs ? `?${qs}` : ''}`)
  },
  sendDraft: (draftId: number) =>
    request<{ ok: boolean; status?: string; error?: string }>(
      `/fanpage-care/drafts/${draftId}/send`,
      { method: 'POST' }
    ),
  rejectDraft: (draftId: number) =>
    request<{ ok: boolean; status?: string }>(
      `/fanpage-care/drafts/${draftId}/reject`,
      { method: 'POST' }
    ),
  handoffToStaff: (data: {
    title: string
    intent: string
    priority?: number
    comment_id?: string
  }) =>
    request<{ ok: boolean; task_id?: string }>(`/fanpage-care/handoff`, {
      method: 'POST',
      body: JSON.stringify({
        title: data.title,
        intent: data.intent,
        priority: data.priority ?? 2,
        comment_id: data.comment_id ?? '',
      }),
    }),

  // Messenger Conversations
  getConversations: (params?: string | { page_id?: string; brand?: string }) => {
    let qs = ''
    if (typeof params === 'string') {
      qs = params ? `?page_id=${encodeURIComponent(params)}` : ''
    } else if (params) {
      const sp = new URLSearchParams()
      if (params.page_id) sp.set('page_id', params.page_id)
      if (params.brand) sp.set('brand', params.brand)
      qs = sp.toString() ? `?${sp.toString()}` : ''
    }
    return request<{ ok: boolean; conversations: CareConversation[] }>(`/fanpage-care/conversations${qs}`)
  },
  getConversationThread: (pageId: string, psid: string) =>
    request<{ ok: boolean; page_id: string; psid: string; events: CareEvent[] }>(
      `/fanpage-care/conversations/thread?page_id=${encodeURIComponent(pageId)}&psid=${encodeURIComponent(psid)}`
    ),
  sendDirectMessage: (pageId: string, psid: string, message: string) =>
    request<{ ok: boolean; page_id?: string; psid?: string; message?: string; error?: string }>(
      '/fanpage-care/conversations/send',
      {
        method: 'POST',
        body: JSON.stringify({ page_id: pageId, psid, message }),
      }
    ),
  releaseTakeover: (pageId: string, psid: string) =>
    request<{ ok: boolean; page_id: string; psid: string; takeover_until: number }>(
      '/fanpage-care/conversations/release-takeover',
      {
        method: 'POST',
        body: JSON.stringify({ page_id: pageId, psid }),
      }
    ),

  // Customers CRM
  getCustomers: (
    paramsOrSearch?: string | {
      search?: string
      brand?: string
      page_id?: string
      tag?: string
      limit?: number
    },
    tag?: string,
    limit = 50
  ) => {
    const query = new URLSearchParams()
    if (typeof paramsOrSearch === 'object' && paramsOrSearch !== null) {
      if (paramsOrSearch.search) query.set('q', paramsOrSearch.search)
      if (paramsOrSearch.brand) query.set('brand', paramsOrSearch.brand)
      if (paramsOrSearch.page_id) query.set('page_id', paramsOrSearch.page_id)
      if (paramsOrSearch.tag) query.set('tag', paramsOrSearch.tag)
      if (paramsOrSearch.limit) query.set('limit', String(paramsOrSearch.limit))
    } else {
      if (paramsOrSearch) query.set('q', paramsOrSearch)
      if (tag) query.set('tag', tag)
      if (limit) query.set('limit', String(limit))
    }
    const qs = query.toString()
    return request<{ ok: boolean; customers: CareCustomer[]; total?: number; reason?: string }>(
      `/fanpage-care/customers${qs ? `?${qs}` : ''}`
    )
  },
  backfillCustomers: (days = 90) =>
    request<{ ok: boolean; events_scanned?: number; customers_created?: number; customers_updated?: number }>(
      '/fanpage-care/customers/backfill',
      {
        method: 'POST',
        body: JSON.stringify({ days }),
      }
    ),
  getCustomerDetail: (crmId: string) =>
    request<CareCustomerDetail>(`/fanpage-care/customers/${encodeURIComponent(crmId)}`),
  mergeCustomers: (primaryCrmId: string, secondaryCrmId: string) =>
    request<{ ok: boolean; crm_id?: string }>('/fanpage-care/customers/merge', {
      method: 'POST',
      body: JSON.stringify({
        primary_crm_id: primaryCrmId,
        secondary_crm_id: secondaryCrmId,
      }),
    }),
  deleteCustomer: (crmId: string) =>
    request<{ ok: boolean; deleted?: boolean }>(
      `/fanpage-care/customers/${encodeURIComponent(crmId)}`,
      { method: 'DELETE' }
    ),

  // Tasks (Kanban)
  getTasks: (brain = 'brain') =>
    request<KanbanBoardView>(`/kanban?brain=${encodeURIComponent(brain)}`),
  moveTask: (id: string, status: string, brain = 'brain') => {
    const form = new FormData()
    form.append('id', id)
    form.append('status', status)
    form.append('brain', brain)
    return request<{ ok: boolean; status?: string; error?: string }>('/kanban/task/move', {
      method: 'POST',
      body: form,
    })
  },
  createTask: (data: { title: string; intent?: string; priority?: number; brain?: string }) => {
    const form = new FormData()
    form.append('title', data.title)
    form.append('intent', data.intent || data.title)
    form.append('priority', String(data.priority ?? 2))
    form.append('brain', data.brain || 'brain')
    return request<{ ok: boolean; id?: string }>('/kanban/task', {
      method: 'POST',
      body: form,
    })
  },

  // Trends & Usage (Manager & Owner)
  getUsageSummary: () => request<any>('/usage/summary'),

  // System Audit Log (from /inbox)
  getAuditLog: () => request<{ items?: any[] }>('/inbox'),

  // TikTok Channel (View-only for Ops Staff/Manager)
  getTikTokStatus: () => request<TikTokStatusResponse>('/tiktok/status'),
}

export interface TikTokPostItem {
  ts: number
  datetime: string
  kit: string
  brand: string
  accountId: string
  username: string
  postpeer_id: string
  urls: string[]
  caption: string
  status: string
  tiktok_url?: string
  draft?: boolean
  photos_count: number
}

export interface TikTokStatusResponse {
  ok: boolean
  connected: boolean
  masked_key: string
  accounts: Array<{
    id: string
    name: string
    username?: string
    platform: string
    status?: string
  }>
  kits: Array<{
    file: string
    stem: string
    name: string
    enabled: boolean
    account_id: string
    username: string
    brand: string
  }>
  loop: {
    enabled: boolean
    status: string
    file: string
  }
  recent_posts: TikTokPostItem[]
  role?: string
}

