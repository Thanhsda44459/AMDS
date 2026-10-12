import { beforeEach, describe, expect, it, vi } from 'vitest'
import { batDauAnalytics, flush, ghiSuKien, xinDongY } from './service'
import { daDongY, damBaoAnonymousId, useConsentStore } from '../stores/consentStore'

// Không mock module nào: muốn chứng minh "chưa đồng ý thì không gọi request"
// thì phải để chính cái cổng đó quyết định, không làm thay nó.
// Import tĩnh cả hai module để chúng dùng CHUNG một instance store —
// resetModules rồi import lại sẽ tạo store khác và test sẽ kiểm nhầm store rỗng.

function laiFetch() {
  const goi: string[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) => {
      goi.push(String(url))
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () =>
          Promise.resolve({ status: 'granted', receipt: 'r', tracked_online_users: 1, accepted: 1 }),
      })
    }),
  )
  return goi
}

function resetConsent() {
  localStorage.clear()
  sessionStorage.clear()
  useConsentStore.setState({ trangThai: 'chua-chon', receipt: null, trackedOnlineUsers: null })
}

describe('cổng consent', () => {
  beforeEach(resetConsent)

  it('chưa chọn thì chưa đồng ý', () => {
    expect(useConsentStore.getState().trangThai).toBe('chua-chon')
    expect(daDongY()).toBe(false)
  })

  it('đồng ý rồi mới coi là granted và nhớ lựa chọn', () => {
    useConsentStore.getState().datTrangThai('granted')
    expect(daDongY()).toBe(true)
    expect(localStorage.getItem('quan4-consent')).toBe('granted')
  })

  it('từ chối thì không phải granted', () => {
    useConsentStore.getState().datTrangThai('revoked')
    expect(daDongY()).toBe(false)
  })

  it('anonymous_id ổn định giữa các lần gọi', () => {
    const a = damBaoAnonymousId()
    expect(a).toBe(damBaoAnonymousId())
    expect(a.startsWith('anon-')).toBe(true)
    expect(a.length).toBeGreaterThanOrEqual(16)
  })

  it('anonymous_id và session_id là hai định danh khác nhau', () => {
    const anon = damBaoAnonymousId()
    expect(sessionStorage.getItem('quan4-session-id') ?? '').not.toBe(anon)
  })
})

describe('không có consent thì không gửi request analytics nào', () => {
  beforeEach(resetConsent)

  it('ghiSuKien bị chặn ngay ở cổng, không gọi fetch', async () => {
    const goi = laiFetch()
    await ghiSuKien('page_viewed', { poi_id: 'x' })
    batDauAnalytics()
    await flush(true)
    expect(goi.filter((u) => u.includes('/analytics/'))).toHaveLength(0)
  })

  it('batDauAnalytics không hẹn giờ gì khi chưa đồng ý', () => {
    const hen = vi.spyOn(window, 'setInterval')
    batDauAnalytics()
    expect(hen).not.toHaveBeenCalled()
    hen.mockRestore()
  })

  it('đã đồng ý thì mới gọi /analytics/collect', async () => {
    const goi = laiFetch()
    useConsentStore.setState({ trangThai: 'granted', receipt: 'receipt-hop-le' })
    await flush(true)
    expect(goi.some((u) => u.includes('/analytics/collect'))).toBe(true)
  })

  it('thiếu receipt thì không gửi, dù đã đồng ý', async () => {
    const goi = laiFetch()
    useConsentStore.setState({ trangThai: 'granted', receipt: null })
    await flush(true)
    expect(goi).toHaveLength(0)
  })
})

describe('xinDongY phải bật được trạng thái, không chỉ lưu receipt', () => {
  beforeEach(resetConsent)

  it('gọi API thành công thì trạng thái thành granted', async () => {
    laiFetch()
    const ok = await xinDongY()
    expect(ok).toBe(true)
    expect(useConsentStore.getState().trangThai).toBe('granted')
    expect(useConsentStore.getState().receipt).toBe('r')
    expect(localStorage.getItem('quan4-consent')).toBe('granted')
  })

  it('API lỗi thì không được bật, và không ghi consent vào localStorage', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })),
    )
    const ok = await xinDongY()
    expect(ok).toBe(false)
    expect(useConsentStore.getState().trangThai).toBe('chua-chon')
    expect(localStorage.getItem('quan4-consent')).toBeNull()
  })

  it('sau khi bật thì batDauAnalytics mới hẹn được nhịp gửi', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })),
    )
    // Chưa đồng ý: không hẹn gì.
    let hen = vi.spyOn(window, 'setInterval')
    batDauAnalytics()
    expect(hen).not.toHaveBeenCalled()
    hen.mockRestore()

    laiFetch()
    await xinDongY()

    hen = vi.spyOn(window, 'setInterval')
    batDauAnalytics()
    // session_started + page_viewed, và hai nhịp 15s/20s.
    expect(hen).toHaveBeenCalled()
    hen.mockRestore()
  })
})