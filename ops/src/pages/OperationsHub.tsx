import React, { useState } from 'react'
import {
  Users,
  FileText,
  BookOpen,
  Mail,
  BarChart3,
  Kanban,
  DollarSign,
  Calendar,
  Layers,
  ArrowRight,
  Sparkles,
  Bot,
  CheckCircle2,
  AlertCircle,
  Clock,
  ShieldCheck,
  ChevronRight,
  X,
  FileCheck,
  Award,
  Eye,
  Check,
  Briefcase,
  GraduationCap,
  FolderGit2,
  Sliders,
  Play,
  RotateCcw,
} from 'lucide-react'
import { useAuth } from '../lib/auth'

interface HubModuleItem {
  id: string
  title: string
  subtitle: string
  category: 'pipeline' | 'people_knowledge' | 'executive'
  isNew?: boolean
  managedCount: number
  icon: any
  iconBg: string
  iconColor: string
  aiLockedWorkflow: string
  humanReviewRole: string
  aiConfidence: number
  records: {
    id: string
    name: string
    target: string
    aiStatus: string
    updated: string
    humanVerdict: 'pending' | 'approved' | 'review_needed'
    details: string
  }[]
}

const modulesData: HubModuleItem[] = [
  // CỤM PIPELINE PHÍA TRÊN
  {
    id: 'pipe_lead',
    title: 'Lead, tư vấn và chăm sóc lại',
    subtitle: 'Phân loại, nuôi dưỡng và kích hoạt lại tệp khách hàng tiềm năng.',
    category: 'pipeline',
    managedCount: 2,
    icon: Users,
    iconBg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
    aiLockedWorkflow: 'AI tự động bắt SĐT, chấm điểm độ nóng (Lead Score) và kích hoạt kịch bản chăm sóc lại qua Messenger/SMS.',
    humanReviewRole: 'Tư vấn viên kiểm tra danh sách gợi ý và bấm gọi chốt đơn.',
    aiConfidence: 97,
    records: [
      {
        id: 'rec_101',
        name: 'Trần Thị Mai',
        target: 'Khách quan tâm gói Game VIP',
        aiStatus: 'AI đã bắt SĐT 0967***, chuẩn bị bảng giá ưu đãi 15%',
        updated: '10 phút trước',
        humanVerdict: 'pending',
        details: 'Khách hàng có lịch sử hỏi 3 lần về gói bảo hành. AI đề xuất nháp tư vấn chuyên sâu.',
      },
      {
        id: 'rec_102',
        name: 'Lê Hoàng Nam',
        target: 'Chăm sóc lại sau 7 ngày không phản hồi',
        aiStatus: 'AI tự động gửi voucher giảm giá 50k, khách đã mở tin',
        updated: '35 phút trước',
        humanVerdict: 'approved',
        details: 'Khách phản hồi quan tâm lại. Đã chuyển hồ sơ sang trạng thái Đang tư vấn.',
      },
    ],
  },
  {
    id: 'pipe_progress',
    title: 'Lớp học, học phí và tiến độ',
    subtitle: 'Theo dõi khóa đào tạo, thanh toán và lộ trình hoàn thành của học viên.',
    category: 'pipeline',
    managedCount: 2,
    icon: GraduationCap,
    iconBg: 'bg-blue-50',
    iconColor: 'text-blue-600',
    aiLockedWorkflow: 'AI tự động ghi nhận biên lai chuyển khoản, mở quyền truy cập khóa học và đồng bộ lịch học.',
    humanReviewRole: 'Kế toán đối soát sao kê ngân hàng và ký duyệt chứng chỉ.',
    aiConfidence: 99,
    records: [
      {
        id: 'rec_103',
        name: 'Phạm Minh Tú',
        target: 'Lớp Vận Hành Social Pro K12',
        aiStatus: 'AI đã khớp mã giao dịch VCB 2.500.000đ, cấp tài khoản LMS',
        updated: '1 giờ trước',
        humanVerdict: 'approved',
        details: 'Học viên đã vào lớp thành công, tiến độ học bài đạt 15%.',
      },
      {
        id: 'rec_104',
        name: 'Đặng Thu Trang',
        target: 'Gia hạn gói đào tạo thực chiến 3 tháng',
        aiStatus: 'AI gửi email nhắc đóng học phí đợt 2 kèm mã QR chuyển khoản',
        updated: '2 giờ trước',
        humanVerdict: 'pending',
        details: 'Chờ học viên quét mã QR thanh toán.',
      },
    ],
  },

  // CỤM 1: CON NGƯỜI & TRI THỨC (3 PHÂN HỆ)
  {
    id: 'people_recruitment',
    title: 'Tuyển dụng & Nhân sự',
    subtitle: 'Vị trí, ứng viên và onboarding',
    category: 'people_knowledge',
    isNew: true,
    managedCount: 3,
    icon: Users,
    iconBg: 'bg-purple-50',
    iconColor: 'text-purple-600',
    aiLockedWorkflow: 'AI tự động sàng lọc CV ứng viên, chấm điểm độ phù hợp và cấp phát tài liệu onboarding cho nhân viên mới.',
    humanReviewRole: 'Chủ máy phỏng vấn vòng cuối và xác nhận tiếp nhận nhân sự.',
    aiConfidence: 94,
    records: [
      {
        id: 'rec_201',
        name: 'Nguyễn Văn Minh (Ứng viên CSKH)',
        target: 'Vị trí Trực Fanpage Ca Sáng',
        aiStatus: 'AI đã chấm điểm CV 88/100, tạo bài test kịch bản xử lý phản hồi',
        updated: 'Hôm nay 09:30',
        humanVerdict: 'pending',
        details: 'Ứng viên có 2 năm kinh nghiệm chat page thời trang, kỹ năng gõ nhanh 75 wpm.',
      },
      {
        id: 'rec_202',
        name: 'Lê Thuỳ Dung (Thử việc tuần 1)',
        target: 'Onboarding nhân sự mới',
        aiStatus: 'AI tự động giao 5 bài học SOP và kiểm tra trắc nghiệm chính sách',
        updated: 'Hôm qua',
        humanVerdict: 'approved',
        details: 'Đã hoàn thành 100% bài kiểm tra nội quy, sẵn sàng cấp quyền trực ca phụ.',
      },
      {
        id: 'rec_203',
        name: 'Phân ca trực Tuần 40',
        target: '4 nhân sự trực 3 ca',
        aiStatus: 'AI tự động phân ca dựa trên khung giờ cao điểm có nhiều tin nhắn nhất',
        updated: '2 ngày trước',
        humanVerdict: 'approved',
        details: 'Đã thông báo lịch trực tới từng tài khoản qua Telegram bot nội bộ.',
      },
    ],
  },
  {
    id: 'people_contract',
    title: 'Hợp đồng & Tài liệu',
    subtitle: 'Hợp đồng, chữ ký và hạn dùng',
    category: 'people_knowledge',
    isNew: true,
    managedCount: 2,
    icon: FileText,
    iconBg: 'bg-amber-50',
    iconColor: 'text-amber-600',
    aiLockedWorkflow: 'AI tự động bóc tách dữ liệu khách hàng từ CRM điền vào biểu mẫu hợp đồng pháp lý, kiểm tra điều khoản và tạo link ký số.',
    humanReviewRole: 'Quản lý kiểm tra điều khoản đặc biệt và đóng dấu ký duyệt.',
    aiConfidence: 98,
    records: [
      {
        id: 'rec_204',
        name: 'Hợp đồng dịch vụ #HD-2024-089',
        target: 'Khách hàng Công ty Sao Việt',
        aiStatus: 'AI đã điền đủ MST, SĐT, giá trị 18.000.000đ, sẵn sàng ký',
        updated: '14:20',
        humanVerdict: 'pending',
        details: 'Gói chăm sóc 3 fanpage trọn gói trong 6 tháng. Đã bao gồm cam kết SLA phản hồi < 5 phút.',
      },
      {
        id: 'rec_205',
        name: 'Thỏa thuận bảo mật & NDA nhân sự',
        target: 'Tất cả nhân viên vận hành',
        aiStatus: 'AI kiểm tra 100% nhân sự đã ký số và lưu trữ mã hash trên hệ thống',
        updated: '3 ngày trước',
        humanVerdict: 'approved',
        details: 'Thời hạn lưu trữ 3 năm, bảo vệ toàn diện dữ liệu khách hàng.',
      },
    ],
  },
  {
    id: 'people_sop',
    title: 'SOP & tài liệu',
    subtitle: 'Quy trình và tri thức',
    category: 'people_knowledge',
    isNew: true,
    managedCount: 2,
    icon: BookOpen,
    iconBg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
    aiLockedWorkflow: 'AI tự động lập chỉ mục văn bản quy trình chuẩn (SOP), cập nhật kho tri thức và ép chatbot tuân thủ chính sách giá 100%.',
    humanReviewRole: 'Chủ máy cập nhật bảng giá và quy định mới khi có thay đổi.',
    aiConfidence: 100,
    records: [
      {
        id: 'rec_206',
        name: 'SOP Xử Lý Khiếu Nại & Hoàn Tiền',
        target: 'Phiên bản v2.4 (Áp dụng từ 10/2024)',
        aiStatus: 'AI đã nạp tri thức vào vector store, áp dụng cho bộ đề xuất nháp',
        updated: 'Hôm nay',
        humanVerdict: 'approved',
        details: 'Khách khiếu nại quá 24h được tự động gợi ý tặng voucher đền bù 50.000đ.',
      },
      {
        id: 'rec_207',
        name: 'Playbook Tư Vấn Chốt Đơn Gói Game BSN',
        target: 'Bộ kịch bản xử lý từ chối giá cao',
        aiStatus: 'AI đã đối chiếu 15 mẫu câu trả lời chuẩn giọng thương hiệu',
        updated: 'Hôm qua',
        humanVerdict: 'approved',
        details: 'Tỷ lệ nháp được nhân viên duyệt dùng đạt 92% trong 7 ngày qua.',
      },
    ],
  },

  // CỤM 2: ĐIỀU HÀNH & HỖ TRỢ (5 PHÂN HỆ)
  {
    id: 'exec_inbox',
    title: 'Hộp thư xử lý',
    subtitle: 'Email, yêu cầu và phản hồi',
    category: 'executive',
    isNew: true,
    managedCount: 2,
    icon: Mail,
    iconBg: 'bg-blue-50',
    iconColor: 'text-blue-600',
    aiLockedWorkflow: 'AI tự động phân luồng email theo độ khẩn cấp (P1, P2, P3), trích xuất tóm tắt và soạn sẵn email phúc đáp.',
    humanReviewRole: 'Nhân viên phụ trách đọc duyệt trước khi nhấn nút phát hành email.',
    aiConfidence: 95,
    records: [
      {
        id: 'rec_301',
        name: 'Email yêu cầu báo giá doanh nghiệp',
        target: 'Từ đối tác: hoptac@saoviet.edu.vn',
        aiStatus: 'AI đã bóc tách nhu cầu 50 tài khoản, soạn sẵn email phản hồi kèm file PDF',
        updated: '11:15',
        humanVerdict: 'pending',
        details: 'Cần kiểm tra mức chiết khấu trước khi gửi đi.',
      },
      {
        id: 'rec_302',
        name: 'Yêu cầu hỗ trợ kỹ thuật API Graph',
        target: 'Cảnh báo token fanpage hết hạn',
        aiStatus: 'AI tự động làm mới token và kiểm tra kết nối webhook thành công',
        updated: '06:00',
        humanVerdict: 'approved',
        details: 'Hệ thống đã hoạt động bình thường, không gián đoạn tin nhắn khách.',
      },
    ],
  },
  {
    id: 'exec_kpi',
    title: 'KPI & báo cáo',
    subtitle: 'Mục tiêu và kết quả',
    category: 'executive',
    isNew: true,
    managedCount: 2,
    icon: BarChart3,
    iconBg: 'bg-rose-50',
    iconColor: 'text-rose-600',
    aiLockedWorkflow: 'AI tự động tổng hợp số liệu 24/7: thời gian phản hồi trung bình, tỷ lệ chuyển đổi, tỷ lệ sử dụng nháp AI và doanh thu.',
    humanReviewRole: 'Ban giám đốc kiểm tra bảng tổng kết và phê duyệt thưởng hiệu suất.',
    aiConfidence: 100,
    records: [
      {
        id: 'rec_303',
        name: 'Báo cáo hiệu suất ca trực Tuần 39',
        target: '4 nhân sự CSKH',
        aiStatus: 'AI hoàn tất tính toán: 1,420 tin nhắn xử lý, thời gian trung bình 1.8 phút',
        updated: '08:00',
        humanVerdict: 'approved',
        details: 'Nhân viên Trần Văn Minh đạt hiệu suất cao nhất (420 ca, 98% hài lòng).',
      },
      {
        id: 'rec_304',
        name: 'Đo lường độ chính xác của Javis Copilot',
        target: 'Tỷ lệ duyệt nháp AI',
        aiStatus: 'AI ghi nhận 89.4% nháp được gửi đi trực tiếp hoặc chỉnh sửa nhẹ < 10%',
        updated: 'Hôm qua',
        humanVerdict: 'approved',
        details: 'Tiết kiệm ước tính 48 giờ gõ phím cho đội ngũ tư vấn.',
      },
    ],
  },
  {
    id: 'exec_projects',
    title: 'Dự án',
    subtitle: 'Tiến độ và đầu việc lớn',
    category: 'executive',
    managedCount: 2,
    icon: Kanban,
    iconBg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
    aiLockedWorkflow: 'AI tự động gom các tác vụ rời rạc trên bảng Kanban vào mục tiêu dự án lớn và cảnh báo nguy cơ chậm tiến độ.',
    humanReviewRole: 'Project Manager điều phối nguồn lực và nghiệm thu kết quả các mốc.',
    aiConfidence: 96,
    records: [
      {
        id: 'rec_305',
        name: 'Chiến dịch Mở bán Gói Game Mùa Thu',
        target: 'Mục tiêu: 200 đơn hàng trong 14 ngày',
        aiStatus: 'AI tự động theo dõi: Đã đạt 156/200 đơn (78%), còn 4 ngày',
        updated: '12:00',
        humanVerdict: 'pending',
        details: 'Cần đẩy mạnh thêm 2 bài đăng video TikTok để hoàn thành chỉ tiêu.',
      },
      {
        id: 'rec_306',
        name: 'Nâng cấp Hạ tầng VPS Javis Ops 2.0',
        target: 'Tối ưu tốc độ tải và bảo mật dữ liệu',
        aiStatus: 'AI đã chạy script sao lưu SQLite, dọn dẹp log và kiểm thử tải',
        updated: '3 ngày trước',
        humanVerdict: 'approved',
        details: 'Hệ thống vận hành mượt mà, phản hồi < 100ms.',
      },
    ],
  },
  {
    id: 'exec_finance',
    title: 'Tài chính',
    subtitle: 'Thu chi và phê duyệt',
    category: 'executive',
    managedCount: 2,
    icon: DollarSign,
    iconBg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
    aiLockedWorkflow: 'AI tự động quét ảnh chụp sao kê chuyển khoản từ khách hàng, khớp với mã đơn hàng và sinh sẵn Phiếu thu nháp.',
    humanReviewRole: 'Kế toán chỉ cần kiểm tra số tiền và nhấn Duyệt để ghi nhận doanh thu.',
    aiConfidence: 99.2,
    records: [
      {
        id: 'rec_307',
        name: 'Phiếu thu #PT-1049 (Chuyển khoản VCB)',
        target: 'Khách hàng: Nguyễn Thị Hoa (0967 123 456)',
        aiStatus: 'AI đã nhận diện ảnh chụp bill 450.000đ, đúng số tài khoản và nội dung',
        updated: '14:32',
        humanVerdict: 'pending',
        details: 'Chờ kế toán bấm xác nhận để tự động gửi thông báo thanh toán thành công cho khách.',
      },
      {
        id: 'rec_308',
        name: 'Phiếu chi ngân sách quảng cáo Fanpage',
        target: 'Chi phí Meta Ads 7 ngày',
        aiStatus: 'AI tổng hợp hóa đơn tự động từ Meta: 4.800.000đ, chi phí/lead 12.000đ',
        updated: 'Hôm qua',
        humanVerdict: 'approved',
        details: 'Chỉ số ROI đạt 3.8x, hiệu quả vượt kỳ vọng.',
      },
    ],
  },
  {
    id: 'exec_calendar',
    title: 'Lịch & nhắc việc',
    subtitle: 'Lịch công ty và deadline',
    category: 'executive',
    managedCount: 4,
    icon: Calendar,
    iconBg: 'bg-teal-50',
    iconColor: 'text-teal-600',
    aiLockedWorkflow: 'AI tự động bắt các mốc thời gian hẹn trong hội thoại khách hàng, tự lên lịch hẹn và đẩy chuông nhắc nhân viên trước 15 phút.',
    humanReviewRole: 'Nhân viên thực hiện cuộc gọi hoặc họp demo đúng giờ.',
    aiConfidence: 98.5,
    records: [
      {
        id: 'rec_309',
        name: 'Lịch hẹn gọi tư vấn lại cho khách VIP',
        target: 'Khách: Trần Thị Mai - 0967 123 456',
        aiStatus: 'AI tự động ghim lịch vào 15:00 hôm nay theo yêu cầu của khách',
        updated: 'Đang đếm ngược',
        humanVerdict: 'pending',
        details: 'Chuông báo sẽ reo lúc 14:45 để nhân viên chuẩn bị bảng báo giá.',
      },
      {
        id: 'rec_310',
        name: 'Lịch họp bàn giao ca trực chiều',
        target: 'Đội ngũ trực Fanpage',
        aiStatus: 'AI tự động tổng hợp danh sách 8 khách cần lưu ý đặc biệt trong ca',
        updated: '13:00',
        humanVerdict: 'approved',
        details: 'Đã gửi tóm tắt vào nhóm nội bộ.',
      },
      {
        id: 'rec_311',
        name: 'Hạn kiểm tra định kỳ máy chủ VPS',
        target: 'Bảo trì hệ thống định kỳ',
        aiStatus: 'AI tự động kiểm tra dung lượng ổ đĩa (đã dùng 28%) và nhiệt độ CPU',
        updated: '08:00',
        humanVerdict: 'approved',
        details: 'Các chỉ số đều ở mức xanh an toàn tuyệt đối.',
      },
      {
        id: 'rec_312',
        name: 'Nhắc khách hàng gia hạn dịch vụ',
        target: '3 khách hàng sắp hết hạn trong 48h',
        aiStatus: 'AI đã gửi thông báo tự động và ghim lịch follow-up cho nhân viên LT',
        updated: 'Hôm qua',
        humanVerdict: 'pending',
        details: 'Đã có 1 khách phản hồi muốn gia hạn thêm 1 năm.',
      },
    ],
  },
]

