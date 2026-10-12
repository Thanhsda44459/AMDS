import { expect, test } from '@playwright/test'

// TEST-006 — luồng cơ bản: mở app → chọn ngôn ngữ → bản đồ hiện POI.
// Đây là "happy path" ngắn nhất để phát hiện app hỏng khiếu ngay ở CI, nên
// dùng selector theo nhãn người dùng thấy thay vì class CSS (đổi style không
// được làm vỡ test).

test.describe('Khám phá', () => {
  test('mở app thì có bản đồ và danh sách quán', async ({ page }) => {
    await page.goto('/')

    await expect(page.getByRole('heading', { name: 'Linh Ứng Guide' })).toBeVisible()
    await expect(page.locator('.map-frame')).toBeVisible()
    // Seed 5 quán; danh sách phải đủ 5 để biết API và store đồng bộ.
    await expect(page.locator('.poi-btn')).toHaveCount(5)
  })

  test('chọn tiếng Anh thì nội dung POI đổi sang bản tiếng Anh', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.poi-btn')).toHaveCount(5)
    const dauTien = page.locator('.poi-btn').first()
    const tiengViet = await dauTien.innerText()

    await page.getByRole('button', { name: 'English' }).click()

    // Tên quán tiếng Anh khác hẳn tiếng Việt nên phải đổi thật, không phải chỉ
    // đổi nhãn nút. Chờ tới khi danh sách về lại trước rồi so nội dung.
    await expect(dauTien).not.toHaveText(tiengViet, { timeout: 15_000 })
  })

  test('bấm vào một quán thì hiện chi tiết', async ({ page }) => {
    await page.goto('/')
    await page.locator('.poi-btn').first().click()
    await expect(page.getByRole('region', { name: 'Chi tiết điểm tham quan' })).toBeVisible()
  })
})

// TEST-001 liên quan: hộp thoại consent phải xuất hiện và tôn trọng lựa chọn.
// Đặt ở đây vì nó là điều kiện tiên quyết cho mọi sự kiện analytics, và chỉ
// quan sát được qua UI thật.
test.describe('Consent', () => {
  test('mặc định hỏi consent, từ chối thì không gửi request analytics', async ({ page }) => {
    const goiAnalytics: string[] = []
    page.on('request', (r) => {
      if (r.url().includes('/analytics/collect')) goiAnalytics.push(r.url())
    })

    await page.goto('/')
    await expect(
      page.getByRole('dialog', { name: 'Xin phép chia sẻ dữ liệu ẩn danh' }),
    ).toBeVisible()

    await page.getByRole('button', { name: 'Không cho phép' }).click()
    await expect(page.getByRole('dialog')).toHaveCount(0)

    // Đợi qua nhịp heartbeat 20s là ràng buộc thật của ANA-001; ở đây chỉ cần
    // chắc là không có request nào ngay sau khi từ chối.
    await page.waitForTimeout(2000)
    expect(goiAnalytics).toHaveLength(0)
  })

  test('cho phép thì bật thu thập và nhớ lựa chọn qua lần tải sau', async ({ page }) => {
    await page.goto('/')
    // `exact: true` bắt buộc: "Cho phép" là chuỗi con của "Không cho phép",
    // nên không có nó thì selector khớp cả hai nút và Playwright báo
    // "strict mode violation".
    await page.getByRole('button', { name: 'Cho phép', exact: true }).click()
    await expect(page.getByText('đang bật')).toBeVisible()

    await page.reload()
    // Lựa chọn được nhớ: không hỏi lại, và vẫn hiện là đang bật.
    await expect(page.getByRole('dialog')).toHaveCount(0)
    await expect(page.getByText('đang bật')).toBeVisible()
  })
})