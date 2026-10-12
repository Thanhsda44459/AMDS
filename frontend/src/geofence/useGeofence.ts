import { useEffect, useRef } from 'react'
import { GeofenceEngine, type EnginePoi } from './engine'

// Cầu nối React cho GeofenceEngine: GPS -> engine -> gọi doc khi ENTER.
// Reconcile 5s phòng GPS ngừng gửi giữa lúc debounce. Việc đọc to
// do caller quyết (App dùng AudioQueue để không chồng giọng).
export function useGeofence(pois: EnginePoi[], doc: (poi: EnginePoi) => void): void {
  const docRef = useRef(doc)
  const poisRef = useRef(pois)
  useEffect(() => {
    docRef.current = doc
    poisRef.current = pois
  })

  useEffect(() => {
    if (!('geolocation' in navigator)) return
    const engine = new GeofenceEngine()
    engine.onEnter = (poi) => docRef.current(poi)
    let viTriCuoi: { lat: number; lng: number } | null = null
    const id = navigator.geolocation.watchPosition((pos) => {
      viTriCuoi = { lat: pos.coords.latitude, lng: pos.coords.longitude }
      engine.setPois(poisRef.current)
      engine.updatePosition(pos.coords.latitude, pos.coords.longitude)
    })
    const henGio = window.setInterval(() => {
      if (viTriCuoi !== null) {
        engine.setPois(poisRef.current)
        engine.reconcile(viTriCuoi.lat, viTriCuoi.lng)
      }
    }, 5000)
    return () => {
      navigator.geolocation.clearWatch(id)
      window.clearInterval(henGio)
    }
  }, [])
}
