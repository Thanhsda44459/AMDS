import { api, apiText } from '../admin/api'
import { speak } from '../geofence/audio'

const API_GOC = 'http://127.0.0.1:8000'

// Hàng đợi một ô cho file audio: thay thế khi ưu tiên cao hơn.
class FileQueue {
  private audio: HTMLAudioElement | null = null
  private uuTien: number | null = null

  play(url: string, uuTien: number): 'phat' | 'bo' {
    if (this.uuTien !== null && uuTien >= this.uuTien) return 'bo'
    this.stop()
    this.uuTien = uuTien
    // Môi trường test không có Audio, ghi nhận trạng thái là đủ.
    if (typeof Audio === 'undefined') return 'phat'
    this.audio = new Audio(url)
    this.audio.onended = () => {
      this.audio = null
      this.uuTien = null
    }
    void this.audio.play()
    return 'phat'
  }

  stop(): void {
    this.audio?.pause()
    this.audio = null
    this.uuTien = null
  }
}

export const fileQueue = new FileQueue()
let lanPhat = 0

export interface PhatYeuCau {
  poiId: string
  lang: string
  text: string
  audioUrl: string | null
  isFallback: boolean
  uuTien: number
}

// 4 tầng: file sinh sẵn → on-demand → stream → đọc trình duyệt.
// Đổi ngôn ngữ giữa chừng thì bỏ kết quả lỗi thời.
export async function playWithFallback(yeuCau: PhatYeuCau): Promise<string> {
  const token = ++lanPhat
  const conHan = () => token === lanPhat
  const { poiId, lang, text, audioUrl, isFallback, uuTien } = yeuCau

  if (audioUrl !== null && !isFallback) {
    fileQueue.play(`${API_GOC}${audioUrl}`, uuTien)
    return 'tier1'
  }
  if (isFallback) {
    try {
      const goi = await api<{ audio_url: string }>('/audio/on-demand', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ poi_id: poiId, lang }),
      })
      if (!conHan()) return 'bo'
      fileQueue.play(`${API_GOC}${goi.audio_url}`, uuTien)
      return 'tier1.5'
    } catch {
      if (!conHan()) return 'bo'
    }
  }
  try {
    const res = await apiText('/audio/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, lang }),
    })
    if (!conHan()) return 'bo'
    if (!res.ok) throw new Error()
    const blob = await res.blob()
    if (!conHan()) return 'bo'
    fileQueue.play(URL.createObjectURL(blob), uuTien)
    return 'tier2'
  } catch {
    if (!conHan()) return 'bo'
  }
  speak(text, lang)
  return 'tier3'
}
