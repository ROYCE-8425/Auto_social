import React from 'react'
import {
  X,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  Database,
  ExternalLink,
  Settings,
  Users,
  ShoppingBag,
  MessageSquare,
  CheckSquare,
  TrendingUp,
  DollarSign,
  Package,
  BookOpen,
  Calendar,
  FileText,
  Briefcase,
  Layers,
} from 'lucide-react'
import { HubSummaryModuleItem } from '../lib/api'

interface OperationsInsightDrawerProps {
  moduleItem: HubSummaryModuleItem | null
  onClose: () => void
  onNavigate?: (path: string) => void
}

const getModuleIcon = (iconName: string) => {
  switch (iconName) {
    case 'Users':
      return Users
    case 'ShoppingBag':
      return ShoppingBag
    case 'MessageSquare':
      return MessageSquare
    case 'CheckSquare':
      return CheckSquare
    case 'TrendingUp':
      return TrendingUp
    case 'DollarSign':
      return DollarSign
    case 'Package':
      return Package
    case 'BookOpen':
      return BookOpen
    case 'Calendar':
      return Calendar
    case 'FileText':
      return FileText
    case 'Briefcase':
      return Briefcase
    default:
      return Layers
  }
}

export const OperationsInsightDrawer: React.FC<OperationsInsightDrawerProps> = ({
  moduleItem,
  onClose,
  onNavigate,
}) => {
  if (!moduleItem) return null

  const IconComponent = getModuleIcon(moduleItem.icon)
  const isNeedsConfig = moduleItem.status === 'needs_config'
  const isWarning = moduleItem.status === 'warning'

  const handleActionClick = (path: string) => {
    onClose()
    if (onNavigate) {
      // If path starts with /ops/, strip it for tab navigation if needed
      const cleanPath = path.startsWith('/ops/') ? path.replace('/ops/', '') : path
      // Extract tab base before query params
      const tabName = cleanPath.split('?')[0]
      onNavigate(tabName)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/60 backdrop-blur-xs flex justify-end transition-opacity animate-in fade-in duration-200">
      <div
        className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full shadow-2xl flex flex-col text-slate-100 overflow-hidden animate-in slide-in-from-right duration-300"
        role="dialog"
        aria-modal="true"
      >
        {/* Top Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3 min-w-0">
            <div className={`w-11 h-11 rounded-2xl flex items-center justify-center shrink-0 border ${
              isNeedsConfig
                ? 'bg-slate-800/80 border-slate-700 text-slate-400'
                : isWarning
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
            }`}>
              <IconComponent className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-base font-bold text-white truncate">{moduleItem.name}</h2>
                {isNeedsConfig ? (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    Needs config
                  </span>
                ) : isWarning ? (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 inline-flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                    Cần xử lý
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 inline-flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    Đang hoạt động
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-400">
                <Database className="w-3 h-3 text-slate-500" />
                <span className="truncate">{moduleItem.data_source_label}</span>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Executive Answers Frame (3 Questions) */}
          <div className="space-y-4">
            {/* Câu hỏi 1: Hôm nay có gì cần xử lý? */}
            <div className="bg-slate-800/40 border border-slate-800 rounded-2xl p-4">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-indigo-500/20 text-indigo-400 text-[10px] flex items-center justify-center font-mono">1</span>
                <span>Hôm nay có gì cần xử lý?</span>
              </div>
              <div className="flex items-baseline gap-3">
                <span className="text-2xl font-black text-white tracking-tight">{moduleItem.kpi.main}</span>
                <span className="text-xs text-slate-400 font-medium">{moduleItem.kpi.label}</span>
              </div>
              {moduleItem.kpi.sub && (
                <div className="mt-1 text-xs text-indigo-300/90 font-medium">
                  → {moduleItem.kpi.sub}
                </div>
              )}
            </div>

            {/* Câu hỏi 2: Dữ liệu thật đang báo vấn đề gì? */}
            <div className={`rounded-2xl p-4 border ${
              isNeedsConfig
                ? 'bg-slate-800/30 border-slate-800'
                : isWarning
                ? 'bg-amber-950/20 border-amber-500/30'
                : 'bg-emerald-950/20 border-emerald-500/30'
            }`}>
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-indigo-500/20 text-indigo-400 text-[10px] flex items-center justify-center font-mono">2</span>
                <span>Dữ liệu thật đang báo vấn đề gì?</span>
              </div>
              <div className="space-y-2">
                {moduleItem.alerts && moduleItem.alerts.length > 0 ? (
                  moduleItem.alerts.map((alt, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 text-xs">
                      {isWarning ? (
                        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      ) : (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      )}
                      <span className={isWarning ? 'text-amber-200' : 'text-slate-300'}>{alt}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-slate-400 italic">Không có cảnh báo tắc nghẽn.</div>
                )}
              </div>
            </div>

            {/* Câu hỏi 3: Bấm vào đâu để hành động ngay? */}
            <div className="bg-slate-800/40 border border-slate-800 rounded-2xl p-4 space-y-3">
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <span className="w-4 h-4 rounded-full bg-indigo-500/20 text-indigo-400 text-[10px] flex items-center justify-center font-mono">3</span>
                <span>Bấm vào đâu để hành động ngay?</span>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => handleActionClick(moduleItem.primary_action.path)}
                  className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
                >
                  <span>{moduleItem.primary_action.label}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>

                {moduleItem.secondary_actions && moduleItem.secondary_actions.length > 0 && (
                  <div className="flex items-center gap-2 pt-1">
                    {moduleItem.secondary_actions.map((sec, sidx) => (
                      <button
                        key={sidx}
                        type="button"
                        onClick={() => handleActionClick(sec.path)}
                        className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs font-semibold border border-slate-700 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
                      >
                        <span>{sec.label}</span>
                        <ExternalLink className="w-3 h-3 text-slate-400" />
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* AI Guidance Recommendation Box */}
          <div className="p-4 rounded-2xl bg-purple-950/30 border border-purple-500/30 space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-purple-300">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>Gợi ý điều phối từ Javis AI</span>
            </div>
            <p className="text-xs text-purple-200 leading-relaxed font-normal">
              {moduleItem.recommended_action}
            </p>
          </div>

          {/* Live Preview Items from Real Database */}
          {moduleItem.has_real_source && moduleItem.preview_items && moduleItem.preview_items.length > 0 && (
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="font-bold uppercase tracking-wider">Hồ sơ / Mục dữ liệu thực tế:</span>
                <span className="text-[11px] text-slate-500">Trích xuất trực tiếp từ CSDL</span>
              </div>

              <div className="space-y-2">
                {moduleItem.preview_items.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleActionClick(item.target)}
                    className="p-3 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-indigo-500/50 transition-all cursor-pointer flex items-center justify-between gap-3 group"
                  >
                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-white group-hover:text-indigo-300 transition-colors truncate">
                          {item.title}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          item.urgent
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-slate-700 text-slate-300'
                        }`}>
                          {item.badge}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 truncate">{item.desc}</p>
                    </div>

                    <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all shrink-0" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Notice for Needs Config (No Mock Data) */}
          {isNeedsConfig && (
            <div className="p-4 rounded-2xl bg-slate-800/60 border border-dashed border-slate-700 space-y-3 text-center">
              <div className="w-10 h-10 rounded-2xl bg-slate-800 text-slate-400 flex items-center justify-center mx-auto border border-slate-700">
                <Settings className="w-5 h-5 text-amber-400" />
              </div>
              <div className="space-y-1">
                <div className="text-xs font-bold text-white">Chưa kết nối nguồn dữ liệu riêng</div>
                <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
                  Phân hệ này cần kết nối API hoặc Webhook từ phần mềm chuyên dụng (HRM, Chấm công, Kho tài sản ngoài).
                  Hệ thống không tạo dữ liệu giả lập để lưu trữ rời rạc.
                </p>
              </div>
              <button
                type="button"
                onClick={() => handleActionClick('/ops/settings?tab=connections')}
                className="px-4 py-2 rounded-xl bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold transition-colors cursor-pointer inline-flex items-center gap-1.5"
              >
                <span>Mở Cài đặt Kết nối</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
