import { describe, expect, it } from 'vitest'
import { chonPrefetch, tinhBackoff } from './prefetch'
import type { Poi } from '../stores/poiStore'

const poi = (id: string, lat: number, fallback: boolean): Poi => ({
  id, name: id, description: '', lat, lng: 106.7641, trigger_radius: 30, audio_priority: 0,
  lang: 'ja', is_fallback: fallback, audio_url: null,
})

describe('prefetch', () => {
  it('chọn tối đa 3 fallback gần nhất trong 500m', () => {
    const ds = [
      poi('xa', 10.8, true),
      poi('a', 10.7569, true),
      poi('b', 10.757, true),
      poi('c', 10.7571, true),
      poi('d', 10.7572, true),
      poi('sẵn', 10.7569, false),
    ]
    const chon = chonPrefetch(ds, 10.7569, 106.7641)
    expect(chon.map((p) => p.id)).toEqual(['a', 'b', 'c'])
  })

  it('backoff 30 → 60 → 120, trần 10 phút', () => {
    expect(tinhBackoff(0)).toBe(30000)
    expect(tinhBackoff(1)).toBe(60000)
    expect(tinhBackoff(2)).toBe(120000)
    expect(tinhBackoff(99)).toBe(600000)
  })
})
