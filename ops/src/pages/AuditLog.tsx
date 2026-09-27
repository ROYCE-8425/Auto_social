import React, { useState, useEffect } from 'react'
import {
  FileText,
  Clock,
  User,
  Bot,
  CheckCircle,
  AlertCircle,
  Search,
  Filter,
} from 'lucide-react'
import { api } from '../lib/api'
import { formatTime, timeAgo } from '../lib/utils'

export const AuditLog: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [search, setSearch] = useState<string>('')

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await api.getAuditLog()
        setLogs(res.items || [])
      } catch {
        // Fallback
      } finally {
        setLoading(false)
      }
    }
    fetchLogs()
  }, [])

  const filteredLogs = logs.filter((l) => {
    if (!search.trim()) return true
    const q = search.toLowerCase()
    return (
      l.title?.toLowerCase().includes(q) ||
      l.message?.toLowerCase().includes(q) ||
      l.source?.toLowerCase().includes(q) ||
      l.actor?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Nhật Ký Xử Lý (Audit Log)</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Ghi nhận toàn bộ thao tác duyệt câu trả lời, gửi tin nhắn, giao việc và quét hệ thống.
          </p>
        </div>

        <div className="relative w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm theo nội dung, tác vụ..."
            className="w-full pl-9 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-saoviet-500"
          />
        </div>
      </div>

      {/* Log list */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm divide-y divide-slate-100 overflow-hidden">
        {filteredLogs.map((item, idx) => (
          <div key={item.id || idx} className="p-4 hover:bg-slate-50/80 transition-colors">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-lg bg-saoviet-50 border border-saoviet-100 text-saoviet-600 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <FileText className="w-4 h-4" />
                </div>

                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-xs text-slate-900">
                      {item.title || item.action || 'Thao tác hệ thống'}
                    </span>
                    {item.source && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 font-medium">
                        {item.source}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                    {item.message || item.text || item.summary || JSON.stringify(item)}
                  </p>
                </div>
              </div>

              <div className="text-right flex-shrink-0">
                <span className="text-[11px] text-slate-400 block">{formatTime(item.timestamp || item.ts)}</span>
                <span className="text-[10px] text-slate-400 italic block mt-0.5">
                  {timeAgo(item.timestamp || item.ts)}
                </span>
              </div>
            </div>
          </div>
        ))}

        {filteredLogs.length === 0 && !loading && (
          <div className="p-12 text-center text-slate-400 text-xs">
            <Clock className="w-8 h-8 mx-auto mb-2 text-slate-300" />
            <span>Chưa có bản ghi nhật ký nào</span>
          </div>
        )}
      </div>
    </div>
  )
}
