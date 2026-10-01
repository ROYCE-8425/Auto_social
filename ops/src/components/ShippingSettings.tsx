import React, { useState, useEffect } from 'react'
import {
  Truck,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  ExternalLink,
  ShieldAlert,
  Sliders,
  Radio,
  Lock,
  Save,
  Key,
  MapPin,
  HelpCircle,
  Cpu,
} from 'lucide-react'
import { api, ShippingProviderItem, ShippingSettingsResponse } from '../lib/api'
import { useAuth } from '../lib/auth'

export const ShippingSettings: React.FC = () => {
  const { role } = useAuth()
  const [providers, setProviders] = useState<ShippingProviderItem[]>([])
  const [settings, setSettings] = useState<ShippingSettingsResponse | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [isSaving, setIsSaving] = useState<boolean>(false)
  const [isTesting, setIsTesting] = useState<boolean>(false)
  const [testResult, setTestResult] = useState<{ ok: boolean; message?: string; error?: string } | null>(null)
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  // Form fields
  const [ghnToken, setGhnToken] = useState<string>('')
  const [ghnShopId, setGhnShopId] = useState<string>('')
  const [ghnEnv, setGhnEnv] = useState<'sandbox' | 'production'>('sandbox')
  const [pickupName, setPickupName] = useState<string>('')
  const [pickupPhone, setPickupPhone] = useState<string>('')
  const [pickupAddress, setPickupAddress] = useState<string>('')
  const [pickupWard, setPickupWard] = useState<string>('')
  const [pickupDistrict, setPickupDistrict] = useState<number>(1442)
  const [pickupProvince, setPickupProvince] = useState<string>('Hà Nội')

  // Automation rules
  const [autoCreateShipment, setAutoCreateShipment] = useState<boolean>(false)
  const [minConfidence, setMinConfidence] = useState<number>(0.85)
  const [requireSkuMatch, setRequireSkuMatch] = useState<boolean>(true)
  const [killSwitch, setKillSwitch] = useState<boolean>(false)

  const isManagerOrOwner = role === 'owner' || role === 'manager' || (role as string) === 'admin'

  const loadData = async () => {
    setIsLoading(true)
    setStatusMsg(null)
    setTestResult(null)
    try {
      const [provRes, setRes] = await Promise.all([
        api.getShippingProviders(),
        api.getShippingSettings(),
      ])

      if (provRes.ok) setProviders(provRes.providers || [])
      if (setRes.ok && setRes.settings) {
        const s = setRes.settings
        setSettings(s)
        const ghn = s.providers?.ghn || {}
        setGhnToken(ghn.masked_token || ghn.token || '')
        setGhnShopId(ghn.shop_id || '')
        setGhnEnv(ghn.environment || 'sandbox')

        const pk = ghn.pickup_address || {}
        setPickupName(pk.name || 'Kho Sèo Trum Ops')
        setPickupPhone(pk.phone || '')
        setPickupAddress(pk.address || '')
        setPickupWard(pk.ward_code || '')
        setPickupDistrict(pk.district_id || 1442)
        setPickupProvince(pk.province_name || 'Hà Nội')

        const auto = s.automation || {}
        setAutoCreateShipment(bool(auto.auto_create_shipment))
        setMinConfidence(auto.min_confidence ?? 0.85)
        setRequireSkuMatch(bool(auto.require_sku_match ?? true))
        setKillSwitch(bool(auto.kill_switch))
      }
    } catch (err: any) {
      setStatusMsg({ text: err?.message || 'Lỗi tải cấu hình vận chuyển', type: 'error' })
    } finally {
      setIsLoading(false)
    }
  }

  const bool = (v: any) => v === true || v === 'true'

  useEffect(() => {
    loadData()
  }, [])

  const handleTestConnection = async () => {
    setIsTesting(true)
    setTestResult(null)
    try {
      const res = await api.testShippingConnection({
        provider: 'ghn',
        token: ghnToken,
        shop_id: ghnShopId,
        environment: ghnEnv,
      })
      setTestResult(res)
    } catch (err: any) {
      setTestResult({ ok: false, error: err?.message || 'Lỗi kết nối máy chủ vận chuyển' })
    } finally {
      setIsTesting(false)
    }
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isManagerOrOwner) return
    setIsSaving(true)
    setStatusMsg(null)
    try {
      const payload = {
        default_provider: 'ghn',
        providers: {
          ghn: {
            enabled: bool(ghnToken && ghnShopId),
            token: ghnToken,
            shop_id: ghnShopId,
            environment: ghnEnv,
            pickup_address: {
              name: pickupName,
              phone: pickupPhone,
              address: pickupAddress,
              ward_code: pickupWard,
              district_id: Number(pickupDistrict),
              province_name: pickupProvince,
            },
          },
        },
        automation: {
          auto_create_shipment: autoCreateShipment,
          min_confidence: Number(minConfidence),
          require_sku_match: requireSkuMatch,
          kill_switch: killSwitch,
        },
      }
      const res = await api.saveShippingSettings(payload)
      if (res.ok) {
        setStatusMsg({ text: 'Đã lưu cấu hình vận chuyển & automation rules thành công!', type: 'success' })
        setSettings(res.settings)
      }
    } catch (err: any) {
      setStatusMsg({ text: err?.message || 'Lỗi lưu cấu hình vận chuyển', type: 'error' })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ================= HEADER ================= */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center space-x-2">
              <Truck className="w-5 h-5 text-indigo-600" />
              <span>Cổng Vận Chuyển &amp; Giao Hàng (Shipping Gateway)</span>
            </h2>
            <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold border border-emerald-200">
              GHN Express v2
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Quản trị cổng kết nối hãng giao hàng, đồng bộ biểu phí, tạo vận đơn tự động và địa chỉ kho lấy hàng.
          </p>
        </div>

        <button
          type="button"
          onClick={loadData}
          disabled={isLoading}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-blue-600' : ''}`} />
          <span>Tải lại</span>
        </button>
      </div>

      {statusMsg && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center space-x-2 ${
            statusMsg.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {statusMsg.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          )}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* ================= CARRIERS OVERVIEW ================= */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {providers.map((p) => (
          <div
            key={p.id}
            className={`bg-white rounded-2xl border p-4 shadow-2xs space-y-3 flex flex-col justify-between ${
              p.supported ? 'border-slate-200/90' : 'border-slate-200/60 opacity-80'
            }`}
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 rounded-xl bg-slate-100 flex items-center justify-center font-bold text-xs text-slate-700">
                    <Truck className="w-4 h-4 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-xs">{p.name}</h3>
                    <span className="text-[10px] text-slate-400 font-mono block">Cổng: {p.id.toUpperCase()}</span>
                  </div>
                </div>

                <span
                  className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                    p.status === 'ready'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : p.status === 'not_configured'
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-slate-100 text-slate-500 border-slate-200'
                  }`}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full ${
                      p.status === 'ready'
                        ? 'bg-emerald-500 animate-pulse'
                        : p.status === 'not_configured'
                        ? 'bg-amber-500'
                        : 'bg-slate-400'
                    }`}
                  />
                  <span>{p.status_label}</span>
                </span>
              </div>

              <div className="text-[11px] text-slate-500 space-y-1">
                <div>
                  • Tính cước:{' '}
                  <span className="font-semibold text-slate-700">
                    {p.capabilities.includes('fee_calculation') ? 'Có' : 'Chưa'}
                  </span>
                </div>
                <div>
                  • Tạo vận đơn:{' '}
                  <span className="font-semibold text-slate-700">
                    {p.capabilities.includes('create_shipment') ? 'Có' : 'Chưa'}
                  </span>
                </div>
                <div>
                  • Webhook trạng thái:{' '}
                  <span className="font-semibold text-slate-700">
                    {p.capabilities.includes('webhook') ? 'Tự động' : 'Chưa'}
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-400">
              {p.is_default && <span className="text-indigo-600 font-bold">★ Nhà vận chuyển mặc định</span>}
            </div>
          </div>
        ))}
      </div>

      {/* ================= GHN CONFIGURATION FORM ================= */}
      <form onSubmit={handleSave} className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-2xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <Key className="w-4 h-4 text-blue-600" />
              <span>Cấu Hình Xác Thực Giao Hàng Nhanh (GHN Express)</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Nhập mã API Token và Shop ID lấy từ trang quản trị <code>khachhang.ghn.vn</code>.
            </p>
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={isTesting || !ghnToken}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin text-blue-600' : ''}`} />
              <span>Kiểm tra kết nối</span>
            </button>
          </div>
        </div>

        {testResult && (
          <div
            className={`p-3 rounded-xl border text-xs flex items-center space-x-2 animate-fade-in ${
              testResult.ok
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800 font-semibold'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}
          >
            {testResult.ok ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span>{testResult.message || testResult.error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">
              Mã GHN API Token:
            </label>
            <input
              type="text"
              value={ghnToken}
              onChange={(e) => setGhnToken(e.target.value)}
              placeholder="Nhập chuỗi token do GHN cung cấp..."
              disabled={!isManagerOrOwner}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">
              Shop ID (Mã cửa hàng GHN):
            </label>
            <input
              type="text"
              value={ghnShopId}
              onChange={(e) => setGhnShopId(e.target.value)}
              placeholder="Ví dụ: 123456"
              disabled={!isManagerOrOwner}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
            />
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">
              Môi trường kết nối:
            </label>
            <select
              value={ghnEnv}
              onChange={(e: any) => setGhnEnv(e.target.value)}
              disabled={!isManagerOrOwner}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
            >
              <option value="sandbox">Sandbox (Thử nghiệm dev-online-gateway.ghn.vn)</option>
              <option value="production">Production (Vận hành thực online-gateway.ghn.vn)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-bold text-slate-700 block mb-1">
              Webhook Callback URL (Cấu hình trên GHN):
            </label>
            <input
              type="text"
              readOnly
              value={`${window.location.origin}/ops/shipping/webhook/ghn`}
              className="w-full bg-slate-100 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-600 font-mono cursor-not-allowed select-all"
            />
          </div>
        </div>

        {/* ================= PICKUP ADDRESS ================= */}
        <div className="pt-4 border-t border-slate-100 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-emerald-600" />
              <span>Địa Chỉ Kho Lấy Hàng (Pickup Address)</span>
            </h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Thông tin địa điểm để tài xế GHN tới nhận kiện hàng bưu kiện.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Tên kho / Người gửi:</label>
              <input
                type="text"
                value={pickupName}
                onChange={(e) => setPickupName(e.target.value)}
                disabled={!isManagerOrOwner}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Số điện thoại gửi:</label>
              <input
                type="text"
                value={pickupPhone}
                onChange={(e) => setPickupPhone(e.target.value)}
                disabled={!isManagerOrOwner}
                placeholder="0987..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">Địa chỉ chi tiết:</label>
              <input
                type="text"
                value={pickupAddress}
                onChange={(e) => setPickupAddress(e.target.value)}
                disabled={!isManagerOrOwner}
                placeholder="Số nhà, tên đường..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
              />
            </div>
          </div>
        </div>

        {/* ================= AUTOMATION RULES ================= */}
        <div className="pt-4 border-t border-slate-100 space-y-4">
          <div>
            <h4 className="text-sm font-bold text-slate-900 flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-purple-600" />
              <span>Quy Tắc Tự Động Hóa Vận Đơn (Automation Rules)</span>
            </h4>
            <p className="text-xs text-slate-500 mt-0.5">
              Kiểm soát điều kiện an toàn khi cho phép hệ thống tự động xuất vận đơn sang hãng vận chuyển.
            </p>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-800 text-xs block">
                  Tự động tạo vận đơn khi xác nhận đơn
                </span>
                <span className="text-[11px] text-slate-500">
                  Mặc định TẮT. Chỉ tự động đẩy sang GHN khi đủ SĐT, địa chỉ và độ tin cậy AI vượt ngưỡng.
                </span>
              </div>
              <input
                type="checkbox"
                checked={autoCreateShipment}
                onChange={(e) => setAutoCreateShipment(e.target.checked)}
                disabled={!isManagerOrOwner}
                className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-200/60">
              <div>
                <span className="font-bold text-slate-800 text-xs block">
                  Ngưỡng tin cậy AI tối thiểu (Confidence threshold)
                </span>
                <span className="text-[11px] text-slate-500">
                  Chỉ cho phép auto-create khi độ tin cậy &gt;= {Math.round(minConfidence * 100)}%
                </span>
              </div>
              <input
                type="number"
                step="0.05"
                min="0.5"
                max="1.0"
                value={minConfidence}
                onChange={(e) => setMinConfidence(Number(e.target.value))}
                disabled={!isManagerOrOwner}
                className="w-20 bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs text-right font-bold text-slate-800"
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-200/60">
              <div>
                <span className="font-bold text-slate-800 text-xs block">
                  Bắt buộc sản phẩm khớp SKU Catalog
                </span>
                <span className="text-[11px] text-slate-500">
                  Nếu khách yêu cầu sản phẩm ngoài danh mục, chặn tạo đơn tự động và chuyển nhân viên duyệt.
                </span>
              </div>
              <input
                type="checkbox"
                checked={requireSkuMatch}
                onChange={(e) => setRequireSkuMatch(e.target.checked)}
                disabled={!isManagerOrOwner}
                className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Submit button */}
        {isManagerOrOwner && (
          <div className="pt-2 flex items-center justify-end space-x-2">
            <button
              type="submit"
              disabled={isSaving}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs shadow-2xs transition-colors cursor-pointer disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              <span>{isSaving ? 'Đang lưu...' : 'Lưu cấu hình vận chuyển'}</span>
            </button>
          </div>
        )}
      </form>
    </div>
  )
}
