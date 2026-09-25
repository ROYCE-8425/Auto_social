import React, { useState, useEffect } from 'react'
import {
  Share2,
  Video,
  CheckCircle2,
  AlertCircle,
  Clock,
  ExternalLink,
  RefreshCw,
  ShieldAlert,
  Image as ImageIcon,
  Music,
  Layers,
  Sparkles,
  Youtube,
  Instagram,
  MessageCircle,
  Globe,
  TrendingUp,
  BarChart2,
  Send,
  Eye,
  Check,
  ChevronDown,
} from 'lucide-react'
import {
  FacebookBadge,
  TikTokBadge,
  InstagramBadge,
  YouTubeBadge,
  PlatformPill,
  FacebookIcon,
  TikTokIcon,
  InstagramIcon,
  YouTubeIcon,
} from '../components/BrandIcons'
import { api, TikTokStatusResponse, TikTokPostItem } from '../lib/api'
import { useAuth } from '../lib/auth'

interface SocialChannelItem {
  id: 'facebook' | 'tiktok' | 'instagram' | 'youtube'
  name: string
  handle: string
  subname: string
  icon: string
  colorBg: string
  colorText: string
  status: 'connected' | 'warning' | 'disconnected'
  statusLabel: string
  connectedAccount: string
  apiGateway: string
  metrics24h: {
    posts: number
    views: string
    interactions: number
  }
  features: string[]
}

const strategicChannels: SocialChannelItem[] = [
  {
    id: 'facebook',
    name: 'Facebook & Messenger',
    handle: '@JavisOfficial & @BSNGame',
    subname: 'Cột trụ cộng đồng & Hộp thư',
    icon: 'f',
    colorBg: 'bg-blue-600',
    colorText: 'text-white',
    status: 'connected',
    statusLabel: 'Đang kết nối Graph API',
    connectedAccount: 'Page JAVIS Official, Nhóm Game BSN',
    apiGateway: 'Meta Graph API v20.0 (Chính chủ)',
    metrics24h: {
      posts: 3,
      views: '18.4K',
      interactions: 519,
    },
    features: ['Đăng album tự động', 'Soạn nháp Comment & IB', 'Bắt SĐT khách hàng'],
  },
  {
    id: 'tiktok',
    name: 'TikTok Video & Shop',
    handle: '@javis.ops & @game.bsn',
    subname: 'Cột trụ Video ngắn dọc',
    icon: '🎵',
    colorBg: 'bg-slate-900',
    colorText: 'text-white',
    status: 'connected',
    statusLabel: 'Đã lưu key PostPeer',
    connectedAccount: 'seotrum & bsn_vietnam',
    apiGateway: 'PostPeer Gateway API',
    metrics24h: {
      posts: 2,
      views: '42.8K',
      interactions: 1240,
    },
    features: ['Carousel 9:16 dọc', 'Tự gắn âm thanh Hot', 'Quét bình luận video'],
  },
  {
    id: 'instagram',
    name: 'Instagram & Threads',
    handle: '@javis.social & @bsn_game',
    subname: 'Cột trụ Thị giác & Gen Z',
    icon: '📸',
    colorBg: 'bg-gradient-to-tr from-amber-500 via-rose-500 to-purple-600',
    colorText: 'text-white',
    status: 'connected',
    statusLabel: 'Meta Unified Token',
    connectedAccount: 'javis.social (Business IG)',
    apiGateway: 'Meta Instagram Graph & Threads API',
    metrics24h: {
      posts: 2,
      views: '12.6K',
      interactions: 388,
    },
    features: ['Reels & Carousels', 'Tin nhắn Instagram Direct', 'Đăng bài Threads tự động'],
  },
  {
    id: 'youtube',
    name: 'YouTube Shorts & Channel',
    handle: '@JavisOpsVN',
    subname: 'Cột trụ Video chuẩn & SEO',
    icon: '▶',
    colorBg: 'bg-red-600',
    colorText: 'text-white',
    status: 'connected',
    statusLabel: 'Google API v3 Ready',
    connectedAccount: 'Javis Ops Official Channel',
    apiGateway: 'Google YouTube Data API v3',
    metrics24h: {
      posts: 1,
      views: '26.1K',
      interactions: 472,
    },
    features: ['Tự động đẩy YouTube Shorts', 'Bình luận video', 'Lưu trữ tài liệu dài'],
  },
]

interface MultiPostRecord {
  id: string
  time: string
  brand: string
  channel: 'facebook' | 'tiktok' | 'instagram' | 'youtube'
  title: string
  type: string
  status: 'Đã đăng' | 'Lên lịch' | 'Nháp'
  url?: string
}

