import { describe, expect, it } from 'vitest'
import { gopDelta } from './sync'
import type { Poi } from '../stores/poiStore'

const poi = (id: string, name: string): Poi => ({
  id, name, description: '', lat: 0, lng: 0, trigger_radius: 30, audio_priority: 0,
  lang: 'vi', is_fallback: false, audio_url: null,
})

describe('gopDelta', () => {
  it('xóa theo removed, cập nhật theo id, giữ còn lại', () => {
    const cu = [poi('1', 'Mot'), poi('2', 'Hai'), poi('3', 'Ba')]
    const gop = gopDelta(cu, [poi('2', 'Hai-moi'), poi('4', 'Bon')], ['3'])
    const ten = new Map(gop.map((p) => [p.id, p.name]))
    expect(ten.get('1')).toBe('Mot')
    expect(ten.get('2')).toBe('Hai-moi')
    expect(ten.get('4')).toBe('Bon')
    expect(ten.has('3')).toBe(false)
  })

  it('delta rỗng thì giữ nguyên', () => {
    const cu = [poi('1', 'Mot')]
    expect(gopDelta(cu, [], [])).toEqual(cu)
  })
})
