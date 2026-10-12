// AnalyticsService: consent là điều kiện tiên quyết, không phải lựa chọn.
//
// Ràng buộc cứng của ANA-001: **chưa đồng ý thì không có một request analytics
// nào được gửi** (kiểm được bằng tab Network). Vì vậy `ghiSuKien` kiểm tra
// consent ngay ở cổng, trước cả khi ghi vào outbox — nếu chỉ kiểm ở lúc
// flush thì mất mạng rồi mới đồng ý vẫn có sự kiện nằm sẵn trong IDB.

import { laySuKien, themSuKien, xoaSuKien, type SuKienOutbox } from './outbox'
import { damBaoAnonymousId, daDongY, laySessionId, useConsentStore } from '../stores/consentStore'

const API_GOC = 'http://127.0.0.1:8000'

// Nhịp gửi: 15s gộp lô, 20s nhịp tim. Lấy từ sơ đồ luồng analytics.
export const CHU_KY_FLUSH_MS = 15000
export const CHU_KY_HEARTBEAT_MS = 20000
// page_engaged chỉ tính sau 10s người dùng thực sự nhìn trang.
export const NGHENG_ENGAGED_MS = 10000

export const TEN_SU_KIEN = [
  'session_started',
  'page_viewed',
  'page_engaged',
  'search',
  'audio_played',
  'poi_viewed',
] as const

export type TenSuKien = (typeof TEN_SU_KIEN)[number]

export function tenHopLe(ten: string): ten is TenSuKien {
  return (TEN_SU_KIEN as readonly string[]).includes(ten)
}

// Thuộc tính được gửi đi. Không có mục nào chứa thông tin định danh — nếu sau
// này cần thêm, phải thêm vào danh sách chặn phía server trước, không thêm
// ở đây rồi hy vọng server tự lọc.
const THUOC_TINH_CHO_PHEP = ['poi_id', 'query', 'lang', 'tier', 'duration_ms']

export function locThuocTinh(raw: Record<string, unknown>): Record<string, string | number | boolean> {
  const sach: Record<string, string | number | boolean> = {}
  for (const khoa of THUOC_TINH_CHO_PHEP) {
    const gt = raw[khoa]
    if (typeof gt === 'string') sach[khoa] = gt.slice(0, 120)
    else if (typeof gt === 'number' && Number.isFinite(gt)) sach[khoa] = gt
    else if (typeof gt === 'boolean') sach[khoa] = gt
  }
  return sach
}

export async function ghiSuKien(ten: TenSuKien, thuoc_tinh: Record<string, unknown> = {}): Promise<void> {
  if (!daDongY() || !tenHopLe(ten)) return
  const sk: SuKienOutbox = { name: ten, at: Date.now(), properties: locThuocTinh(thuoc_tinh) }
  try {
    await themSuKien(sk)
  } catch {
    return
  }
}

async function gui(bo: { name: string; at: number; properties: Record<string, unknown> }[], heartbeat: boolean) {
  const { receipt } = useConsentStore.getState()
  if (receipt === null) return
  const res = await fetch(`${API_GOC}/analytics/collect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      anonymous_id: damBaoAnonymousId(),
      receipt,
      session_id: laySessionId(),
      heartbeat,
      events: bo,
    }),
  })
  if (res.status === 403) {
    // Server nói consent không còn hiệu lực (thu hồi từ tab khác, hết hạn).
    // Dừng ngay thay vì cứ gửi tiếp rồi nhận 403 mãi.
    useConsentStore.getState().datTrangThai('revoked')
    useConsentStore.getState().datReceipt(null)
    return
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const goi = (await res.json()) as { tracked_online_users: number | null }
  useConsentStore.getState().datTrackedOnlineUsers(goi.tracked_online_users)
}

export async function flush(heartbeat = false): Promise<number> {
  if (!daDongY()) return 0
  const bo = await laySuKien().catch(() => [])
  try {
    await gui(bo, heartbeat)
  } catch {
    return 0
  }
  await xoaSuKien(bo.map((s) => s.id))
  return bo.length
}

export async function xinDongY(): Promise<boolean> {
  const res = await fetch(`${API_GOC}/analytics/consent`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ anonymous_id: damBaoAnonymousId(), granted: true }),
  })
  if (!res.ok) return false
  const goi = (await res.json()) as { status: string; receipt: string }
  if (goi.status !== 'granted') return false
  // Phải set trạng thái, không chỉ lưu receipt: `batDauAnalytics` chỉ chạy khi
  // trạng thái là granted. Thiếu dòng này thì bấm "Cho phép" xong app vẫn
  // im lặng và banner vẫn hỏi lại.
  useConsentStore.getState().datTrangThai('granted')
  useConsentStore.getState().datReceipt(goi.receipt)
  return true
}

export async function thuHoiDongY(): Promise<void> {
  useConsentStore.getState().datTrangThai('revoked')
  useConsentStore.getState().datReceipt(null)
  useConsentStore.getState().datTrackedOnlineUsers(null)
  try {
    await fetch(`${API_GOC}/analytics/consent`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ anonymous_id: damBaoAnonymousId(), granted: false }),
    })
  } catch {
    return
  }
}

/** Mount một lần ở App. Tự dừng khi thu hồi consent, không gửi gì thêm. */
export function batDauAnalytics(): () => void {
  const { trangThai } = useConsentStore.getState()
  if (trangThai !== 'granted') return () => {}

  void ghiSuKien('session_started')
  void ghiSuKien('page_viewed')

  const henEngaged = window.setTimeout(() => {
    if (document.visibilityState === 'visible') void ghiSuKien('page_engaged')
  }, NGHENG_ENGAGED_MS)

  const henFlush = window.setInterval(() => {
    if (useConsentStore.getState().trangThai !== 'granted') return
    void flush(true)
  }, CHU_KY_FLUSH_MS)

  const henHeartbeat = window.setInterval(() => {
    if (document.visibilityState !== 'visible') return
    if (useConsentStore.getState().trangThai !== 'granted') return
    void flush(true)
  }, CHU_KY_HEARTBEAT_MS)

  return () => {
    window.clearTimeout(henEngaged)
    window.clearInterval(henFlush)
    window.clearInterval(henHeartbeat)
  }
}