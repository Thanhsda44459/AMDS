// Đồng bộ delta: tải toàn bộ lần đầu, sau chỉ tải phần đổi.

import type { Poi } from '../stores/poiStore'
import { docCursor, docPois, docPoisFallback, luuCursor, luuPois } from './idb'

const API_GOC = 'http://127.0.0.1:8000'

// Gộp delta vào danh sách cũ: cập nhật/thêm, xóa theo removed_poi_ids.
export function gopDelta(cu: Poi[], capNhat: Poi[], xoaIds: string[]): Poi[] {
  const boXoa = new Set(xoaIds)
  const bang = new Map(cu.filter((p) => !boXoa.has(p.id)).map((p) => [p.id, p]))
  for (const p of capNhat) bang.set(p.id, p)
  return [...bang.values()]
}

export async function dongBo(lang: string): Promise<{ pois: Poi[]; tuMang: boolean }> {
  const cursor = await docCursor(lang).catch(() => 0)
  try {
    if (cursor === 0) {
      const res = await fetch(`${API_GOC}/poi/load-all?lang=${lang}`)
      if (res.status === 304) {
        const banCu = await docPois(lang)
        if (banCu) return { pois: banCu.pois, tuMang: false }
      }
      if (!res.ok) throw new Error()
      const goi = (await res.json()) as { version: number; sync_cursor: number; pois: Poi[] }
      await luuPois(lang, goi.pois, goi.version)
      await luuCursor(lang, goi.sync_cursor)
      return { pois: goi.pois, tuMang: true }
    }
    const res = await fetch(`${API_GOC}/poi/delta?updated_after=${cursor}&lang=${lang}`)
    if (!res.ok) throw new Error()
    const goi = (await res.json()) as { version: number; sync_cursor: number; updated: Poi[]; removed_poi_ids: string[] }
    const banCu = (await docPois(lang)) ?? { pois: [], version: 0 }
    const gop = gopDelta(banCu.pois, goi.updated, goi.removed_poi_ids)
    await luuPois(lang, gop, goi.version)
    await luuCursor(lang, goi.sync_cursor)
    return { pois: gop, tuMang: true }
  } catch {
    // Mất mạng thì đọc IDB, hết cách mới danh sách rỗng.
    return { pois: await docPoisFallback(lang), tuMang: false }
  }
}
