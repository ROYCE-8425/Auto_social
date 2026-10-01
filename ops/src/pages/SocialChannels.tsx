import React, { useState, useEffect, useMemo } from 'react'
import {
  Send,
  CheckCircle2,
  AlertCircle,
  Clock,
  ExternalLink,
  RefreshCw,
  FileText,
  AlertTriangle,
  ArrowRight,
  Settings,
  Sparkles,
  Share2,
} from 'lucide-react'
import {
  FacebookBadge,
  TikTokBadge,
  InstagramBadge,
  YouTubeBadge,
  XTwitterBadge,
  PlatformPill,
  FacebookIcon,
  TikTokIcon,
  InstagramIcon,
  YouTubeIcon,
  XTwitterIcon,
} from '../components/BrandIcons'
import {
  api,
  TikTokStatusResponse,
  TikTokPostItem,
  FacebookStatusResponse,
  ChannelsStatusResponse,
  FacebookPostItem,
  PostPeerAccount,
  SocialPostLogEntry,
} from '../lib/api'
import { useAuth } from '../lib/auth'
import { useCareScope } from '../lib/scope'
import { getSocialProfileUrl } from '../components/PlatformConnections'

export interface UnifiedPublishPostItem {
  id: string
  channel: 'tiktok' | 'facebook' | 'instagram' | 'youtube' | 'twitter' | string
  datetime: string
  brand: string
  caption: string
  format: string
  status: string
  permalink: string
  photos_count?: number
}

