import React, { useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  CheckCircle2,
  Package,
  Plus,
  RefreshCw,
  Save,
  Search,
  Tag,
  Trash2,
} from 'lucide-react'
import { api, OpsProduct } from '../lib/api'
import { useAuth } from '../lib/auth'

const money = (v?: number) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(Number(v || 0))

const bool = (v: unknown) => v === true || v === 1 || v === '1' || v === 'true'

const emptyForm = {
  sku: '',
  name: '',
  category: 'general',
  price: 0,
  sale_price: 0,
  stock: 0,
  weight_gram: 500,
  aliases: '',
  page_id: '*',
  channel: 'messenger',
  custom_price: 0,
}

export const ProductCatalogSettings: React.FC = () => {
  const { role } = useAuth()
  const canManage = role === 'owner' || role === 'manager' || (role as string) === 'admin'
  const [products, setProducts] = useState<OpsProduct[]>([])
  const [keyword, setKeyword] = useState('')
  const [pageId, setPageId] = useState('')
  const [form, setForm] = useState(emptyForm)
  const [selected, setSelected] = useState<OpsProduct | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const activeProducts = useMemo(() => products.filter((p) => bool(p.is_active)), [products])
  const lowStock = useMemo(() => products.filter((p) => Number(p.stock || 0) <= 3), [products])

  const loadProducts = async () => {
    setLoading(true)
    setMessage(null)
    try {
      const res = await api.getProducts({
        keyword: keyword.trim() || undefined,
        page_id: pageId.trim() || undefined,
        channel: 'messenger',
        active_only: false,
      })
      setProducts(res.products || [])
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.message || 'Không tải được danh mục sản phẩm' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadProducts()
  }, [])

  const startEdit = (product: OpsProduct) => {
    const binding = product.page_bindings?.[0]
    setSelected(product)
    setForm({
      sku: product.sku || '',
      name: product.name || '',
      category: product.category || 'general',
      price: Number(product.price || 0),
      sale_price: Number(product.sale_price || 0),
      stock: Number(product.stock || 0),
      weight_gram: Number(product.weight_gram || 500),
      aliases: (product.aliases || []).join(', '),
      page_id: binding?.page_id || '*',
      channel: binding?.channel || 'messenger',
      custom_price: Number(binding?.custom_price || 0),
    })
  }

  const resetForm = () => {
    setSelected(null)
    setForm(emptyForm)
  }

  const saveProduct = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canManage) return
    setSaving(true)
    setMessage(null)
    try {
      const aliases = form.aliases
        .split(',')
        .map((a) => a.trim())
        .filter(Boolean)
      const pageBindings = form.page_id.trim()
        ? [{
            page_id: form.page_id.trim(),
            channel: form.channel.trim() || '*',
            custom_price: Number(form.custom_price || 0) || null,
            auto_sell_allowed: true,
          }]
        : []
      const payload = {
        sku: form.sku.trim(),
        name: form.name.trim(),
        category: form.category.trim() || 'general',
        price: Number(form.price || 0),
        sale_price: Number(form.sale_price || 0),
        stock: Number(form.stock || 0),
        weight_gram: Number(form.weight_gram || 500),
        aliases,
        page_bindings: pageBindings,
        is_active: true,
        auto_sell_enabled: true,
      }
      if (selected?.id) {
        await api.updateProduct(selected.id, payload)
      } else {
        await api.saveProduct(payload)
      }
      setMessage({ type: 'success', text: selected ? 'Đã cập nhật sản phẩm' : 'Đã thêm sản phẩm vào catalog' })
      resetForm()
      await loadProducts()
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.message || 'Không lưu được sản phẩm' })
    } finally {
      setSaving(false)
    }
  }

  const deleteProduct = async (product: OpsProduct) => {
    if (!canManage) return
    if (!window.confirm(`Xóa sản phẩm ${product.sku}?`)) return
    setSaving(true)
    try {
      await api.deleteProduct(product.id)
      setMessage({ type: 'success', text: 'Đã xóa sản phẩm khỏi catalog' })
      await loadProducts()
      if (selected?.id === product.id) resetForm()
    } catch (err: any) {
      setMessage({ type: 'error', text: err?.message || 'Không xóa được sản phẩm' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Package className="w-5 h-5 text-emerald-600" />
              <span>Catalog sản phẩm theo Page</span>
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Đây là nguồn sự thật để Javis nhận diện sản phẩm, báo giá, kiểm tồn và tạo đơn GHN.
            </p>
          </div>
          <button
            type="button"
            onClick={loadProducts}
            disabled={loading}
            className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : ''}`} />
            Tải lại
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-5">
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <div className="text-[11px] font-bold uppercase text-slate-500">Tổng sản phẩm</div>
            <div className="text-2xl font-black text-slate-900 mt-1">{products.length}</div>
          </div>
          <div className="rounded-xl border border-emerald-100 bg-emerald-50 p-4">
            <div className="text-[11px] font-bold uppercase text-emerald-700">Đang bán tự động</div>
            <div className="text-2xl font-black text-emerald-700 mt-1">{activeProducts.length}</div>
          </div>
          <div className="rounded-xl border border-amber-100 bg-amber-50 p-4">
            <div className="text-[11px] font-bold uppercase text-amber-700">Sắp hết hàng</div>
            <div className="text-2xl font-black text-amber-700 mt-1">{lowStock.length}</div>
          </div>
        </div>
      </div>

      {message && (
        <div className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
          message.type === 'success'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : 'bg-rose-50 border-rose-200 text-rose-800'
        }`}>
          {message.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px] gap-5">
        <div className="bg-white border border-slate-200/80 rounded-2xl shadow-2xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row gap-3">
            <label className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="Tìm SKU, tên sản phẩm, alias khách hay gọi"
                className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
              />
            </label>
            <input
              value={pageId}
              onChange={(e) => setPageId(e.target.value)}
              placeholder="Page ID, bỏ trống để xem tất cả"
              className="sm:w-64 px-3 py-2 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
            />
            <button
              type="button"
              onClick={loadProducts}
              className="px-4 py-2 rounded-xl bg-slate-900 text-white text-xs font-bold hover:bg-slate-800"
            >
              Lọc
            </button>
          </div>

          <div className="divide-y divide-slate-100">
            {products.length === 0 && (
              <div className="p-8 text-center text-sm text-slate-500">
                Chưa có sản phẩm thật. Hãy thêm SKU, alias và Page binding trước khi bật tự động chốt đơn.
              </div>
            )}
            {products.map((product) => (
              <div key={product.id} className="p-4 hover:bg-slate-50/70 transition-colors">
                <div className="flex items-start justify-between gap-3">
                  <button type="button" onClick={() => startEdit(product)} className="text-left min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                        {product.sku}
                      </span>
                      <span className="font-bold text-sm text-slate-900">{product.name}</span>
                      {!bool(product.is_active) && (
                        <span className="text-[10px] font-bold text-slate-500 bg-slate-100 border border-slate-200 rounded-full px-2 py-0.5">
                          Tạm ẩn
                        </span>
                      )}
                    </div>
                    <div className="mt-2 grid grid-cols-2 lg:grid-cols-4 gap-2 text-xs text-slate-600">
                      <span>Giá: <strong className="text-slate-900">{money(product.sale_price || product.price)}</strong></span>
                      <span>Tồn: <strong className="text-slate-900">{product.stock || 0}</strong></span>
                      <span>Nhóm: <strong className="text-slate-900">{product.category || 'general'}</strong></span>
                      <span>Page: <strong className="text-slate-900">{product.page_bindings?.[0]?.page_id || 'chưa gắn'}</strong></span>
                    </div>
                    {!!product.aliases?.length && (
                      <div className="mt-2 flex items-center gap-1.5 text-[11px] text-slate-500">
                        <Tag className="w-3 h-3" />
                        <span className="truncate">{product.aliases.join(', ')}</span>
                      </div>
                    )}
                  </button>
                  {canManage && (
                    <button
                      type="button"
                      onClick={() => deleteProduct(product)}
                      className="w-8 h-8 rounded-lg border border-rose-100 text-rose-600 hover:bg-rose-50 flex items-center justify-center"
                      title="Xóa sản phẩm"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <form onSubmit={saveProduct} className="bg-white border border-slate-200/80 rounded-2xl p-5 shadow-2xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-slate-900 text-sm">{selected ? 'Sửa sản phẩm' : 'Thêm sản phẩm'}</h3>
            {selected && (
              <button type="button" onClick={resetForm} className="text-xs font-semibold text-slate-500 hover:text-slate-900">
                Tạo mới
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <input required value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} placeholder="SKU" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
            <input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder="Danh mục" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
          </div>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Tên sản phẩm" className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm" />
          <div className="grid grid-cols-2 gap-3">
            <input type="number" min="0" value={form.price} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} placeholder="Giá gốc" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
            <input type="number" min="0" value={form.sale_price} onChange={(e) => setForm({ ...form, sale_price: Number(e.target.value) })} placeholder="Giá sale" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input type="number" min="0" value={form.stock} onChange={(e) => setForm({ ...form, stock: Number(e.target.value) })} placeholder="Tồn kho" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
            <input type="number" min="1" value={form.weight_gram} onChange={(e) => setForm({ ...form, weight_gram: Number(e.target.value) })} placeholder="Gram" className="px-3 py-2 rounded-xl border border-slate-200 text-sm" />
          </div>
          <textarea value={form.aliases} onChange={(e) => setForm({ ...form, aliases: e.target.value })} placeholder="Alias: chuột silent, mouse không dây..." rows={3} className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm resize-none" />

          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-3">
            <div className="text-[11px] font-bold uppercase text-slate-500">Gắn Page bán hàng</div>
            <div className="grid grid-cols-2 gap-3">
              <input value={form.page_id} onChange={(e) => setForm({ ...form, page_id: e.target.value })} placeholder="page_id hoặc *" className="px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white" />
              <input value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })} placeholder="messenger/facebook/*" className="px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white" />
            </div>
            <input type="number" min="0" value={form.custom_price} onChange={(e) => setForm({ ...form, custom_price: Number(e.target.value) })} placeholder="Giá riêng cho Page này" className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm bg-white" />
          </div>

          <button
            type="submit"
            disabled={!canManage || saving}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-bold hover:bg-emerald-700 disabled:opacity-50"
          >
            {selected ? <Save className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
            {saving ? 'Đang lưu...' : selected ? 'Lưu thay đổi' : 'Thêm vào catalog'}
          </button>
        </form>
      </div>
    </div>
  )
}
