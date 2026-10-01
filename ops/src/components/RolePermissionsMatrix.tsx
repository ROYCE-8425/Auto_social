import React, { useState, useEffect, useMemo } from 'react'
import {
  ShieldCheck,
  Shield,
  RotateCcw,
  Save,
  Check,
  X,
  Search,
  Filter,
  Users,
  Lock,
  Layers,
  Table,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Info,
  Sliders,
  Sparkles,
  RefreshCw,
} from 'lucide-react'
import {
  api,
  RbacCategory,
  RbacRoleInfo,
  RbacPermissionItem,
} from '../lib/api'
import { useAuth } from '../lib/auth'

interface RolePermissionsMatrixProps {
  onSaved?: () => void
}

export const RolePermissionsMatrix: React.FC<RolePermissionsMatrixProps> = ({ onSaved }) => {
  const { user, role: currentUserRole } = useAuth()
  const isOwner = currentUserRole === 'owner' || (currentUserRole as string) === 'admin'

  const [roles, setRoles] = useState<Record<string, RbacRoleInfo>>({})
  const [catalog, setCatalog] = useState<RbacCategory[]>([])
  const [matrix, setMatrix] = useState<Record<string, string[]>>({})
  const [defaultMatrix, setDefaultMatrix] = useState<Record<string, string[]>>({})
  const [initialMatrix, setInitialMatrix] = useState<Record<string, string[]>>({})

  const [selectedRole, setSelectedRole] = useState<string>('manager')
  const [viewMode, setViewMode] = useState<'by_role' | 'matrix_table'>('by_role')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState<string>('')

  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [isSaving, setIsSaving] = useState<boolean>(false)
  const [isResetting, setIsResetting] = useState<boolean>(false)
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  // Tự động ẩn toast sau 4 giây
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000)
      return () => clearTimeout(timer)
    }
  }, [toast])

  const loadPermissionsData = async () => {
    setIsLoading(true)
    try {
      const res = await api.getRbacPermissions()
      setRoles(res.roles || {})
      setCatalog(res.catalog || [])
      setMatrix(res.matrix || {})
      setDefaultMatrix(res.default_matrix || {})
      setInitialMatrix(JSON.parse(JSON.stringify(res.matrix || {})))

      // Nếu role đang chọn không tồn tại, chọn role đầu tiên khác owner
      const roleKeys = Object.keys(res.roles || {}).filter((k) => k !== 'owner')
      if (roleKeys.length > 0 && !res.roles[selectedRole]) {
        setSelectedRole(roleKeys[0])
      }
    } catch (err: any) {
      setToast({
        type: 'error',
        message: err.message || 'Không thể tải dữ liệu phân quyền RBAC',
      })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadPermissionsData()
  }, [])

  // Kiểm tra có thay đổi chưa lưu hay không
  const hasChanges = useMemo(() => {
    if (!initialMatrix || !matrix) return false
    return JSON.stringify(matrix) !== JSON.stringify(initialMatrix)
  }, [matrix, initialMatrix])

  // Danh sách các vai trò (sắp xếp theo level giảm dần)
  const sortedRoleKeys = useMemo(() => {
    return Object.keys(roles).sort((a, b) => {
      const levelA = roles[a]?.level || 0
      const levelB = roles[b]?.level || 0
      return levelB - levelA
    })
  }, [roles])

  // Lấy toàn bộ ID quyền hạn trong catalog
  const allPermissionIds = useMemo(() => {
    const ids: string[] = []
    catalog.forEach((cat) => {
      cat.permissions.forEach((p) => ids.push(p.id))
    })
    return ids
  }, [catalog])

  // Toggle một quyền hạn cho vai trò cụ thể
  const handleToggle = (roleKey: string, permId: string) => {
    if (!isOwner) {
      setToast({
        type: 'error',
        message: 'Chỉ có Chủ sở hữu (Owner) mới có quyền chỉnh sửa ma trận phân quyền',
      })
      return
    }
    if (roleKey === 'owner') return // Owner luôn toàn quyền

    setMatrix((prev) => {
      const currentPerms = prev[roleKey] || []
      const exists = currentPerms.includes(permId)
      const nextPerms = exists
        ? currentPerms.filter((id) => id !== permId)
        : [...currentPerms, permId]
      return {
        ...prev,
        [roleKey]: nextPerms,
      }
    })
  }

  // Chọn tất cả quyền cho vai trò hiện tại
  const handleSelectAll = (roleKey: string) => {
    if (!isOwner || roleKey === 'owner') return
    setMatrix((prev) => ({
      ...prev,
      [roleKey]: [...allPermissionIds],
    }))
  }

  // Bỏ chọn tất cả quyền cho vai trò hiện tại
  const handleDeselectAll = (roleKey: string) => {
    if (!isOwner || roleKey === 'owner') return
    setMatrix((prev) => ({
      ...prev,
      [roleKey]: [],
    }))
  }

  // Khôi phục vai trò hiện tại về mặc định
  const handleResetRoleToDefault = (roleKey: string) => {
    if (!isOwner || roleKey === 'owner') return
    const def = defaultMatrix[roleKey] || []
    setMatrix((prev) => ({
      ...prev,
      [roleKey]: [...def],
    }))
    setToast({
      type: 'success',
      message: `Đã hoàn tác quyền của vai trò [${roles[roleKey]?.title || roleKey}] về chuẩn mặc định.`,
    })
  }

  // Lưu cấu hình phân quyền lên server
  const handleSave = async () => {
    if (!isOwner) return
    setIsSaving(true)
    try {
      const res = await api.saveRbacPermissions(matrix)
      if (res.ok) {
        setMatrix(res.matrix)
        setInitialMatrix(JSON.parse(JSON.stringify(res.matrix)))
        setToast({
          type: 'success',
          message: 'Lưu cấu hình phân quyền thành công! Hệ thống đã kích hoạt phân quyền mới ngay lập tức.',
        })
        if (onSaved) onSaved()
      }
    } catch (err: any) {
      setToast({
        type: 'error',
        message: err.message || 'Không thể lưu ma trận phân quyền',
      })
    } finally {
      setIsSaving(false)
    }
  }

  // Khôi phục toàn bộ ma trận về mặc định ban đầu
  const handleResetAll = async () => {
    if (!isOwner) return
    if (!window.confirm('Bạn có chắc chắn muốn khôi phục toàn bộ phân quyền về cấu hình mặc định chuẩn ban đầu?')) {
      return
    }
    setIsResetting(true)
    try {
      const res = await api.resetRbacPermissions()
      if (res.ok) {
        setMatrix(res.matrix)
        setInitialMatrix(JSON.parse(JSON.stringify(res.matrix)))
        setToast({
          type: 'success',
          message: 'Đã khôi phục ma trận phân quyền về mặc định thành công!',
        })
        if (onSaved) onSaved()
      }
    } catch (err: any) {
      setToast({
        type: 'error',
        message: err.message || 'Lỗi khi khôi phục phân quyền',
      })
    } finally {
      setIsResetting(false)
    }
  }

  // Lọc catalog theo category và search
  const filteredCatalog = useMemo(() => {
    return catalog
      .filter((cat) => {
        if (selectedCategory === 'all') return true
        return cat.category === selectedCategory
      })
      .map((cat) => {
        if (!searchQuery.trim()) return cat
        const q = searchQuery.toLowerCase()
        const matched = cat.permissions.filter(
          (p) =>
            p.name.toLowerCase().includes(q) ||
            p.id.toLowerCase().includes(q) ||
            p.description.toLowerCase().includes(q)
        )
        return {
          ...cat,
          permissions: matched,
        }
      })
      .filter((cat) => cat.permissions.length > 0)
  }, [catalog, selectedCategory, searchQuery])

  // Lấy màu badge cho vai trò
  const getBadgeStyle = (color?: string) => {
    switch (color) {
      case 'purple':
        return 'bg-purple-50 text-purple-700 border-purple-200'
      case 'indigo':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200'
      case 'blue':
        return 'bg-blue-50 text-blue-700 border-blue-200'
      case 'emerald':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200'
      case 'amber':
        return 'bg-amber-50 text-amber-700 border-amber-200'
      case 'pink':
        return 'bg-pink-50 text-pink-700 border-pink-200'
      case 'cyan':
        return 'bg-cyan-50 text-cyan-700 border-cyan-200'
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200'
    }
  }

  if (isLoading) {
    return (
      <div className="bg-white border border-slate-200/80 rounded-2xl p-12 text-center space-y-3">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto" />
        <p className="text-sm font-semibold text-slate-700">Đang tải ma trận phân quyền vai trò...</p>
        <p className="text-xs text-slate-400">Đang đồng bộ danh mục quyền và cấu hình RBAC từ máy chủ</p>
      </div>
    )
  }

  const currentRoleInfo = roles[selectedRole] || {
    title: selectedRole,
    code: selectedRole.toUpperCase(),
    badge_color: 'slate',
    description: '',
    level: 30,
  }

  const grantedCount = selectedRole === 'owner' ? allPermissionIds.length : (matrix[selectedRole] || []).length

  return (
    <div className="space-y-6">
      {/* Toast Alert */}
      {toast && (
        <div
          className={`p-4 rounded-xl border flex items-center justify-between shadow-lg transition-all animate-fade-in ${
            toast.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
              : 'bg-rose-50 border-rose-200 text-rose-900'
          }`}
        >
          <div className="flex items-center space-x-3">
            {toast.type === 'success' ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            )}
            <span className="text-xs font-semibold">{toast.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setToast(null)}
            className="text-slate-400 hover:text-slate-600 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header Container */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-2xs space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center space-x-2">
              <span className="p-1.5 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-600">
                <Sliders className="w-5 h-5" />
              </span>
              <h2 className="text-base font-bold text-slate-900">
                Thiết Lập Phân Quyền Vai Trò (Role Permissions Matrix)
              </h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200">
                Fail-Closed Active
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-2xl">
              Cấu hình các quyền hạn được phép thực thi đối với từng vị trí nhân sự (Manager, CSKH, Sales, Kho, Marketing, Kỹ thuật).
              {isOwner ? (
                <span className="text-indigo-600 font-semibold ml-1">
                  Chủ máy có thể bật/tắt từng quyền và bấm [Lưu cấu hình] để áp dụng ngay lập tức.
                </span>
              ) : (
                <span className="text-amber-600 font-semibold ml-1">
                  (Chế độ xem: Chỉ Chủ sở hữu mới có quyền chỉnh sửa ma trận).
                </span>
              )}
            </p>
          </div>

          {/* Right Header Action Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200/80 text-xs">
              <button
                type="button"
                onClick={() => setViewMode('by_role')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                  viewMode === 'by_role'
                    ? 'bg-white text-indigo-700 shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Theo từng vai trò</span>
              </button>
              <button
                type="button"
                onClick={() => setViewMode('matrix_table')}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                  viewMode === 'matrix_table'
                    ? 'bg-white text-indigo-700 shadow-2xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Table className="w-3.5 h-3.5" />
                <span>Bảng ma trận tổng thể</span>
              </button>
            </div>

            {/* Reset to Default Button */}
            {isOwner && (
              <button
                type="button"
                onClick={handleResetAll}
                disabled={isResetting || isSaving}
                className="flex items-center space-x-1 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
                title="Khôi phục toàn bộ phân quyền về chuẩn mặc định"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin text-amber-600' : ''}`} />
                <span>Khôi phục chuẩn</span>
              </button>
            )}

            {/* Save Button */}
            {isOwner && (
              <button
                type="button"
                onClick={handleSave}
                disabled={isSaving || !hasChanges}
                className={`flex items-center space-x-1.5 px-4 py-1.5 rounded-xl text-xs font-bold transition-all shadow-2xs cursor-pointer ${
                  hasChanges
                    ? 'bg-emerald-600 hover:bg-emerald-700 text-white animate-pulse'
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-50'
                }`}
              >
                {isSaving ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Save className="w-3.5 h-3.5" />
                )}
                <span>{hasChanges ? 'Lưu thay đổi (*)' : 'Lưu cấu hình'}</span>
              </button>
            )}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* VIEW MODE 1: THEO TỪNG VAI TRÒ (BY ROLE CONFIGURATOR) */}
        {/* ========================================================================= */}
        {viewMode === 'by_role' && (
          <div className="space-y-6">
            {/* Role Tabs Strip */}
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                Chọn vai trò để thiết lập quyền hạn:
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
                {sortedRoleKeys.map((rKey) => {
                  const r = roles[rKey]
                  const isSelected = selectedRole === rKey
                  const pCount = rKey === 'owner' ? allPermissionIds.length : (matrix[rKey] || []).length
                  const isOwnerRole = rKey === 'owner'

                  return (
                    <button
                      key={rKey}
                      type="button"
                      onClick={() => setSelectedRole(rKey)}
                      className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer relative flex flex-col justify-between ${
                        isSelected
                          ? 'bg-indigo-50/80 border-indigo-400 ring-2 ring-indigo-500/20 shadow-xs'
                          : 'bg-slate-50/60 border-slate-200/80 hover:bg-white hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between w-full mb-1">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider border ${getBadgeStyle(
                            r?.badge_color
                          )}`}
                        >
                          {r?.code || rKey.toUpperCase()}
                        </span>
                        {isOwnerRole && <Lock className="w-3 h-3 text-purple-600" />}
                      </div>

                      <div className="truncate text-xs font-bold text-slate-800" title={r?.title}>
                        {r?.title?.split('/')[0]?.trim() || rKey}
                      </div>

                      <div className="mt-2 flex items-center justify-between text-[10px]">
                        <span className="text-slate-500 font-mono">
                          {isOwnerRole ? 'Toàn quyền' : `${pCount}/${allPermissionIds.length}`}
                        </span>
                        <div
                          className={`w-2 h-2 rounded-full ${
                            pCount > 0 ? 'bg-emerald-500' : 'bg-slate-300'
                          }`}
                        />
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Selected Role Summary Banner */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-slate-50 via-indigo-50/40 to-slate-50 border border-indigo-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2 py-0.5 rounded-md text-xs font-extrabold border ${getBadgeStyle(
                      currentRoleInfo.badge_color
                    )}`}
                  >
                    {currentRoleInfo.code}
                  </span>
                  <h3 className="text-sm font-bold text-slate-900">{currentRoleInfo.title}</h3>
                  <span className="text-xs text-slate-500 font-mono bg-white px-2 py-0.5 rounded border border-slate-200">
                    Cấp độ (Level): {currentRoleInfo.level}
                  </span>
                </div>
                <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
                  {currentRoleInfo.description}
                </p>
                {selectedRole === 'owner' && (
                  <p className="text-xs font-semibold text-purple-700 flex items-center space-x-1 mt-1">
                    <ShieldCheck className="w-4 h-4 text-purple-600" />
                    <span>
                      Vai trò Chủ sở hữu sở hữu toàn quyền tuyệt đối (*), không thể hủy để đảm bảo không bị khóa khỏi hệ thống.
                    </span>
                  </p>
                )}
              </div>

              {/* Quick Actions for Selected Role */}
              {isOwner && selectedRole !== 'owner' && (
                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => handleSelectAll(selectedRole)}
                    className="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[11px] font-semibold text-slate-700 shadow-2xs transition-colors cursor-pointer"
                  >
                    Cấp tất cả
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDeselectAll(selectedRole)}
                    className="px-2.5 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-[11px] font-semibold text-rose-700 hover:text-rose-800 shadow-2xs transition-colors cursor-pointer"
                  >
                    Gỡ tất cả
                  </button>
                  <button
                    type="button"
                    onClick={() => handleResetRoleToDefault(selectedRole)}
                    className="px-2.5 py-1.5 rounded-lg border border-indigo-200 bg-indigo-50/80 hover:bg-indigo-100 text-[11px] font-semibold text-indigo-700 shadow-2xs transition-colors cursor-pointer"
                  >
                    Khôi phục vai trò này
                  </button>
                </div>
              )}
            </div>

            {/* Filter & Search Bar */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setSelectedCategory('all')}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                    selectedCategory === 'all'
                      ? 'bg-slate-900 text-white shadow-2xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  Tất cả ({allPermissionIds.length})
                </button>
                {catalog.map((cat) => (
                  <button
                    key={cat.category}
                    type="button"
                    onClick={() => setSelectedCategory(cat.category)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      selectedCategory === cat.category
                        ? 'bg-indigo-600 text-white shadow-2xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {cat.category_title.split('&')[0].trim()} ({cat.permissions.length})
                  </button>
                ))}
              </div>

              <div className="relative min-w-[220px]">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Lọc quyền (tên, mã ID)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-xl border border-slate-200 text-xs focus:outline-hidden focus:ring-2 focus:ring-indigo-500/30"
                />
              </div>
            </div>

            {/* Categories & Permission Toggle Switches */}
            <div className="space-y-4">
              {filteredCatalog.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500 border border-dashed border-slate-200 rounded-xl">
                  Không tìm thấy quyền hạn nào khớp với từ khóa tìm kiếm.
                </div>
              ) : (
                filteredCatalog.map((cat) => {
                  const rolePerms = matrix[selectedRole] || []
                  const isOwnerRole = selectedRole === 'owner'
                  const enabledInCat = isOwnerRole
                    ? cat.permissions.length
                    : cat.permissions.filter((p) => rolePerms.includes(p.id)).length

                  return (
                    <div
                      key={cat.category}
                      className="border border-slate-200/90 rounded-xl bg-white overflow-hidden shadow-2xs"
                    >
                      {/* Category Header */}
                      <div className="bg-slate-50/80 px-4 py-2.5 border-b border-slate-100 flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Layers className="w-4 h-4 text-indigo-600" />
                          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                            {cat.category_title}
                          </h4>
                        </div>
                        <span className="text-[11px] font-mono text-slate-500">
                          Đã cấp {enabledInCat}/{cat.permissions.length} quyền
                        </span>
                      </div>

                      {/* Permissions List */}
                      <div className="divide-y divide-slate-100">
                        {cat.permissions.map((perm) => {
                          const isChecked = isOwnerRole || rolePerms.includes(perm.id)
                          const isDefault = (defaultMatrix[selectedRole] || []).includes(perm.id)
                          const isSensitive =
                            perm.id.includes('unmask') ||
                            perm.id.includes('delete') ||
                            perm.id.includes('config') ||
                            perm.id.includes('token_cost')

                          return (
                            <div
                              key={perm.id}
                              className={`p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-colors ${
                                isChecked ? 'bg-white' : 'bg-slate-50/40 opacity-75'
                              }`}
                            >
                              <div className="space-y-1 flex-1 pr-4">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="text-xs font-bold text-slate-900">{perm.name}</span>
                                  <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                                    {perm.id}
                                  </span>
                                  {isDefault && (
                                    <span className="text-[9px] font-semibold text-indigo-600 bg-indigo-50 px-1.5 py-0.2 rounded border border-indigo-100">
                                      Mặc định
                                    </span>
                                  )}
                                  {isSensitive && (
                                    <span className="text-[9px] font-bold text-amber-700 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200">
                                      Nhạy cảm / Bảo mật
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-slate-500 leading-relaxed">
                                  {perm.description}
                                </p>
                              </div>

                              {/* Toggle Switch */}
                              <div className="flex items-center space-x-2 shrink-0 self-end sm:self-center">
                                <label className="relative inline-flex items-center cursor-pointer">
                                  <input
                                    type="checkbox"
                                    checked={isChecked}
                                    disabled={!isOwner || isOwnerRole}
                                    onChange={() => handleToggle(selectedRole, perm.id)}
                                    className="sr-only peer"
                                  />
                                  <div
                                    className={`w-11 h-6 bg-slate-200 peer-focus:outline-hidden rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all ${
                                      isOwnerRole
                                        ? 'bg-purple-600 opacity-90 cursor-not-allowed'
                                        : !isOwner
                                        ? 'cursor-not-allowed opacity-60'
                                        : 'peer-checked:bg-emerald-600'
                                    }`}
                                  />
                                </label>
                                <span
                                  className={`text-xs font-bold min-w-[50px] text-right ${
                                    isChecked ? 'text-emerald-700' : 'text-slate-400'
                                  }`}
                                >
                                  {isChecked ? 'Được cấp' : 'Bị chặn'}
                                </span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW MODE 2: BẢNG MA TRẬN PHÂN QUYỀN TỔNG THỂ (FULL MATRIX TABLE) */}
        {/* ========================================================================= */}
        {viewMode === 'matrix_table' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="flex items-center space-x-1">
                <Info className="w-3.5 h-3.5 text-indigo-600" />
                <span>
                  Bấm trực tiếp vào các ô quyền hạn (✓ / ✗) để bật/tắt nhanh cho bất kỳ vai trò nào.
                </span>
              </span>
              <span className="font-mono">
                {allPermissionIds.length} quyền hạn × {sortedRoleKeys.length} vai trò
              </span>
            </div>

            <div className="border border-slate-200 rounded-xl overflow-x-auto shadow-2xs">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-100/90 border-b border-slate-200">
                    <th className="p-3 font-bold text-slate-700 min-w-[260px] sticky left-0 bg-slate-100 z-10 border-r border-slate-200">
                      Quyền Hạn / Chức Năng
                    </th>
                    {sortedRoleKeys.map((rKey) => {
                      const r = roles[rKey]
                      return (
                        <th
                          key={rKey}
                          className="p-3 text-center min-w-[100px] border-r border-slate-200/80 last:border-r-0"
                        >
                          <div className="flex flex-col items-center space-y-1">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-extrabold uppercase border ${getBadgeStyle(
                                r?.badge_color
                              )}`}
                            >
                              {r?.code || rKey.toUpperCase()}
                            </span>
                            <span className="font-bold text-slate-800 text-[11px] truncate max-w-[90px]">
                              {r?.title?.split('/')[0]?.trim()}
                            </span>
                          </div>
                        </th>
                      )
                    })}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {catalog.map((cat) => (
                    <React.Fragment key={cat.category}>
                      {/* Category Header Row */}
                      <tr className="bg-indigo-50/40">
                        <td
                          colSpan={sortedRoleKeys.length + 1}
                          className="p-2.5 font-bold text-indigo-900 uppercase tracking-wider text-[11px] border-b border-indigo-100"
                        >
                          {cat.category_title}
                        </td>
                      </tr>

                      {/* Permission Rows */}
                      {cat.permissions.map((perm) => (
                        <tr key={perm.id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="p-2.5 font-medium text-slate-800 sticky left-0 bg-white z-10 border-r border-slate-200">
                            <div className="font-semibold text-slate-900">{perm.name}</div>
                            <div className="font-mono text-[10px] text-slate-400">{perm.id}</div>
                          </td>
                          {sortedRoleKeys.map((rKey) => {
                            const isOwnerRole = rKey === 'owner'
                            const isChecked = isOwnerRole || (matrix[rKey] || []).includes(perm.id)

                            return (
                              <td
                                key={rKey}
                                className="p-2 text-center border-r border-slate-100 last:border-r-0"
                              >
                                {isOwnerRole ? (
                                  <span
                                    className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-purple-50 text-purple-700 border border-purple-200 font-bold"
                                    title="Chủ máy luôn sở hữu toàn quyền"
                                  >
                                    ★
                                  </span>
                                ) : (
                                  <button
                                    type="button"
                                    disabled={!isOwner}
                                    onClick={() => handleToggle(rKey, perm.id)}
                                    title={
                                      isOwner
                                        ? `Bấm để ${isChecked ? 'gỡ' : 'cấp'} quyền [${perm.name}] cho [${roles[rKey]?.title}]`
                                        : 'Chỉ Owner mới có thể chỉnh sửa'
                                    }
                                    className={`w-7 h-7 rounded-lg inline-flex items-center justify-center transition-all cursor-pointer ${
                                      isChecked
                                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-emerald-100 shadow-2xs font-bold'
                                        : 'bg-slate-50 text-slate-300 hover:text-slate-500 hover:bg-slate-100 border border-slate-200'
                                    }`}
                                  >
                                    {isChecked ? (
                                      <Check className="w-4 h-4 stroke-[3]" />
                                    ) : (
                                      <X className="w-3.5 h-3.5 stroke-[2]" />
                                    )}
                                  </button>
                                )}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Footer info & Unsaved Indicator */}
        {hasChanges && (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-amber-800 text-xs">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              <span className="font-semibold">
                Bạn có các thay đổi phân quyền chưa được lưu vào hệ thống!
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setMatrix(JSON.parse(JSON.stringify(initialMatrix)))}
                className="px-3 py-1.5 rounded-lg border border-amber-300 bg-white text-slate-700 font-semibold hover:bg-amber-100/50 cursor-pointer"
              >
                Hủy thay đổi
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={isSaving}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold cursor-pointer shadow-2xs"
              >
                {isSaving ? 'Đang lưu...' : 'Lưu ngay'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
