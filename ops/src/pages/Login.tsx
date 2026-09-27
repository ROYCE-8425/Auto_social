import React, { useState } from 'react'
import { Lock, User, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react'
import { useAuth } from '../lib/auth'

export const Login: React.FC = () => {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

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
      setError(err.message || 'Sai tên đăng nhập hoặc mật khẩu')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
      {/* Background glowing gradients */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-saoviet-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-72 h-72 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10 px-4">
        {/* Brand logo */}
        <div className="text-center">
          <div className="inline-flex w-16 h-16 rounded-2xl bg-gradient-to-tr from-saoviet-600 to-saoviet-400 items-center justify-center text-white font-black text-3xl shadow-xl shadow-saoviet-500/20 mb-4">
            JO
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            JAVIS OPS
          </h2>
          <p className="mt-2 text-sm text-slate-400">
            Hệ thống Vận hành CSKH & Quản lý Fanpage
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-slate-800/80 backdrop-blur-xl py-8 px-6 shadow-2xl rounded-2xl border border-slate-700 sm:px-10">
            <form className="space-y-5" onSubmit={handleSubmit}>
              {error && (
                <div className="p-3.5 rounded-xl bg-red-900/30 border border-red-700/50 flex items-start space-x-2 text-red-300 text-xs font-medium animate-in fade-in">
                  <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Tên đăng nhập
                </label>
                <div className="relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <User className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    placeholder="nhanvien / quanly / admin"
                    autoComplete="username"
                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-saoviet-500 focus:border-transparent text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Mật khẩu
                </label>
                <div className="relative rounded-xl shadow-sm">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                    <Lock className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="••••••••"
                    autoComplete="current-password"
                    className="block w-full pl-10 pr-3 py-2.5 bg-slate-900/80 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-saoviet-500 focus:border-transparent text-sm"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center space-x-2 py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-white bg-gradient-to-r from-saoviet-500 to-saoviet-600 hover:from-saoviet-600 hover:to-saoviet-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-slate-900 focus:ring-saoviet-500 disabled:opacity-50 transition-all cursor-pointer"
              >
                <span>{loading ? 'Đang đăng nhập...' : 'Đăng nhập vào hệ thống'}</span>
                {!loading && <ArrowRight className="w-4 h-4" />}
              </button>
            </form>

            <div className="mt-6 pt-5 border-t border-slate-700/60 flex items-center justify-center space-x-2 text-xs text-slate-400">
              <ShieldCheck className="w-4 h-4 text-saoviet-400" />
              <span>Phân quyền RBAC — nhân viên / quản lý / chủ máy</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
