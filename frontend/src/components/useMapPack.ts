import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { StyleSpecification } from 'maplibre-gl'
import { Protocol } from 'pmtiles'

const API_GOC = 'http://127.0.0.1:8000'
export type CheDo = 'cloud' | 'offline' | 'hybrid'

// Đăng ký giao thức một lần, tile đi qua fetch nên SW cache phục vụ offline.
let daDangKyPmtiles = false
function damBaoPmtiles() {
  if (daDangKyPmtiles) return
  maplibregl.addProtocol('pmtiles', new Protocol().tile)
  daDangKyPmtiles = true
}

export interface TepPack {
  file: string
  sha256: string
  bytes: number
}

// Hysteresis: vào offline ngay khi mất mạng, về cloud trễ để chống nhấp nháy.
const TRE_VE_CLOUD_MS = 10000

async function sha256Hex(buf: ArrayBuffer): Promise<string> {
  const hash = await crypto.subtle.digest('SHA-256', buf)
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, '0')).join('')
}

export function useMapPack() {
  const [cheDo, setCheDo] = useState<CheDo>('hybrid')
  const [stylePack, setStylePack] = useState<StyleSpecification | null>(null)
  const [trangThai, setTrangThai] = useState('')
  const henGio = useRef(0)

  // Chỉ kích hoạt sau khi hash đạt, style.json của pack quyết định vẽ gì.
  const kichHoat = async (tenCache: string, styleUrl: string) => {
    damBaoPmtiles()
    const cache = await caches.open(tenCache)
    const res = await cache.match(styleUrl)
    if (!res) {
      setTrangThai('Thiếu style.json trong pack, cần repairRequired')
      return
    }
    setStylePack(await res.json())
  }

  const taiPack = async (scope: string, thayThe = false) => {
    setTrangThai('Đang tải manifest...')
    let manifest: { files: TepPack[]; fingerprint: string }
    try {
      const res = await fetch(`${API_GOC}/maps/manifest?scope=${scope}`)
      manifest = (await res.json()) as typeof manifest
    } catch {
      setTrangThai('Manifest lỗi, thử lại sau')
      return
    }
    if (manifest.files.length === 0) {
      setTrangThai('Scope chưa có tệp .pmtiles trên server')
      return
    }
    const tenCache = `map-pack-${scope}`
    if (!thayThe) {
      const cu = await caches.open(tenCache).then((c) => c.keys())
      const styleCu = cu.find((r) => r.url.endsWith('.json'))
      if (styleCu) {
        await kichHoat(tenCache, styleCu.url)
        setTrangThai('Đã có pack, dùng luôn')
        return
      }
    }
    const cache = await caches.open(tenCache)
    let styleUrl: string | null = null
    for (const tep of manifest.files) {
      setTrangThai(`Đang tải ${tep.file}...`)
      try {
        const res = await fetch(`${API_GOC}/maps/pack/${tep.file}`)
        const buf = await res.arrayBuffer()
        if ((await sha256Hex(buf)) !== tep.sha256) {
          setTrangThai('Tệp hỏng (sai hash), cần repairRequired')
          await cache.delete(`${API_GOC}/maps/pack/${tep.file}`)
          return
        }
        const urlDayDu = `${API_GOC}/maps/pack/${tep.file}`
        await cache.put(urlDayDu, new Response(buf))
        if (tep.file.endsWith('.json')) styleUrl = urlDayDu
      } catch (e) {
        // Hết dung lượng thì dọn cache runtime nhường chỗ cho pack.
        if (e instanceof DOMException && e.name === 'QuotaExceededError') {
          for (const ten of await caches.keys()) {
            if (!ten.startsWith('map-pack-')) await caches.delete(ten)
          }
          setTrangThai('Đã dọn cache runtime, bấm tải lại')
          return
        }
        setTrangThai('Tải thất bại')
        return
      }
    }
    if (!styleUrl) {
      setTrangThai('Pack thiếu style.json, cần repairRequired')
      return
    }
    await kichHoat(tenCache, styleUrl)
    setTrangThai(`Cài xong pack ${scope}`)
  }

  // Hybrid: rớt mạng thì giữ pack, có mạng lại thì chờ 10s mới về cloud.
  const [tamOffline, setTamOffline] = useState(false)
  useEffect(() => {
    if (cheDo !== 'hybrid') return
    const capNhat = () => {
      if (!navigator.onLine) {
        window.clearTimeout(henGio.current)
        setTamOffline(true)
      } else {
        window.clearTimeout(henGio.current)
        henGio.current = window.setTimeout(() => setTamOffline(false), TRE_VE_CLOUD_MS)
      }
    }
    window.addEventListener('online', capNhat)
    window.addEventListener('offline', capNhat)
    return () => {
      window.removeEventListener('online', capNhat)
      window.removeEventListener('offline', capNhat)
    }
  }, [cheDo])

  useEffect(() => () => window.clearTimeout(henGio.current), [])

  return { cheDo, setCheDo, stylePack, tamOffline, trangThai, taiPack }
}

export type PackHook = ReturnType<typeof useMapPack>