export const PublishingPage: React.FC = () => {
  const { role } = useAuth()
  const { scope, scopeBrand } = useCareScope()
  const [selectedChannelFilter, setSelectedChannelFilter] = useState<string>('all')
  const [tiktokData, setTiktokData] = useState<TikTokStatusResponse | null>(null)
  const [facebookData, setFacebookData] = useState<FacebookStatusResponse | null>(null)
  const [channelsData, setChannelsData] = useState<ChannelsStatusResponse | null>(null)
  const [socialPosts, setSocialPosts] = useState<SocialPostLogEntry[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const loadData = async () => {
    setIsLoading(true)
    setErrorMsg(null)
    try {
      const [channelsRes, fbRes, ttRes, socialPostsRes] = await Promise.allSettled([
        api.getChannelsStatus(),
        api.getFacebookStatus(),
        api.getTikTokStatus(),
        api.getSocialPosts({ limit: 50 }),
      ])

      let fb: FacebookStatusResponse | null = null
      let tt: TikTokStatusResponse | null = null

      if (channelsRes.status === 'fulfilled' && channelsRes.value && channelsRes.value.ok) {
        setChannelsData(channelsRes.value)
        fb = channelsRes.value.facebook
        tt = channelsRes.value.tiktok
      }

      if (fbRes.status === 'fulfilled' && fbRes.value) {
        fb = fbRes.value
      }
      if (ttRes.status === 'fulfilled' && ttRes.value) {
        tt = ttRes.value
      }
      if (socialPostsRes.status === 'fulfilled' && socialPostsRes.value?.ok) {
        setSocialPosts(socialPostsRes.value.posts || [])
      }

      setFacebookData(fb)
      setTiktokData(tt)
    } catch (err: any) {
      setErrorMsg(err?.message || 'Không thể tải dữ liệu xuất bản.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Trích xuất các tài khoản PostPeer từ dữ liệu đồng bộ
  const postpeerAccounts: PostPeerAccount[] = useMemo(() => {
    return channelsData?.postpeer?.accounts || (tiktokData?.accounts as PostPeerAccount[]) || []
  }, [channelsData, tiktokData])

  const xAccount = useMemo(
    () => postpeerAccounts.find((a) => a.platform === 'twitter' || a.platform === 'x'),
    [postpeerAccounts]
  )
  const igAccount = useMemo(
    () => postpeerAccounts.find((a) => a.platform === 'instagram'),
    [postpeerAccounts]
  )
  const ytAccount = useMemo(
    () => postpeerAccounts.find((a) => a.platform === 'youtube'),
    [postpeerAccounts]
  )
  const ttAccount = useMemo(
    () => postpeerAccounts.find((a) => a.platform === 'tiktok'),
    [postpeerAccounts]
  )

  // Danh sách bài đăng thực tế gộp từ TikTok (PostPeer), Facebook (Meta Graph API) và Social Gateway
  const realPosts = useMemo<UnifiedPublishPostItem[]>(() => {
    const list: UnifiedPublishPostItem[] = []
    const seenIds = new Set<string>()

    // 1. Social Provider Adapter posts (từ social-posts.jsonl)
    socialPosts.forEach((p) => {
      const pid = p.id || p.external_post_id || ''
      if (pid) seenIds.add(pid)
      list.push({
        id: pid || `soc_${Math.random()}`,
        channel: p.platform,
        datetime: p.created_at || '',
        brand: p.brand === 'saoviet' ? 'Royce Shop' : p.brand === 'bsn' ? 'Game Giá Rẻ BSN' : (p.brand || 'Social'),
        caption: p.caption || 'Bài đăng mạng xã hội',
        format: p.media_count ? `Bài đăng (${p.media_count} media)` : 'Bài đăng',
        status: p.status === 'published' ? `Đã đăng (#${(p.external_post_id || pid).slice(0, 8)})` : (p.status || 'Đã xuất bản'),
        permalink: p.permalink_url || '',
        photos_count: p.media_count,
      })
    })

    // 2. TikTok posts từ file log tiktok-posts.jsonl
    const ttPosts: TikTokPostItem[] = tiktokData?.recent_posts || []
    ttPosts.forEach((p, idx) => {
      const postpeerId = p.postpeer_id || `tt_${idx}`
      if (seenIds.has(postpeerId)) return
      seenIds.add(postpeerId)
      list.push({
        id: postpeerId,
        channel: 'tiktok',
        datetime: p.datetime || '',
        brand: p.brand === 'saoviet' ? 'Royce Shop' : p.brand === 'bsn' ? 'Game Giá Rẻ BSN' : (p.brand || 'TikTok'),
        caption: p.caption || 'Bài đăng TikTok Carousel',
        format: p.photos_count ? `Carousel (${p.photos_count} ảnh)` : 'Video ngắn',
        status: p.status === 'published' ? `Đã đăng (#${postpeerId.slice(0, 8)})` : (p.status || 'Đã xuất bản'),
        permalink: p.tiktok_url || '',
        photos_count: p.photos_count,
      })
    })

    // 3. Facebook posts từ Meta Graph API
    const fbPosts: FacebookPostItem[] = facebookData?.recent_posts || []
    fbPosts.forEach((p) => {
      if (seenIds.has(p.id)) return
      seenIds.add(p.id)
      list.push({
        id: p.id,
        channel: 'facebook',
        datetime: p.datetime || p.created_time || '',
        brand: p.page_name || (p.brand === 'saoviet' ? 'Royce Shop' : 'Game Giá Rẻ BSN'),
        caption: p.caption || 'Bài viết Fanpage Facebook',
        format: p.format || 'Bài viết',
        status: 'Đã xuất bản',
        permalink: p.permalink_url || '',
      })
    })

    // Sắp xếp bài đăng mới nhất lên đầu
    list.sort((a, b) => (b.datetime || '').localeCompare(a.datetime || ''))
    return list
  }, [socialPosts, tiktokData, facebookData])

  // Lọc theo Brand Scope (Toàn bộ / Game BSN / Sao Việt)
  const scopedPosts = useMemo(() => {
    if (scope === 'brand' && scopeBrand) {
      return realPosts.filter((p) => {
        const b = p.brand.toLowerCase()
        if (scopeBrand === 'bsn') return b.includes('bsn') || b.includes('game')
        if (scopeBrand === 'saoviet') return b.includes('sao') || b.includes('royce') || b.includes('việt')
        return true
      })
    }
    return realPosts
  }, [realPosts, scope, scopeBrand])

  const filteredPosts = useMemo(() => {
    if (selectedChannelFilter === 'all') return scopedPosts
    return scopedPosts.filter((p) => p.channel === selectedChannelFilter)
  }, [scopedPosts, selectedChannelFilter])

  const fbCount = useMemo(() => scopedPosts.filter((p) => p.channel === 'facebook').length, [scopedPosts])
  const ttCount = useMemo(() => scopedPosts.filter((p) => p.channel === 'tiktok').length, [scopedPosts])
  const xCount = useMemo(() => scopedPosts.filter((p) => p.channel === 'twitter' || p.channel === 'x').length, [scopedPosts])
  const igCount = useMemo(() => scopedPosts.filter((p) => p.channel === 'instagram').length, [scopedPosts])
  const ytCount = useMemo(() => scopedPosts.filter((p) => p.channel === 'youtube').length, [scopedPosts])

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* ================= HEADER ================= */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-blue-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <Send className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Trung Tâm Xuất Bản (Publishing)
              </h1>
              <span className="px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 text-[10px] font-bold border border-purple-200">
                Nhật ký &amp; Lịch phát hành
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Theo dõi nhật ký phân phối bài đăng, video ngắn và carousel ảnh thực tế qua 5 nền tảng mạng xã hội.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            type="button"
            onClick={loadData}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-purple-600' : ''}`} />
            <span>Làm mới nhật ký</span>
          </button>
          <a
            href="#settings"
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-2xs transition-colors"
          >
            <Settings className="w-3.5 h-3.5" />
            <span>Cài đặt kết nối</span>
          </a>
        </div>
      </div>

      {errorMsg && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 text-xs text-rose-700 flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* ================= PUBLISHING CAPABILITIES STRIP (5 PLATFORMS) ================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
        {/* 1. TikTok Publishing */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex flex-col justify-between space-y-3">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <TikTokBadge size="sm" />
                <span className="font-bold text-slate-900 text-xs">TikTok</span>
              </div>
              {ttAccount ? (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Sẵn sàng</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[10px] border border-slate-200">
                  <span>Chưa có Key</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {ttAccount ? (
                <>
                  Tài khoản{' '}
                  <a
                    href={getSocialProfileUrl('tiktok', ttAccount.username)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-slate-900 hover:text-purple-600 underline decoration-dotted inline-flex items-center space-x-0.5"
                    title="Mở TikTok @seotrum"
                  >
                    <span>{ttAccount.username}</span>
                    <ExternalLink className="w-2.5 h-2.5 ml-0.5 text-slate-400" />
                  </a>{' '}
                  kết nối qua PostPeer Gateway. Xuất bản video &amp; carousel ảnh dọc.
                </>
              ) : (
                'Hỗ trợ xuất bản video ngắn và album ảnh (carousel) tự động qua cổng PostPeer Gateway API.'
              )}
            </p>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Định dạng: Video/Ảnh</span>
            <a
              href={getSocialProfileUrl('tiktok', ttAccount?.username || 'seotrum')}
              target="_blank"
              rel="noopener noreferrer"
              className="text-purple-600 hover:text-purple-700 font-bold inline-flex items-center space-x-1"
            >
              <span>Mở TikTok</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* 2. Facebook Publishing */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex flex-col justify-between space-y-3">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FacebookBadge size="sm" />
                <span className="font-bold text-slate-900 text-xs">Facebook</span>
              </div>
              {facebookData?.connected && (facebookData.pages?.length ?? 0) > 0 ? (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>{facebookData.pages.length} Page</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[10px] border border-slate-200">
                  <span>Chưa kết nối</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {facebookData?.connected && (facebookData.pages?.length ?? 0) > 0 ? (
                <>
                  Đã kết nối {facebookData.pages.length} Fanpage ({facebookData.permissions === 'full' ? 'Toàn quyền' : 'Chỉ đọc'}). Hỗ trợ xuất bản bài viết, album ảnh.
                </>
              ) : (
                'Cổng Meta Graph API chưa nhận diện Fanpage. Cần nạp Page Access Token.'
              )}
            </p>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Định dạng: Bài/Album</span>
            <a
              href={facebookData?.pages?.[0]?.id ? `https://www.facebook.com/${facebookData.pages[0].id}` : 'https://www.facebook.com/343562028848465'}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 font-bold inline-flex items-center space-x-1"
            >
              <span>Mở Fanpage</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* 3. X (Twitter) Publishing */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex flex-col justify-between space-y-3">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <XTwitterBadge size="sm" />
                <span className="font-bold text-slate-900 text-xs">X (Twitter)</span>
              </div>
              {xAccount ? (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Sẵn sàng</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[10px] border border-slate-200">
                  <span>Chưa kết nối</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {xAccount ? (
                <>
                  Tài khoản{' '}
                  <a
                    href={getSocialProfileUrl('twitter', xAccount.username)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-slate-900 hover:text-black underline decoration-dotted inline-flex items-center space-x-0.5"
                    title="Mở X @RoyceDaiDe"
                  >
                    <span>{xAccount.username}</span>
                    <ExternalLink className="w-2.5 h-2.5 ml-0.5 text-slate-400" />
                  </a>{' '}
                  kết nối qua PostPeer Gateway. Xuất bản Tweet, hình ảnh và thread.
                </>
              ) : (
                'Hỗ trợ xuất bản bài đăng tweet văn bản và hình ảnh qua cổng PostPeer Gateway API.'
              )}
            </p>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Định dạng: Tweet &amp; Media</span>
            <a
              href={getSocialProfileUrl('twitter', xAccount?.username || 'RoyceDaiDe')}
              target="_blank"
              rel="noopener noreferrer"
              className="text-slate-900 hover:text-black font-bold inline-flex items-center space-x-1"
            >
              <span>Mở X</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* 4. Instagram Publishing */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex flex-col justify-between space-y-3">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <InstagramBadge size="sm" />
                <span className="font-bold text-slate-900 text-xs">Instagram</span>
              </div>
              {igAccount ? (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Sẵn sàng</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[10px] border border-slate-200">
                  <span>Chưa kết nối</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {igAccount ? (
                <>
                  Tài khoản{' '}
                  <a
                    href={getSocialProfileUrl('instagram', igAccount.username)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-slate-900 hover:text-pink-600 underline decoration-dotted inline-flex items-center space-x-0.5"
                    title="Mở Instagram @trannhuy.inf"
                  >
                    <span>{igAccount.username}</span>
                    <ExternalLink className="w-2.5 h-2.5 ml-0.5 text-pink-400" />
                  </a>{' '}
                  kết nối qua PostPeer Gateway. Xuất bản bài đăng ảnh, Carousel và Reels.
                </>
              ) : (
                'Hỗ trợ xuất bản bài đăng ảnh và Reels tự động qua cổng PostPeer Gateway API.'
              )}
            </p>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Định dạng: Ảnh, Reels</span>
            <a
              href={getSocialProfileUrl('instagram', igAccount?.username || 'trannhuy.inf')}
              target="_blank"
              rel="noopener noreferrer"
              className="text-pink-600 hover:text-pink-700 font-bold inline-flex items-center space-x-1"
            >
              <span>Mở Instagram</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* 5. YouTube Shorts Publishing */}
        <div className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs flex flex-col justify-between space-y-3">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <YouTubeBadge size="sm" />
                <span className="font-bold text-slate-900 text-xs">YouTube</span>
              </div>
              {ytAccount ? (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Sẵn sàng</span>
                </span>
              ) : (
                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[10px] border border-slate-200">
                  <span>Chưa kết nối</span>
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed">
              {ytAccount ? (
                <>
                  Kênh{' '}
                  <a
                    href={getSocialProfileUrl('youtube', ytAccount.username)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold text-slate-900 hover:text-red-600 underline decoration-dotted inline-flex items-center space-x-0.5"
                    title="Mở YouTube @trannhuy4641"
                  >
                    <span>{ytAccount.username}</span>
                    <ExternalLink className="w-2.5 h-2.5 ml-0.5 text-red-400" />
                  </a>{' '}
                  kết nối qua PostPeer Gateway. Xuất bản video ngắn Shorts chuẩn 9:16.
                </>
              ) : (
                'Hỗ trợ xuất bản video ngắn Shorts tự động qua cổng PostPeer Gateway API.'
              )}
            </p>
          </div>
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Định dạng: Shorts 9:16</span>
            <a
              href={getSocialProfileUrl('youtube', ytAccount?.username || 'trannhuy4641')}
              target="_blank"
              rel="noopener noreferrer"
              className="text-red-600 hover:text-red-700 font-bold inline-flex items-center space-x-1"
            >
              <span>Mở YouTube</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>

      {/* ================= RECENT POSTS LOG ================= */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden space-y-3 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Nhật ký phân phối bài đăng thực tế ({filteredPosts.length})
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Chỉ hiển thị bài đăng có ID và log thực từ các cổng kết nối PostPeer Gateway và Meta Graph API.
            </p>
          </div>

          {/* Filter channel tabs */}
          <div className="flex flex-wrap items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            {[
              { id: 'all', label: 'Tất cả (thật)', count: scopedPosts.length, icon: null },
              { id: 'facebook', label: 'Facebook', count: fbCount, icon: <FacebookIcon className="w-3.5 h-3.5 text-[#1877F2]" /> },
              { id: 'tiktok', label: 'TikTok', count: ttCount, icon: <TikTokIcon className="w-3.5 h-3.5" colored /> },
              { id: 'twitter', label: 'X (Twitter)', count: xCount, icon: <XTwitterIcon className="w-3.5 h-3.5" /> },
              { id: 'instagram', label: 'Instagram', count: igCount, icon: <InstagramIcon className="w-3.5 h-3.5 text-[#E60064]" /> },
              { id: 'youtube', label: 'YouTube', count: ytCount, icon: <YouTubeIcon className="w-3.5 h-3.5 text-[#FF0000]" /> },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setSelectedChannelFilter(tab.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer ${
                  selectedChannelFilter === tab.id
                    ? 'bg-white text-slate-900 shadow-2xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab.icon}
                <span>{tab.label}</span>
                {tab.count > 0 && (
                  <span
                    className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                      selectedChannelFilter === tab.id
                        ? 'bg-slate-100 text-slate-800'
                        : 'bg-slate-200/70 text-slate-600'
                    }`}
                  >
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Posts Table or Empty State */}
        {filteredPosts.length === 0 ? (
          <div className="p-10 text-center bg-slate-50 border border-dashed border-slate-200 rounded-2xl space-y-2">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <FileText className="w-5 h-5" />
            </div>
            <div className="text-xs font-semibold text-slate-700">Chưa có bài đăng thật từ kênh này.</div>
            <div className="text-[11px] text-slate-400 max-w-md mx-auto leading-relaxed">
              Hệ thống không hiển thị bài đăng mẫu hay số liệu giả lập reach/orders. Khi bạn xuất bản bài thật qua PostPeer Gateway hoặc Meta Graph, nhật ký phân phối kèm ID xuất bản và liên kết gốc sẽ hiển thị tại đây.
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600">
              <thead className="bg-slate-50/80 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
                <tr>
                  <th className="py-3 px-3">Thời gian</th>
                  <th className="py-3 px-3">Nền tảng</th>
                  <th className="py-3 px-3">Trang / Thương hiệu</th>
                  <th className="py-3 px-3">Tiêu đề / Caption</th>
                  <th className="py-3 px-3">Định dạng</th>
                  <th className="py-3 px-3">Trạng thái</th>
                  <th className="py-3 px-3 text-right">Liên kết gốc</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {filteredPosts.map((post) => (
                  <tr key={post.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 text-slate-400 whitespace-nowrap text-[11px]">
                      <div className="flex items-center space-x-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>{post.datetime || 'Vừa xong'}</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <PlatformPill platform={post.channel} />
                    </td>
                    <td className="py-3 px-3 font-semibold text-slate-800 whitespace-nowrap">
                      {post.brand}
                    </td>
                    <td className="py-3 px-3 text-slate-900 font-semibold max-w-sm truncate" title={post.caption}>
                      {post.caption || 'Bài đăng không có nội dung chữ'}
                    </td>
                    <td className="py-3 px-3 text-slate-500 whitespace-nowrap text-[11px]">
                      {post.format}
                    </td>
                    <td className="py-3 px-3 whitespace-nowrap">
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        <span>{post.status}</span>
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right whitespace-nowrap">
                      {post.permalink ? (
                        <a
                          href={post.permalink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700 font-semibold inline-flex items-center space-x-1"
                        >
                          <span>Xem</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span className="text-slate-400 text-[11px] italic">Chưa có URL</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

// Backwards compatibility alias
export const SocialChannelsPage = PublishingPage
