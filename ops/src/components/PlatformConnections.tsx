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
} from 'lucide-react'
import {
  FacebookBadge,
  TikTokBadge,
  InstagramBadge,
  YouTubeBadge,
  FacebookIcon,
  TikTokIcon,
  InstagramIcon,
  YouTubeIcon,
} from './BrandIcons'
import {
  api,
  TikTokStatusResponse,
  FacebookStatusResponse,
  ChannelsStatusResponse,
  ChannelInfoItem,
} from '../lib/api'
import { useAuth } from '../lib/auth'

export const PlatformConnections: React.FC = () => {
  const { role } = useAuth()
  const [tiktokData, setTiktokData] = useState<TikTokStatusResponse | null>(null)
  const [facebookData, setFacebookData] = useState<FacebookStatusResponse | null>(null)
  const [channelsData, setChannelsData] = useState<ChannelsStatusResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string>('')

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

  // Đếm các kênh kết nối thật
  const connectedCount = (facebookData?.connected ? 1 : 0) + (tiktokData?.connected ? 1 : 0)
  const totalRealPages = facebookData?.pages?.length || 0
  const totalTikTokAccounts = tiktokData?.accounts?.length || 0

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
        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Kênh API hoạt động</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">
              <span className="text-emerald-600">{connectedCount}</span>
              <span className="text-slate-400 text-sm font-normal"> / 4 nền tảng</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Fanpages Facebook nạp Token</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">
              <span className="text-blue-600">{totalRealPages}</span>
              <span className="text-slate-400 text-sm font-normal"> trang quản lý</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
            <FacebookIcon className="w-5 h-5 text-[#1877F2]" />
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-2xs flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 font-medium">Tài khoản TikTok PostPeer</span>
            <div className="text-2xl font-black text-slate-900 mt-0.5">
              <span className="text-purple-600">{totalTikTokAccounts}</span>
              <span className="text-slate-400 text-sm font-normal"> tài khoản OAuth</span>
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold">
            <TikTokIcon className="w-5 h-5" colored />
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
                  <div className="flex items-center space-x-2">
                    <FacebookBadge size="sm" />
                    <div>
                      <div className="font-bold text-slate-900">Facebook &amp; Messenger</div>
                      <span className="text-[10px] text-slate-400 font-mono">Meta Graph v25.0</span>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  {facebookData?.connected ? (
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
                  <span className="inline-flex items-center space-x-1 text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full text-[11px] border border-amber-200">
                    <Info className="w-3 h-3 text-amber-600" />
                    <span>Chưa hỗ trợ trực tiếp</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap font-mono text-[11px]">
                  <span>Polling ({facebookData?.poll_interval_seconds || 60}s/lần)</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-700 font-mono text-[11px]">
                  {facebookData?.last_poll || 'Chưa ghi nhận'}
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap">
                  {facebookData?.connected ? (
                    <span className="text-emerald-600 font-semibold text-[11px]">Đã sẵn sàng</span>
                  ) : (
                    <a
                      href="/hub/mcp"
                      className="text-blue-600 hover:text-blue-700 font-bold inline-flex items-center space-x-1"
                    >
                      <span>Nạp Page Token</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </a>
                  )}
                </td>
              </tr>

              {/* Row 2: TikTok */}
              <tr className="hover:bg-slate-50/60 transition-colors">
                <td className="py-3.5 px-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    <TikTokBadge size="sm" />
                    <div>
                      <div className="font-bold text-slate-900">TikTok Video &amp; Carousel</div>
                      <span className="text-[10px] text-slate-400 font-mono">PostPeer Gateway</span>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  {tiktokData?.connected ? (
                    <span className="inline-flex items-center space-x-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full text-[11px] font-bold border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                      <span>{totalTikTokAccounts} TK kết nối</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center space-x-1 text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full text-[11px] border border-rose-200">
                      <XCircle className="w-3 h-3 text-rose-500" />
                      <span>Chưa có Key</span>
                    </span>
                  )}
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center space-x-1 text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                    <span>Không hỗ trợ</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  {tiktokData?.connected ? (
                    <span className="inline-flex items-center space-x-1 text-purple-700 bg-purple-50 px-2 py-0.5 rounded-full text-[11px] font-bold border border-purple-200">
                      <Send className="w-3 h-3 text-purple-600" />
                      <span>Hỗ trợ thật (Video/Photos)</span>
                    </span>
                  ) : (
                    <span className="text-slate-400 text-[11px]">Cần Key</span>
                  )}
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap font-mono text-[11px]">
                  <span>Task Polling API</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-700 font-mono text-[11px]">
                  {tiktokData?.connected ? 'Đang hoạt động' : 'Chưa ghi nhận'}
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap">
                  {tiktokData?.connected ? (
                    <span className="text-emerald-600 font-semibold text-[11px]">Đã sẵn sàng</span>
                  ) : (
                    <a
                      href="/app"
                      className="text-purple-600 hover:text-purple-700 font-bold inline-flex items-center space-x-1"
                    >
                      <span>Cấu hình PostPeer</span>
                      <ArrowUpRight className="w-3 h-3" />
                    </a>
                  )}
                </td>
              </tr>

              {/* Row 3: Instagram */}
              <tr className="hover:bg-slate-50/60 transition-colors opacity-80">
                <td className="py-3.5 px-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    <InstagramBadge size="sm" />
                    <div>
                      <div className="font-bold text-slate-900">Instagram &amp; Threads</div>
                      <span className="text-[10px] text-slate-400 font-mono">Meta Graph</span>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center space-x-1 text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                    <span>Chưa kết nối</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="text-slate-400 text-[11px]">Chưa hỗ trợ</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="text-slate-400 text-[11px]">Chưa hỗ trợ</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-400 text-[11px]">
                  <span>Chưa hỗ trợ</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-400 font-mono text-[11px]">
                  Chưa ghi nhận
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap text-slate-400 text-[11px]">
                  Chờ tích hợp connector
                </td>
              </tr>

              {/* Row 4: YouTube */}
              <tr className="hover:bg-slate-50/60 transition-colors opacity-80">
                <td className="py-3.5 px-4 whitespace-nowrap">
                  <div className="flex items-center space-x-2">
                    <YouTubeBadge size="sm" />
                    <div>
                      <div className="font-bold text-slate-900">YouTube Shorts &amp; Video</div>
                      <span className="text-[10px] text-slate-400 font-mono">Google Data v3</span>
                    </div>
                  </div>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center space-x-1 text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                    <span>Chưa kết nối</span>
                  </span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="text-slate-400 text-[11px]">Chưa hỗ trợ</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="text-slate-400 text-[11px]">Chưa hỗ trợ</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-400 text-[11px]">
                  <span>Chưa hỗ trợ</span>
                </td>
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-400 font-mono text-[11px]">
                  Chưa ghi nhận
                </td>
                <td className="py-3.5 px-4 text-right whitespace-nowrap text-slate-400 text-[11px]">
                  Chờ OAuth Google
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
                <Send className="w-4 h-4 text-amber-500 shrink-0" />
                <div>
                  <div className="text-[10px] text-slate-400 font-medium">Xuất bản bài viết</div>
                  <div className="font-bold text-slate-800">Chưa hỗ trợ trực tiếp</div>
                </div>
              </div>
            </div>

            {/* Config Info */}
            <div className="space-y-1.5 text-xs text-slate-600 bg-slate-50/50 p-3 rounded-xl border border-slate-100">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Quyền truy cập Token:</span>
                <span className="font-mono font-bold text-slate-700 uppercase">
                  {facebookData?.permissions || 'readonly'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Chu kỳ quét (Polling):</span>
                <span className="font-mono text-slate-700">
                  {facebookData?.poll_interval_seconds || 60} giây / lần
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Lần quét sự kiện gần nhất:</span>
                <span className="text-slate-800 font-mono font-medium">
                  {facebookData?.last_poll || 'Chưa ghi nhận'}
                </span>
              </div>
            </div>

            {/* Connected Real Pages List */}
            <div className="space-y-1.5">
              <div className="text-xs font-bold text-slate-800 flex items-center justify-between">
                <span>Danh sách Fanpage thật ({totalRealPages})</span>
                {facebookData?.connected && (
                  <span className="text-[10px] text-emerald-600 font-normal">Page Access Token hợp lệ</span>
                )}
              </div>
              {facebookData?.pages && facebookData.pages.length > 0 ? (
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                  {facebookData.pages.map((p) => (
                    <div
                      key={p.id}
                      className="bg-slate-50 p-2 rounded-xl border border-slate-200/70 text-xs flex items-center justify-between"
                    >
                      <div className="font-semibold text-slate-900 truncate max-w-[200px]" title={p.name}>
                        {p.name}
                      </div>
                      <span className="font-mono text-[10px] text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                        ID: {p.id}
                      </span>
                    </div>
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
            <span className="text-slate-400">Nguồn dữ liệu: Meta Graph API</span>
            <a
              href="/hub/mcp"
              className="text-blue-600 hover:text-blue-700 font-bold inline-flex items-center space-x-1"
            >
              <span>Quản lý Token</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* --- 2. TIKTOK DETAILED CARD --- */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-4">
          <div className="space-y-3.5">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <TikTokBadge size="md" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">
                    TikTok PostPeer Gateway
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    PostPeer Content Distribution API
                  </span>
                </div>
              </div>

              {tiktokData?.connected ? (
                <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Đã kết nối</span>
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
                  <div className="text-[10px] text-slate-400 font-medium">Xuất bản bài viết</div>
                  <div className="font-bold text-slate-800">
                    {tiktokData?.connected ? 'Hỗ trợ thật (Video/Photos)' : 'Chưa kích hoạt'}
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

            {/* Config Info */}
            <div className="space-y-1.5 text-xs text-slate-600 bg-slate-50/50 p-3 rounded-xl border border-slate-100">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">PostPeer API Key:</span>
                <span className="font-mono text-slate-700">
                  {tiktokData?.masked_key || 'Chưa cấu hình'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Bộ phát hàng ngày (Daily Loop):</span>
                <span
                  className={`font-semibold ${
                    tiktokData?.loop?.enabled ? 'text-emerald-600' : 'text-slate-500'
                  }`}
                >
                  {tiktokData?.loop?.enabled ? 'Đang bật' : 'Tắt'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Brand Kits TikTok:</span>
                <span className="text-slate-800 font-semibold">
                  {(tiktokData?.kits || []).filter((k) => k.enabled).length} / {(tiktokData?.kits || []).length} bộ kích hoạt
                </span>
              </div>
            </div>

            {/* Connected TikTok Accounts */}
            <div className="space-y-1.5">
              <div className="text-xs font-bold text-slate-800 flex items-center justify-between">
                <span>Tài khoản TikTok OAuth ({totalTikTokAccounts})</span>
                {tiktokData?.connected && (
                  <span className="text-[10px] text-purple-600 font-normal">Đã xác thực</span>
                )}
              </div>
              {tiktokData?.accounts && tiktokData.accounts.length > 0 ? (
                <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                  {tiktokData.accounts.map((acc) => (
                    <div
                      key={acc.id}
                      className="bg-slate-50 p-2 rounded-xl border border-slate-200/70 text-xs flex items-center justify-between"
                    >
                      <div className="font-semibold text-slate-900 truncate">
                        {acc.name || acc.username || acc.id}
                      </div>
                      <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-bold border border-emerald-200">
                        {acc.status || 'Active'}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-slate-400 italic p-3 bg-slate-50 rounded-xl border border-dashed border-slate-200 text-center">
                  Chưa có tài khoản nào được kết nối qua PostPeer
                </div>
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-400">Nguồn dữ liệu: PostPeer Gateway</span>
            <a
              href="/app"
              className="text-purple-600 hover:text-purple-700 font-bold inline-flex items-center space-x-1"
            >
              <span>Mở Buồng lái /app</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* --- 3. INSTAGRAM CARD --- */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4 opacity-90">
          <div className="space-y-3.5">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <InstagramBadge size="md" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">
                    Instagram &amp; Threads
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Meta Instagram Graph API
                  </span>
                </div>
              </div>

              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-bold border border-slate-200">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                <span>Chưa hỗ trợ</span>
              </span>
            </div>

            <div className="bg-amber-50/70 border border-amber-200/70 p-3.5 rounded-xl text-xs space-y-2 text-amber-900">
              <div className="flex items-center space-x-1.5 font-bold">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>Chưa cấu hình connector</span>
              </div>
              <p className="text-[11px] text-amber-800 leading-relaxed">
                Hệ thống chưa kết nối Meta Instagram Graph API riêng. Hiện tại chưa hỗ trợ upload Reels, đăng ảnh Carousel hay tự động chăm sóc Direct Messages.
              </p>
            </div>

            <div className="space-y-1.5 text-xs text-slate-500">
              <div className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                <span>Không hiển thị số liệu reach, follower hay tương tác giả định.</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                <span>Sẽ tự động kích hoạt khi nạp connector Instagram chính thức tại Hub MCP.</span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-400">Trạng thái: Đang chuẩn bị</span>
            <a
              href="/hub/mcp"
              className="text-slate-600 hover:text-slate-900 font-medium inline-flex items-center space-x-1"
            >
              <span>Xem tài liệu Hub MCP</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* --- 4. YOUTUBE CARD --- */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs flex flex-col justify-between space-y-4 opacity-90">
          <div className="space-y-3.5">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <YouTubeBadge size="md" />
                <div>
                  <h3 className="font-bold text-slate-900 text-sm leading-tight">
                    YouTube Shorts &amp; Video
                  </h3>
                  <span className="text-[11px] text-slate-400 font-mono">
                    Google YouTube Data API v3
                  </span>
                </div>
              </div>

              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 text-xs font-bold border border-slate-200">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                <span>Chưa hỗ trợ</span>
              </span>
            </div>

            <div className="bg-amber-50/70 border border-amber-200/70 p-3.5 rounded-xl text-xs space-y-2 text-amber-900">
              <div className="flex items-center space-x-1.5 font-bold">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>Chưa cấu hình connector</span>
              </div>
              <p className="text-[11px] text-amber-800 leading-relaxed">
                Hệ thống chưa kết nối Google YouTube Data API v3 qua OAuth 2.0. Chưa hỗ trợ upload video Shorts tự động hay kiểm duyệt bình luận kênh.
              </p>
            </div>

            <div className="space-y-1.5 text-xs text-slate-500">
              <div className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                <span>Không hiển thị lượt xem hay người đăng ký giả lập.</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-300" />
                <span>Sẽ kích hoạt khi cấu hình OAuth Client ID trong server Javis.</span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
            <span className="text-slate-400">Trạng thái: Đang chuẩn bị</span>
            <a
              href="/hub/mcp"
              className="text-slate-600 hover:text-slate-900 font-medium inline-flex items-center space-x-1"
            >
              <span>Xem tài liệu Hub MCP</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}
