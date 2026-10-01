import React, { useState, useEffect } from 'react'
import {
  Share2,
  CheckCircle2,
  AlertCircle,
  Clock,
  ExternalLink,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  XCircle,
  Settings,
  Radio,
  Send,
  MessageSquare,
  Key,
  Database,
  ArrowUpRight,
  Info,
  Layers,
} from 'lucide-react'
import {
  FacebookBadge,
  TikTokBadge,
  InstagramBadge,
  YouTubeBadge,
  XTwitterBadge,
  ZaloBadge,
  FacebookIcon,
  TikTokIcon,
  InstagramIcon,
  YouTubeIcon,
  XTwitterIcon,
  ZaloIcon,
  PlatformBadge,
  PlatformPill,
} from './BrandIcons'
import {
  api,
  TikTokStatusResponse,
  FacebookStatusResponse,
  ChannelsStatusResponse,
  ChannelInfoItem,
  PostPeerAccount,
} from '../lib/api'
import { useAuth } from '../lib/auth'
export function getSocialProfileUrl(platform: string, identifier?: string): string {
  const p = (platform || '').toLowerCase()
  const clean = (identifier || '').replace(/^@/, '').trim()
  if (p === 'tiktok') {
    return `https://www.tiktok.com/@${clean || 'seotrum'}`
  }
  if (p === 'twitter' || p === 'x') {
    return `https://x.com/${clean || 'RoyceDaiDe'}`
  }
  if (p === 'instagram') {
    return `https://www.instagram.com/${clean || 'trannhuy.inf'}/`
  }
  if (p === 'youtube') {
    return `https://www.youtube.com/@${clean || 'trannhuy4641'}`
  }
  if (p === 'facebook') {
    if (/^\d+$/.test(clean) || /^[a-zA-Z0-9.]+$/.test(clean)) {
      return `https://www.facebook.com/${clean}`
    }
    return 'https://www.facebook.com/343562028848465'
  }
  if (p === 'zalo') {
    return clean ? `https://zalo.me/${clean}` : 'https://zalo.me/0877104996'
  }
  return '#'
}

