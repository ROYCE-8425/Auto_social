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
  Target,
  Rocket,
  TrendingUp,
  CheckSquare,
  MessageSquare,
  Zap,
  Loader2,
  Copy,
} from 'lucide-react'
import { useAuth } from '../lib/auth'
import { api, CampaignAutopilotPayload, CampaignAutopilotResponse } from '../lib/api'


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
        name: 'Nâng cấp Hạ tầng VPS Sèo Trum Ops 2.0',
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

  // Trụ cột 09: AI Campaign Autopilot
  const [isAutopilotModalOpen, setIsAutopilotModalOpen] = useState(false)
  const [autopilotLoading, setAutopilotLoading] = useState(false)
  const [autopilotCopied, setAutopilotCopied] = useState(false)
  const [campaignTab, setCampaignTab] = useState<'milestones' | 'calendar' | 'objections' | 'checklist'>('milestones')
  const [campaignForm, setCampaignForm] = useState<CampaignAutopilotPayload>({
    goal: 'Tuyển 50 học viên khóa Tin học MOS thực chiến',
    budget_vnd: 10000000,
    target_revenue_vnd: 50000000,
    duration_weeks: 4,
    platforms: ['facebook', 'tiktok', 'zalo'],
  })
  const [campaignPlan, setCampaignPlan] = useState<CampaignAutopilotResponse['campaign_plan'] | null>(null)

  const handleGenerateAutopilot = async () => {
    setAutopilotLoading(true)
    try {
      const res = await api.createCampaignAutopilot(campaignForm)
      if (res && (res.campaign_plan || res.ok)) {
        setCampaignPlan(res.campaign_plan || (res as any))
      }
    } catch (err) {
      console.error('Lỗi khởi tạo chiến dịch AI Autopilot:', err)
    } finally {
      setAutopilotLoading(false)
    }
  }

  const handleCopyPlan = () => {
    if (!campaignPlan) return
    const text = [
      `=== KẾ HOẠCH CHIẾN DỊCH AI AUTOPILOT ===`,
      `Mục tiêu: ${campaignPlan.goal}`,
      `Ngân sách: ${Number(campaignPlan.budget_vnd || 0).toLocaleString('vi-VN')} đ`,
      `Doanh số kỳ vọng: ${Number(campaignPlan.target_revenue_vnd || 0).toLocaleString('vi-VN')} đ`,
      `Dự phóng ROI: ${campaignPlan.roi_projected || '5.0x'}`,
      ``,
      `--- CÁC MỐC TUẦN (MILESTONES) ---`,
      ...(campaignPlan.milestones || []).map((m) => `Tuần ${m.week}: ${m.theme} | KPI: ${m.kpi_target} | Hành động: ${m.key_action}`),
      ``,
      `--- LỊCH 12 BÀI ĐA NỀN TẢNG ---`,
      ...(campaignPlan.content_calendar || []).map((c) => `Ngày ${c.day} [${(c.platform || '').toUpperCase()}]: Hook: "${c.hook || ''}" -> CTA: "${c.cta || ''}" (Target: ${c.lead_target || 4} leads)`),
      ``,
      `--- KỊCH BẢN XỬ LÝ TỪ CHỐI ---`,
      ...(campaignPlan.sales_objection_playbook || []).map((s) => `Từ chối: "${s.customer_objection}"\n-> Phản hồi: ${s.ai_counter_argument}\n-> Đề nghị chốt: ${s.closing_offer}`),
      ``,
      `--- CHECKLIST NGHIỆM THU ---`,
      ...(campaignPlan.review_checklist || []).map((item, idx) => `[${idx + 1}] ${item}`),
    ].join('\n')

    navigator.clipboard.writeText(text)
    setAutopilotCopied(true)
    setTimeout(() => setAutopilotCopied(false), 2000)
  }


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

      {/* ================= TRỤ CỘT 09: AI CAMPAIGN AUTOPILOT LAUNCHER ================= */}
      <div className="bg-gradient-to-br from-indigo-950 via-slate-900 to-purple-950 border border-indigo-500/30 rounded-3xl p-6 shadow-xl relative overflow-hidden text-white">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-400/30 text-purple-200 text-xs font-semibold">
              <Rocket className="w-3.5 h-3.5 text-purple-400" />
              <span>Trụ cột 09 · AI Campaign Autopilot</span>
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight flex items-center space-x-2">
                <span>Điều phối chiến dịch theo mục tiêu doanh số</span>
              </h2>
              <p className="text-xs sm:text-sm text-slate-300 mt-1.5 leading-relaxed">
                Chỉ cần nhập mục tiêu &amp; ngân sách: AI tự động phân rã lộ trình 4 tuần, thiết kế lịch 12 bài nội dung đa nền tảng (Facebook, TikTok, Zalo), tạo kịch bản xử lý từ chối cho nhân viên tư vấn và bảng kiểm tra nghiệm thu.
              </p>
            </div>

            {/* Feature Pills */}
            <div className="flex flex-wrap gap-2 pt-1 text-xs">
              <span className="px-3 py-1 rounded-xl bg-white/10 border border-white/10 text-slate-200 font-medium flex items-center space-x-1.5">
                <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                <span>Lộ trình 4 tuần đa kênh</span>
              </span>
              <span className="px-3 py-1 rounded-xl bg-white/10 border border-white/10 text-slate-200 font-medium flex items-center space-x-1.5">
                <FileText className="w-3.5 h-3.5 text-blue-400" />
                <span>12 góc nội dung kèm Hook &amp; CTA</span>
              </span>
              <span className="px-3 py-1 rounded-xl bg-white/10 border border-white/10 text-slate-200 font-medium flex items-center space-x-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                <span>Playbook xử lý từ chối giá cao</span>
              </span>
              <span className="px-3 py-1 rounded-xl bg-white/10 border border-white/10 text-slate-200 font-medium flex items-center space-x-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                <span>Ma trận 3 cấp kiểm duyệt</span>
              </span>
            </div>
          </div>

          {/* Action CTA */}
          <div className="shrink-0 w-full lg:w-auto flex flex-col sm:flex-row lg:flex-col gap-3">
            <button
              type="button"
              onClick={() => {
                setIsAutopilotModalOpen(true)
                if (!campaignPlan) {
                  handleGenerateAutopilot()
                }
              }}
              className="flex items-center justify-center space-x-2 px-6 py-3.5 rounded-2xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/25 transition-all transform hover:-translate-y-0.5 cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-purple-200" />
              <span>{campaignPlan ? 'Xem kế hoạch Autopilot' : 'Khởi tạo chiến dịch với AI'}</span>
            </button>
            {campaignPlan && (
              <div className="text-center text-[11px] text-purple-200 font-medium bg-purple-900/40 border border-purple-500/30 px-3 py-1.5 rounded-xl">
                ROI dự phóng: <span className="font-bold text-emerald-400">{campaignPlan.roi_projected}</span> · {(campaignPlan.content_calendar || []).length} bài đăng
              </div>
            )}
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

      {/* ================= MODAL TRỤ CỘT 09: AI CAMPAIGN AUTOPILOT ================= */}
      {isAutopilotModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 overflow-y-auto animate-fade-in">
          <div className="bg-slate-900 border border-slate-700/80 rounded-3xl w-full max-w-5xl text-white shadow-2xl overflow-hidden my-6 max-h-[92vh] flex flex-col">
            {/* Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60 shrink-0">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-2xl bg-purple-500/20 border border-purple-500/40 text-purple-400 flex items-center justify-center">
                  <Rocket className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-base sm:text-lg font-bold text-white">
                      AI Campaign Autopilot
                    </h2>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
                      SME Operations
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Lập kế hoạch chiến dịch 4 tuần, lịch 12 bài nội dung và kịch bản chốt sale
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setIsAutopilotModalOpen(false)}
                className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Scrollable Body */}
            <div className="p-5 overflow-y-auto space-y-6 flex-1 text-slate-200">
              {/* Form Controls */}
              <div className="bg-slate-800/70 border border-slate-700/70 rounded-2xl p-4 space-y-4">
                <div className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
                  <Sliders className="w-3.5 h-3.5 text-purple-400" />
                  <span>Thiết lập mục tiêu chiến dịch</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="sm:col-span-3">
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Mục tiêu kinh doanh / Chương trình
                    </label>
                    <input
                      type="text"
                      value={campaignForm.goal || ''}
                      onChange={(e) => setCampaignForm({ ...campaignForm, goal: e.target.value })}
                      placeholder="VD: Tuyển 50 học viên khóa Tin học MOS thực chiến"
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs sm:text-sm text-white focus:outline-hidden focus:border-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Ngân sách dự kiến (VND)
                    </label>
                    <input
                      type="number"
                      value={campaignForm.budget_vnd || 10000000}
                      onChange={(e) => setCampaignForm({ ...campaignForm, budget_vnd: Number(e.target.value) })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs sm:text-sm text-white focus:outline-hidden focus:border-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Doanh số kỳ vọng (VND)
                    </label>
                    <input
                      type="number"
                      value={campaignForm.target_revenue_vnd || 50000000}
                      onChange={(e) => setCampaignForm({ ...campaignForm, target_revenue_vnd: Number(e.target.value) })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs sm:text-sm text-white focus:outline-hidden focus:border-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Thời gian triển khai
                    </label>
                    <select
                      value={campaignForm.duration_weeks || 4}
                      onChange={(e) => setCampaignForm({ ...campaignForm, duration_weeks: Number(e.target.value) })}
                      className="w-full px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs sm:text-sm text-white focus:outline-hidden focus:border-purple-500"
                    >
                      <option value={2}>2 tuần (Chiến dịch nhanh)</option>
                      <option value={4}>4 tuần (Chu kỳ chuẩn 1 tháng)</option>
                      <option value={6}>6 tuần (Chiến dịch mở rộng)</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <div className="text-[11px] text-slate-400">
                    Phân phối đa kênh: <span className="text-purple-300 font-semibold">Facebook, TikTok, Zalo</span>
                  </div>
                  <button
                    type="button"
                    onClick={handleGenerateAutopilot}
                    disabled={autopilotLoading}
                    className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-bold text-xs shadow-md transition-all cursor-pointer"
                  >
                    {autopilotLoading ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>AI đang phân rã kế hoạch...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Tạo kế hoạch Autopilot mới</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Plan Output if Available */}
              {campaignPlan && (
                <div className="space-y-4">
                  {/* Projected Metrics Strip */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-slate-800/80 border border-slate-700 p-3 rounded-2xl">
                      <div className="text-[11px] text-slate-400">Mục tiêu</div>
                      <div className="text-sm font-bold text-white truncate mt-0.5" title={campaignPlan.goal}>
                        {campaignPlan.goal}
                      </div>
                    </div>
                    <div className="bg-slate-800/80 border border-slate-700 p-3 rounded-2xl">
                      <div className="text-[11px] text-slate-400">Ngân sách</div>
                      <div className="text-sm font-bold text-amber-400 mt-0.5">
                        {Number(campaignPlan.budget_vnd || 10000000).toLocaleString('vi-VN')} đ
                      </div>
                    </div>
                    <div className="bg-slate-800/80 border border-slate-700 p-3 rounded-2xl">
                      <div className="text-[11px] text-slate-400">Doanh thu dự kiến</div>
                      <div className="text-sm font-bold text-emerald-400 mt-0.5">
                        {Number(campaignPlan.target_revenue_vnd || 50000000).toLocaleString('vi-VN')} đ
                      </div>
                    </div>
                    <div className="bg-slate-800/80 border border-slate-700 p-3 rounded-2xl">
                      <div className="text-[11px] text-slate-400">Dự phóng ROI</div>
                      <div className="text-sm font-bold text-cyan-400 mt-0.5">
                        {campaignPlan.roi_projected || '5.0x'}
                      </div>
                    </div>
                  </div>

                  {/* Navigation Tabs */}
                  <div className="flex items-center space-x-1 border-b border-slate-800 pb-2">
                    <button
                      type="button"
                      onClick={() => setCampaignTab('milestones')}
                      className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        campaignTab === 'milestones'
                          ? 'bg-purple-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Lộ trình {(campaignPlan.milestones || []).length} tuần</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setCampaignTab('calendar')}
                      className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        campaignTab === 'calendar'
                          ? 'bg-purple-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Lịch {(campaignPlan.content_calendar || []).length} bài đa kênh</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setCampaignTab('objections')}
                      className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        campaignTab === 'objections'
                          ? 'bg-purple-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      <MessageSquare className="w-3.5 h-3.5" />
                      <span>Xử lý từ chối (Playbook)</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setCampaignTab('checklist')}
                      className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        campaignTab === 'checklist'
                          ? 'bg-purple-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      <CheckSquare className="w-3.5 h-3.5" />
                      <span>Nghiệm thu (Checklist)</span>
                    </button>
                  </div>

                  {/* Tab 1: Milestones */}
                  {campaignTab === 'milestones' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {(campaignPlan.milestones || []).map((m) => (
                        <div
                          key={m.week}
                          className="bg-slate-800/60 border border-slate-700/70 p-4 rounded-2xl space-y-2 hover:border-slate-600 transition-all"
                        >
                          <div className="flex items-center justify-between">
                            <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[11px] font-bold">
                              Tuần {m.week}
                            </span>
                            <span className="text-[11px] text-slate-400">KPI giai đoạn</span>
                          </div>
                          <div className="font-bold text-white text-sm">{m.theme}</div>
                          <div className="bg-slate-900/60 p-2 rounded-xl text-xs space-y-1">
                            <div className="text-emerald-300 font-medium flex items-center space-x-1">
                              <Target className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                              <span>Chỉ tiêu: {m.kpi_target}</span>
                            </div>
                            <div className="text-slate-300 text-[11px] flex items-start space-x-1">
                              <Zap className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                              <span>Hành động chính: {m.key_action}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 2: Content Calendar */}
                  {campaignTab === 'calendar' && (
                    <div className="space-y-2.5">
                      {(campaignPlan.content_calendar || []).map((post, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-800/60 border border-slate-700/70 p-3.5 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 hover:border-slate-600 transition-all"
                        >
                          <div className="space-y-1 max-w-xl">
                            <div className="flex items-center space-x-2">
                              <span className="px-2 py-0.5 rounded-md bg-slate-700 text-slate-200 text-[10px] font-bold">
                                Ngày {post.day}
                              </span>
                              <span
                                className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase ${
                                  post.platform === 'tiktok'
                                    ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                                    : post.platform === 'facebook'
                                    ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                }`}
                              >
                                {post.platform}
                              </span>
                              <span className="text-[11px] text-slate-400">{post.content_type || post.angle}</span>
                            </div>
                            <div className="text-xs sm:text-sm font-semibold text-white">
                              "{post.hook || ''}"
                            </div>
                            <div className="text-[11px] text-slate-400">
                              <span className="text-purple-300 font-medium">CTA chốt:</span> {post.cta}
                            </div>
                          </div>
                          <div className="shrink-0 flex sm:flex-col items-center sm:items-end justify-between w-full sm:w-auto text-xs">
                            <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-bold">
                              +{post.lead_target || 4} Leads
                            </span>
                            <span className="text-[10px] text-slate-400 mt-1">Duyệt cấp 1</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 3: Sales Objections */}
                  {campaignTab === 'objections' && (
                    <div className="space-y-3">
                      {(campaignPlan.sales_objection_playbook || []).map((obj, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-800/60 border border-slate-700/70 p-4 rounded-2xl space-y-2 hover:border-slate-600 transition-all"
                        >
                          <div className="flex items-center space-x-2 text-rose-400 font-bold text-xs sm:text-sm">
                            <AlertCircle className="w-4 h-4 shrink-0" />
                            <span>Khách từ chối: "{obj.customer_objection}"</span>
                          </div>
                          <div className="bg-slate-900/60 p-3 rounded-xl space-y-1.5 text-xs">
                            <div className="text-slate-300">
                              <span className="text-blue-400 font-semibold">AI giải tỏa băn khoăn:</span>{' '}
                              {obj.ai_counter_argument}
                            </div>
                            <div className="text-emerald-300 font-medium">
                              <span className="text-emerald-400 font-semibold">Đòn bẩy chốt đơn:</span>{' '}
                              {obj.closing_offer}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 4: Checklist */}
                  {campaignTab === 'checklist' && (
                    <div className="space-y-2.5">
                      {(campaignPlan.review_checklist || []).map((item, idx) => (
                        <div
                          key={idx}
                          className="bg-slate-800/60 border border-slate-700/70 p-3 rounded-2xl flex items-center space-x-3 text-xs sm:text-sm text-slate-200"
                        >
                          <div className="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0">
                            <Check className="w-4 h-4" />
                          </div>
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between shrink-0">
              <div className="text-[11px] text-slate-400">
                AI Operations Center · Tự động đồng bộ báo cáo và ma trận rủi ro
              </div>
              <div className="flex items-center space-x-2">
                {campaignPlan && (
                  <button
                    type="button"
                    onClick={handleCopyPlan}
                    className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs transition-colors cursor-pointer"
                  >
                    {autopilotCopied ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400">Đã chép kế hoạch!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Sao chép toàn bộ</span>
                      </>
                    )}
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => setIsAutopilotModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-colors cursor-pointer"
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

