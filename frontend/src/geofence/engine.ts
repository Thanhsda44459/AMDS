// GeofenceEngine thuần TypeScript, không phụ thuộc React (ADR-007).
// Hook useGeofence chỉ làm cầu nối. Test được mà không cần render.

export interface EnginePoi {
  id: string
  lat: number
  lng: number
  trigger_radius: number
  audio_priority: number
}

export interface EngineOpts {
  throttleMs?: number
  debounceMs?: number
  cooldownMs?: number
  now?: () => number
}

// Khoảng cách Haversine (mặt cầu), không dùng Euclid trên lat/lng.
export function distanceMeters(aLat: number, aLng: number, bLat: number, bLng: number): number {
  const R = 6371000
  const dLat = ((bLat - aLat) * Math.PI) / 180
  const dLng = ((bLng - aLng) * Math.PI) / 180
  const s =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((aLat * Math.PI) / 180) * Math.cos((bLat * Math.PI) / 180) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(s))
}

interface TrangThaiPoi {
  dangChoTu?: number
  docLanCuoi?: number
}

export class GeofenceEngine {
  private pois: EnginePoi[] = []
  private trangThai = new Map<string, TrangThaiPoi>()
  private xuLyLanCuoi = -Infinity
  private readonly throttleMs: number
  private readonly debounceMs: number
  private readonly cooldownMs: number
  private readonly now: () => number
  onEnter: (poi: EnginePoi) => void = () => {}

  constructor(opts: EngineOpts = {}) {
    this.throttleMs = opts.throttleMs ?? 5000
    this.debounceMs = opts.debounceMs ?? 3000
    this.cooldownMs = opts.cooldownMs ?? 5 * 60 * 1000
    this.now = opts.now ?? (() => Date.now())
  }

  setPois(pois: EnginePoi[]): void {
    this.pois = pois
  }

  // Vị trí mới từ GPS. Throttle 5s để tiết kiệm pin/CPU.
  updatePosition(lat: number, lng: number): void {
    const t = this.now()
    if (t - this.xuLyLanCuoi < this.throttleMs) return
    this.xuLyLanCuoi = t
    this.quyetDinh(lat, lng, t)
  }

  // Vòng reconcile an toàn mỗi 5s: GPS ngừng gửi thì mục chờ vẫn được xác nhận.
  reconcile(lat: number, lng: number): void {
    this.quyetDinh(lat, lng, this.now())
  }

  private quyetDinh(lat: number, lng: number, t: number): void {
    const vuaXacNhan: { poi: EnginePoi; dist: number }[] = []
    for (const poi of this.pois) {
      const dist = distanceMeters(lat, lng, poi.lat, poi.lng)
      const st = this.trangThai.get(poi.id) ?? {}
      if (dist <= poi.trigger_radius) {
        const conCooldown = st.docLanCuoi !== undefined && t - st.docLanCuoi < this.cooldownMs
        if (conCooldown) continue
        if (st.dangChoTu === undefined) {
          st.dangChoTu = t
          this.trangThai.set(poi.id, st)
        } else if (t - st.dangChoTu >= this.debounceMs) {
          vuaXacNhan.push({ poi, dist })
          st.dangChoTu = undefined
          // Mốc cooldown tính từ lúc đọc xong (ADR-006, chọn B).
          st.docLanCuoi = t
          this.trangThai.set(poi.id, st)
        }
      } else if (st.dangChoTu !== undefined) {
        // Ra khỏi vòng trước khi đủ 3s thì hủy chờ.
        st.dangChoTu = undefined
        this.trangThai.set(poi.id, st)
      }
    }
    if (vuaXacNhan.length === 0) return
    // Nhiều POI cùng đủ điều kiện: ưu tiên nhỏ trước, hòa thì gần hơn.
    vuaXacNhan.sort((a, b) => a.poi.audio_priority - b.poi.audio_priority || a.dist - b.dist)
    this.onEnter(vuaXacNhan[0].poi)
  }
}
