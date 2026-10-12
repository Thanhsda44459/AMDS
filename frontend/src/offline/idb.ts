// IndexedDB hai lớp cùng SW cache: SW bị dọn thì IDB còn dữ liệu.
//
// Module này là **chủ sở hữu duy nhất** của schema `quan4-offline`. Ai cần
// thêm object store thì khai ở đây và export hằng tên ra, đừng tự mở DB ở
// module khác: IndexedDB chỉ cho mở đúng version đã tồn tại, nên nếu outbox
// mở version 2 rồi idb.ts mở version 1 thì mọi lần đọc POI offline sẽ ném
// `VersionError` — lúc đó mới phát hiện là quá trễ.

import type { Poi } from '../stores/poiStore'

const TEN_DB = 'quan4-offline'
export const KHO_POI = 'pois_by_lang'
export const KHO_META = 'meta'
export const KHO_OUTBOX = 'analytics_outbox'
// v1: POI + meta. v2: thêm outbox analytics cho Phase 10.
const PHIEN_DB = 2

export function moDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const yeuCau = indexedDB.open(TEN_DB, PHIEN_DB)
    yeuCau.onupgradeneeded = () => {
      const db = yeuCau.result
      if (!db.objectStoreNames.contains(KHO_POI)) {
        db.createObjectStore(KHO_POI, { keyPath: 'lang' })
      }
      if (!db.objectStoreNames.contains(KHO_META)) {
        db.createObjectStore(KHO_META, { keyPath: 'khoa' })
      }
      if (!db.objectStoreNames.contains(KHO_OUTBOX)) {
        db.createObjectStore(KHO_OUTBOX, { keyPath: 'id', autoIncrement: true })
      }
    }
    yeuCau.onsuccess = () => resolve(yeuCau.result)
    yeuCau.onerror = () => reject(yeuCau.error)
  })
}

function ghi(db: IDBDatabase, kho: string, giaTri: unknown): Promise<void> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(kho, 'readwrite')
    tx.objectStore(kho).put(giaTri)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
}

function doc<T>(db: IDBDatabase, kho: string, khoa: string): Promise<T | null> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(kho, 'readonly')
    const yeuCau = tx.objectStore(kho).get(khoa)
    yeuCau.onsuccess = () => resolve((yeuCau.result as T) ?? null)
    yeuCau.onerror = () => reject(yeuCau.error)
  })
}

export async function luuPois(lang: string, pois: Poi[], version: number): Promise<void> {
  const db = await moDb()
  await ghi(db, KHO_POI, { lang, pois, version, saved_at: Date.now() })
  db.close()
}

export async function docPois(lang: string): Promise<{ pois: Poi[]; version: number } | null> {
  const db = await moDb()
  const ban = await doc<{ pois: Poi[]; version: number }>(db, KHO_POI, lang)
  db.close()
  return ban
}

// Chuỗi fallback offline: chọn → en → vi để không màn hình trống.
export async function docPoisFallback(lang: string): Promise<Poi[]> {
  for (const thu of [lang, 'en', 'vi']) {
    try {
      const ban = await docPois(thu)
      if (ban && ban.pois.length > 0) return ban.pois
    } catch {
      continue
    }
  }
  return []
}

export async function luuCursor(lang: string, cursor: number): Promise<void> {
  const db = await moDb()
  await ghi(db, KHO_META, { khoa: `cursor-${lang}`, cursor })
  db.close()
}

export async function docCursor(lang: string): Promise<number> {
  const db = await moDb()
  const ban = await doc<{ cursor: number }>(db, KHO_META, `cursor-${lang}`)
  db.close()
  return ban?.cursor ?? 0
}
