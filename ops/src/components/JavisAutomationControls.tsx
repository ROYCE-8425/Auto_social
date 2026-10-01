import React, { useEffect, useState } from 'react'
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  MessageCircle,
  RefreshCw,
  Save,
  ShieldAlert,
} from 'lucide-react'
import { api, CareConfig, CareState } from '../lib/api'
import { useAuth } from '../lib/auth'

const bool = (v: unknown, fallback = false) => {
  if (v === undefined || v === null) return fallback
  return v === true || v === 1 || v === '1' || v === 'true'
}

const modeMeta = {
  suggest: {
    title: 'Nháp chờ duyệt',
    desc: 'Javis chỉ đọc, phân loại và tạo bản nháp. Nhân viên bấm gửi.',
  },
  auto: {
    title: 'Bán tự động',
    desc: 'Javis được gửi các case an toàn như FAQ, lead, báo giá, hỏi thiếu thông tin.',
  },
  full: {
    title: 'Tự động mạnh',
    desc: 'Mở hành động rủi ro cao hơn. Chỉ Owner nên bật khi catalog/rule đã kiểm xong.',
  },
}

type Mode = 'suggest' | 'auto' | 'full'

interface Props {
  initialState: CareState | null
  onSaved?: (state: CareState) => void
}

export const JavisAutomationControls: React.FC<Props> = ({ initialState, onSaved }) => {
  const { role } = useAuth()
  const isOwner = role === 'owner'
  const canManage = role === 'owner' || role === 'manager' || (role as string) === 'admin'

  const [enabled, setEnabled] = useState(false)
  const [mode, setMode] = useState<Mode>('suggest')
  const [pollComments, setPollComments] = useState(true)
  const [pollMessenger, setPollMessenger] = useState(true)
  const [replyComments, setReplyComments] = useState(false)
  const [replyMessenger, setReplyMessenger] = useState(false)
  const [hideSpam, setHideSpam] = useState(false)
  const [killSwitch, setKillSwitch] = useState(false)
  const [quietHours, setQuietHours] = useState('21-07')
  const [pollInterval, setPollInterval] = useState(1)
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const applyConfig = (cfg?: CareConfig) => {
    const c = cfg || {}
    const features = c.features || {}
    setEnabled(bool(c.enabled, false))
    setMode((['suggest', 'auto', 'full'].includes(String(c.mode)) ? c.mode : 'suggest') as Mode)
    setPollComments(bool(features.poll_comments, true))
    setPollMessenger(bool(features.poll_messenger, true))
    setReplyComments(bool(features.auto_reply_comments, false))
    setReplyMessenger(bool(features.auto_reply_messenger, false))
    setHideSpam(bool(features.hide_spam, false))
    setKillSwitch(bool(c.kill_switch, false))
    setQuietHours(String(c.quiet_hours || '21-07'))
    setPollInterval(Number(c.poll_interval_min || 1))
  }

  useEffect(() => {
    applyConfig(initialState?.config)
  }, [initialState])

  const refresh = async () => {
    setLoading(true)
    setMessage(null)
    try {
      const state = await api.getCareState()
      applyConfig(state.config)
      onSaved?.(state)
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.message || 'Không tải được trạng thái Javis' })
    } finally {
      setLoading(false)
    }
  }

  const save = async () => {
    if (!canManage) return
    setSaving(true)
    setMessage(null)
    try {
      const nextMode = !isOwner && mode === 'full' ? 'auto' : mode
      const patch: Partial<CareConfig> = {
        enabled,
        mode: nextMode,
        quiet_hours: quietHours.trim() || '21-07',
        poll_interval_min: Math.max(1, Number(pollInterval || 1)),
        features: {
          poll_comments: pollComments,
          poll_messenger: pollMessenger,
          auto_reply_comments: replyComments,
          auto_reply_messenger: replyMessenger,
          hide_spam: hideSpam,
          crm: true,
          drafts: true,
        },
      }
      if (isOwner) patch.kill_switch = killSwitch

      const res = await api.saveCareSettings(patch)
      const state = await api.getCareState()
      applyConfig(res.config || state.config)
      onSaved?.(state)
      setMessage({ type: 'success', text: 'Đã lưu chế độ làm việc của Javis' })
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.message || 'Không lưu được cấu hình Javis' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs space-y-5">
      <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Bot className="w-5 h-5 text-blue-600" />
            <span>Bảng điều khiển Javis làm việc</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Chọn chế độ, bật/tắt tự động trả lời và dừng khẩn cấp ngay trong Ops.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={refresh}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : ''}`} />
            Tải lại
          </button>
          <button
            type="button"
            onClick={save}
            disabled={!canManage || saving}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-bold hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="w-3.5 h-3.5" />
            {saving ? 'Đang lưu...' : 'Lưu chế độ'}
          </button>
        </div>
      </div>

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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {(['suggest', 'auto', 'full'] as Mode[]).map((m) => {
          const disabled = m === 'full' && !isOwner
          return (
            <button
              key={m}
              type="button"
              onClick={() => !disabled && setMode(m)}
              disabled={disabled}
              className={`text-left rounded-xl border p-4 transition-colors ${
                mode === m
                  ? 'bg-blue-50 border-blue-300 text-blue-900'
                  : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-black">{modeMeta[m].title}</span>
                <span className="text-[10px] font-mono uppercase">{m}</span>
              </div>
              <p className="text-xs mt-2 leading-relaxed text-slate-600">{modeMeta[m].desc}</p>
            </button>
          )
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        <Toggle label="Bật Javis Care" desc="Cho phép poller đọc comment/inbox và xử lý workflow." checked={enabled} onChange={setEnabled} />
        <Toggle label="Quét bình luận" desc="Đọc comment mới từ Fanpage." checked={pollComments} onChange={setPollComments} />
        <Toggle label="Quét Messenger" desc="Đọc hội thoại inbox Facebook." checked={pollMessenger} onChange={setPollMessenger} />
        <Toggle label="Tự trả lời comment" desc="Gửi comment reply khi mode/policy cho phép." checked={replyComments} onChange={setReplyComments} />
        <Toggle label="Tự trả lời Messenger" desc="Cho phép Javis gửi inbox khi case an toàn." checked={replyMessenger} onChange={setReplyMessenger} />
        <Toggle label="Ẩn spam" desc="Ẩn nội dung spam/toxic theo policy." checked={hideSpam} onChange={setHideSpam} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <label className="rounded-xl border border-slate-200 p-3 bg-slate-50">
          <span className="text-[11px] font-bold text-slate-500 uppercase">Giờ im lặng</span>
          <input
            value={quietHours}
            onChange={(e) => setQuietHours(e.target.value)}
            className="mt-2 w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm"
            placeholder="21-07"
          />
        </label>
        <label className="rounded-xl border border-slate-200 p-3 bg-slate-50">
          <span className="text-[11px] font-bold text-slate-500 uppercase">Chu kỳ quét phút</span>
          <input
            type="number"
            min="1"
            value={pollInterval}
            onChange={(e) => setPollInterval(Number(e.target.value))}
            className="mt-2 w-full px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm"
          />
        </label>
        <button
          type="button"
          onClick={() => isOwner && setKillSwitch(!killSwitch)}
          disabled={!isOwner}
          className={`rounded-xl border p-3 text-left transition-colors ${
            killSwitch
              ? 'bg-rose-600 border-rose-600 text-white'
              : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          <span className="flex items-center gap-2 text-sm font-black">
            <ShieldAlert className="w-4 h-4" />
            Kill Switch
          </span>
          <span className={`block text-xs mt-2 ${killSwitch ? 'text-rose-50' : 'text-slate-500'}`}>
            {isOwner ? 'Dừng khẩn cấp mọi hành động tự động.' : 'Chỉ Owner được đổi Kill Switch.'}
          </span>
        </button>
      </div>

      <div className="rounded-xl border border-blue-100 bg-blue-50 p-3 text-xs text-blue-900 flex items-start gap-2">
        <MessageCircle className="w-4 h-4 shrink-0 mt-0.5" />
        <span>
          Lưu ý: mode ở đây quyết định Javis có được gửi tin hay chỉ tạo nháp. Tab Automation quyết định từng case bán hàng cụ thể có được chạy hay không.
        </span>
      </div>
    </div>
  )
}

const Toggle: React.FC<{
  label: string
  desc: string
  checked: boolean
  onChange: (checked: boolean) => void
}> = ({ label, desc, checked, onChange }) => (
  <button
    type="button"
    onClick={() => onChange(!checked)}
    className={`rounded-xl border p-3 text-left transition-colors ${
      checked ? 'bg-emerald-50 border-emerald-200' : 'bg-white border-slate-200 hover:bg-slate-50'
    }`}
  >
    <span className="flex items-center justify-between gap-3">
      <span className="text-sm font-bold text-slate-900">{label}</span>
      <span className={`w-10 h-5 rounded-full p-0.5 transition-colors ${checked ? 'bg-emerald-500' : 'bg-slate-300'}`}>
        <span className={`block w-4 h-4 rounded-full bg-white shadow-sm transition-transform ${checked ? 'translate-x-5' : 'translate-x-0'}`} />
      </span>
    </span>
    <span className="block text-xs text-slate-500 mt-2 leading-relaxed">{desc}</span>
  </button>
)