export const OperationsHub: React.FC = () => {
  const [selectedModule, setSelectedModule] = useState<HubModuleItem | null>(null)
  const [modules, setModules] = useState<HubModuleItem[]>(modulesData)
  const [filterVerdict, setFilterVerdict] = useState<'all' | 'pending' | 'approved'>('all')

  const handleApproveRecord = (moduleId: string, recordId: string) => {
    setModules((prev) =>
      prev.map((mod) => {
        if (mod.id !== moduleId) return mod
        return {
          ...mod,
          records: mod.records.map((r) =>
            r.id === recordId ? { ...r, humanVerdict: 'approved' as const } : r
          ),
        }
      })
    )
    if (selectedModule && selectedModule.id === moduleId) {
      setSelectedModule((prev) => {
        if (!prev) return null
        return {
          ...prev,
          records: prev.records.map((r) =>
            r.id === recordId ? { ...r, humanVerdict: 'approved' as const } : r
          ),
        }
      })
    }
  }

  // Pipeline modules
  const pipelineModules = modules.filter((m) => m.category === 'pipeline')
  // Con người & tri thức modules
  const peopleModules = modules.filter((m) => m.category === 'people_knowledge')
  // Điều hành & hỗ trợ modules
  const execModules = modules.filter((m) => m.category === 'executive')

  // Total stats
  const totalManaged = modules.reduce((acc, m) => acc + m.managedCount, 0)
  const totalPending = modules.reduce(
    (acc, m) => acc + m.records.filter((r) => r.humanVerdict === 'pending').length,
    0
  )

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* ================= HERO BANNER: TRIẾT LÝ QUY TRÌNH TỰ ĐỘNG & KIỂM ĐỊNH ================= */}
      <div className="bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-3xl p-6 text-white shadow-xl relative overflow-hidden">
        {/* Glow decoration */}
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 rounded-full bg-blue-500/20 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 -mb-20 w-72 h-72 rounded-full bg-purple-500/20 blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-200 text-xs font-semibold">
              <Bot className="w-3.5 h-3.5 text-blue-400" />
              <span>AI Autonomous Pipeline &amp; Human Inspection</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white">
              Trung tâm Con người &amp; Điều hành
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              <strong>Javis AI tự động khóa quy trình hoàn toàn:</strong> Tự động bóc tách tin nhắn, đối chiếu SOP, tạo hợp đồng, nhắc việc và phân loại tài chính.
              <br />
              <span className="text-blue-300 font-semibold">Con người giữ vai trò Trọng tài &amp; Thẩm định:</span> Kiểm tra độ tin cậy, duyệt kết quả và nghiệm thu chất lượng.
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white/10 backdrop-blur-md p-4 rounded-2xl border border-white/10">
            <div className="text-center px-2">
              <div className="text-2xl font-black text-emerald-400">92%</div>
              <div className="text-[10px] text-slate-300 font-medium mt-0.5">Tự động hoá</div>
            </div>
            <div className="text-center px-2 border-l border-white/10">
              <div className="text-2xl font-black text-white">{totalManaged}</div>
              <div className="text-[10px] text-slate-300 font-medium mt-0.5">Hồ sơ quy trình</div>
            </div>
            <div className="text-center px-2 border-l border-white/10">
              <div className="text-2xl font-black text-amber-300">{totalPending}</div>
              <div className="text-[10px] text-slate-300 font-medium mt-0.5">Chờ người duyệt</div>
            </div>
            <div className="text-center px-2 border-l border-white/10">
              <div className="text-2xl font-black text-cyan-300">98.4%</div>
              <div className="text-[10px] text-slate-300 font-medium mt-0.5">Độ chuẩn AI</div>
            </div>
          </div>
        </div>
      </div>

      {/* ================= CỤM PIPELINE KHÁCH HÀNG & DỊCH VỤ ================= */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {pipelineModules.map((item) => {
          const Icon = item.icon
          return (
            <div
              key={item.id}
              onClick={() => setSelectedModule(item)}
              className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs hover:shadow-md transition-all cursor-pointer flex items-center justify-between group"
            >
              <div className="flex items-center space-x-3.5">
                <div className={`w-11 h-11 rounded-2xl ${item.iconBg} ${item.iconColor} flex items-center justify-center shrink-0`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-bold text-slate-900 group-hover:text-blue-600 transition-colors">
                      {item.title}
                    </h3>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{item.managedCount} hồ sơ đang quản lý</p>
                </div>
              </div>
              <div className="flex items-center space-x-2 text-slate-400 group-hover:text-blue-600 transition-colors">
                <span className="text-xs font-semibold hidden sm:inline">Kiểm tra</span>
                <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          )
        })}
      </div>

      {/* ================= CỤM 1: CON NGƯỜI & TRI THỨC (3 PHÂN HỆ) ================= */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight">Con người &amp; tri thức</h2>
            <p className="text-xs text-slate-500 mt-0.5">Tuyển dụng, hồ sơ, hợp đồng và quy trình nội bộ.</p>
          </div>
          <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-bold">
            3 phân hệ
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {peopleModules.map((item) => {
            const Icon = item.icon
            return (
              <div
                key={item.id}
                onClick={() => setSelectedModule(item)}
                className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between h-40 group"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div className={`w-10 h-10 rounded-2xl ${item.iconBg} ${item.iconColor} flex items-center justify-center`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {item.isNew && (
                      <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 text-[10px] font-bold border border-amber-200">
                        mới
                      </span>
                    )}
                  </div>
                  <h3 className="font-bold text-slate-900 text-sm mt-3 group-hover:text-blue-600 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{item.subtitle}</p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-400">
                  <span>{item.managedCount} hồ sơ đang quản lý</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
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
            return (
              <div
                key={item.id}
                onClick={() => setSelectedModule(item)}
                className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between h-40 group"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div className={`w-10 h-10 rounded-2xl ${item.iconBg} ${item.iconColor} flex items-center justify-center`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {item.isNew && (
                      <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 text-[10px] font-bold border border-amber-200">
                        mới
                      </span>
                    )}
                  </div>
                  <h3 className="font-bold text-slate-900 text-sm mt-3 group-hover:text-blue-600 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{item.subtitle}</p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-400">
                  <span>{item.managedCount} hồ sơ đang quản lý</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
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
                onClick={() => setSelectedModule(item)}
                className="bg-white border border-slate-200/80 rounded-2xl p-4 shadow-2xs hover:shadow-md transition-all cursor-pointer flex flex-col justify-between h-40 group"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <div className={`w-10 h-10 rounded-2xl ${item.iconBg} ${item.iconColor} flex items-center justify-center`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {item.isNew && (
                      <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 text-[10px] font-bold border border-amber-200">
                        mới
                      </span>
                    )}
                  </div>
                  <h3 className="font-bold text-slate-900 text-sm mt-3 group-hover:text-blue-600 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{item.subtitle}</p>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs text-slate-400">
                  <span>{item.managedCount} hồ sơ đang quản lý</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ================= MODAL / INSPECTION DRAWER: CON NGƯỜI ĐÁNH GIÁ & DUYỆT ================= */}
      {selectedModule && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6 space-y-5 animate-in zoom-in-95 duration-150 max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-start justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-3">
                <div className={`w-11 h-11 rounded-2xl ${selectedModule.iconBg} ${selectedModule.iconColor} flex items-center justify-center shrink-0`}>
                  <selectedModule.icon className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-bold text-slate-900 text-base">{selectedModule.title}</h3>
                    <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 text-[10px] font-bold border border-blue-200">
                      Độ tin cậy AI: {selectedModule.aiConfidence}%
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">{selectedModule.subtitle}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedModule(null)}
                className="text-slate-400 hover:text-slate-700 p-1 rounded-xl"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* AI Process Locked Banner */}
            <div className="bg-blue-50/80 border border-blue-200/80 rounded-2xl p-4 text-xs space-y-2">
              <div className="flex items-center space-x-1.5 font-bold text-blue-900">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                <span>Quy trình tự động hóa khép kín bởi AI:</span>
              </div>
              <p className="text-slate-700 leading-relaxed">{selectedModule.aiLockedWorkflow}</p>
              <div className="pt-1 text-[11px] text-blue-700 font-medium">
                👉 <strong>Nhiệm vụ của bạn (Human Role):</strong> {selectedModule.humanReviewRole}
              </div>
            </div>

            {/* List of Managed Records */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Hồ sơ đang xử lý ({selectedModule.records.length})
                </h4>
                <div className="text-[11px] text-slate-400">Nhấn Duyệt để hoàn tất kết quả</div>
              </div>

              <div className="space-y-3">
                {selectedModule.records.map((rec) => (
                  <div
                    key={rec.id}
                    className="p-4 rounded-2xl border border-slate-200 bg-white hover:border-slate-300 transition-all space-y-2.5 shadow-2xs"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="font-bold text-slate-900 text-sm">{rec.name}</div>
                        <div className="text-xs text-blue-600 font-medium">{rec.target}</div>
                      </div>
                      <div>
                        {rec.humanVerdict === 'approved' ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-bold">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Đã duyệt kết quả</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 text-[11px] font-bold">
                            <Clock className="w-3.5 h-3.5" />
                            <span>Chờ bạn nghiệm thu</span>
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="bg-slate-50 p-2.5 rounded-xl text-xs space-y-1 border border-slate-100">
                      <div className="flex items-center space-x-1 text-slate-800 font-semibold">
                        <Sparkles className="w-3 h-3 text-purple-600" />
                        <span>AI hoàn thành:</span>
                        <span className="font-normal text-slate-600">{rec.aiStatus}</span>
                      </div>
                      <div className="text-[11px] text-slate-500">{rec.details}</div>
                    </div>

                    <div className="flex items-center justify-between pt-1 text-xs">
                      <span className="text-[11px] text-slate-400">Cập nhật: {rec.updated}</span>
                      <div className="flex items-center space-x-2">
                        {rec.humanVerdict === 'pending' ? (
                          <button
                            type="button"
                            onClick={() => handleApproveRecord(selectedModule.id, rec.id)}
                            className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-sm transition-all cursor-pointer"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Duyệt kết quả</span>
                          </button>
                        ) : (
                          <span className="text-emerald-600 font-semibold text-xs flex items-center space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Hoàn tất quy trình</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedModule(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
