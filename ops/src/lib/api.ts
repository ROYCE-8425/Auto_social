// API client for Ops Dashboard - Aligned 1-to-1 with Javis Backend

export type OpsRole = 'owner' | 'manager' | 'cskh' | 'sales' | 'warehouse' | 'marketing' | 'technical' | 'staff'

export interface OpsUser {
  id: string
  username: string
  role: OpsRole
  name: string
  role_title?: string
  code?: string
  permissions?: string[]
  enabled?: boolean
  created_at?: number
}

export interface OpsDirectoryUser {
  id: string
  username: string
  name: string
  role: OpsRole
  role_title?: string
  code?: string
  badge_color?: string
  enabled?: boolean
}

export interface RbacPermissionItem {
  id: string
  name: string
  description: string
}

export interface RbacCategory {
  category: string
  category_title: string
  permissions: RbacPermissionItem[]
}

export interface RbacRoleInfo {
  title: string
  code: string
  badge_color: string
  description: string
  level: number
}

export interface RbacPermissionsPayload {
  roles: Record<string, RbacRoleInfo>
  catalog: RbacCategory[]
  matrix: Record<string, string[]>
  default_matrix: Record<string, string[]>
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

  // Staff Directory (Safe for all authenticated users to assign tasks)
  getDirectory: () => request<{ users: OpsDirectoryUser[] }>('/ops/directory'),

