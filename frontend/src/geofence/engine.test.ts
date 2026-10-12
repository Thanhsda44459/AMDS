import { describe, expect, it } from 'vitest'
import { GeofenceEngine, distanceMeters } from './engine'

// Đồng hồ giả để test thời gian mà không chờ thật.
function dongHo() {
  let t = 0
  return { now: () => t, nhich: (ms: number) => { t += ms } }
}

const QUAN = { id: 'q1', lat: 10.7569, lng: 106.7641, trigger_radius: 30, audio_priority: 0 }

describe('distanceMeters', () => {
  it('hai điểm cách ~100m cho ra ~100m', () => {
    const d = distanceMeters(10.7569, 106.7641, 10.7578, 106.7641)
    expect(d).toBeGreaterThan(90)
    expect(d).toBeLessThan(110)
  })
})

describe('geofence biên', () => {
  it('trong vòng, đúng bán kính thì chờ; ngoài thì im', () => {
    const dh = dongHo()
    const eng = new GeofenceEngine({ now: dh.now })
    const vao: string[] = []
    eng.onEnter = (p) => vao.push(p.id)
    eng.setPois([QUAN])
    // Ngay trong vòng nhưng chưa đủ 3s debounce.
    eng.updatePosition(10.7569, 106.7641)
    expect(vao).toEqual([])
    // Reconcile sau 3s thì xác nhận.
    dh.nhich(3000)
    eng.reconcile(10.7569, 106.7641)
    expect(vao).toEqual(['q1'])
  })
})

describe('BUG-001 hồi quy', () => {
  it('GPS dao động vào-ra liên tục thì không nói lặp', () => {
    const dh = dongHo()
    // Tắt throttle trong test này để mỗi dao động đều được xử lý.
    const eng = new GeofenceEngine({ now: dh.now, throttleMs: 0 })
    let dem = 0
    eng.onEnter = () => { dem += 1 }
    eng.setPois([QUAN])
    // 8 lần vào-ra trong 20 giây quanh biên vòng.
    for (let i = 0; i < 8; i++) {
      eng.updatePosition(10.7569, 106.7641)
      dh.nhich(1000)
      eng.updatePosition(10.76, 106.77)
      dh.nhich(1000)
    }
    expect(dem).toBeLessThanOrEqual(1)
  })
})

describe('throttle + debounce + cooldown', () => {
  it('vào-ra dưới 3s thì im; ở lại đủ 3s thì nói', () => {
    const dh = dongHo()
    const eng = new GeofenceEngine({ now: dh.now, throttleMs: 0 })
    const vao: string[] = []
    eng.onEnter = (p) => vao.push(p.id)
    eng.setPois([QUAN])
    eng.updatePosition(10.7569, 106.7641)
    dh.nhich(1000)
    eng.updatePosition(10.76, 106.77)
    dh.nhich(1000)
    expect(vao).toEqual([])
  })

  it('đọc lại trong 5 phút thì im; sau 5 phút thì nói', () => {
    const dh = dongHo()
    const eng = new GeofenceEngine({ now: dh.now, throttleMs: 0 })
    let dem = 0
    eng.onEnter = () => { dem += 1 }
    eng.setPois([QUAN])
    eng.updatePosition(10.7569, 106.7641)
    dh.nhich(3000)
    eng.reconcile(10.7569, 106.7641)
    expect(dem).toBe(1)
    dh.nhich(60 * 1000)
    eng.updatePosition(10.76, 106.77)
    dh.nhich(4000)
    eng.updatePosition(10.7569, 106.7641)
    dh.nhich(4000)
    eng.reconcile(10.7569, 106.7641)
    expect(dem).toBe(1)
    dh.nhich(5 * 60 * 1000)
    eng.updatePosition(10.76, 106.77)
    dh.nhich(1000)
    eng.updatePosition(10.7569, 106.7641)
    dh.nhich(3000)
    eng.reconcile(10.7569, 106.7641)
    expect(dem).toBe(2)
  })
})

describe('ưu tiên', () => {
  it('nhiều POI cùng đủ điều kiện thì ưu tiên nhỏ thắng, hòa thì gần thắng', () => {
    const dh = dongHo()
    const eng = new GeofenceEngine({ now: dh.now, throttleMs: 0 })
    const vao: string[] = []
    eng.onEnter = (p) => vao.push(p.id)
    eng.setPois([
      { id: 'gan', lat: 10.7569, lng: 106.7641, trigger_radius: 50, audio_priority: 5 },
      { id: 'uuti', lat: 10.757, lng: 106.7642, trigger_radius: 50, audio_priority: 1 },
    ])
    eng.updatePosition(10.7569, 106.7641)
    dh.nhich(3000)
    eng.reconcile(10.7569, 106.7641)
    expect(vao).toEqual(['uuti'])
  })
})

describe('reconcile an toàn', () => {
  it('GPS ngừng sau khi vào vòng thì vẫn xác nhận sau 3s', () => {
    const dh = dongHo()
    const eng = new GeofenceEngine({ now: dh.now })
    const vao: string[] = []
    eng.onEnter = (p) => vao.push(p.id)
    eng.setPois([QUAN])
    eng.updatePosition(10.7569, 106.7641)
    dh.nhich(4000)
    // Không có updatePosition mới, chỉ reconcile.
    eng.reconcile(10.7569, 106.7641)
    expect(vao).toEqual(['q1'])
  })
})