const recentMultiPosts: MultiPostRecord[] = [
  {
    id: 'p1',
    time: '14:20 Hôm nay',
    brand: 'BSN Game',
    channel: 'tiktok',
    title: 'Top 5 tựa game thế giới mở hot nhất tháng này bạn không nên bỏ lỡ',
    type: 'Carousel 9:16 (5 ảnh)',
    status: 'Đã đăng',
    url: 'https://tiktok.com',
  },
  {
    id: 'p2',
    time: '14:05 Hôm nay',
    brand: 'BSN Game',
    channel: 'youtube',
    title: 'Top 5 tựa game thế giới mở hot nhất tháng này #shorts',
    type: 'YouTube Shorts 9:16',
    status: 'Đã đăng',
    url: 'https://youtube.com',
  },
  {
    id: 'p3',
    time: '13:45 Hôm nay',
    brand: 'BSN Game',
    channel: 'instagram',
    title: 'Bộ ảnh gaming gear góc máy cực chất cho game thủ',
    type: 'Instagram Carousel + Threads',
    status: 'Đã đăng',
    url: 'https://instagram.com',
  },
  {
    id: 'p4',
    time: '11:30 Hôm nay',
    brand: 'Sao Việt',
    channel: 'facebook',
    title: 'Khai giảng lớp Vận Hành Social Media Chuyên Nghiệp K12',
    type: 'Album ảnh Facebook',
    status: 'Đã đăng',
    url: 'https://facebook.com',
  },
  {
    id: 'p5',
    time: 'Hôm qua 19:00',
    brand: 'BSN Game',
    channel: 'tiktok',
    title: 'Hướng dẫn cài đặt và tối ưu FPS cho máy yếu',
    type: 'Video ngắn 9:16',
    status: 'Đã đăng',
    url: 'https://tiktok.com',
  },
  {
    id: 'p6',
    time: 'Hôm qua 18:30',
    brand: 'BSN Game',
    channel: 'youtube',
    title: 'Cách tăng 30% FPS khi chơi game mượt mà #shorts',
    type: 'YouTube Shorts 9:16',
    status: 'Đã đăng',
    url: 'https://youtube.com',
  },
  {
    id: 'p7',
    time: 'Hôm qua 15:00',
    brand: 'Sao Việt',
    channel: 'instagram',
    title: 'Tips trả lời khách hàng trong 30 giây với Javis AI',
    type: 'Instagram Reels',
    status: 'Đã đăng',
    url: 'https://instagram.com',
  },
]

