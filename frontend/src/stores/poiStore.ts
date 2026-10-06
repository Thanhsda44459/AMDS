import { create } from 'zustand'

// Một POI như backend trả về ở GET /poi.
export interface Poi {
  id: string
  name: string
  description: string
  lat: number
  lng: number
}

interface PoiState {
  pois: Poi[]
  loading: boolean
  error: string
  fetchPOIs: () => Promise<void>
}

// State toàn cục (nơi duy nhất giữ danh sách POI cho mọi component).
export const usePoiStore = create<PoiState>((set) => ({
  pois: [],
  loading: false,
  error: '',
  fetchPOIs: async () => {
    set({ loading: true, error: '' })
    try {
      const res = await fetch('http://127.0.0.1:8000/poi')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = (await res.json()) as Poi[]
      set({ pois: data, loading: false })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Lỗi không rõ', loading: false })
    }
  },
}))
