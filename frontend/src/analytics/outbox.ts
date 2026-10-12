// Outbox sự kiện trong IndexedDB: mất mạng thì giữ, có mạng thì gửi lại.
// Đây là lý do không gửi thẳng từ component — sự kiện không được mất vì
// một lần fetch thất bại.
//
// Mở DB và tạo store thì do `offline/idb.ts` làm chủ, không tự mở ở đây:
// hai module mở cùng một DB ở hai version khác nhau sẽ hỏng (VersionError).

import { KHO_OUTBOX, moDb } from '../offline/idb'

export interface SuKienOutbox {
  id?: number
  name: string
  at: number
  properties: Record<string, string | number | boolean>
}

export async function themSuKien(sk: SuKienOutbox): Promise<void> {
  const db = await moDb()
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(KHO_OUTBOX, 'readwrite')
    tx.objectStore(KHO_OUTBOX).add(sk)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
  db.close()
}

export async function laySuKien(gioi_han = 50): Promise<Required<SuKienOutbox>[]> {
  const db = await moDb()
  const ket_qua = await new Promise<Required<SuKienOutbox>[]>((resolve, reject) => {
    const tx = db.transaction(KHO_OUTBOX, 'readonly')
    const req = tx.objectStore(KHO_OUTBOX).getAll(undefined, gioi_han)
    req.onsuccess = () => resolve(req.result as Required<SuKienOutbox>[])
    req.onerror = () => reject(req.error)
  })
  db.close()
  return ket_qua
}

export async function xoaSuKien(ids: number[]): Promise<void> {
  if (ids.length === 0) return
  const db = await moDb()
  await new Promise<void>((resolve, reject) => {
    const tx = db.transaction(KHO_OUTBOX, 'readwrite')
    const store = tx.objectStore(KHO_OUTBOX)
    for (const id of ids) store.delete(id)
    tx.oncomplete = () => resolve()
    tx.onerror = () => reject(tx.error)
  })
  db.close()
}

export async function demSuKien(): Promise<number> {
  const db = await moDb()
  const so = await new Promise<number>((resolve, reject) => {
    const tx = db.transaction(KHO_OUTBOX, 'readonly')
    const req = tx.objectStore(KHO_OUTBOX).count()
    req.onsuccess = () => resolve(req.result)
    req.onerror = () => reject(req.error)
  })
  db.close()
  return so
}