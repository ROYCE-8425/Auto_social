import React, { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  ClipboardList,
  Play,
  RefreshCw,
  Save,
  ShieldAlert,
} from 'lucide-react'
import { api, OpsAutomationRule, OpsOutboxMessage } from '../lib/api'
import { useAuth } from '../lib/auth'

const bool = (v: unknown) => v === true || v === 1 || v === '1' || v === 'true'

const caseLabels: Record<string, string> = {
  faq_reply: 'Trả lời FAQ',
  price_reply: 'Báo giá theo catalog',
  stock_reply: 'Báo tồn kho',
  ask_missing_phone: 'Xin số điện thoại',
  ask_missing_address: 'Xin địa chỉ giao hàng',
  create_order_draft: 'Tạo đơn nháp',
  auto_confirm_order: 'Tự xác nhận đơn',
  auto_create_shipment: 'Tự tạo vận đơn GHN',
  send_tracking_code: 'Gửi mã vận đơn',
  handoff_to_staff: 'Chuyển người thật',
}

const levelLabels: Record<number, string> = {
  0: 'Tắt / chỉ ghi nhận',
  1: 'Tạo dữ liệu nội bộ',
  2: 'Bán tự động qua outbox',
  3: 'Tự động đầy đủ',
}

export const AutomationRulesSettings: React.FC = () => {
  const { role } = useAuth()
  const canManage = role === 'owner' || role === 'manager' || (role as string) === 'admin'
  const [pageId, setPageId] = useState('*')
  const [channel, setChannel] = useState('messenger')
  const [rules, setRules] = useState<OpsAutomationRule[]>([])
  const [outbox, setOutbox] = useState<OpsOutboxMessage[]>([])
  const [killSwitch, setKillSwitch] = useState(false)
  const [testText, setTestText] = useState('Chốt cho mình 1 sản phẩm về 25 Hai Bà Trưng, Hà Nội, sđt 0988112233')
  const [testResult, setTestResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [savingId, setSavingId] = useState<string | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const enabledCount = useMemo(() => rules.filter((r) => bool(r.enabled)).length, [rules])
  const fullAutoCount = useMemo(() => rules.filter((r) => bool(r.enabled) && Number(r.level || 0) >= 3).length, [rules])

  const loadData = async () => {
    setLoading(true)
    setMessage(null)
    try {
      const [ruleRes, outboxRes, killRes] = await Promise.all([
        api.getAutomationRules({ page_id: pageId.trim() || '*', channel: channel.trim() || '*' }),
        api.getOutboxMessages({ page_id: pageId.trim() === '*' ? undefined : pageId.trim(), limit: 8 }),
        api.getAutomationKillSwitch(),
      ])
      setRules(ruleRes.rules || [])
      setOutbox(outboxRes.messages || [])
      setKillSwitch(bool(killRes.kill_switch))
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.message || 'Không tải được cấu hình tự động hóa' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const updateLocalRule = (id: string, patch: Partial<OpsAutomationRule>) => {
    setRules((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)))
  }

  const saveRule = async (rule: OpsAutomationRule) => {
    if (!canManage) return
    setSavingId(rule.id)
    setMessage(null)
    try {
      const saved = await api.saveAutomationRule({
        ...rule,
        page_id: pageId.trim() || '*',
        channel: channel.trim() || '*',
      })
      updateLocalRule(rule.id, saved.rule)
      setMessage({ type: 'success', text: `Đã lưu rule ${caseLabels[rule.case_type] || rule.case_type}` })
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.message || 'Không lưu được rule' })
    } finally {
      setSavingId(null)
    }
  }

  const toggleKillSwitch = async () => {
    if (!canManage) return
    setLoading(true)
    setMessage(null)
    try {
      const res = await api.setAutomationKillSwitch(!killSwitch)
      setKillSwitch(bool(res.kill_switch))
      setMessage({
        type: bool(res.kill_switch) ? 'error' : 'success',
        text: bool(res.kill_switch) ? 'Đã bật Kill Switch, mọi automation bán hàng sẽ dừng' : 'Đã tắt Kill Switch',
      })
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.message || 'Không đổi được Kill Switch' })
    } finally {
      setLoading(false)
    }
  }

  const runSimulation = async () => {
    setLoading(true)
    setTestResult(null)
    try {
      const res = await api.evaluateAutomation({
        thread_id: `ui_test_${Date.now()}`,
        page_id: pageId.trim() || '*',
        channel: channel.trim() || 'messenger',
        messages: [{ sender: 'customer', text: testText }],
        customer_info: { name: 'Khách test' },
      })
      setTestResult(res)
      await loadData()
    } catch (err: any) {
      setTestResult({ ok: false, error: err?.message || 'Không chạy được mô phỏng' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs space-y-5">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Bot className="w-5 h-5 text-blue-600" />
              <span>Automation Case Engine</span>
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Cấu hình Javis xử lý từng case: tư vấn, báo giá, hỏi thiếu thông tin, tạo đơn, gọi GHN và gửi mã vận đơn.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={toggleKillSwitch}
              disabled={loading || !canManage}
              className={`inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold border ${
                killSwitch
                  ? 'bg-rose-600 text-white border-rose-600 hover:bg-rose-700'
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
              } disabled:opacity-50`}
            >
              <ShieldAlert className="w-4 h-4" />
              {killSwitch ? 'Kill Switch đang bật' : 'Bật Kill Switch'}
            </button>
            <button
              type="button"
              onClick={loadData}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : ''}`} />
              Tải lại
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <input value={pageId} onChange={(e) => setPageId(e.target.value)} placeholder="Page ID hoặc *" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
          <input value={channel} onChange={(e) => setChannel(e.target.value)} placeholder="messenger/facebook/*" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
          <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
            <div className="text-[10px] font-bold uppercase text-slate-500">Rule bật</div>
            <div className="text-lg font-black text-slate-900">{enabledCount}/{rules.length}</div>
          </div>
          <div className="rounded-xl border border-blue-100 bg-blue-50 px-3 py-2">
            <div className="text-[10px] font-bold uppercase text-blue-700">Full auto</div>
            <div className="text-lg font-black text-blue-700">{fullAutoCount}</div>
          </div>
        </div>
      </div>

      {killSwitch && (
        <div className="p-3.5 rounded-xl border border-rose-200 bg-rose-50 text-rose-800 text-xs flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>Kill Switch đang bật: engine sẽ không trả lời, không tạo đơn và không gọi GHN.</span>
        </div>
      )}

      {message && (
        <div className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
          message.type === 'success'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : 'bg-rose-50 border-rose-200 text-rose-800'
        }`}>
          {message.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px] gap-5">
        <div className="bg-white border border-slate-200/80 rounded-2xl shadow-2xs overflow-hidden">
          <div className="p-4 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ClipboardList className="w-4 h-4 text-blue-600" />
              Rule theo case
            </h3>
          </div>
          <div className="divide-y divide-slate-100">
            {rules.map((rule) => (
              <div key={rule.id} className="p-4 space-y-3">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-bold text-sm text-slate-900">{caseLabels[rule.case_type] || rule.case_type}</div>
                    <div className="text-[11px] text-slate-500 font-mono truncate">
                      {rule.case_type} · {rule.page_id || '*'} · {rule.channel || '*'}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700">
                      <input
                        type="checkbox"
                        checked={bool(rule.enabled)}
                        onChange={(e) => updateLocalRule(rule.id, { enabled: e.target.checked })}
                        className="rounded border-slate-300"
                      />
                      Bật
                    </label>
                    <button
                      type="button"
                      onClick={() => saveRule(rule)}
                      disabled={!canManage || savingId === rule.id}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 text-white text-xs font-bold hover:bg-slate-800 disabled:opacity-50"
                    >
                      <Save className="w-3.5 h-3.5" />
                      Lưu
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
                  <select
                    value={Number(rule.level || 0)}
                    onChange={(e) => updateLocalRule(rule.id, { level: Number(e.target.value) })}
                    className="px-3 py-2 rounded-xl border border-slate-200 text-xs bg-white"
                  >
                    {[0, 1, 2, 3].map((level) => (
                      <option key={level} value={level}>{level} - {levelLabels[level]}</option>
                    ))}
                  </select>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={Number(rule.min_confidence ?? 0.85)}
                    onChange={(e) => updateLocalRule(rule.id, { min_confidence: Number(e.target.value) })}
                    className="px-3 py-2 rounded-xl border border-slate-200 text-xs"
                    title="Độ tin cậy tối thiểu"
                  />
                  <input
                    type="number"
                    min="0"
                    value={Number(rule.max_cod_amount || 0)}
                    onChange={(e) => updateLocalRule(rule.id, { max_cod_amount: Number(e.target.value) })}
                    className="px-3 py-2 rounded-xl border border-slate-200 text-xs"
                    title="COD tối đa"
                  />
                  <label className="px-3 py-2 rounded-xl border border-slate-200 text-xs flex items-center gap-1.5">
                    <input
                      type="checkbox"
                      checked={bool(rule.require_staff_approval)}
                      onChange={(e) => updateLocalRule(rule.id, { require_staff_approval: e.target.checked })}
                    />
                    Cần duyệt
                  </label>
                </div>
              </div>
            ))}
            {rules.length === 0 && (
              <div className="p-8 text-center text-sm text-slate-500">Chưa có rule. Bấm tải lại hoặc kiểm tra backend.</div>
            )}
          </div>
        </div>

        <div className="space-y-5">
          <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Test một hội thoại</h3>
            <textarea
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm resize-none"
            />
            <button
              type="button"
              onClick={runSimulation}
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-bold hover:bg-blue-700 disabled:opacity-50"
            >
              <Play className="w-4 h-4" />
              Chạy engine
            </button>
            {testResult && (
              <pre className="max-h-72 overflow-auto rounded-xl bg-slate-950 text-slate-100 text-[11px] p-3">
                {JSON.stringify(testResult, null, 2)}
              </pre>
            )}
          </div>

          <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs space-y-3">
            <h3 className="text-sm font-bold text-slate-900">Outbox gần nhất</h3>
            {outbox.map((msg) => (
              <div key={msg.id} className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                <div className="flex items-center justify-between gap-2 text-[11px]">
                  <span className="font-mono text-slate-500">{msg.id}</span>
                  <span className="font-bold text-slate-700">{msg.status}</span>
                </div>
                <p className="text-xs text-slate-700 mt-2 leading-relaxed">{msg.body}</p>
              </div>
            ))}
            {outbox.length === 0 && <div className="text-xs text-slate-500">Chưa có tin nhắn automation nào trong outbox.</div>}
          </div>
        </div>
      </div>
    </div>
  )
}