  // RBAC Roles & Capabilities Matrix
  getRbacRoles: () =>
    request<{
      roles: Record<string, RbacRoleInfo>
      permissions: Record<string, string[]>
    }>('/ops/rbac/roles'),
  getRbacPermissions: () => request<RbacPermissionsPayload>('/ops/rbac/permissions'),
  saveRbacPermissions: (matrix: Record<string, string[]>) =>
    request<{ ok: boolean; matrix: Record<string, string[]> }>('/ops/rbac/permissions', {
      method: 'POST',
      body: JSON.stringify({ matrix }),
    }),
  resetRbacPermissions: () =>
    request<{ ok: boolean; matrix: Record<string, string[]> }>('/ops/rbac/permissions/reset', {
      method: 'POST',
    }),


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
  getOpsTasks: () => request<{ ok: boolean; tasks: any[] }>('/ops/tasks'),
  createOpsTask: (data: any) =>
    request<{ ok: boolean; task: any }>('/ops/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  moveOpsTask: (taskId: string, targetCol: string) =>
    request<{ ok: boolean; task: any }>(`/ops/tasks/${encodeURIComponent(taskId)}/move`, {
      method: 'POST',
      body: JSON.stringify({ targetCol }),
    }),
  updateOpsTask: (taskId: string, data: any) =>
    request<{ ok: boolean; task: any }>(`/ops/tasks/${encodeURIComponent(taskId)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  deleteOpsTask: (taskId: string) =>
    request<{ ok: boolean }>(`/ops/tasks/${encodeURIComponent(taskId)}`, {
      method: 'DELETE',
    }),

  // Trends & Usage (Manager & Owner)
  getUsageSummary: () => request<any>('/usage/summary'),

  // System Audit Log (from /inbox)
  getAuditLog: () => request<{ items?: any[] }>('/inbox'),

  // TikTok Channel (View-only for Ops Staff/Manager)
  getTikTokStatus: () => request<TikTokStatusResponse>('/tiktok/status'),

  // Social Channels Connectors Status (Facebook, TikTok, Zalo, Instagram, YouTube)
  getFacebookStatus: () => request<FacebookStatusResponse>('/connect/facebook/status'),
  getChannelsStatus: () => request<ChannelsStatusResponse>('/ops/channels/status'),

  // Q&A ca làm việc Javis Ops (Internal staff shift assistant)
  askOpsQA: (data: { message: string; scope?: any }) =>
    request<OpsQAResponse>('/ops/qa', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // AI Operations Center (SME)
  getDailyBriefing: () => request<DailyBriefing>('/ops/briefing/today'),
  sendDailyBriefing: (channel: string = 'telegram') =>
    request<{ ok: boolean; channel: string; dispatched_at: string; message: string }>('/ops/briefing/send', {
      method: 'POST',
      body: JSON.stringify({ channel }),
    }),
  evaluateLeadScore: (data: EvaluateLeadPayload) =>
    request<LeadScoreResult>('/ops/lead-scoring/evaluate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getAttributionMatrix: () => request<AttributionMatrixResponse>('/ops/attribution/matrix'),
  getAttributionInsights: () => request<AttributionInsightsResponse>('/ops/attribution/insights'),
  getCompetitorRadar: () => request<CompetitorRadarResponse>('/ops/competitor/radar'),
  getCampaigns: () => request<CampaignListResponse>('/ops/campaigns'),
  getCampaign: (id: string) => request<CampaignDetailResponse>(`/ops/campaigns/${encodeURIComponent(id)}`),
  createCampaignAutopilot: (data: CampaignAutopilotPayload) =>
    request<CampaignAutopilotResponse>('/ops/campaigns/autopilot', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // ============================================================
  // Social Commerce Order System & Shipping Gateway
  // ============================================================
  getOrders: (params?: { status?: string; crm_id?: string; thread_id?: string; page_id?: string; limit?: number }) => {
    const query = new URLSearchParams()
    if (params?.status) query.set('status', params.status)
    if (params?.crm_id) query.set('crm_id', params.crm_id)
    if (params?.thread_id) query.set('thread_id', params.thread_id)
    if (params?.page_id) query.set('page_id', params.page_id)
    if (params?.limit) query.set('limit', String(params.limit))
    const qs = query.toString()
    return request<{ ok: boolean; orders: OpsOrder[]; total: number }>(`/ops/orders${qs ? `?${qs}` : ''}`)
  },
  getOrder: (id: string) => request<{ ok: boolean; order: OpsOrder }>(`/ops/orders/${encodeURIComponent(id)}`),
  createOrder: (data: Partial<OpsOrder>) =>
    request<{ ok: boolean; order: OpsOrder }>('/ops/orders', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateOrder: (id: string, updates: Partial<OpsOrder>) =>
    request<{ ok: boolean; order: OpsOrder }>(`/ops/orders/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }),
  extractOrderFromThread: (data: {
    messages: any[]
    customer_name?: string
    page_id?: string
    thread_id?: string
    crm_id?: string
    auto_save?: boolean
  }) =>
    request<ExtractOrderResponse>('/ops/orders/extract-from-thread', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  extractOrderDetails: (id: string, data: { messages: any[]; customer_name?: string }) =>
    request<{ ok: boolean; extracted: ExtractOrderResponse; order?: OpsOrder }>(`/ops/orders/${encodeURIComponent(id)}/extract`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  confirmOrder: (id: string) =>
    request<{ ok: boolean; order: OpsOrder; auto_shipment?: any }>(`/ops/orders/${encodeURIComponent(id)}/confirm`, {
      method: 'POST',
    }),
  createShipment: (id: string, provider: string = 'ghn') =>
    request<{ ok: boolean; shipment?: OpsShipment; order?: OpsOrder; error?: string; status?: string }>(
      `/ops/orders/${encodeURIComponent(id)}/create-shipment`,
      {
        method: 'POST',
        body: JSON.stringify({ provider }),
      }
    ),
  syncShipmentStatus: (id: string) =>
    request<{ ok: boolean; tracking?: any; shipment?: OpsShipment; order?: OpsOrder; error?: string; status?: string }>(
      `/ops/orders/${encodeURIComponent(id)}/sync-shipment`,
      {
        method: 'POST',
      }
    ),
  cancelOrder: (id: string, reason?: string) =>
    request<{ ok: boolean; order: OpsOrder; shipment_cancelled?: any }>(`/ops/orders/${encodeURIComponent(id)}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
  getShippingProviders: () => request<{ ok: boolean; providers: ShippingProviderItem[] }>('/ops/shipping/providers'),
  getShippingSettings: () => request<{ ok: boolean; settings: ShippingSettingsResponse }>('/ops/shipping/settings'),
  saveShippingSettings: (settings: any) =>
    request<{ ok: boolean; message: string; settings: ShippingSettingsResponse }>('/ops/shipping/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    }),
  testShippingConnection: (data: { provider?: string; token?: string; shop_id?: string; environment?: string }) =>
    request<{ ok: boolean; status: string; message?: string; error?: string }>('/ops/shipping/test-connection', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getProducts: (params?: string | { keyword?: string; page_id?: string; channel?: string; active_only?: boolean }) => {
    const cleanParams = typeof params === 'string' ? { keyword: params } : (params || {})
    const qs = new URLSearchParams()
    if (cleanParams.keyword) qs.set('keyword', cleanParams.keyword)
    if (cleanParams.page_id) qs.set('page_id', cleanParams.page_id)
    if (cleanParams.channel) qs.set('channel', cleanParams.channel)
    if (cleanParams.active_only !== undefined) qs.set('active_only', String(cleanParams.active_only))
    const query = qs.toString()
    return request<{ ok: boolean; products: OpsProduct[] }>(`/ops/products${query ? `?${query}` : ''}`)
  },
  saveProduct: (data: Partial<OpsProduct>) =>
    request<{ ok: boolean; product: OpsProduct }>('/ops/products', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  updateProduct: (id: string, data: Partial<OpsProduct>) =>
    request<{ ok: boolean; product: OpsProduct }>(`/ops/products/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  deleteProduct: (id: string) =>
    request<{ ok: boolean; message?: string }>(`/ops/products/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }),
  addProductAlias: (productId: string, alias: string) =>
    request<{ ok: boolean; alias: any }>(`/ops/products/${encodeURIComponent(productId)}/aliases`, {
      method: 'POST',
      body: JSON.stringify({ alias }),
    }),
  bindProductToPage: (
    productId: string,
    data: { page_id: string; channel?: string; custom_price?: number | null; auto_sell_allowed?: boolean }
  ) =>
    request<{ ok: boolean; binding: any }>(`/ops/products/${encodeURIComponent(productId)}/bindings`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  importProductsCsv: (csv_content: string) =>
    request<{ ok: boolean; imported_count: number; errors: string[] }>('/ops/products/import-csv', {
      method: 'POST',
      body: JSON.stringify({ csv_content }),
    }),
  getAutomationRules: (params?: { page_id?: string; channel?: string }) => {
    const qs = new URLSearchParams()
    if (params?.page_id) qs.set('page_id', params.page_id)
    if (params?.channel) qs.set('channel', params.channel)
    const query = qs.toString()
    return request<{ ok: boolean; rules: OpsAutomationRule[] }>(`/ops/automation/rules${query ? `?${query}` : ''}`)
  },
  saveAutomationRule: (data: Partial<OpsAutomationRule>) =>
    request<{ ok: boolean; rule: OpsAutomationRule }>('/ops/automation/rules', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  deleteAutomationRule: (id: string) =>
    request<{ ok: boolean }>(`/ops/automation/rules/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }),
  getAutomationRuns: (params?: { page_id?: string; thread_id?: string; limit?: number }) => {
    const qs = new URLSearchParams()
    if (params?.page_id) qs.set('page_id', params.page_id)
    if (params?.thread_id) qs.set('thread_id', params.thread_id)
    if (params?.limit) qs.set('limit', String(params.limit))
    const query = qs.toString()
    return request<{ ok: boolean; runs: OpsAutomationRun[] }>(`/ops/automation/runs${query ? `?${query}` : ''}`)
  },
  getOutboxMessages: (params?: { status?: string; page_id?: string; limit?: number }) => {
    const qs = new URLSearchParams()
    if (params?.status) qs.set('status', params.status)
    if (params?.page_id) qs.set('page_id', params.page_id)
    if (params?.limit) qs.set('limit', String(params.limit))
    const query = qs.toString()
    return request<{ ok: boolean; messages: OpsOutboxMessage[] }>(`/ops/automation/outbox${query ? `?${query}` : ''}`)
  },
  updateOutboxStatus: (messageId: string, status: string, error?: string) =>
    request<{ ok: boolean }>(`/ops/automation/outbox/${encodeURIComponent(messageId)}/status`, {
      method: 'POST',
      body: JSON.stringify({ status, error }),
    }),
  getAutomationKillSwitch: () => request<{ ok: boolean; kill_switch: boolean }>('/ops/automation/kill-switch'),
  setAutomationKillSwitch: (enabled: boolean) =>
    request<{ ok: boolean; kill_switch: boolean; message: string }>('/ops/automation/kill-switch', {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    }),
  evaluateAutomation: (data: {
    thread_id?: string
    page_id?: string
    channel?: string
    messages: Array<{ sender?: string; text?: string }>
    customer_info?: any
  }) =>
    request<any>('/ops/automation/evaluate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // ============================================================
  // Operations Hub Real Aggregator & Business Operational Modules
  // ============================================================
  getOpsHubSummary: () => request<OpsHubSummaryResponse>('/ops/hub/summary'),
  getModules: (params?: { category?: string; status?: string }) => {
    const qs = new URLSearchParams()
    if (params?.category) qs.set('category', params.category)
    if (params?.status) qs.set('status', params.status)
    const q = qs.toString()
    return request<{ ok: boolean; modules: BusinessModule[] }>(`/ops/modules${q ? `?${q}` : ''}`)
  },
  getModule: (code: string) =>
    request<{ ok: boolean; module: BusinessModule }>(`/ops/modules/${encodeURIComponent(code)}`),
  getModuleRecords: (
    code: string,
    params?: {
      status?: string
      priority?: string
      search?: string
      owner_id?: string
      limit?: number
      offset?: number
    }
  ) => {
    const qs = new URLSearchParams()
    if (params?.status) qs.set('status', params.status)
    if (params?.priority) qs.set('priority', params.priority)
    if (params?.search) qs.set('search', params.search)
    if (params?.owner_id) qs.set('owner_id', params.owner_id)
    if (params?.limit) qs.set('limit', String(params.limit))
    if (params?.offset) qs.set('offset', String(params.offset))
    const q = qs.toString()
    return request<{ ok: boolean; module_code: string; total: number; records: ModuleRecord[] }>(
      `/ops/modules/${encodeURIComponent(code)}/records${q ? `?${q}` : ''}`
    )
  },
  createModuleRecord: (code: string, data: Partial<ModuleRecord>) =>
    request<{ ok: boolean; record: ModuleRecord }>(`/ops/modules/${encodeURIComponent(code)}/records`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getModuleRecord: (code: string, id: string) =>
    request<{ ok: boolean; record: ModuleRecord }>(
      `/ops/modules/${encodeURIComponent(code)}/records/${encodeURIComponent(id)}`
    ),
  updateModuleRecord: (code: string, id: string, data: Partial<ModuleRecord>) =>
    request<{ ok: boolean; record: ModuleRecord }>(
      `/ops/modules/${encodeURIComponent(code)}/records/${encodeURIComponent(id)}`,
      {
        method: 'PATCH',
        body: JSON.stringify(data),
      }
    ),
  deleteModuleRecord: (code: string, id: string) =>
    request<{ ok: boolean; deleted: boolean }>(
      `/ops/modules/${encodeURIComponent(code)}/records/${encodeURIComponent(id)}`,
      {
        method: 'DELETE',
      }
    ),
  addModuleComment: (code: string, id: string, content: string) =>
    request<{ ok: boolean; comment: ModuleComment }>(
      `/ops/modules/${encodeURIComponent(code)}/records/${encodeURIComponent(id)}/comments`,
      {
        method: 'POST',
        body: JSON.stringify({ content }),
      }
    ),
  addModuleAttachment: (
    code: string,
    id: string,
    data: { file_name: string; file_url: string; file_type?: string }
  ) =>
    request<{ ok: boolean; attachment: ModuleAttachment }>(
      `/ops/modules/${encodeURIComponent(code)}/records/${encodeURIComponent(id)}/attachments`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    ),

  // ============================================================
  // Company Document Vault (Kho Tài Liệu Doanh Nghiệp)
  // ============================================================
  getDocuments: (params?: {
    category?: string
    status?: string
    department?: string
    search?: string
    linked_type?: string
    linked_id?: string
    is_template?: boolean
    expiring_soon?: boolean
    limit?: number
    offset?: number
  }) => {
    const query = new URLSearchParams()
    if (params?.category) query.set('category', params.category)
    if (params?.status) query.set('status', params.status)
    if (params?.department) query.set('department', params.department)
    if (params?.search) query.set('search', params.search)
    if (params?.linked_type) query.set('linked_type', params.linked_type)
    if (params?.linked_id) query.set('linked_id', params.linked_id)
    if (params?.is_template !== undefined) query.set('is_template', String(params.is_template))
    if (params?.expiring_soon) query.set('expiring_soon', 'true')
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const q = query.toString()
    return request<DocumentListResponse>(`/ops/documents${q ? `?${q}` : ''}`)
  },

  getDocumentStats: () => request<{ ok: boolean; stats: DocumentStats }>('/ops/documents/stats'),

  getDocumentTemplates: (category?: string) => {
    const q = category ? `?category=${encodeURIComponent(category)}` : ''
    return request<{ ok: boolean; templates: CompanyDocument[] }>(`/ops/documents/templates${q}`)
  },

  getDocument: (id: string) =>
    request<{ ok: boolean; document: CompanyDocument }>(`/ops/documents/${encodeURIComponent(id)}`),

  uploadDocument: async (formData: FormData) => {
    const res = await fetch('/ops/documents/upload', {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) {
      const text = await res.text()
      let msg = text
      try {
        const j = JSON.parse(text)
        if (j.error) msg = j.error
      } catch (_) {}
      throw new Error(msg || `Upload thất bại: HTTP ${res.status}`)
    }
    return res.json() as Promise<{ ok: boolean; document: CompanyDocument }>
  },

  updateDocument: (id: string, data: Partial<CompanyDocument>) =>
    request<{ ok: boolean; document: CompanyDocument }>(`/ops/documents/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteDocument: (id: string) =>
    request<{ ok: boolean; deleted: boolean }>(`/ops/documents/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    }),

  approveDocument: (id: string, action: 'approve' | 'reject', notes?: string) =>
    request<{ ok: boolean; document: CompanyDocument }>(`/ops/documents/${encodeURIComponent(id)}/approve`, {
      method: 'POST',
      body: JSON.stringify({ action, notes }),
    }),

  signDocument: (id: string, signer_name?: string, notes?: string) =>
    request<{ ok: boolean; document: CompanyDocument }>(`/ops/documents/${encodeURIComponent(id)}/sign`, {
      method: 'POST',
      body: JSON.stringify({ signer_name, notes }),
    }),

  addDocumentVersion: async (id: string, formData: FormData) => {
    const res = await fetch(`/ops/documents/${encodeURIComponent(id)}/versions`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) {
      const text = await res.text()
      let msg = text
      try {
        const j = JSON.parse(text)
        if (j.error) msg = j.error
      } catch (_) {}
      throw new Error(msg || `Cập nhật phiên bản thất bại: HTTP ${res.status}`)
    }
    return res.json() as Promise<{ ok: boolean; document: CompanyDocument }>
  },

  getDocumentFileUrl: (id: string, download = false) =>
    `/ops/documents/${encodeURIComponent(id)}/file${download ? '?download=true' : ''}`,
}


export interface OpsQAResponse {
  ok: boolean
  reply: string
  citations?: string[]
  used_stats?: boolean
  error?: string
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

export interface FacebookPageItem {
  id: string
  name: string
  category: string
  connected: boolean
  has_token?: boolean
  source?: string
}

export interface FacebookStatusResponse {
  ok: boolean
  connected: boolean
  connector_id: string
  label: string
  permissions: string
  fanpage_care_enabled: boolean
  kill_switch: boolean
  poll_interval_seconds: number
  last_poll: string | null
  pages: FacebookPageItem[]
  error?: string
}

export interface ChannelInfoItem {
  id: string
  name: string
  connected: boolean
  statusLabel: string
  publish_supported: boolean
  note: string
}

export interface ChannelsStatusResponse {
  ok: boolean
  facebook: FacebookStatusResponse
  tiktok: TikTokStatusResponse
  other_channels: ChannelInfoItem[]
}

export interface DailyBriefingLead {
  lead_id: string
  name: string
  score: number
  intent: string
  next_best_action: string
  assigned_to: string
  phone?: string
}

export interface DailyBriefing {
  ok: boolean
  briefing: {
    date: string
    greeting: string
    kpis: {
      inbox_yesterday: number
      new_leads: number
      orders_closed: number
      revenue_vnd: number
    }
    top_converting_post: {
      id: string
      title: string
      platform: string
      orders: number
      revenue_vnd: number
    }
    urgent_hot_leads: DailyBriefingLead[]
    warnings: string[]
  }
  telegram_ready_text: string
}

export interface EvaluateLeadPayload {
  lead_id?: string
  name?: string
  signals?: {
    asked_price?: boolean
    left_phone?: boolean
    repeated_inquiry?: boolean
    clicked_link?: boolean
    viewed_cart?: boolean
    responded_in_5m?: boolean
    negative_signal?: boolean
    hours_since_last_customer_msg?: number
  }
  customer_history?: any
}

export interface LeadScoreResult {
  ok: boolean
  score_info: {
    lead_id: string
    score: number
    tier: 'hot' | 'warm' | 'cold'
    confidence: number
    positive_factors: string[]
    risk_factors: string[]
    calculated_at: string
  }
  next_best_action: {
    action: string
    recommended_action: string
    reasoning: string
    urgency: 'high' | 'medium' | 'low'
    suggested_script: string
    channel: string
  }
  approval_level: {
    level: 'low' | 'medium' | 'high'
    label: string
    description: string
    requires_human: boolean
    approver_role: string
  }
}

export interface AttributionItem {
  post_id: string
  title: string
  platform: string
  posted_at: string
  views: number
  inboxes: number
  leads: number
  orders: number
  revenue_vnd: number
  conversion_rate: number
  status: string
}

export interface AttributionMatrixResponse {
  ok: boolean
  summary: {
    total_views: number
    total_inboxes: number
    total_leads: number
    total_orders: number
    total_revenue_vnd: number
    top_converting_platform: string
  }
  items: AttributionItem[]
}

export interface AttributionInsightsResponse {
  ok: boolean
  data_source?: 'real' | 'empty' | 'not_configured'
  winning_patterns: Array<{
    hook_type: string
    pattern_example?: string
    avg_conversion_rate: number
    avg_revenue_vnd: number
    recommendation: string
  }>
  timing_recommendation: {
    best_days: string[]
    best_hours: string[]
    rationale: string
  } | null
  content_to_replicate: string[]
  learning_system_status?: string
}

export interface CompetitorRadarResponse {
  ok: boolean
  competitors: Array<{
    name: string
    platform: string
    followers_est: number
    top_topics: string[]
    weakness: string
    recent_angle: string
  }>
  content_gap_analysis: Array<{
    topic: string
    competitor_coverage: string
    our_status: string
    recommended_action: string
    potential_reach: string
  }>
  actionable_counter_hooks: string[]
}

export interface CampaignAutopilotPayload {
  goal?: string
  budget_vnd?: number
  duration_weeks?: number
  target_revenue_vnd?: number
  platforms?: string[]
}

export interface CampaignItemRecord {
  id: string
  campaign_id: string
  day: number
  week: number
  platform: string
  content_type: string
  angle: string
  hook: string
  cta: string
  lead_target: number
  status: string
  task_id?: string
  external_post_id?: string
  created_at: number
  updated_at: number
}

export interface CampaignRecord {
  id: string
  goal: string
  target_metric: string
  duration_weeks: number
  budget_vnd: number
  target_revenue_vnd: number
  roi_projected: string
  platforms: string[]
  status: string
  task_ids: string[]
  total_items?: number
  items?: CampaignItemRecord[]
  created_at: number
  updated_at: number
  plan?: any
}

export interface CampaignListResponse {
  ok: boolean
  campaigns: CampaignRecord[]
}

export interface CampaignDetailResponse {
  ok: boolean
  campaign: CampaignRecord
  items: CampaignItemRecord[]
  task_ids: string[]
}

export interface CampaignAutopilotResponse {
  ok: boolean
  campaign_id?: string
  task_ids?: string[]
  status?: string
  items?: CampaignItemRecord[]
  campaign_plan?: {
    goal: string
    budget_vnd: number
    target_revenue_vnd: number
    roi_projected: string
    platforms?: string[]
    milestones: Array<{
      week: number
      theme: string
      kpi_target: string
      key_action: string
    }>
    content_calendar: Array<{
      day: number
      week: number
      platform: string
      content_type: string
      angle: string
      hook: string
      cta: string
      lead_target: number
      status?: string
      task_id?: string
      external_post_id?: string
    }>
    sales_script?: {
      greeting: string
      qualify_question: string
      closing_hook: string
    }
    sales_objection_playbook: Array<{
      customer_objection: string
      ai_counter_argument: string
      closing_offer: string
    }>
    review_checklist: string[]
    created_at: number | string
  }
}

// ============================================================
// Order & Shipping Types
// ============================================================

export interface OpsOrderItem {
  id?: number
  order_id?: string
  product_id?: string
  sku?: string
  name: string
  quantity: number
  price: number
  total: number
}

export interface OpsShipment {
  id: string
  order_id: string
  provider: string
  tracking_code?: string
  external_order_code?: string
  status: string
  fee: number
  cod_amount: number
  expected_delivery_time?: string
  created_at: number
  updated_at: number
}

export interface OpsOrder {
  id: string
  crm_id?: string
  customer_name?: string
  customer_phone?: string
  page_id?: string
  thread_id?: string
  status:
    | 'draft'
    | 'needs_info'
    | 'ready_to_confirm'
    | 'confirmed'
    | 'shipment_pending'
    | 'shipment_created'
    | 'picking'
    | 'shipping'
    | 'delivered'
    | 'failed'
    | 'cancelled'
    | 'returned'
  total_amount: number
  cod_amount: number
  shipping_fee: number
  payment_method: string
  shipping_address?: string
  shipping_address_obj?: any
  customer_notes?: string
  internal_notes?: string
  ai_confidence?: number
  missing_fields?: string[]
  items?: OpsOrderItem[]
  shipment?: OpsShipment
  audit_logs?: Array<{
    id: number
    order_id: string
    action: string
    actor: string
    details?: string
    created_at: number
  }>
  created_at: number
  updated_at: number
}

export interface ExtractOrderResponse {
  ok: boolean
  customer_name: string
  customer_phone?: string
  shipping_address?: string
  items: OpsOrderItem[]
  total_amount: number
  cod_amount: number
  ai_confidence: number
  missing_fields: string[]
  status: string
  followup_question?: string
  is_product_matched: boolean
  saved_order?: OpsOrder
}

export interface ShippingProviderItem {
  id: string
  name: string
  logo: string
  supported: boolean
  is_default: boolean
  status: string
  status_label: string
  capabilities: string[]
}

export interface ShippingSettingsResponse {
  default_provider: string
  providers: {
    ghn: {
      name: string
      enabled: boolean
      has_token?: boolean
      masked_token?: string
      token?: string
      shop_id: string
      environment: 'sandbox' | 'production'
      pickup_address: {
        name: string
        phone: string
        address: string
        ward_code: string
        district_id: number
        province_name: string
      }
    }
    ghtk?: any
    viettel_post?: any
  }
  automation: {
    auto_create_shipment: boolean
    min_confidence: number
    require_sku_match: boolean
    max_cod_amount: number
    kill_switch: boolean
  }
}

export interface OpsProduct {
  id: string
  sku: string
  name: string
  description?: string
  price: number
  sale_price?: number
  category: string
  is_active: number | boolean
  auto_sell_enabled?: number | boolean
  auto_sell_allowed?: number | boolean
  stock: number
  weight_gram?: number
  image_url?: string
  aliases?: string[]
  page_bindings?: Array<{
    id?: string
    page_id: string
    channel?: string
    custom_price?: number | null
    auto_sell_allowed?: number | boolean
  }>
  created_at?: number
  updated_at?: number
}

export interface OpsAutomationRule {
  id: string
  page_id: string
  channel: string
  case_type: string
  enabled: number | boolean
  level: number
  min_confidence: number
  require_product_match?: number | boolean
  require_phone?: number | boolean
  require_address?: number | boolean
  max_cod_amount?: number
  require_staff_approval?: number | boolean
  message_template?: string
  cooldown_seconds?: number
  created_at?: number
  updated_at?: number
}

export interface OpsAutomationRun {
  id: string
  case_type: string
  thread_id?: string
  page_id?: string
  order_id?: string
  status: string
  decision_reason: string
  payload?: any
  created_at: number
}

export interface OpsOutboxMessage {
  id: string
  thread_id?: string
  page_id?: string
  channel?: string
  recipient_id?: string
  body: string
  status: string
  error?: string
  created_at: number
  sent_at?: number
}

// ============================================================
// Business Operational Modules Interfaces
// ============================================================
export interface BusinessModuleWorkflow {
  id: string
  label: string
  color: string
}

export interface BusinessModule {
  id: string
  code: string
  name: string
  category: 'pipeline' | 'people_knowledge' | 'executive'
  description: string
  icon: string
  color: string
  status: string
  is_connected: number | boolean
  created_at: number
  updated_at: number
  record_count: number
  computed_status: string
  status_label: string
  status_counts?: Record<string, number>
  workflows?: BusinessModuleWorkflow[]
}

export interface ModuleActivity {
  id: string
  record_id: string
  action: string
  actor_id: string
  before?: Record<string, any>
  after?: Record<string, any>
  created_at: number
}

export interface ModuleComment {
  id: string
  record_id: string
  actor_id: string
  content: string
  created_at: number
}

export interface ModuleAttachment {
  id: string
  record_id: string
  file_name: string
  file_url: string
  file_type?: string
  created_at: number
}

export interface ModuleRecord {
  id: string
  module_code: string
  title: string
  description?: string
  status: string
  priority: string
  owner_id?: string
  source?: string
  payload_json?: string
  payload?: Record<string, any>
  due_at?: string | null
  created_at: number
  updated_at: number
  activities?: ModuleActivity[]
  comments?: ModuleComment[]
  attachments?: ModuleAttachment[]
}

export interface HubSummaryModuleItem {
  code: string
  name: string
  category: string
  icon: string
  status: 'active' | 'warning' | 'needs_config' | 'coming_soon'
  has_real_source: boolean
  data_source_label: string
  kpi: {
    main: string
    label: string
    sub?: string
  }
  alerts: string[]
  recommended_action: string
  primary_action: {
    label: string
    path: string
  }
  secondary_actions?: {
    label: string
    path: string
  }[]
  preview_items?: {
    id: string
    title: string
    desc: string
    badge: string
    urgent?: boolean
    target: string
  }[]
}

export interface OpsHubSummaryResponse {
  ok: boolean
  executive_summary: {
    need_action_today: number
    critical_alerts: number
    revenue_recorded: number
    orders_total: number
    orders_draft: number
    crm_customers_total: number
    hot_leads_count: number
    inbox_drafts_total: number
    tasks_urgent: number
  }
  modules: HubSummaryModuleItem[]
}

// ============================================================
// Company Document Vault Interfaces
// ============================================================

export type DocumentCategory =
  | 'contract'
  | 'sop'
  | 'policy'
  | 'invoice'
  | 'template'
  | 'legal'
  | 'hr'
  | 'marketing'

export type DocumentApprovalStatus =
  | 'draft'
  | 'pending'
  | 'pending_approval'
  | 'approved'
  | 'rejected'
  | 'signed'
  | 'expired'

export interface DocumentVersion {
  id: string
  document_id: string
  version: string
  filename: string
  file_name?: string
  file_path: string
  file_size: number
  uploaded_by: string
  notes?: string
  change_note?: string
  created_at: number
}

export interface DocumentActivity {
  id: string
  document_id: string
  actor: string
  actor_id?: string
  action: string
  details?: string
  note?: string
  created_at: number
}

export interface CompanyDocument {
  id: string
  code: string
  title: string
  category: DocumentCategory
  department: string
  owner: string
  owner_id?: string
  version: string
  approval_status: DocumentApprovalStatus
  expiry_date?: string | null
  expires_at?: number | null
  permission_level: 'public' | 'internal' | 'confidential' | 'restricted'
  linked_entity_type?: 'customer' | 'order' | 'task' | 'staff' | null
  linked_entity_id?: string | null
  filename: string
  file_name?: string
  file_path: string
  file_size: number
  mime_type: string
  is_template: boolean | number
  template_type?: string | null
  description?: string
  tags?: string[]
  created_at: number
  updated_at: number
  is_expiring_soon?: boolean
  is_expired?: boolean
  versions?: DocumentVersion[]
  activities?: DocumentActivity[]
}

export interface DocumentStats {
  total: number
  pending_approval: number
  expiring_soon: number
  expired: number
  missing_signature: number
  by_category: Record<string, number>
  by_status: Record<string, number>
  by_department: Record<string, number>
  categories_count: number
}

export interface DocumentListResponse {
  ok: boolean
  total: number
  documents: CompanyDocument[]
}



