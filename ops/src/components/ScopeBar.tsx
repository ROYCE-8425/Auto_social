import React from 'react'
import { Layers, Gamepad2, GraduationCap, ChevronDown, Check } from 'lucide-react'
import { useCareScope } from '../lib/scope'

export const ScopeBar: React.FC = () => {
  const { scope, scopeBrand, scopePageId, eligiblePages, setScope } = useCareScope()

  const bsnPages = eligiblePages.filter((p) => (p.brand || '').toLowerCase().trim() === 'bsn')
  const saoVietPages = eligiblePages.filter((p) => (p.brand || '').toLowerCase().trim() === 'saoviet')

  const isAll = scope === 'all'
  const isBsn = scope === 'brand' && scopeBrand === 'bsn'
  const isSaoViet = scope === 'brand' && scopeBrand === 'saoviet'
  const isPage = scope === 'page'

  return (
    <div className="bg-slate-100/90 border-b border-slate-200/80 px-4 sm:px-6 lg:px-8 py-2">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex items-center space-x-2 text-xs font-semibold text-slate-500 flex-shrink-0">
          <Layers className="w-3.5 h-3.5 text-slate-400" />
          <span>Phạm vi hiển thị:</span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          {/* Tất cả page */}
          <button
            type="button"
            onClick={() => setScope('all')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              isAll
                ? 'bg-slate-900 text-white shadow-2xs'
                : 'bg-white text-slate-700 hover:bg-slate-200/80 border border-slate-200'
            }`}
          >
            {isAll && <Check className="w-3 h-3 text-emerald-400" />}
            <span>Tất cả page</span>
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                isAll ? 'bg-slate-800 text-slate-200' : 'bg-slate-100 text-slate-600'
              }`}
            >
              {eligiblePages.length}
            </span>
          </button>

          {/* Nhóm Game BSN */}
          <button
            type="button"
            onClick={() => setScope('brand', 'bsn')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              isBsn
                ? 'bg-purple-600 text-white shadow-2xs'
                : 'bg-white text-purple-700 hover:bg-purple-50 border border-purple-200'
            }`}
          >
            <Gamepad2 className="w-3.5 h-3.5" />
            {isBsn && <Check className="w-3 h-3 text-white" />}
            <span>Nhóm Game BSN</span>
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                isBsn ? 'bg-purple-700 text-white' : 'bg-purple-100 text-purple-800'
              }`}
            >
              {bsnPages.length}
            </span>
          </button>

          {/* Nhóm Sao Việt */}
          <button
            type="button"
            onClick={() => setScope('brand', 'saoviet')}
            className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              isSaoViet
                ? 'bg-saoviet-600 text-white shadow-2xs'
                : 'bg-white text-saoviet-700 hover:bg-saoviet-50 border border-saoviet-200'
            }`}
          >
            <GraduationCap className="w-3.5 h-3.5" />
            {isSaoViet && <Check className="w-3 h-3 text-white" />}
            <span>Nhóm Sao Việt</span>
            <span
              className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                isSaoViet ? 'bg-saoviet-700 text-white' : 'bg-saoviet-100 text-saoviet-800'
              }`}
            >
              {saoVietPages.length}
            </span>
          </button>

          {/* Dropdown 1 Page cụ thể */}
          <div className="relative inline-block">
            <select
              value={isPage ? scopePageId : ''}
              onChange={(e) => {
                const val = e.target.value
                if (val) {
                  setScope('page', '', val)
                }
              }}
              className={`text-xs font-semibold pl-2.5 pr-7 py-1 rounded-lg appearance-none border transition-all cursor-pointer focus:outline-none focus:ring-1 focus:ring-slate-400 ${
                isPage
                  ? 'bg-blue-600 text-white border-blue-700 shadow-2xs'
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
              }`}
            >
              <option value="" disabled className="text-slate-900 bg-white">
                Chọn 1 Fanpage ▾
              </option>
              {eligiblePages.map((p) => {
                const pid = p.page_id || p.id
                const brandLabel = p.brand === 'bsn' ? '[BSN]' : '[Sao Việt]'
                return (
                  <option key={pid} value={pid} className="text-slate-900 bg-white">
                    {brandLabel} {p.name}
                  </option>
                )
              })}
            </select>
            <ChevronDown
              className={`w-3 h-3 absolute right-2 top-2 pointer-events-none ${
                isPage ? 'text-white' : 'text-slate-400'
              }`}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
