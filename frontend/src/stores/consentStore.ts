import { create } from 'zustand'

const KHOA = 'quan4-consent'

export type TrangThaiConsent = 'chua-chon' | 'granted' | 'revoked'

// anonymous_id = định danh thiết bị ngẫu nhiên, KHÔNG phải định danh người.
// Sinh một lần rồi giữ trong localStorage để server đếm được "thiết bị"
// chứ không đếm tab (nhiều tab cùng id vẫn là một thiết bị).
function taoIdChonNhiem(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return `anon-${crypto.randomUUID()}`
  return `anon-${Math.random().toString(36).slice(2)}${Math.random().toString(36).slice(2)}`
}

export function damBaoAnonymousId(): string {
  const cu = localStorage.getItem('quan4-anon-id')
  if (cu !== null && cu.length >= 16) return cu
  const moi = taoIdChonNhiem()
  localStorage.setItem('quan4-anon-id', moi)
  return moi
}

// session_id đổi mỗi lần mở app, nằm trong sessionStorage nên tab mới là
// phiên mới. Tách khỏi anonymous_id là điểm mấu chốt của việc đếm thiết bị.
export function laySessionId(): string {
  const cu = sessionStorage.getItem('quan4-session-id')
  if (cu !== null && cu.length >= 8) return cu
  const moi = `sess-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`
  sessionStorage.setItem('quan4-session-id', moi)
  return moi
}

interface ConsentState {
  trangThai: TrangThaiConsent
  receipt: string | null
  trackedOnlineUsers: number | null
  datTrangThai: (t: TrangThaiConsent) => void
  datReceipt: (r: string | null) => void
  datTrackedOnlineUsers: (n: number | null) => void
}

function docTrangThai(): TrangThaiConsent {
  const cu = localStorage.getItem(KHOA)
  return cu === 'granted' || cu === 'revoked' ? cu : 'chua-chon'
}

export const useConsentStore = create<ConsentState>((set) => ({
  trangThai: docTrangThai(),
  receipt: null,
  // null = chưa có số liệu (Redis tắt), khác 0 = thật sự không có ai online.
  trackedOnlineUsers: null,
  datTrangThai: (t) => {
    localStorage.setItem(KHOA, t)
    set({ trangThai: t })
  },
  datReceipt: (r) => set({ receipt: r }),
  datTrackedOnlineUsers: (n) => set({ trackedOnlineUsers: n }),
}))

export function daDongY(): boolean {
  return useConsentStore.getState().trangThai === 'granted'
}