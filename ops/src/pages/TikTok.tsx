import React, { useState, useEffect } from 'react'
import {
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
} from 'lucide-react'
import { api, TikTokStatusResponse, TikTokPostItem } from '../lib/api'
import { useAuth } from '../lib/auth'

export const TikTokPage: React.FC = () => {
  const { role } = useAuth()
  const [data, setData] = useState<TikTokStatusResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadStatus = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await api.getTikTokStatus()
      setData(res)
    } catch (err: any) {
      setError(err.message || 'Không thể tải thông tin kênh TikTok')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadStatus()
    const interval = setInterval(loadStatus, 20000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-pink-500 via-rose-500 to-red-500 flex items-center justify-center text-white shadow-md shadow-rose-500/20">
            <Video className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              Kênh TikTok Carousel
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                View-Only
              </span>
            </h1>
            <p className="text-sm text-slate-500">
              Giám sát 10 bài đăng carousel 9:16 gần nhất và trạng thái vòng lặp tự động.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadStatus}
            disabled={isLoading}
            className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin text-rose-500' : ''}`} />
            Làm mới
          </button>
        </div>
      </div>

      {/* Security notice for staff */}
      <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="text-xs sm:text-sm text-amber-800">
          <p className="font-semibold mb-0.5">Phân quyền vận hành: Nhân viên & Quản lý</p>
          <p>
            Nhân viên chỉ có quyền <strong>xem trạng thái và nhật ký bài đăng</strong>. Chức năng đăng bài thật, tải ảnh lên kho dataset và thay đổi mã khóa PostPeer API chỉ được mở cho <strong>Chủ máy</strong> tại Buồng lái chính <code className="bg-amber-100/80 px-1 py-0.5 rounded font-mono">/app</code>. Mọi yêu cầu đăng bài trực tiếp từ tài khoản Staff sẽ bị máy chủ từ chối (403 Forbidden).
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 flex items-center gap-3 text-rose-700 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Overview stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Connection status */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Kết nối PostPeer
              </span>
              {data?.connected ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Đã kết nối
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                  <AlertCircle className="w-3.5 h-3.5" />
                  Chưa nối
                </span>
              )}
            </div>
            <div className="text-lg font-bold text-slate-900">
              {data?.accounts && data.accounts.length > 0 ? (
                data.accounts.map((a) => a.username || a.name).join(', ')
              ) : (
                '@seotrum'
              )}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Khóa API: <span className="font-mono">{data?.masked_key || 'Chưa cấu hình'}</span>
            </p>
          </div>
          <div className="pt-4 border-t border-slate-100 mt-4 text-xs text-slate-500 flex items-center justify-between">
            <span>Tài khoản tích hợp:</span>
            <span className="font-semibold text-slate-700">{data?.accounts?.length || 0} nick</span>
          </div>
        </div>

        {/* Auto loop status */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Vòng lặp tự động (Loop)
              </span>
              {data?.loop?.enabled ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                  Đang Bật
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                  Mặc định Tắt
                </span>
              )}
            </div>
            <div className="text-lg font-bold text-slate-900">
              dang-video-tiktok-hang-ngay
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Trạng thái: {data?.loop?.status || 'Đang tắt (an toàn)'}
            </p>
          </div>
          <div className="pt-4 border-t border-slate-100 mt-4 text-xs text-slate-500 flex items-center justify-between">
            <span>Tự chèn nhạc:</span>
            <span className="font-semibold text-emerald-600 flex items-center gap-1">
              <Music className="w-3.5 h-3.5" /> Bật (autoAddMusic)
            </span>
          </div>
        </div>

        {/* Brand kits */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Thương hiệu hỗ trợ
              </span>
              <span className="text-xs text-slate-500 font-medium">
                {data?.kits?.length || 0} Kit
              </span>
            </div>
            <div className="space-y-2">
              {data?.kits?.map((k) => (
                <div key={k.file} className="flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-800">{k.name}</span>
                  <span className="font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                    {k.username || (k.account_id ? `${k.account_id.substring(0, 8)}...` : 'Chưa gán')}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="pt-4 border-t border-slate-100 mt-4 text-xs text-slate-500 flex items-center justify-between">
            <span>Định dạng chuẩn:</span>
            <span className="font-semibold text-slate-700 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5" /> 4–6 ảnh 9:16 dọc
            </span>
          </div>
        </div>
      </div>

      {/* Recent 10 Posts Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              Nhật ký 10 bài đăng TikTok gần nhất
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Dữ liệu được lưu trong tệp JSONL của máy chủ (<code className="font-mono">tiktok-posts.jsonl</code>)
            </p>
          </div>
          <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-3 py-1 rounded-full">
            {data?.recent_posts?.length || 0} bài gần đây
          </span>
        </div>

        {(!data?.recent_posts || data.recent_posts.length === 0) ? (
          <div className="p-12 text-center text-slate-400">
            <ImageIcon className="w-12 h-12 mx-auto mb-3 text-slate-300 stroke-1" />
            <p className="text-sm font-medium text-slate-600">Chưa có bài đăng nào được ghi nhận</p>
            <p className="text-xs text-slate-400 mt-1">
              Chủ máy có thể bấm nút [Đăng thử] trong Buồng lái /app để đăng carousel đầu tiên.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500 font-semibold text-xs border-b border-slate-200 uppercase tracking-wider">
                <tr>
                  <th className="px-5 py-3.5">Thời gian</th>
                  <th className="px-5 py-3.5">Thương hiệu / Kit</th>
                  <th className="px-5 py-3.5">Tài khoản</th>
                  <th className="px-5 py-3.5">Số ảnh</th>
                  <th className="px-5 py-3.5">Trạng thái</th>
                  <th className="px-5 py-3.5">Nội dung tóm tắt</th>
                  <th className="px-5 py-3.5 text-right">Chi tiết</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {data.recent_posts.map((p, idx) => (
                  <tr key={p.postpeer_id || idx} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-5 py-4 whitespace-nowrap text-xs text-slate-500">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{p.datetime || new Date(p.ts * 1000).toLocaleString('vi-VN')}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 font-semibold text-slate-800 text-xs">
                      <span className="capitalize">{p.brand || 'BSN'}</span>
                      <div className="text-[11px] text-slate-400 font-normal truncate max-w-[150px]">
                        {p.kit}
                      </div>
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap text-xs font-mono text-slate-600">
                      {p.username || `@${p.accountId?.substring(0, 8) || 'seotrum'}`}
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap text-xs">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-100 font-medium text-slate-700">
                        <ImageIcon className="w-3 h-3 text-slate-500" />
                        {p.photos_count || p.urls?.length || 0} ảnh
                      </span>
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap text-xs">
                      {p.draft ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                          Hộp thư nháp
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Đã đăng
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-xs text-slate-600 max-w-xs truncate">
                      {p.caption || '—'}
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap text-right text-xs">
                      {p.tiktok_url ? (
                        <a
                          href={p.tiktok_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-rose-600 hover:text-rose-700 font-medium"
                        >
                          Xem bài <ExternalLink className="w-3.5 h-3.5" />
                        </a>
                      ) : (
                        <span className="text-slate-400 font-mono text-[11px]">
                          ID: {p.postpeer_id ? `${p.postpeer_id.substring(0, 8)}...` : '—'}
                        </span>
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
