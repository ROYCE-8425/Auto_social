import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatTime(ts: number | string | undefined | null): string {
  if (!ts) return ''
  const t = typeof ts === 'string' ? new Date(ts).getTime() : ts * (ts < 1e11 ? 1000 : 1)
  if (isNaN(t)) return String(ts)
  const d = new Date(t)
  return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) + ' ' +
         d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function timeAgo(ts: number | string | undefined | null): string {
  if (!ts) return ''
  const t = typeof ts === 'string' ? new Date(ts).getTime() : ts * (ts < 1e11 ? 1000 : 1)
  if (isNaN(t)) return ''
  const diffSec = Math.floor((Date.now() - t) / 1000)
  if (diffSec < 60) return 'Vừa xong'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} phút trước`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} giờ trước`
  return `${Math.floor(diffSec / 86400)} ngày trước`
}

export function maskPhone(phone: string | null | undefined, unmask: boolean = false): string {
  if (!phone) return ''
  const clean = phone.trim()
  if (unmask || clean.length < 7) return clean
  const start = clean.slice(0, 3)
  const end = clean.slice(-3)
  return `${start}****${end}`
}