export const PlatformConnections: React.FC = () => {
  const { role } = useAuth()
  const [tiktokData, setTiktokData] = useState<TikTokStatusResponse | null>(null)
  const [facebookData, setFacebookData] = useState<FacebookStatusResponse | null>(null)
  const [channelsData, setChannelsData] = useState<ChannelsStatusResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string>('')

  // Modal nạp/cập nhật API Key PostPeer
  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false)
  const [inputKey, setInputKey] = useState('')
  const [isSavingKey, setIsSavingKey] = useState(false)
  const [keyErrorMsg, setKeyErrorMsg] = useState<string | null>(null)
  const [keySuccessMsg, setKeySuccessMsg] = useState<string | null>(null)

  const handleSavePostPeerKey = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputKey.trim()) return
    setIsSavingKey(true)
    setKeyErrorMsg(null)
    setKeySuccessMsg(null)
    try {
      const res = await api.savePostPeerKey(inputKey.trim())
      if (res.ok) {
        setKeySuccessMsg(res.message || 'Cập nhật API Key PostPeer thành công!')
        setInputKey('')
        setTimeout(() => {
          setIsKeyModalOpen(false)
          setKeySuccessMsg(null)
        }, 1200)
        await loadData()
      } else {
        setKeyErrorMsg(res.error || 'Không thể lưu key.')
      }
    } catch (err: any) {
      setKeyErrorMsg(err?.message || 'Lỗi khi lưu key PostPeer.')
    } finally {
      setIsSavingKey(false)
    }
  }

  const loadData = async () => {
    setIsLoading(true)
    setErrorMsg(null)
    try {
      const [channelsRes, fbRes, ttRes] = await Promise.allSettled([
        api.getChannelsStatus(),
        api.getFacebookStatus(),
        api.getTikTokStatus(),
      ])

      if (channelsRes.status === 'fulfilled' && channelsRes.value && channelsRes.value.ok) {
        setChannelsData(channelsRes.value)
        setFacebookData(channelsRes.value.facebook)
        setTiktokData(channelsRes.value.tiktok)
      } else {
        if (fbRes.status === 'fulfilled' && fbRes.value) {
          setFacebookData(fbRes.value)
        }
        if (ttRes.status === 'fulfilled' && ttRes.value) {
          setTiktokData(ttRes.value)
        }
      }
      const now = new Date()
      setLastRefreshedAt(
        `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
      )
    } catch (err: any) {
      setErrorMsg(err?.message || 'Không thể đồng bộ trạng thái kênh.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Trích xuất toàn bộ tài khoản kết nối qua cổng PostPeer Gateway
  const postpeerAccounts: PostPeerAccount[] =
    channelsData?.postpeer?.accounts || (tiktokData?.accounts as PostPeerAccount[]) || []
  const postpeerConnected = Boolean(channelsData?.postpeer?.connected || tiktokData?.connected)
  const postpeerMaskedKey = channelsData?.postpeer?.masked_key || tiktokData?.masked_key || ''

  const xAccount = postpeerAccounts.find((a) => a.platform === 'twitter' || a.platform === 'x')
  const igAccount = postpeerAccounts.find((a) => a.platform === 'instagram')
  const ytAccount = postpeerAccounts.find((a) => a.platform === 'youtube')
  const ttAccount = postpeerAccounts.find((a) => a.platform === 'tiktok')

  // Đếm các kênh kết nối thật: Facebook + TikTok + X + Instagram + YouTube
  const totalRealPages = facebookData?.pages?.length || 0
  const totalPostpeerAccounts = postpeerAccounts.length
  const connectedPlatforms = [
    facebookData?.connected ? 'facebook' : null,
    ttAccount ? 'tiktok' : null,
    xAccount ? 'twitter' : null,
    igAccount ? 'instagram' : null,
    ytAccount ? 'youtube' : null,
  ].filter(Boolean)
  const connectedCount = connectedPlatforms.length

  return (
    <div className="space-y-6">
      {/* ================= SECTION HEADER ================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center space-x-2">
              <Share2 className="w-5 h-5 text-blue-600" />
              <span>Kết Nối Nền Tảng (Platform Connectors)</span>
            </h2>
            <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-[10px] font-bold border border-blue-200">
              Gateway &amp; API Thật
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Minh bạch từng năng lực kết nối: tài khoản, hộp thư/inbox, đăng bài xuất bản, cơ chế đồng bộ và hành động cần cấu hình.
          </p>
        </div>

        <div className="flex items-center space-x-2.5 shrink-0">
          {lastRefreshedAt && (
            <span className="text-[11px] text-slate-400 font-mono hidden md:inline">
              Cập nhật lúc {lastRefreshedAt}
            </span>
          )}
          <button
            type="button"
            onClick={loadData}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-blue-600' : ''}`} />
            <span>Đồng bộ trạng thái</span>
          </button>
          <a
            href="/hub/mcp"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-2xs transition-colors"
          >
            <span>Hub MCP</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 text-xs text-rose-700 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* ================= OVERVIEW METRICS STRIP ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Metric 1 */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Kênh API &amp; Gateway hoạt động</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">
              <span className="text-emerald-600">{connectedCount}</span>
              <span className="text-slate-400 text-sm font-normal"> / 5 nền tảng</span>
            </div>
            <div className="flex items-center gap-1.5 mt-2">
              <FacebookBadge size="sm" />
              <TikTokBadge size="sm" />
              <XTwitterBadge size="sm" />
              <InstagramBadge size="sm" />
              <YouTubeBadge size="sm" />
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold self-start">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Fanpages Facebook (Meta Graph)</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">
              <span className="text-blue-600">{totalRealPages}</span>
              <span className="text-slate-400 text-sm font-normal"> trang quản lý</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-2 truncate">
              {facebookData?.pages?.map((p) => p.name).join(', ') || 'Chưa nạp Token'}
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold self-start">
            <FacebookIcon className="w-5 h-5 text-[#1877F2]" />
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Tài khoản PostPeer Gateway</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">
              <span className="text-purple-600">{totalPostpeerAccounts}</span>
              <span className="text-slate-400 text-sm font-normal"> tài khoản OAuth</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-2 flex items-center gap-2">
              <span className="font-semibold text-slate-700">TikTok, X, Instagram, YouTube</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold self-start">
            <Layers className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* ================= CAPABILITIES MATRIX TABLE ================= */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden">
        <div className="p-4 bg-slate-50/80 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
              <Database className="w-4 h-4 text-blue-600" />
              <span>Ma Trận Năng Lực Kết Nối (Capabilities Matrix)</span>
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Định nghĩa chuẩn xác từng khả năng vận hành của từng cổng kết nối ngoại vi.
            </p>
          </div>
          <span className="text-[11px] text-slate-400 italic">
            Không sử dụng dữ liệu giả lập
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-100/60 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200 text-[10px]">
              <tr>
                <th className="py-3 px-4">Nền tảng</th>
                <th className="py-3 px-3">Tài khoản (Account)</th>
                <th className="py-3 px-3">Hộp thư (Inbox)</th>
                <th className="py-3 px-3">Xuất bản (Publishing)</th>
                <th className="py-3 px-3">Đồng bộ (Webhook/Polling)</th>
                <th className="py-3 px-3">Lần đồng bộ gần nhất</th>
                <th className="py-3 px-4 text-right">Hành động yêu cầu</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {/* Row 1: Facebook */}
              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3.5 px-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2.5">
                    <FacebookBadge size="sm" />
                    <div>
                      <div className="font-bold text-slate-900">Facebook &amp; Messenger</div>
                      <span className="text-[10px] text-slate-400 font-mono">Meta Graph v25.0</span>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  {facebookData?.connected && facebookData.pages && facebookData.pages.length > 0 ? (
                    <div className="flex flex-col gap-1.5 py-0.5">
                      {facebookData.pages.map((p) => (
                        <a
                          key={p.id}
                          href={`https://www.facebook.com/${p.id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          title={`Mở Fanpage ${p.name} trên Facebook`}
                          className="inline-flex items-center space-x-1.5 text-blue-700 bg-blue-50/90 hover:bg-blue-100 hover:text-blue-900 px-2 py-0.5 rounded-lg text-[11px] font-bold border border-blue-200 transition-all shadow-2xs group"
                        >
                          <FacebookIcon className="w-3 h-3 shrink-0" />
                          <span className="truncate max-w-[140px] group-hover:underline">{p.name}</span>
                          <ExternalLink className="w-2.5 h-2.5 opacity-60 group-hover:opacity-100 shrink-0 text-blue-600" />
                        </a>
                      ))}
                    </div>
                  ) : facebookData?.connected ? (
                    <span className="inline-flex items-center space-x-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full text-[11px] font-bold border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      <span>{totalRealPages} Trang nạp Token</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1 text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full text-[11px] border border-slate-200">
                      <XCircle className="w-3 h-3 text-slate-400" />
                      <span>Chưa nạp Token</span>
                    </span>
                  )}
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  {facebookData?.fanpage_care_enabled ? (
                    <span className="inline-flex items-center space-x-1 text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full text-[11px] font-bold border border-blue-200">
                      <MessageSquare className="w-3 h-3 text-blue-600" />
                      <span>Hỗ trợ thật (Fanpage Care)</span>
                    </span>
                  ) : (
                    <span className="text-slate-400 text-[11px]">Tắt</span>
                  )}
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center space-x-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full text-[11px] font-bold border border-emerald-200">
                    <Send className="w-3 h-3 text-emerald-600" />
                    <span>Bài viết &amp; Album ảnh</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap font-mono text-[11px]">
                  <span>Polling ({facebookData?.poll_interval_seconds || 60}s/lần)</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-700 font-mono text-[11px]">
                  {facebookData?.last_poll || 'Chưa ghi nhận'}
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap">
                  <div className="flex items-center justify-end space-x-2">
                    {facebookData?.connected && facebookData.pages?.[0] ? (
                      <a
                        href={`https://www.facebook.com/${facebookData.pages[0].id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        title="Mở Fanpage trên Facebook"
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 shadow-2xs transition-colors"
                      >
                        <span>Mở Trang</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <a
                        href="/hub/mcp"
                        className="text-blue-600 hover:text-blue-700 font-bold inline-flex items-center space-x-1"
                      >
                        <span>Nạp Page Token</span>
                        <ArrowUpRight className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </td>
              </tr>

              {/* Row 2: TikTok */}
              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3.5 px-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2.5">
                    <TikTokBadge size="sm" />
                    <div>
                      <div className="font-bold text-slate-900">TikTok Video &amp; Carousel</div>
                      <span className="text-[10px] text-slate-400 font-mono">PostPeer Gateway</span>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  {ttAccount ? (
                    <a
                      href={getSocialProfileUrl('tiktok', ttAccount.username || ttAccount.name)}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={`Mở trang TikTok @${(ttAccount.username || ttAccount.name).replace(/^@/, '')}`}
                      className="inline-flex items-center space-x-1.5 text-emerald-800 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 rounded-lg text-[11px] font-bold border border-emerald-200 transition-all shadow-2xs group"
                    >
                      <TikTokIcon className="w-3 h-3 shrink-0" />
                      <span className="group-hover:underline">@{ (ttAccount.username || ttAccount.name).replace(/^@/, '') }</span>
                      <ExternalLink className="w-2.5 h-2.5 opacity-60 group-hover:opacity-100 shrink-0 text-emerald-700" />
                    </a>
                  ) : (
                    <span className="inline-flex items-center space-x-1 text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full text-[11px] border border-rose-200">
                      <XCircle className="w-3 h-3 text-rose-500" />
                      <span>Chưa kết nối</span>
                    </span>
                  )}
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center space-x-1 text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                    <span>Không hỗ trợ</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center space-x-1 text-purple-700 bg-purple-50 px-2 py-0.5 rounded-full text-[11px] font-bold border border-purple-200">
                    <Send className="w-3 h-3 text-purple-600" />
                    <span>Hỗ trợ thật (Video/Photos)</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap font-mono text-[11px]">
                  <span>PostPeer Gateway API</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-700 font-mono text-[11px]">
                  {postpeerConnected ? 'Đang hoạt động' : 'Chưa ghi nhận'}
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap">
                  <div className="flex items-center justify-end space-x-2">
                    {ttAccount ? (
                      <a
                        href={getSocialProfileUrl('tiktok', ttAccount.username || ttAccount.name)}
                        target="_blank"
                        rel="noopener noreferrer"
                        title="Mở trang TikTok trong tab mới"
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-bold text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-300 shadow-2xs transition-colors"
                      >
                        <span>Mở TikTok</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-slate-400 text-[11px]">Chưa kết nối</span>
                    )}
                  </div>
                </td>
              </tr>

              {/* Row 3: X (Twitter) */}
              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3.5 px-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2.5">
                    <XTwitterBadge size="sm" />
                    <div>
                      <div className="font-bold text-slate-900">X (Twitter) Tweet &amp; Media</div>
                      <span className="text-[10px] text-slate-400 font-mono">PostPeer Gateway</span>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  {xAccount ? (
                    <a
                      href={getSocialProfileUrl('x', xAccount.username || xAccount.name)}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={`Mở trang X (Twitter) @${(xAccount.username || xAccount.name).replace(/^@/, '')}`}
                      className="inline-flex items-center space-x-1.5 text-slate-900 bg-slate-100 hover:bg-slate-200 px-2.5 py-1 rounded-lg text-[11px] font-bold border border-slate-300 transition-all shadow-2xs group"
                    >
                      <XTwitterIcon className="w-3 h-3 shrink-0" />
                      <span className="group-hover:underline">@{ (xAccount.username || xAccount.name).replace(/^@/, '') }</span>
                      <ExternalLink className="w-2.5 h-2.5 opacity-60 group-hover:opacity-100 shrink-0 text-slate-800" />
                    </a>
                  ) : (
                    <span className="inline-flex items-center space-x-1 text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                      <span>Chưa kết nối</span>
                    </span>
                  )}
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center space-x-1 text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                    <span>Không hỗ trợ</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center space-x-1 text-slate-900 bg-slate-100 px-2 py-0.5 rounded-full text-[11px] font-bold border border-slate-300">
                    <Send className="w-3 h-3 text-slate-800" />
                    <span>Hỗ trợ thật (Tweet/Media)</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap font-mono text-[11px]">
                  <span>PostPeer Gateway API</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-700 font-mono text-[11px]">
                  {xAccount ? 'Đang hoạt động' : 'Chưa ghi nhận'}
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap">
                  <div className="flex items-center justify-end space-x-2">
                    {xAccount ? (
                      <a
                        href={getSocialProfileUrl('x', xAccount.username || xAccount.name)}
                        target="_blank"
                        rel="noopener noreferrer"
                        title="Mở trang X trong tab mới"
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-bold text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-300 shadow-2xs transition-colors"
                      >
                        <span>Mở X</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-slate-400 text-[11px]">Chưa kết nối</span>
                    )}
                  </div>
                </td>
              </tr>

              {/* Row 4: Instagram */}
              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3.5 px-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2.5">
                    <InstagramBadge size="sm" />
                    <div>
                      <div className="font-bold text-slate-900">Instagram Photo &amp; Reels</div>
                      <span className="text-[10px] text-slate-400 font-mono">PostPeer Gateway</span>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  {igAccount ? (
                    <a
                      href={getSocialProfileUrl('instagram', igAccount.username || igAccount.name)}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={`Mở trang Instagram @${(igAccount.username || igAccount.name).replace(/^@/, '')}`}
                      className="inline-flex items-center space-x-1.5 text-rose-800 bg-rose-50 hover:bg-rose-100 px-2.5 py-1 rounded-lg text-[11px] font-bold border border-rose-200 transition-all shadow-2xs group"
                    >
                      <InstagramIcon className="w-3 h-3 shrink-0" />
                      <span className="group-hover:underline">@{ (igAccount.username || igAccount.name).replace(/^@/, '') }</span>
                      <ExternalLink className="w-2.5 h-2.5 opacity-60 group-hover:opacity-100 shrink-0 text-rose-700" />
                    </a>
                  ) : (
                    <span className="inline-flex items-center space-x-1 text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                      <span>Chưa kết nối</span>
                    </span>
                  )}
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="text-slate-400 text-[11px]">Không hỗ trợ</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center space-x-1 text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full text-[11px] font-bold border border-rose-200">
                    <Send className="w-3 h-3 text-rose-600" />
                    <span>Hỗ trợ thật (Ảnh/Reels)</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap font-mono text-[11px]">
                  <span>PostPeer Gateway API</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-700 font-mono text-[11px]">
                  {igAccount ? 'Đang hoạt động' : 'Chưa ghi nhận'}
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap">
                  <div className="flex items-center justify-end space-x-2">
                    {igAccount ? (
                      <a
                        href={getSocialProfileUrl('instagram', igAccount.username || igAccount.name)}
                        target="_blank"
                        rel="noopener noreferrer"
                        title="Mở trang Instagram trong tab mới"
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 shadow-2xs transition-colors"
                      >
                        <span>Mở Instagram</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-slate-400 text-[11px]">Chưa kết nối</span>
                    )}
                  </div>
                </td>
              </tr>

              {/* Row 5: YouTube */}
              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3.5 px-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2.5">
                    <YouTubeBadge size="sm" />
                    <div>
                      <div className="font-bold text-slate-900">YouTube Shorts &amp; Video</div>
                      <span className="text-[10px] text-slate-400 font-mono">PostPeer Gateway</span>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  {ytAccount ? (
                    <a
                      href={getSocialProfileUrl('youtube', ytAccount.username || ytAccount.name)}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={`Mở kênh YouTube @${(ytAccount.username || ytAccount.name).replace(/^@/, '')}`}
                      className="inline-flex items-center space-x-1.5 text-red-800 bg-red-50 hover:bg-red-100 px-2.5 py-1 rounded-lg text-[11px] font-bold border border-red-200 transition-all shadow-2xs group"
                    >
                      <YouTubeIcon className="w-3 h-3 shrink-0" />
                      <span className="group-hover:underline">@{ (ytAccount.username || ytAccount.name).replace(/^@/, '') }</span>
                      <ExternalLink className="w-2.5 h-2.5 opacity-60 group-hover:opacity-100 shrink-0 text-red-700" />
                    </a>
                  ) : (
                    <span className="inline-flex items-center space-x-1 text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                      <span>Chưa kết nối</span>
                    </span>
                  )}
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="text-slate-400 text-[11px]">Không hỗ trợ</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center space-x-1 text-red-700 bg-red-50 px-2 py-0.5 rounded-full text-[11px] font-bold border border-red-200">
                    <Send className="w-3 h-3 text-red-600" />
                    <span>Hỗ trợ thật (Shorts/Video)</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap font-mono text-[11px]">
                  <span>PostPeer Gateway API</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-700 font-mono text-[11px]">
                  {ytAccount ? 'Đang hoạt động' : 'Chưa ghi nhận'}
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap">
                  <div className="flex items-center justify-end space-x-2">
                    {ytAccount ? (
                      <a
                        href={getSocialProfileUrl('youtube', ytAccount.username || ytAccount.name)}
                        target="_blank"
                        rel="noopener noreferrer"
                        title="Mở kênh YouTube trong tab mới"
                        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-bold text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 shadow-2xs transition-colors"
                      >
                        <span>Mở YouTube</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="text-slate-400 text-[11px]">Chưa kết nối</span>
                    )}
                  </div>
                </td>
              </tr>

              {/* Row 6: Zalo */}
              <tr className="hover:bg-slate-50/60 transition-colors opacity-95">
                <td className="py-3.5 px-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2.5">
                    <ZaloBadge size="sm" />
                    <div>
                      <div className="font-bold text-slate-900">Zalo OA &amp; Cá nhân</div>
                      <span className="text-[10px] text-slate-400 font-mono">Zalo Agent MCP</span>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <a
                    href="https://zalo.me/0877104996"
                    target="_blank"
                    rel="noopener noreferrer"
                    title="Mở Zalo CSKH (0877 104 996)"
                    className="inline-flex items-center space-x-1.5 text-blue-800 bg-blue-50 hover:bg-blue-100 px-2.5 py-1 rounded-lg text-[11px] font-bold border border-blue-200 transition-all shadow-2xs group"
                  >
                    <ZaloIcon className="w-3 h-3 shrink-0" />
                    <span className="group-hover:underline">Zalo: 0877 104 996</span>
                    <ExternalLink className="w-2.5 h-2.5 opacity-60 group-hover:opacity-100 shrink-0 text-blue-700" />
                  </a>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="text-blue-600 text-[11px] font-semibold">Chăm sóc tin nhắn MCP</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="text-slate-400 text-[11px]">Chưa hỗ trợ</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap font-mono text-[11px]">
                  <span>Local Agent stdio</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-700 font-mono text-[11px]">
                  Sẵn sàng khi gọi
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap">
                  <div className="flex items-center justify-end space-x-2">
                    <a
                      href="https://zalo.me/0877104996"
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Mở chat Zalo"
                      className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 shadow-2xs transition-colors"
                    >
                      <span>Mở Zalo</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* ================= DETAILED CONNECTOR CARDS ================= */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* --- 1. FACEBOOK DETAILED CARD --- */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-4">
          <div className="space-y-3.5">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <FacebookBadge size="md" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">
                    Facebook &amp; Messenger Connector
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Meta Pages Graph API v25.0
                  </span>
                </div>
              </div>

              {facebookData?.connected ? (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Đang kết nối</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-bold border border-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  <span>Chưa kết nối</span>
                </span>
              )}
            </div>

            {/* Capability Badges */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-blue-600 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Hộp thư &amp; Bình luận</div>
                  <div className="font-bold text-slate-800">
                    {facebookData?.fanpage_care_enabled ? 'Hỗ trợ thật (Đang bật)' : 'Đang tắt'}
                  </div>
                </div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <Send className="w-4 h-4 text-blue-600 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Xuất bản bài viết</div>
                  <div className="font-bold text-slate-800">
                    {facebookData?.connected ? 'Hỗ trợ thật (Bài/Album)' : 'Chưa kích hoạt'}
                  </div>
                </div>
              </div>
            </div>

            {/* Config Info */}
            <div className="space-y-1.5 text-xs text-slate-600 bg-slate-50/50 p-3 rounded-xl border border-slate-100">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Quyền hạn API (Permissions):</span>
                <span className="font-semibold text-slate-800 uppercase">
                  {facebookData?.permissions || '—'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Chu kỳ đồng bộ (Polling):</span>
                <span className="font-mono text-slate-700">
                  {facebookData?.poll_interval_seconds || 60}s/lần
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Lần đồng bộ gần nhất:</span>
                <span className="font-mono text-slate-700">
                  {facebookData?.last_poll || 'Chưa ghi nhận'}
                </span>
              </div>
            </div>

            {/* Connected Facebook Pages */}
            <div className="space-y-1.5">
              <div className="text-xs font-bold text-slate-800 flex items-center justify-between">
                <span>Fanpages được quản lý ({totalRealPages})</span>
                {facebookData?.connected && (
                  <span className="text-[10px] text-emerald-600 font-normal">Token hợp lệ</span>
                )}
              </div>
              {facebookData?.pages && facebookData.pages.length > 0 ? (
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                  {facebookData.pages.map((p) => (
                    <a
                      key={p.id}
                      href={`https://www.facebook.com/${p.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-slate-50 hover:bg-blue-50/80 p-2 rounded-xl border border-slate-200/70 hover:border-blue-300 text-xs flex items-center justify-between transition-colors group cursor-pointer"
                      title="Mở Fanpage trên Facebook"
                    >
                      <div className="font-semibold text-slate-900 group-hover:text-blue-600 flex items-center space-x-1.5 min-w-0">
                        <span className="truncate">{p.name}</span>
                        <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-blue-600 shrink-0" />
                      </div>
                      <span className="font-mono text-[10px] text-slate-400 group-hover:text-blue-500 shrink-0 ml-2">
                        ID: {p.id}
                      </span>
                    </a>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center">
                  Chưa nạp Page Access Token trong Javis/page_tokens.json
                </div>
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            {facebookData?.pages && facebookData.pages.length > 0 ? (
              <a
                href={`https://www.facebook.com/${facebookData.pages[0].id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-2.5 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold border border-blue-200 transition-colors inline-flex items-center space-x-1.5 cursor-pointer shadow-2xs"
              >
                <span>Mở Page ({facebookData.pages[0].name.slice(0, 14)}...)</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            ) : (
              <span className="text-slate-400">Nguồn: Meta Graph API</span>
            )}
            <a
              href="/hub/mcp"
              className="text-blue-600 hover:text-blue-700 font-bold inline-flex items-center space-x-1"
            >
              <span>Quản lý Token</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* --- 2. POSTPEER MULTI-PLATFORM GATEWAY CARD --- */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-4">
          <div className="space-y-3.5">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-pink-500 text-white flex items-center justify-center font-black shadow-sm">
                  PP
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">
                    PostPeer Social Gateway API
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Multi-Platform Distribution Hub
                  </span>
                </div>
              </div>

              {postpeerConnected ? (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Đã kết nối {totalPostpeerAccounts} tài khoản</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 text-xs font-bold border border-rose-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                  <span>Chưa kết nối</span>
                </span>
              )}
            </div>

            {/* Capability Badges */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <Send className="w-4 h-4 text-purple-600 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Xuất bản đa kênh</div>
                  <div className="font-bold text-slate-800">
                    {postpeerConnected ? 'TikTok, X, Instagram, YouTube' : 'Chưa kích hoạt'}
                  </div>
                </div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <Radio className="w-4 h-4 text-emerald-600 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Daily Loop phát hành</div>
                  <div className="font-bold text-emerald-700">
                    {tiktokData?.loop?.enabled ? 'Đang bật' : 'Tắt'}
                  </div>
                </div>
              </div>
            </div>

            {/* Config Info */}
            <div className="space-y-1.5 text-xs text-slate-600 bg-slate-50/50 p-3 rounded-xl border border-slate-100">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">PostPeer Access Key:</span>
                <span className="font-mono text-slate-700">
                  {postpeerMaskedKey || 'Chưa cấu hình'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">OAuth Provider:</span>
                <span className="font-semibold text-slate-800">PostPeer Gateway API v1</span>
              </div>
            </div>

            {/* Connected PostPeer Accounts List */}
            <div className="space-y-2">
              <div className="text-xs font-bold text-slate-800 flex items-center justify-between">
                <span>Tài khoản mạng xã hội OAuth ({totalPostpeerAccounts})</span>
                <span className="text-[10px] text-emerald-600 font-normal">Đã xác thực</span>
              </div>

              {postpeerAccounts && postpeerAccounts.length > 0 ? (
                <div className="space-y-2">
                  {postpeerAccounts.map((acc) => {
                    const platformNorm = (acc.platform || '').toLowerCase()
                    const isTwitter = platformNorm === 'twitter' || platformNorm === 'x'
                    const isInstagram = platformNorm === 'instagram'
                    const isYouTube = platformNorm === 'youtube'
                    const isTikTok = platformNorm === 'tiktok'

                    const profileUrl = getSocialProfileUrl(acc.platform, acc.username || acc.name)
                    return (
                      <div
                        key={acc.id}
                        className="bg-slate-50/90 hover:bg-slate-100/80 p-2.5 rounded-xl border border-slate-200/80 flex items-center justify-between gap-3 transition-colors"
                      >
                        <div className="flex items-center space-x-2.5 min-w-0">
                          {isTwitter && <XTwitterBadge size="sm" />}
                          {isInstagram && <InstagramBadge size="sm" />}
                          {isYouTube && <YouTubeBadge size="sm" />}
                          {isTikTok && <TikTokBadge size="sm" />}
                          {!isTwitter && !isInstagram && !isYouTube && !isTikTok && (
                            <PlatformBadge platform={acc.platform} size="sm" />
                          )}
                          <div className="min-w-0">
                            <a
                              href={profileUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-bold text-slate-900 hover:text-purple-600 text-xs truncate flex items-center space-x-1 cursor-pointer group"
                              title={`Mở trang ${acc.platform}`}
                            >
                              <span className="truncate">{acc.username || acc.name}</span>
                              <ExternalLink className="w-3 h-3 text-slate-400 group-hover:text-purple-600 shrink-0" />
                            </a>
                            <div className="text-[10px] text-slate-400 font-mono truncate">
                              ID: {acc.id}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-2 shrink-0">
                          <PlatformPill platform={acc.platform} className="text-[10px] py-0.5 px-2" />
                          <a
                            href={profileUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[10px] text-purple-700 bg-purple-50 hover:bg-purple-100 px-2 py-0.5 rounded-full font-bold border border-purple-200 inline-flex items-center space-x-1 transition-colors cursor-pointer"
                          >
                            <span>Mở trang</span>
                            <ExternalLink className="w-2.5 h-2.5" />
                          </a>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center">
                  Chưa có tài khoản nào được kết nối qua PostPeer
                </div>
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <button
              type="button"
              onClick={() => {
                setIsKeyModalOpen(true)
                setKeyErrorMsg(null)
                setKeySuccessMsg(null)
              }}
              className="px-2.5 py-1.5 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-700 font-semibold border border-purple-200 transition-colors inline-flex items-center space-x-1.5 cursor-pointer shadow-2xs"
            >
              <Key className="w-3.5 h-3.5 text-purple-600" />
              <span>Cập nhật API Key</span>
            </button>
            <a
              href="/app"
              className="text-purple-600 hover:text-purple-700 font-bold inline-flex items-center space-x-1"
            >
              <span>Mở Buồng lái /app</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* --- 3. TIKTOK DETAILED CARD --- */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-4">
          <div className="space-y-3.5">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <TikTokBadge size="md" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">
                    TikTok Connector
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    PostPeer Content Distribution API
                  </span>
                </div>
              </div>

              {ttAccount ? (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Đã kết nối</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-bold border border-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  <span>Chưa kết nối</span>
                </span>
              )}
            </div>

            {/* Capability Badges */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <Send className="w-4 h-4 text-black shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Xuất bản nội dung</div>
                  <div className="font-bold text-slate-800">
                    {ttAccount ? 'Video & Carousel (Sẵn sàng)' : 'Chưa kích hoạt'}
                  </div>
                </div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-slate-400 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Hộp thư &amp; Bình luận</div>
                  <div className="font-bold text-slate-500">Không hỗ trợ (Chưa có API)</div>
                </div>
              </div>
            </div>

            {/* Account Info Box */}
            {ttAccount ? (
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Tài khoản TikTok OAuth:</span>
                  <a
                    href={getSocialProfileUrl('tiktok', ttAccount.username || ttAccount.name)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-slate-900 hover:text-black inline-flex items-center space-x-1 cursor-pointer underline decoration-dotted"
                  >
                    <span>{ttAccount.username || ttAccount.name}</span>
                    <ExternalLink className="w-3 h-3 text-slate-500" />
                  </a>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Account ID:</span>
                  <span className="font-mono text-slate-600">{ttAccount.id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Trạng thái:</span>
                  <span className="text-emerald-700 font-semibold">{ttAccount.status || 'Active'}</span>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center">
                Chưa có tài khoản TikTok nào được liên kết qua PostPeer
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <a
              href={getSocialProfileUrl('tiktok', ttAccount ? (ttAccount.username || ttAccount.name) : 'seotrum')}
              target="_blank"
              rel="noopener noreferrer"
              className="px-2.5 py-1.5 rounded-xl bg-slate-900 hover:bg-black text-white font-semibold transition-colors inline-flex items-center space-x-1.5 cursor-pointer shadow-2xs"
            >
              <span>Mở trang TikTok</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <span className="text-emerald-600 font-semibold">Sẵn sàng xuất bản</span>
          </div>
        </div>

        {/* --- 4. X (TWITTER) DETAILED CARD --- */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-4">
          <div className="space-y-3.5">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <XTwitterBadge size="md" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">
                    X (Twitter) Connector
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    PostPeer Content Distribution API
                  </span>
                </div>
              </div>

              {xAccount ? (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Đã kết nối</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-bold border border-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  <span>Chưa kết nối</span>
                </span>
              )}
            </div>

            {/* Capability Badges */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <Send className="w-4 h-4 text-black shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Xuất bản bài viết</div>
                  <div className="font-bold text-slate-800">
                    {xAccount ? 'Tweet & Media (Sẵn sàng)' : 'Chưa kích hoạt'}
                  </div>
                </div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-slate-400 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Hộp thư &amp; DM</div>
                  <div className="font-bold text-slate-500">Không hỗ trợ (Chưa có API)</div>
                </div>
              </div>
            </div>

            {/* Account Info Box */}
            {xAccount ? (
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Tài khoản X OAuth:</span>
                  <a
                    href={getSocialProfileUrl('twitter', xAccount.username || xAccount.name)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-slate-900 hover:text-black inline-flex items-center space-x-1 cursor-pointer underline decoration-dotted"
                  >
                    <span>{xAccount.username || xAccount.name}</span>
                    <ExternalLink className="w-3 h-3 text-slate-500" />
                  </a>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Account ID:</span>
                  <span className="font-mono text-slate-600">{xAccount.id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Trạng thái:</span>
                  <span className="text-emerald-700 font-semibold">{xAccount.status || 'Active'}</span>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center">
                Chưa có tài khoản X (Twitter) nào được liên kết qua PostPeer
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <a
              href={getSocialProfileUrl('twitter', xAccount ? (xAccount.username || xAccount.name) : 'RoyceDaiDe')}
              target="_blank"
              rel="noopener noreferrer"
              className="px-2.5 py-1.5 rounded-xl bg-slate-900 hover:bg-black text-white font-semibold transition-colors inline-flex items-center space-x-1.5 cursor-pointer shadow-2xs"
            >
              <span>Mở trang X</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <span className="text-emerald-600 font-semibold">Sẵn sàng xuất bản</span>
          </div>
        </div>

        {/* --- 5. INSTAGRAM DETAILED CARD --- */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-4">
          <div className="space-y-3.5">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <InstagramBadge size="md" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">
                    Instagram Connector
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    PostPeer Content Distribution API
                  </span>
                </div>
              </div>

              {igAccount ? (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Đã kết nối</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-bold border border-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  <span>Chưa kết nối</span>
                </span>
              )}
            </div>

            {/* Capability Badges */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <Send className="w-4 h-4 text-rose-600 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Xuất bản bài viết</div>
                  <div className="font-bold text-slate-800">
                    {igAccount ? 'Ảnh & Reels (Sẵn sàng)' : 'Chưa kích hoạt'}
                  </div>
                </div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-slate-400 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Direct Message (DM)</div>
                  <div className="font-bold text-slate-500">Không hỗ trợ (Chưa có API)</div>
                </div>
              </div>
            </div>

            {/* Account Info Box */}
            {igAccount ? (
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Tài khoản Instagram:</span>
                  <a
                    href={getSocialProfileUrl('instagram', igAccount.username || igAccount.name)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-slate-900 hover:text-pink-600 inline-flex items-center space-x-1 cursor-pointer underline decoration-dotted"
                  >
                    <span>{igAccount.username || igAccount.name}</span>
                    <ExternalLink className="w-3 h-3 text-pink-500" />
                  </a>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Account ID:</span>
                  <span className="font-mono text-slate-600">{igAccount.id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Trạng thái:</span>
                  <span className="text-emerald-700 font-semibold">{igAccount.status || 'Active'}</span>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center">
                Chưa có tài khoản Instagram nào được liên kết qua PostPeer
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <a
              href={getSocialProfileUrl('instagram', igAccount ? (igAccount.username || igAccount.name) : 'trannhuy.inf')}
              target="_blank"
              rel="noopener noreferrer"
              className="px-2.5 py-1.5 rounded-xl bg-gradient-to-r from-pink-500 to-rose-500 hover:from-pink-600 hover:to-rose-600 text-white font-semibold transition-all inline-flex items-center space-x-1.5 cursor-pointer shadow-2xs"
            >
              <span>Mở trang Instagram</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <span className="text-emerald-600 font-semibold">Sẵn sàng xuất bản</span>
          </div>
        </div>

        {/* --- 6. YOUTUBE SHORTS DETAILED CARD --- */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-4">
          <div className="space-y-3.5">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <YouTubeBadge size="md" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">
                    YouTube Shorts Connector
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    PostPeer Content Distribution API
                  </span>
                </div>
              </div>

              {ytAccount ? (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Đã kết nối</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-bold border border-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                  <span>Chưa kết nối</span>
                </span>
              )}
            </div>

            {/* Capability Badges */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <Send className="w-4 h-4 text-red-600 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Xuất bản video</div>
                  <div className="font-bold text-slate-800">
                    {ytAccount ? 'Shorts & Video (Sẵn sàng)' : 'Chưa kích hoạt'}
                  </div>
                </div>
              </div>
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100 flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-slate-400 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Bình luận kênh</div>
                  <div className="font-bold text-slate-500">Không hỗ trợ (Chưa có API)</div>
                </div>
              </div>
            </div>

            {/* Account Info Box */}
            {ytAccount ? (
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Tài khoản YouTube:</span>
                  <a
                    href={getSocialProfileUrl('youtube', ytAccount.username || ytAccount.name)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-slate-900 hover:text-red-600 inline-flex items-center space-x-1 cursor-pointer underline decoration-dotted"
                  >
                    <span>{ytAccount.username || ytAccount.name}</span>
                    <ExternalLink className="w-3 h-3 text-red-500" />
                  </a>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Channel ID:</span>
                  <span className="font-mono text-slate-600">{ytAccount.id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Trạng thái:</span>
                  <span className="text-emerald-700 font-semibold">{ytAccount.status || 'Active'}</span>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center">
                Chưa có tài khoản YouTube nào được liên kết qua PostPeer
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <a
              href={getSocialProfileUrl('youtube', ytAccount ? (ytAccount.username || ytAccount.name) : 'trannhuy4641')}
              target="_blank"
              rel="noopener noreferrer"
              className="px-2.5 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-semibold transition-colors inline-flex items-center space-x-1.5 cursor-pointer shadow-2xs"
            >
              <span>Mở kênh YouTube</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <span className="text-emerald-600 font-semibold">Sẵn sàng xuất bản</span>
          </div>
        </div>
      </div>

      {/* ================= MODAL CẬP NHẬT API KEY POSTPEER ================= */}
      {isKeyModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
                  <Key className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-sm">Cập nhật PostPeer API Key</h3>
                  <p className="text-[11px] text-slate-500">Kết nối xuất bản TikTok, X, Instagram, YouTube</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsKeyModalOpen(false)}
                className="w-7 h-7 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center transition-colors cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSavePostPeerKey} className="mt-4 space-y-4">
              {keyErrorMsg && (
                <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>{keyErrorMsg}</span>
                </div>
              )}

              {keySuccessMsg && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-700 flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>{keySuccessMsg}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">
                  PostPeer Access / API Key
                </label>
                <input
                  type="password"
                  value={inputKey}
                  onChange={(e) => setInputKey(e.target.value)}
                  placeholder={postpeerMaskedKey ? `Đang dùng: ${postpeerMaskedKey}` : 'Dán API Key tại đây (vd: GzM8...)'}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-purple-500 focus:ring-2 focus:ring-purple-200 text-xs font-mono outline-hidden transition-all"
                  autoFocus
                />
                <p className="text-[11px] text-slate-400 mt-1.5 flex items-center justify-between">
                  <span>Khóa bí mật được mã hóa và lưu an toàn trên máy chủ.</span>
                  <a
                    href="https://postpeer.dev"
                    target="_blank"
                    rel="noreferrer"
                    className="text-purple-600 hover:underline font-medium inline-flex items-center space-x-0.5"
                  >
                    <span>Lấy key tại PostPeer</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </p>
              </div>

              <div className="flex items-center justify-end space-x-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setIsKeyModalOpen(false)}
                  disabled={isSavingKey}
                  className="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  Đóng
                </button>
                <button
                  type="submit"
                  disabled={isSavingKey || !inputKey.trim()}
                  className="px-4 py-2 rounded-xl text-xs font-bold bg-purple-600 hover:bg-purple-700 text-white shadow-sm transition-colors cursor-pointer disabled:opacity-50 inline-flex items-center space-x-1.5"
                >
                  {isSavingKey ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Đang xác thực...</span>
                    </>
                  ) : (
                    <span>Lưu &amp; Xác thực kết nối</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