export const SocialChannelsPage: React.FC = () => {
  const { role } = useAuth()
  const [selectedChannelFilter, setSelectedChannelFilter] = useState<string>('all')
  const [tiktokData, setTiktokData] = useState<TikTokStatusResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const loadData = async () => {
    setIsLoading(true)
    try {
      const res = await api.getTikTokStatus()
      setTiktokData(res)
    } catch (_) {
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const filteredPosts = recentMultiPosts.filter((p) => {
    if (selectedChannelFilter === 'all') return true
    return p.channel === selectedChannelFilter
  })

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* ================= HEADER ================= */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-3.5">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Share2 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Mạng Xã Hội Đa Kênh
              </h1>
              <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 text-[10px] font-bold border border-blue-200">
                4 Kênh Chiến Lược
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Tối ưu phân phối đa nền tảng: Facebook, TikTok, Instagram &amp; Threads, YouTube.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          <button
            type="button"
            onClick={loadData}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-blue-600' : ''}`} />
            <span>Đồng bộ trạng thái</span>
          </button>
        </div>
      </div>

      {/* ================= STRATEGIC REASONING BANNER ================= */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 rounded-2xl p-5 text-white shadow-lg relative overflow-hidden">
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1.5 max-w-3xl">
            <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-[11px] font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Chiến Lược Tối Ưu: Tập Trung "Bộ Tứ Quyền Lực"</span>
            </div>
            <h2 className="text-base sm:text-lg font-bold text-white">
              Tại sao chỉ chọn 4 nền tảng trọng tâm thay vì dàn trải cả 9 kênh?
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed">
              <strong>1. Tận dụng hạ tầng Meta chung:</strong> Facebook + Messenger + Instagram + Threads dùng chung 1 Meta Business Suite và API token.
              <br />
              <strong>2. Ma trận 1 Nội dung $\rightarrow$ 4 Kênh:</strong> 1 video dọc đăng đồng thời lên <strong>TikTok + YouTube Shorts + Facebook Reels + IG Reels</strong>, tiếp cận 95% khách hàng Việt Nam mà không tốn công biên tập nhiều lần.
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-md p-3.5 rounded-xl border border-white/10 text-center shrink-0 space-y-1">
            <span className="text-xs text-slate-300 block">Tổng lượt tiếp cận 24h</span>
            <div className="text-2xl font-black text-cyan-300">99.9K+</div>
            <span className="text-[10px] text-emerald-400 font-semibold">↑ 34% so với tuần trước</span>
          </div>
        </div>
      </div>

      {/* ================= 4 STRATEGIC PLATFORM CARDS ================= */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {strategicChannels.map((ch) => (
          <div
            key={ch.id}
            className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs hover:shadow-md transition-all flex flex-col justify-between space-y-3"
          >
            <div>
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  {ch.id === 'facebook' && <FacebookBadge size="md" />}
                  {ch.id === 'tiktok' && <TikTokBadge size="md" />}
                  {ch.id === 'instagram' && <InstagramBadge size="md" />}
                  {ch.id === 'youtube' && <YouTubeBadge size="md" />}
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm leading-tight">{ch.name}</h3>
                    <span className="text-[10px] text-slate-400 font-mono block">{ch.handle}</span>
                  </div>
                </div>

                <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Hoạt động</span>
                </span>
              </div>

              {/* Subname & Account */}
              <div className="pt-2 text-xs text-slate-600">
                <span className="font-semibold text-slate-800">{ch.subname}</span>
                <p className="text-[11px] text-slate-400 mt-0.5 truncate">
                  Tài khoản: <strong className="text-slate-700">{ch.connectedAccount}</strong>
                </p>
              </div>

              {/* Metrics mini boxes */}
              <div className="grid grid-cols-3 gap-1.5 bg-slate-50 p-2 rounded-xl border border-slate-100 mt-2.5 text-center">
                <div>
                  <div className="text-xs font-black text-slate-900">{ch.metrics24h.posts}</div>
                  <div className="text-[9px] text-slate-400 font-medium">Bài 24h</div>
                </div>
                <div className="border-l border-slate-200">
                  <div className="text-xs font-black text-blue-600">{ch.metrics24h.views}</div>
                  <div className="text-[9px] text-slate-400 font-medium">Lượt xem</div>
                </div>
                <div className="border-l border-slate-200">
                  <div className="text-xs font-black text-emerald-600">{ch.metrics24h.interactions}</div>
                  <div className="text-[9px] text-slate-400 font-medium">Tương tác</div>
                </div>
              </div>
            </div>

            {/* Feature tags */}
            <div className="pt-2 border-t border-slate-100 space-y-1">
              {ch.features.map((feat, idx) => (
                <div key={idx} className="flex items-center space-x-1.5 text-[11px] text-slate-600">
                  <Check className="w-3 h-3 text-emerald-600 shrink-0" />
                  <span className="truncate">{feat}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* ================= RECENT 10 MULTI-PLATFORM POSTS LOG ================= */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden space-y-3 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Nhật ký phân phối nội dung đa kênh
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Theo dõi lịch sử bài đăng, video Shorts và Reels tự động qua hệ thống.
            </p>
          </div>

          {/* Filter channel tabs */}
          <div className="flex flex-wrap items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold">
            {[
              { id: 'all', label: 'Tất cả kênh (4)', icon: null },
              { id: 'facebook', label: 'Facebook', icon: <FacebookIcon className="w-3.5 h-3.5 text-[#1877F2]" /> },
              { id: 'tiktok', label: 'TikTok', icon: <TikTokIcon className="w-3.5 h-3.5" colored /> },
              { id: 'instagram', label: 'Instagram', icon: <InstagramIcon className="w-3.5 h-3.5 text-[#E60064]" /> },
              { id: 'youtube', label: 'YouTube', icon: <YouTubeIcon className="w-3.5 h-3.5 text-[#FF0000]" /> },
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
              </button>
            ))}
          </div>
        </div>

        {/* Posts Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-50/80 text-slate-500 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
              <tr>
                <th className="py-3 px-3">Thời gian</th>
                <th className="py-3 px-3">Nền tảng</th>
                <th className="py-3 px-3">Thương hiệu</th>
                <th className="py-3 px-3">Tiêu đề / Nội dung</th>
                <th className="py-3 px-3">Định dạng</th>
                <th className="py-3 px-3">Trạng thái</th>
                <th className="py-3 px-3 text-right">Xem bài</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {filteredPosts.map((post) => (
                <tr key={post.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-3 text-slate-400 whitespace-nowrap text-[11px]">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span>{post.time}</span>
                    </div>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <PlatformPill platform={post.channel} />
                  </td>
                  <td className="py-3 px-3 font-semibold text-slate-800 whitespace-nowrap">
                    {post.brand}
                  </td>
                  <td className="py-3 px-3 text-slate-900 font-semibold max-w-sm truncate">
                    {post.title}
                  </td>
                  <td className="py-3 px-3 text-slate-500 whitespace-nowrap text-[11px]">
                    {post.type}
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>{post.status}</span>
                    </span>
                  </td>
                  <td className="py-3 px-3 text-right whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => alert(`Mở bài đăng trên ${post.channel}`)}
                      className="text-blue-600 hover:text-blue-700 font-semibold inline-flex items-center space-x-1"
                    >
                      <span>Xem</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
