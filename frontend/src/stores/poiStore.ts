import { create } from 'zustand'
import { dongBo } from '../offline/sync'

// Một POI như backend trả về ở GET /poi (đã hydrate ngôn ngữ).
export interface Poi {
  id: string
  name: string
  description: string
  lat: number
  lng: number
  trigger_radius: number
  audio_priority: number
  lang: string
  is_fallback: boolean
  audio_url: string | null
}

export const NGON_NGU: { ma: string; ten: string }[] = [
  { ma: 'vi', ten: 'Tiếng Việt' },
  { ma: 'en', ten: 'English' },
  { ma: 'zh', ten: '中文' },
  { ma: 'ja', ten: '日本語' },
  { ma: 'ko', ten: '한국어' },
]

interface PoiState {
  pois: Poi[]
  loading: boolean
  error: string
  lang: string
  setLang: (lang: string) => void
  fetchPOIs: () => Promise<void>
}

// State toàn cục (nơi duy nhất giữ danh sách POI cho mọi component).
export const usePoiStore = create<PoiState>((set, get) => ({
  pois: [],
  loading: false,
  error: '',
  // Cài đặt ngôn ngữ nội dung, không phải bí mật nên lưu localStorage được.
  lang: localStorage.getItem('quan4-lang') ?? 'vi',
  setLang: (lang: string) => {
    localStorage.setItem('quan4-lang', lang)
    set({ lang })
    void get().fetchPOIs()
  },
  fetchPOIs: async () => {
    set({ loading: true, error: '' })
    try {
      // Online thì delta sync, offline thì IDB fallback (không màn hình trống).
      const { pois, tuMang } = await dongBo(get().lang)
      if (!tuMang && pois.length === 0) throw new Error('offline')
      set({ pois, loading: false })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : 'Lỗi không rõ', loading: false })
    }
  },
}))
