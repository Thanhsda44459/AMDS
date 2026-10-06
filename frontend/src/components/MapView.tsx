import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Poi } from '../stores/poiStore'

// Tâm Quận 4, khu Vĩnh Khánh ăn uống.
const TAM_Q4: [number, number] = [106.7641, 10.7569]
const STYLE_MIEN_PHI = 'https://demotiles.maplibre.org/style.json'

interface Props {
  pois: Poi[]
  selectedId: string | null
  onSelect: (id: string) => void
}

// Lời hướng dẫn theo từng lỗi định vị của trình duyệt.
function loiDinhVi(code?: number): string {
  if (code === 1) return 'Bạn đã chặn quyền vị trí. Bật lại trong cài đặt trình duyệt để thấy chấm xanh.'
  if (code === 2) return 'Không có tín hiệu vị trí. Bản đồ vẫn kéo xem được.'
  if (code === 3) return 'Hết giờ chờ vị trí. Bản đồ vẫn dùng được.'
  return ''
}

export default function MapView({ pois, selectedId, onSelect }: Props) {
  const khungRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const [thongBaoViTri, setThongBaoViTri] = useState('')
  const [dungCloud, setDungCloud] = useState(false)

  // MAP-001 + MAP-006: dựng bản đồ, có key thì dùng style cloud, không thì demo miễn phí.
  useEffect(() => {
    if (khungRef.current === null || mapRef.current !== null) return
    const key = import.meta.env.VITE_MAPTILER_KEY as string | undefined
    const style = key !== undefined && key !== '' ? `https://api.maptiler.com/maps/streets-v2/style.json?key=${key}` : STYLE_MIEN_PHI
    setDungCloud(style !== STYLE_MIEN_PHI)
    const map = new maplibregl.Map({
      container: khungRef.current,
      style,
      center: TAM_Q4,
      zoom: 14,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-right')
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // MAP-002: một marker cho mỗi POI, chú ý thứ tự [lng, lat]. Dọn khi pois đổi.
  useEffect(() => {
    const map = mapRef.current
    if (map === null) return
    const markers: maplibregl.Marker[] = []
    for (const poi of pois) {
      const marker = new maplibregl.Marker({
        color: poi.id === selectedId ? '#e11d48' : '#2563eb',
      })
        .setLngLat([poi.lng, poi.lat])
        .addTo(map)
      // MAP-003: bấm marker thì báo id về App để mở panel.
      marker.getElement().addEventListener('click', () => onSelect(poi.id))
      markers.push(marker)
    }
    return () => {
      for (const m of markers) m.remove()
    }
  }, [pois, selectedId, onSelect])

  // MAP-004 + MAP-005: chấm xanh vị trí user, xử lý 3 lỗi mà bản đồ vẫn dùng được.
  useEffect(() => {
    if (!('geolocation' in navigator)) {
      queueMicrotask(() => setThongBaoViTri('Thiết bị không hỗ trợ định vị. Bản đồ vẫn xem được.'))
      return
    }
    let cham: maplibregl.Marker | null = null
    const id = navigator.geolocation.watchPosition(
      (pos) => {
        const map = mapRef.current
        if (map === null) return
        setThongBaoViTri('')
        if (cham === null) {
          const el = document.createElement('div')
          el.style.width = '14px'
          el.style.height = '14px'
          el.style.borderRadius = '50%'
          el.style.background = '#22c55e'
          el.style.border = '3px solid white'
          cham = new maplibregl.Marker({ element: el }).setLngLat([pos.coords.longitude, pos.coords.latitude]).addTo(map)
        } else {
          cham.setLngLat([pos.coords.longitude, pos.coords.latitude])
        }
      },
      (err) => setThongBaoViTri(loiDinhVi(err.code)),
      { enableHighAccuracy: true, timeout: 8000 },
    )
    return () => {
      navigator.geolocation.clearWatch(id)
      cham?.remove()
    }
  }, [])

  return (
    <div>
      <div ref={khungRef} style={{ width: '100%', height: '380px' }} />
      <p>{dungCloud ? 'Đang dùng nền MapTiler cloud.' : 'Đang dùng nền demo miễn phí. Thêm VITE_MAPTILER_KEY để dùng cloud.'}</p>
      {thongBaoViTri !== '' && <p>{thongBaoViTri}</p>}
    </div>
  )
}
