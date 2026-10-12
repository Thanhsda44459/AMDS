import type { Poi } from '../stores/poiStore'

// Prefetch nền POI is_fallback trong 500m, 3 POI mỗi đợt.
// 429 thì backoff 30 → 60 → 120s... tối đa 10 phút.
export function tinhBackoff(lanThatBai: number): number {
  return Math.min(30 * 2 ** lanThatBai * 1000, 10 * 60 * 1000)
}

function khoangCach(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371000
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLng = ((lng2 - lng1) * Math.PI) / 180
  const s =
    Math.sin(dLat / 2) ** 2 + Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(s))
}

// Chọn tối đa 3 POI fallback gần nhất trong 500m.
export function chonPrefetch(pois: Poi[], lat: number, lng: number): Poi[] {
  return pois
    .filter((p) => p.is_fallback)
    .map((p) => ({ p, kc: khoangCach(lat, lng, p.lat, p.lng) }))
    .filter(({ kc }) => kc <= 500)
    .sort((a, b) => a.kc - b.kc)
    .slice(0, 3)
    .map(({ p }) => p)
}
