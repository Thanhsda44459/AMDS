// Tier 3 của kiến trúc audio đích: speechSynthesis của trình duyệt.
// Ở V1 đây là tầng duy nhất, sau này hạ xuống làm lưới an toàn cuối.

export function speak(text: string, lang = 'vi-VN'): void {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return
  const utt = new SpeechSynthesisUtterance(text)
  utt.lang = lang
  window.speechSynthesis.speak(utt)
}

// Hàng đợi một ô: chỉ một nội dung phát tại một thời điểm.
// Nội dung mới ưu tiên cao hơn (số nhỏ hơn) thì thay thế, ngược lại bỏ.
export class AudioQueue {
  private dangPhatUuTien: number | null = null

  play(text: string, lang: string, uuTien: number): 'phat' | 'bo' {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return 'bo'
    if (this.dangPhatUuTien !== null && uuTien >= this.dangPhatUuTien) return 'bo'
    window.speechSynthesis.cancel()
    this.dangPhatUuTien = uuTien
    const utt = new SpeechSynthesisUtterance(text)
    utt.lang = lang
    utt.onend = () => {
      this.dangPhatUuTien = null
    }
    window.speechSynthesis.speak(utt)
    return 'phat'
  }
}
