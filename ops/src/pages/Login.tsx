import React, { useState } from 'react'
import {
  Lock,
  User,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  Eye,
  EyeOff,
  Sparkles,
  Radio,
  ExternalLink,
  HelpCircle,
  CheckCircle2,
} from 'lucide-react'
import { useAuth } from '../lib/auth'
import {
  FacebookIcon,
  TikTokIcon,
  InstagramIcon,
  YouTubeIcon,
  XTwitterIcon,
  ZaloIcon,
} from '../components/BrandIcons'

export const Login: React.FC = () => {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedRole, setSelectedRole] = useState<string | null>(null)

  const quickRoles = [
    { id: 'admin', label: 'Chủ máy', icon: '👑', desc: 'Toàn quyền' },
    { id: 'quanly', label: 'Quản lý', icon: '💼', desc: 'Vận hành' },
    { id: 'nhanvien', label: 'CSKH', icon: '🎧', desc: 'Tư vấn' },
  ]

  const handleSelectRole = (roleId: string) => {
    setUsername(roleId)
    setSelectedRole(roleId)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password) {
      setError('Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu')
      return
    }
    setError(null)
    setLoading(true)
    try {
      await login({ username: username.trim(), password })
    } catch (err: any) {
      setError(err?.message || 'Sai tên đăng nhập hoặc mật khẩu')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col justify-between relative overflow-hidden selection:bg-orange-500/30 selection:text-orange-200">
      {/* ================= BACKGROUND AMBIENT GLOWS & GRID ================= */}
      {/* Background Dot Matrix Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#ffffff0d_1px,transparent_1px)] [background-size:28px_28px] pointer-events-none" />

      {/* Ambient glowing radial orbs */}
      <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[700px] h-[500px] bg-gradient-to-b from-orange-500/15 via-amber-500/10 to-transparent rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute -bottom-40 -left-20 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[130px] pointer-events-none" />
      <div className="absolute top-1/3 -right-32 w-[450px] h-[450px] bg-purple-600/10 rounded-full blur-[130px] pointer-events-none" />

      {/* ================= TOP STATUS BAR ================= */}
      <header className="relative z-20 w-full px-6 py-4 flex items-center justify-between max-w-6xl mx-auto">
        <div className="flex items-center space-x-2.5">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]" />
          <span className="text-[11px] font-mono tracking-wider text-slate-400 uppercase">
            Javis OS v25.0 • Live Ops &amp; Social Gateway
          </span>
        </div>

        <a
          href="https://zalo.me/0877104996"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white transition-colors bg-white/5 hover:bg-white/10 px-3 py-1.5 rounded-full border border-white/10 backdrop-blur-md"
        >
          <HelpCircle className="w-3.5 h-3.5 text-orange-400" />
          <span>Hotline: 0877 104 996</span>
          <ExternalLink className="w-2.5 h-2.5 opacity-60" />
        </a>
      </header>

      {/* ================= MAIN HERO LOGIN CONTAINER ================= */}
      <main className="relative z-10 w-full max-w-md mx-auto px-4 py-8 flex flex-col items-center">
        {/* Brand Header */}
        <div className="text-center mb-6">
          <div className="relative inline-block mb-3.5">
            <div className="w-18 h-18 rounded-3xl bg-gradient-to-tr from-orange-600 via-orange-500 to-amber-400 flex items-center justify-center text-white font-black text-3xl shadow-[0_12px_32px_rgba(249,115,22,0.35)] ring-1 ring-white/30 transform hover:scale-105 transition-transform duration-300">
              ST
            </div>
            <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-emerald-500 border-2 border-[#070b14] flex items-center justify-center text-[10px] text-white font-bold shadow-sm">
              ✓
            </div>
          </div>

          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center justify-center gap-2">
            <span>SÈO TRUM OPS</span>
            <span className="text-xs px-2 py-0.5 rounded-md bg-orange-500/20 text-orange-300 border border-orange-500/30 font-bold uppercase tracking-wider">
              PRO
            </span>
          </h1>
          <p className="mt-1 text-xs text-slate-400 max-w-sm">
            Hệ thống Vận hành CSKH &amp; Tự động hóa Đa kênh
          </p>
        </div>

        {/* Glass Card */}
        <div className="w-full bg-slate-900/70 backdrop-blur-2xl p-6 sm:p-8 rounded-3xl border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.6)] relative overflow-hidden">
          {/* Subtle top card border glow */}
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-orange-500/50 to-transparent" />

          {/* Quick Role Fill Pills */}
          <div className="mb-5">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="w-3 h-3 text-orange-400" />
                <span>Chọn vai trò nhanh</span>
              </span>
              <span className="text-[10px] text-slate-500">1-click điền</span>
            </div>

            <div className="grid grid-cols-3 gap-2">
              {quickRoles.map((r) => {
                const isActive = selectedRole === r.id || username === r.id
                return (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => handleSelectRole(r.id)}
                    className={`py-2 px-2.5 rounded-xl border text-xs font-semibold flex flex-col items-center justify-center transition-all cursor-pointer ${
                      isActive
                        ? 'bg-orange-500/20 border-orange-500/60 text-white shadow-sm shadow-orange-500/20'
                        : 'bg-white/5 border-white/10 text-slate-300 hover:bg-white/10 hover:border-white/20'
                    }`}
                  >
                    <span className="text-sm leading-none mb-1">{r.icon}</span>
                    <span className="text-[11px] font-bold">{r.label}</span>
                    <span className="text-[9px] text-slate-400">{r.desc}</span>
                  </button>
                )
              })}
            </div>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            {error && (
              <div className="p-3.5 rounded-xl bg-rose-500/15 border border-rose-500/40 flex items-start space-x-2.5 text-rose-300 text-xs font-medium animate-in fade-in duration-200">
                <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
                <span className="leading-relaxed">{error}</span>
              </div>
            )}

            {/* Username Field */}
            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5">
                Tên đăng nhập
              </label>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-orange-400 transition-colors">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value)
                    setSelectedRole(null)
                  }}
                  required
                  placeholder="nhanvien / quanly / admin"
                  autoComplete="username"
                  className="block w-full pl-10 pr-3.5 py-2.5 bg-slate-950/80 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500/40 focus:border-orange-500/80 text-sm transition-all"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-bold text-slate-300">
                  Mật khẩu
                </label>
                <a
                  href="https://zalo.me/0877104996"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[11px] text-orange-400 hover:text-orange-300 transition-colors"
                >
                  Quên mật khẩu?
                </a>
              </div>
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500 group-focus-within:text-orange-400 transition-colors">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="Nhập mật khẩu của bạn"
                  autoComplete="current-password"
                  className="block w-full pl-10 pr-10 py-2.5 bg-slate-950/80 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500/40 focus:border-orange-500/80 text-sm transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-500 hover:text-slate-300 cursor-pointer transition-colors"
                  title={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center space-x-2 text-xs text-slate-400 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-950 text-orange-500 focus:ring-orange-500/30 focus:ring-offset-slate-900 w-3.5 h-3.5 cursor-pointer"
                />
                <span>Ghi nhớ phiên đăng nhập (30 ngày)</span>
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-orange-500 via-amber-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500/50 shadow-lg shadow-orange-500/25 active:scale-[0.99] disabled:opacity-50 transition-all cursor-pointer mt-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Đang xác thực bảo mật...</span>
                </>
              ) : (
                <>
                  <span>Đăng nhập vào hệ thống</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Social Platforms Integrated Strip */}
          <div className="mt-6 pt-5 border-t border-white/10 text-center">
            <span className="text-[10px] text-slate-500 font-medium tracking-wider uppercase block mb-2.5">
              Hệ thống kết nối đa nền tảng
            </span>
            <div className="flex items-center justify-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400 flex items-center justify-center" title="Facebook & Messenger">
                <FacebookIcon className="w-3.5 h-3.5" />
              </div>
              <div className="w-7 h-7 rounded-lg bg-slate-800 border border-white/20 text-white flex items-center justify-center" title="TikTok Video & Carousel">
                <TikTokIcon className="w-3.5 h-3.5" />
              </div>
              <div className="w-7 h-7 rounded-lg bg-slate-800 border border-white/20 text-white flex items-center justify-center" title="X (Twitter)">
                <XTwitterIcon className="w-3.5 h-3.5" />
              </div>
              <div className="w-7 h-7 rounded-lg bg-pink-600/20 border border-pink-500/30 text-pink-400 flex items-center justify-center" title="Instagram Photo & Reels">
                <InstagramIcon className="w-3.5 h-3.5" />
              </div>
              <div className="w-7 h-7 rounded-lg bg-red-600/20 border border-red-500/30 text-red-400 flex items-center justify-center" title="YouTube Shorts">
                <YouTubeIcon className="w-3.5 h-3.5" />
              </div>
              <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-400/30 text-blue-300 flex items-center justify-center" title="Zalo OA & CSKH">
                <ZaloIcon className="w-3.5 h-3.5" />
              </div>
            </div>

            <div className="mt-4 flex items-center justify-center space-x-1.5 text-[11px] text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 text-orange-400" />
              <span>Phân quyền RBAC chuẩn hóa • Chủ máy / Quản lý / CSKH</span>
            </div>
          </div>
        </div>
      </main>

      {/* ================= FOOTER ================= */}
      <footer className="relative z-20 py-4 px-6 text-center text-xs text-slate-500 border-t border-white/5">
        <p>
          © 2026 Sèo Trum Ops • Nền tảng Điều hành &amp; Tự động hóa Bán hàng Đa kênh.
        </p>
      </footer>
    </div>
  )
}
