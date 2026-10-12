import { describe, expect, it, vi } from 'vitest'
import { playWithFallback } from './playback'

const GOC = { poiId: 'p1', lang: 'ja', text: 'Phở ngon', audioUrl: null as string | null, isFallback: true, uuTien: 0 }

describe('playWithFallback', () => {
  it('tier1 khi có file và không fallback', async () => {
    const tier = await playWithFallback({ ...GOC, audioUrl: '/f.mp3', isFallback: false })
    expect(tier).toBe('tier1')
  })

  it('rơi dần 1.5 → 2 → 3 khi từng tầng lỗi', async () => {
    const goi = vi.fn()
    vi.stubGlobal('fetch', goi)
    goi.mockResolvedValueOnce({ ok: true, json: async () => ({ audio_url: '/o.mp3' }) })
    expect(await playWithFallback(GOC)).toBe('tier1.5')
    goi.mockRejectedValueOnce(new Error('mang hong'))
    goi.mockResolvedValueOnce({ ok: true, blob: async () => new Blob(['x']) })
    expect(await playWithFallback(GOC)).toBe('tier2')
    goi.mockRejectedValue(new Error('mang hong'))
    expect(await playWithFallback(GOC)).toBe('tier3')
    vi.unstubAllGlobals()
  })

  it('đổi ngôn ngữ giữa chừng thì bỏ kết quả cũ', async () => {
    const goi = vi.fn()
    vi.stubGlobal('fetch', goi)
    let giai: (v: { ok: boolean; json: () => Promise<unknown> }) => void = () => {}
    goi.mockImplementationOnce(() => new Promise((res) => { giai = res }))
    const truoc = playWithFallback(GOC)
    const sau = playWithFallback({ ...GOC, lang: 'ko' })
    giai({ ok: true, json: async () => ({ audio_url: '/cu.mp3' }) })
    expect(await truoc).toBe('bo')
    await sau
    vi.unstubAllGlobals()
  })
})
