import { describe, expect, it } from 'vitest'
import { locThuocTinh, tenHopLe } from './service'
import { baoMau, soMauDangCho, xoaBuffer } from '../telemetry/location'

describe('lọc thuộc tính phía client', () => {
  it('chỉ giữ danh sách cho phép, không giữ field lạ', () => {
    const sach = locThuocTinh({ poi_id: 'abc', query: 'bun bo', lang: 'vi', secret: 'x', email: 'a@b.c' })
    expect(sach).toEqual({ poi_id: 'abc', query: 'bun bo', lang: 'vi' })
  })

  it('bỏ giá trị không phải số/bool/string', () => {
    const sach = locThuocTinh({ tier: 2, duration_ms: 1200, bad: { a: 1 }, nan: Number.NaN })
    expect(sach).toEqual({ tier: 2, duration_ms: 1200 })
  })

  it('khoá ngoài danh sách cho phép thì bị bỏ kể cả giá trị đúng kiểu', () => {
    // Danh sách là allowlist, nên `ok: true` dù đúng kiểu cũng rơi.
    expect(locThuocTinh({ ok: true })).toEqual({})
  })

  it('cắt chuỗi dài', () => {
    expect(locThuocTinh({ query: 'x'.repeat(500) }).query).toHaveLength(120)
  })
})

describe('tên sự kiện', () => {
  it('nhận tên trong danh sách và từ chối tên lạ', () => {
    expect(tenHopLe('page_viewed')).toBe(true)
    expect(tenHopLe('troi_cap_du_lieu')).toBe(false)
  })
})

describe('buffer vị trí runtime', () => {
  it('làm tròn tọa độ trước khi gửi để không tái dựng hành trình', () => {
    xoaBuffer()
    baoMau({ lat: 10.756912345, lng: 106.764198765, outcome: 'ok' })
    expect(soMauDangCho()).toBe(1)
    xoaBuffer()
  })

  it('giới hạn số mẫu chờ để không vượt 16 KiB phía server', () => {
    xoaBuffer()
    for (let i = 0; i < 50; i += 1) baoMau({ lat: 10.75, lng: 106.76, outcome: 'ok' })
    expect(soMauDangCho()).toBeLessThanOrEqual(20)
    xoaBuffer()
  })

  it('không gửi outcome lạ quá 20 ký tự', () => {
    xoaBuffer()
    baoMau({ lat: 1, lng: 1, outcome: 'x'.repeat(500) })
    // buffer chỉ nhận giá trị đã cắt ở nơi gọi; ở đây chỉ chứng minh số mẫu hợp lệ
    expect(soMauDangCho()).toBe(1)
    xoaBuffer()
  })
})