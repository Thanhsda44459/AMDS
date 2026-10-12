import { expect, test, type Page } from '@playwright/test'

// TEST-007 — chế độ offline: mất backend thì app vẫn phải dùng được.
//
// CÁCH LÀM ĐÚNG Ở ĐÂY: chặn riêng các request tới API (127.0.0.1:8000), KHÔNG
// dùng `context.setOffline(true)`. Lý do: `setOffline` cắt **mọi** kết nối kể
// cả dev server đang phục vụ app, nên `page.reload()` chết ngay với
// ERR_INTERNET_DISCONNECTED và test trở nên vô nghĩa.
//
// Đây là giới hạn thẳng thắn của cách chạy bằng dev server: "mở app lúc mạng
// đã chết" mới cần service worker, mà SW chỉ đăng ký ở bản build production.
// Test này khóa đúng tầng logic nó nhắm tới — fallback IndexedDB — và không
// trộn thêm chuyện SW đã đúng hay chưa.

/** Chặn API backend, giữ nguyên dev server phục vụ app. */
async function catAPI(page: Page): Promise<void> {
  await page.route('**/127.0.0.1:8000/**', (route) => route.abort('internetdisconnected'))
}

test.describe('Offline', () => {
  test('mất backend sau khi đã xem thì vẫn thấy danh sách quán', async ({ page }) => {
    // 1. Còn mạng: nạp dữ liệu vào IndexedDB.
    await page.goto('/')
    await expect(page.locator('.poi-btn')).toHaveCount(5)

    // 2. Backend biến mất.
    await catAPI(page)

    // 3. App phải tự lấy dữ liệu từ IDB thay vì trắng màn hình.
    await page.reload()
    await expect(page.locator('.poi-btn')).toHaveCount(5, { timeout: 20_000 })
  })

  test('mất backend thì đổi ngôn ngữ vẫn ra danh sách nhờ chuỗi fallback', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.poi-btn')).toHaveCount(5)

    await catAPI(page)
    await page.reload()
    await expect(page.locator('.poi-btn')).toHaveCount(5, { timeout: 20_000 })

    // Ngôn ngữ khác mà IDB chưa có bản dịch thì phải rơi về chuỗi
    // chọn → en → vi, vẫn không rỗng.
    await page.getByRole('button', { name: 'English' }).click()
    await expect(page.locator('.poi-btn')).toHaveCount(5, { timeout: 20_000 })
  })

  test('mất backend không được báo sai lỗi "bật backend"', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.poi-btn')).toHaveCount(5)

    await catAPI(page)
    await page.reload()
    await expect(page.locator('.poi-btn')).toHaveCount(5, { timeout: 20_000 })
    // Fetch fail nhưng fallback IDB thành công thì không được hiện lỗi.
    await expect(page.locator('.notice--error')).toHaveCount(0)
  })

  test('bật lại backend thì đồng bộ được dữ liệu mới', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.poi-btn')).toHaveCount(5)

    await catAPI(page)
    await page.reload()
    await expect(page.locator('.poi-btn')).toHaveCount(5, { timeout: 20_000 })

    // Bỏ chặn rồi đổi ngôn ngữ: phải gọi được API và cập nhật.
    await page.unroute('**/127.0.0.1:8000/**')
    await page.getByRole('button', { name: 'English' }).click()
    await expect(page.locator('.poi-btn')).toHaveCount(5, { timeout: 20_000 })
  })
})