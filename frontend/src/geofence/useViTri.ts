import { useEffect, useState } from 'react'

// Vị trí user dùng chung cho prefetch, tách khỏi MapView để dễ test.
export function useViTri(): { lat: number; lng: number } | null {
  const [viTri, setViTri] = useState<{ lat: number; lng: number } | null>(null)
  useEffect(() => {
    if (!('geolocation' in navigator)) return
    const id = navigator.geolocation.watchPosition((pos) => {
      setViTri({ lat: pos.coords.latitude, lng: pos.coords.longitude })
    })
    return () => navigator.geolocation.clearWatch(id)
  }, [])
  return viTri
}
