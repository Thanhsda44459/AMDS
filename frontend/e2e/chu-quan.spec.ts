import { expect, test } from '@playwright/test'

// TEST-008 — luồng chủ quán: đăng ký → duyệt → gửi quán → nhận thông báo.
//
// Đây là luồng dài nhất của ứng dụng nên nó đi qua cả hai cổng: tab Owner (khách)
// và tab Admin (vận hành). Nếu chỉ test từng đầu mối riêng lẻ thì hỏng "đứt
// giữa đường" — ví dụ owner gửi được quán nhưng admin không thấy đơn — sẽ lọt qua.

const CHU_QUAN = 'chuquan_e2e'
const MAT_KHAU = 'e2e123456'
const TEN_QUAN = 'Quán mới E2E'

test.describe('Luồng chủ quán', () => {
  test('đăng ký, được duyệt, gửi quán và nhận thông báo', async ({ page }) => {
    // --- 1. Khách đăng ký làm chủ quán ---
    await page.goto('/')
    await page.getByRole('button', { name: 'Chủ quán' }).click()
    await page.getByPlaceholder('Tên đăng nhập').fill(CHU_QUAN)
    await page.getByPlaceholder('Mật khẩu').fill(MAT_KHAU)
    await page.getByPlaceholder('CCCD').fill('123456789012')
    await page.getByRole('button', { name: 'Đăng ký chủ quán' }).click()

    // Đăng ký xong vẫn chưa đăng nhập, nên giao diện còn hiện form login và
    // KHÔNG hiện thông báo chờ duyệt (OwnerApp chỉ render thông báo khi đã
    // đăng nhập). Phải đăng nhập trước rồi mới kiểm được trạng thái.
    await page.getByPlaceholder('Tên đăng nhập').fill(CHU_QUAN)
    await page.getByPlaceholder('Mật khẩu').fill(MAT_KHAU)
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
    await expect(page.getByText('Tài khoản chờ duyệt, chưa gửi được quán.')).toBeVisible()

    // --- 2. Admin duyệt tài khoản ---
    await page.getByRole('button', { name: 'Admin' }).click()
    await page.getByPlaceholder('Tên đăng nhập').fill('e2e-admin')
    await page.getByPlaceholder('Mật khẩu').fill(MAT_KHAU)
    await page.getByRole('button', { name: 'Đăng nhập' }).click()

    await expect(page.getByRole('heading', { name: /Kiểm duyệt chủ quán/ })).toBeVisible()
    const dong = page.locator('tr', { hasText: CHU_QUAN })
    await expect(dong).toHaveCount(1)
    await dong.getByRole('button', { name: 'Duyệt', exact: true }).click()
    // Đơn biến mất khỏi hàng đợi sau khi duyệt.
    await expect(page.locator('tr', { hasText: CHU_QUAN })).toHaveCount(0)

    // --- 3. Chủ quán đăng nhập và gửi quán ---
    await page.getByRole('button', { name: 'Chủ quán' }).click()
    await page.getByPlaceholder('Tên đăng nhập').fill(CHU_QUAN)
    await page.getByPlaceholder('Mật khẩu').fill(MAT_KHAU)
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
    await page.getByPlaceholder('Tên quán').fill(TEN_QUAN)
    await page.getByPlaceholder('Mô tả').fill('Quán ngon, giá hợp lý.')
    await page.getByRole('button', { name: 'Gửi', exact: true }).click()

    // --- 4. Admin duyệt quán, chủ quán nhận thông báo ---
    await page.getByRole('button', { name: 'Admin' }).click()
    // Ở bước 3 chủ quán đã đăng nhập và ghi đè cookie phiên dùng chung, nên tab
    // Admin thấy phiên chủ quán và bị chặn (xem CONG_KHACH trong AdminApp) —
    // phải đăng nhập lại admin thì hàng đợi chờ duyệt mới hiện ra.
    await page.getByPlaceholder('Tên đăng nhập').fill('e2e-admin')
    await page.getByPlaceholder('Mật khẩu').fill(MAT_KHAU)
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
    await expect(page.getByRole('heading', { name: /Kiểm duyệt chủ quán/ })).toBeVisible()
    const dongQuan = page.locator('tr', { hasText: TEN_QUAN })
    await expect(dongQuan).toHaveCount(1, { timeout: 15_000 })
    await dongQuan.getByRole('button', { name: 'Duyệt quán' }).click()

    await page.getByRole('button', { name: 'Chủ quán' }).click()
    // Quay lại tab này là OwnerApp được mount lại từ đầu (App chỉ render nó
    // khi tab đang mở), nên phải đăng nhập lại thì danh sách thông báo mới
    // được tải — không có cơ chế khôi phục phiên trong component.
    await page.getByPlaceholder('Tên đăng nhập').fill(CHU_QUAN)
    await page.getByPlaceholder('Mật khẩu').fill(MAT_KHAU)
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
    await expect(page.getByText(/đã được duyệt/)).toBeVisible({ timeout: 15_000 })
  })

  test('chủ quán chưa được duyệt thì không gửi được quán', async ({ page }) => {
    // Ranh giới quan trọng: nút "Gửi" phải bị chặn ở server (403), không chỉ ẩn nút.
    const chuaDuyet = 'chuquan_chua_duyet'
    await page.goto('/')
    await page.getByRole('button', { name: 'Chủ quán' }).click()
    await page.getByPlaceholder('Tên đăng nhập').fill(chuaDuyet)
    await page.getByPlaceholder('Mật khẩu').fill(MAT_KHAU)
    await page.getByPlaceholder('CCCD').fill('987654321098')
    await page.getByRole('button', { name: 'Đăng ký chủ quán' }).click()

    await page.getByPlaceholder('Tên đăng nhập').fill(chuaDuyet)
    await page.getByPlaceholder('Mật khẩu').fill(MAT_KHAU)
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click()
    await expect(page.getByText('Tài khoản chờ duyệt, chưa gửi được quán.')).toBeVisible()
  })
})