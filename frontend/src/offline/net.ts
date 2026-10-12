// Một module duy nhất đọc trạng thái mạng, cả app hỏi ở đây (REF-4).

export type TrangThaiMang = 'online' | 'offline' | 'dang-tham-do'

const nguoiNghe = new Set<(trangThai: TrangThaiMang) => void>()
let trangThai: TrangThaiMang = navigator.onLine ? 'online' : 'offline'

function bao() {
  for (const fn of nguoiNghe) fn(trangThai)
}

window.addEventListener('online', () => {
  trangThai = 'online'
  bao()
})
window.addEventListener('offline', () => {
  trangThai = 'offline'
  bao()
})

export function layTrangThaiMang(): TrangThaiMang {
  return trangThai
}

export function theoDoiMang(fn: (trangThai: TrangThaiMang) => void): () => void {
  nguoiNghe.add(fn)
  return () => {
    nguoiNghe.delete(fn)
  }
}

// Probe khởi động 2.5s, tối đa 2 lần mỗi 8s để không tuyên bố hỏng quá sớm.
export async function thamDoBackend(urlGoc: string): Promise<boolean> {
  trangThai = 'dang-tham-do'
  bao()
  for (let lan = 0; lan < 2; lan++) {
    const dieuKhien = new AbortController()
    const henGio = window.setTimeout(() => dieuKhien.abort(), 2500)
    try {
      const res = await fetch(`${urlGoc}/health`, { signal: dieuKhien.signal })
      window.clearTimeout(henGio)
      if (res.ok) {
        trangThai = 'online'
        bao()
        return true
      }
    } catch {
      window.clearTimeout(henGio)
    }
    if (lan === 0) await new Promise((r) => window.setTimeout(r, 8000))
  }
  trangThai = navigator.onLine ? 'online' : 'offline'
  bao()
  return trangThai === 'online'
}
