// Kênh quan sát vị trí runtime — TÁCH BIỆT khỏi analytics (ANA-005).
//
// Đây là lane chẩn đoán: "GPS có hoạt động không, độ chính xác bao nhiêu,
// có bị từ chối quyền không". Nó CỐ Ý không phụ thuộc consent analytics —
// gộp vào thì hoặc hỏng ranh giới riêng tư, hoặc biến chẩn đoán thành theo dõi.
// File này không import analytics/service để ranh giới đó nằm ngay trong code.

const API_GOC = 'http://127.0.0.1:8000'

export const CHU_KY_FLUSH_MS = 60000
// Server chặn payload >16 KiB, nên tự cắt trước khi gửi cho đừng bị 413.
const TOI_DA_MAU = 20

export interface MauViTri {
  lat: number
  lng: number
  accuracy?: number
  outcome: string
}

let buffer: MauViTri[] = []
let sessionId = ''
let henGio = 0

export function baoMau(mau: MauViTri): void {
  if (buffer.length >= TOI_DA_MAU) buffer.shift()
  buffer.push({
    lat: Number(mau.lat.toFixed(3)),
    lng: Number(mau.lng.toFixed(3)),
    ...(mau.accuracy === undefined ? {} : { accuracy: Math.round(mau.accuracy) }),
    outcome: mau.outcome,
  })
}

async function gui(): Promise<void> {
  if (buffer.length === 0 || sessionId === '') return
  const mau = buffer
  buffer = []
  try {
    await fetch(`${API_GOC}/runtime-observability/location`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      keepalive: true,
      body: JSON.stringify({ session_id: sessionId, samples: mau }),
    })
  } catch {
    return
  }
}

/** sendBeacon để đóng tab không mất mẫu cuối cùng. */
export function flushBangBeacon(): void {
  if (buffer.length === 0 || sessionId === '') return
  const mau = buffer
  buffer = []
  const blob = new Blob([JSON.stringify({ session_id: sessionId, samples: mau })], {
    type: 'application/json',
  })
  navigator.sendBeacon?.(`${API_GOC}/runtime-observability/location`, blob)
}

export function batDauQuanSatVịTri(lamLaySessionId: () => string): () => void {
  sessionId = lamLaySessionId()
  henGio = window.setInterval(() => void gui(), CHU_KY_FLUSH_MS)
  window.addEventListener('pagehide', flushBangBeacon)
  return () => {
    window.clearInterval(henGio)
    window.removeEventListener('pagehide', flushBangBeacon)
  }
}

export function soMauDangCho(): number {
  return buffer.length
}

export function xoaBuffer(): void {
  buffer = []
}