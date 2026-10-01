# -*- coding: utf-8 -*-
import sys

def main():
    with open('ops/src/pages/OperationsHub.tsx', 'r', encoding='utf-8') as f:
        text = f.read()

    start_marker = '      {/* ================= CỤM PIPELINE KHÁCH HÀNG & DỊCH VỤ ================= */}'
    end_marker = '      {/* ================= MODAL TRỤ CỘT 09: AI CAMPAIGN AUTOPILOT ================= */}'

    if start_marker not in text:
        print("Start marker not found")
        sys.exit(1)
    if end_marker not in text:
        print("End marker not found")
        sys.exit(1)

    part1 = text[:text.index(start_marker)]
    part3 = text[text.index(end_marker):]

    replacement_content = """      {/* ================= CỤM PIPELINE KHÁCH HÀNG & DỊCH VỤ ================= */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">Quy trình Lead &amp; Bán hàng</h2>
            <p className="text-xs text-slate-500 mt-0.5">Tiếp nhận, phân loại và kích hoạt phễu chốt đơn khách hàng.</p>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200 inline-flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Đang hoạt động</span>
          </span>
        </div>

        {/* Main Card: Lead, tư vấn và chăm sóc lại */}
        <div
          onClick={() => {
            if (onNavigate) onNavigate('customers')
          }}
          className="bg-white border border-slate-200/90 hover:border-emerald-500/50 rounded-3xl p-5 sm:p-6 shadow-2xs hover:shadow-md transition-all cursor-pointer group"
        >
          {/* Card Top Row */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div className="flex items-start sm:items-center space-x-3.5">
              <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 border border-emerald-200/50 group-hover:bg-emerald-600 group-hover:text-white transition-all">
                <Users className="w-6 h-6" />
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="text-base font-bold text-slate-900 group-hover:text-emerald-600 transition-colors">
                    Lead, tư vấn và chăm sóc lại
                  </h3>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200 inline-flex items-center space-x-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span>Đang hoạt động</span>
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Đồng bộ khách hàng tiềm năng, phân loại phễu và kích hoạt quy trình chốt đơn đa kênh.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2 shrink-0">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  if (onNavigate) onNavigate('customers')
                }}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs flex items-center space-x-1.5 transition-all cursor-pointer"
              >
                <span>Mở CRM Lead</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Sub-entrypoints to 4 connected real features */}
          <div className="pt-4 space-y-2.5">
            <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
              Các phân hệ nghiệp vụ thật đã kết nối trong chu trình:
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* Entrypoint 1: Customers / CRM Lead */}
              <div
                onClick={(e) => {
                  e.stopPropagation()
                  if (onNavigate) onNavigate('customers')
                }}
                className="p-3.5 rounded-2xl border border-slate-200/80 bg-slate-50/60 hover:bg-emerald-50/50 hover:border-emerald-300 transition-all flex flex-col justify-between space-y-2 group/sub cursor-pointer"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                      <Users className="w-4 h-4" />
                    </div>
                    <span className="px-2 py-0.5 rounded-md bg-emerald-100/80 text-emerald-700 text-[10px] font-bold">
                      CRM thật
                    </span>
                  </div>
                  <div className="font-bold text-xs text-slate-900 group-hover/sub:text-emerald-700">
                    Khách hàng &amp; CRM Lead
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    Hồ sơ khách hàng, phân loại tệp, số điện thoại và lịch sử tương tác.
                  </p>
                </div>
                <div className="text-[11px] font-semibold text-emerald-600 flex items-center space-x-1 pt-1 border-t border-slate-200/60">
                  <span>Mở Khách hàng</span>
                  <ArrowRight className="w-3 h-3 group-hover/sub:translate-x-0.5 transition-transform" />
                </div>
              </div>

              {/* Entrypoint 2: Inbox / Fanpage Care */}
              <div
                onClick={(e) => {
                  e.stopPropagation()
                  if (onNavigate) onNavigate('inbox')
                }}
                className="p-3.5 rounded-2xl border border-slate-200/80 bg-slate-50/60 hover:bg-blue-50/50 hover:border-blue-300 transition-all flex flex-col justify-between space-y-2 group/sub cursor-pointer"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="w-8 h-8 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
                      <Mail className="w-4 h-4" />
                    </div>
                    <span className="px-2 py-0.5 rounded-md bg-blue-100/80 text-blue-700 text-[10px] font-bold">
                      Phân loại Lead
                    </span>
                  </div>
                  <div className="font-bold text-xs text-slate-900 group-hover/sub:text-blue-700">
                    Hộp thư Fanpage Care
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    Chăm sóc tin nhắn 24h/3d/7d, duyệt tin nhắn nháp AI và tạo việc cứu khách.
                  </p>
                </div>
                <div className="text-[11px] font-semibold text-blue-600 flex items-center space-x-1 pt-1 border-t border-slate-200/60">
                  <span>Mở Hộp thư</span>
                  <ArrowRight className="w-3 h-3 group-hover/sub:translate-x-0.5 transition-transform" />
                </div>
              </div>

              {/* Entrypoint 3: Tasks / Kanban */}
              <div
                onClick={(e) => {
                  e.stopPropagation()
                  if (onNavigate) onNavigate('tasks')
                }}
                className="p-3.5 rounded-2xl border border-slate-200/80 bg-slate-50/60 hover:bg-purple-50/50 hover:border-purple-300 transition-all flex flex-col justify-between space-y-2 group/sub cursor-pointer"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center">
                      <CheckSquare className="w-4 h-4" />
                    </div>
                    <span className="px-2 py-0.5 rounded-md bg-purple-100/80 text-purple-700 text-[10px] font-bold">
                      Kanban thật
                    </span>
                  </div>
                  <div className="font-bold text-xs text-slate-900 group-hover/sub:text-purple-700">
                    Việc cần làm (Tasks)
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    Thẻ cứu lead dừng tương tác, phân công cho nhân viên kỹ thuật và tư vấn.
                  </p>
                </div>
                <div className="text-[11px] font-semibold text-purple-600 flex items-center space-x-1 pt-1 border-t border-slate-200/60">
                  <span>Mở Bảng việc</span>
                  <ArrowRight className="w-3 h-3 group-hover/sub:translate-x-0.5 transition-transform" />
                </div>
              </div>

              {/* Entrypoint 4: Orders */}
              <div
                onClick={(e) => {
                  e.stopPropagation()
                  if (onNavigate) onNavigate('orders')
                }}
                className="p-3.5 rounded-2xl border border-slate-200/80 bg-slate-50/60 hover:bg-amber-50/50 hover:border-amber-300 transition-all flex flex-col justify-between space-y-2 group/sub cursor-pointer"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="w-8 h-8 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center">
                      <ShoppingBag className="w-4 h-4" />
                    </div>
                    <span className="px-2 py-0.5 rounded-md bg-amber-100/80 text-amber-700 text-[10px] font-bold">
                      Đơn hàng thật
                    </span>
                  </div>
                  <div className="font-bold text-xs text-slate-900 group-hover/sub:text-amber-700">
                    Đơn hàng &amp; Chốt sale
                  </div>
                  <p className="text-[11px] text-slate-500 leading-relaxed">
                    Đơn hàng phát sinh từ hội thoại tư vấn và quản lý doanh thu chốt đơn.
                  </p>
                </div>
                <div className="text-[11px] font-semibold text-amber-600 flex items-center space-x-1 pt-1 border-t border-slate-200/60">
                  <span>Mở Đơn hàng</span>
                  <ArrowRight className="w-3 h-3 group-hover/sub:translate-x-0.5 transition-transform" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ================= CỤM 1: CON NGƯỜI & TRI THỨC (3 PHÂN HỆ) ================= */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">Con người &amp; tri thức</h2>
            <p className="text-xs text-slate-500 mt-0.5">Tuyển dụng, hồ sơ, hợp đồng và quy trình nội bộ.</p>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold border border-emerald-200 inline-flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Đã kết nối CSDL vận hành</span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {peopleModules.map((item) => {
            const Icon = item.icon
            return (
              <div
                key={item.id}
                onClick={() => openModule(item)}
                className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between h-40 group"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className={`w-10 h-10 rounded-2xl ${item.iconBg} ${item.iconColor} flex items-center justify-center shrink-0`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-[10px] font-bold border border-blue-200 inline-flex items-center space-x-1 shrink-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                      <span>Đã kết nối</span>
                    </span>
                  </div>
                  <h3 className="font-bold text-slate-900 text-sm mt-3 group-hover:text-blue-600 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{item.subtitle}</p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                  <span className="text-[11px] text-slate-500 truncate max-w-[170px]">Chưa có hồ sơ · Bấm tạo</span>
                  <span className="text-[11px] font-semibold text-blue-600 group-hover:text-blue-700 flex items-center space-x-1 shrink-0">
                    <span>Mở vận hành</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ================= CỤM 2: ĐIỀU HÀNH & HỖ TRỢ (5 PHÂN HỆ) ================= */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">Điều hành &amp; hỗ trợ</h2>
            <p className="text-xs text-slate-500 mt-0.5">Yêu cầu đến, chỉ số quản trị và các nghiệp vụ nền.</p>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-bold">
            5 phân hệ
          </span>
        </div>

        {/* First Row of Executive: 3 cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {execModules.slice(0, 3).map((item) => {
            const Icon = item.icon
            const isActive = item.status === 'active'
            return (
              <div
                key={item.id}
                onClick={() => openModule(item)}
                className={`bg-white border rounded-2xl p-4 shadow-2xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between h-40 group ${
                  isActive ? 'border-blue-200/80 hover:border-blue-400' : 'border-slate-200/80'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className={`w-10 h-10 rounded-2xl ${item.iconBg} ${item.iconColor} flex items-center justify-center shrink-0`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {isActive ? (
                      <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200 inline-flex items-center space-x-1 shrink-0">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span>Đang hoạt động</span>
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 text-[10px] font-semibold border border-slate-200 shrink-0">
                        <span>Đã kết nối</span>
                      </span>
                    )}
                  </div>
                  <h3 className={`font-bold text-sm mt-3 transition-colors ${
                    isActive ? 'text-slate-900 group-hover:text-blue-600' : 'text-slate-900 group-hover:text-blue-600'
                  }`}>
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{item.subtitle}</p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                  <span className="text-[11px] text-slate-500 truncate max-w-[170px]">
                    {isActive ? (item.workbenchLabel || 'Mở màn làm việc') : 'Chưa có hồ sơ · Bấm tạo'}
                  </span>
                  <span className="text-[11px] font-semibold text-blue-600 group-hover:text-blue-700 flex items-center space-x-1 shrink-0">
                    <span>{isActive ? (item.workbenchLabel || 'Mở màn làm việc') : 'Mở vận hành'}</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Second Row of Executive: 2 cards (Tài chính & Lịch nhắc việc) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {execModules.slice(3, 5).map((item) => {
            const Icon = item.icon
            return (
              <div
                key={item.id}
                onClick={() => openModule(item)}
                className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between h-40 group"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className={`w-10 h-10 rounded-2xl ${item.iconBg} ${item.iconColor} flex items-center justify-center shrink-0`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-[10px] font-bold border border-blue-200 inline-flex items-center space-x-1 shrink-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                      <span>Đã kết nối</span>
                    </span>
                  </div>
                  <h3 className="font-bold text-slate-900 text-sm mt-3 group-hover:text-blue-600 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{item.subtitle}</p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                  <span className="text-[11px] text-slate-500 truncate max-w-[200px]">Chưa có hồ sơ · Bấm tạo</span>
                  <span className="text-[11px] font-semibold text-blue-600 group-hover:text-blue-700 flex items-center space-x-1 shrink-0">
                    <span>Mở vận hành</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ================= WORKSPACE VẬN HÀNH THẬT CHO TỪNG PHÂN HỆ ================= */}
      {activeOperationalModule && (
        <ModuleOperationalWorkspace
          module={activeOperationalModule}
          isOpen={!!activeOperationalModule}
          onClose={() => setActiveOperationalModule(null)}
          onModuleUpdated={fetchLiveModules}
          onNavigate={onNavigate}
        />
      )}

"""

    final_text = part1 + replacement_content + part3
    with open('ops/src/pages/OperationsHub.tsx', 'w', encoding='utf-8') as f:
        f.write(final_text)

    print("Updated OperationsHub.tsx successfully!")

if __name__ == '__main__':
    main()
