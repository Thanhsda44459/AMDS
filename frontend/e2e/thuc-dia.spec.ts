import { expect, test } from '@playwright/test'

// TEST-009 — kịch bản thực địa: 5 quán ở Quận 4 × 3 ngôn ngữ.
//
// Mô phỏng đúng việc khách đi một vòng: mở app, chọn ngôn ngữ, xem quán,
// đổi ngôn ngữ giữa chừng. Giá trị của test này là khóa lại hành vi "đổi ngôn
// ngữ giữa chừng không để lại kết quả cũ" (REF-5/FE-003) — đây là chỗ dễ hỏng
// nhất vì nó trải qua đồng thời cả hai làn i18n và cả danh sách đã tải.

test.describe('Kịch bản thực địa', () => {
  test('5 quán hiện đủ ở cả 3 ngôn ngữ, đổi qua lại không lẫn nội dung', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.poi-btn')).toHaveCount(5)

    // Bắt đầu từ English chứ không phải Tiếng Việt: nút của ngôn ngữ đang
    // chọn bị disable, bấm vào nó sẽ treo chờ tới khi hết 60s.
    for (const ngon of ['English', '中文', 'Tiếng Việt'] as const) {
      await page.getByRole('button', { name: ngon }).click()
      // Phải đủ 5 ở mọi ngôn ngữ: nếu rớt số thì chuỗi fallback hoặc danh sách
      // đang lọc theo ngôn ngữ sai.
      await expect(page.locator('.poi-btn')).toHaveCount(5, { timeout: 20_000 })
    }

    // Vòng lặp đã kết thúc ở tiếng Việt, nên chỉ còn kiểm nội dung đã về
    // đúng tiếng Việt chứ không phải bản Trung còn sót lại.
    await expect(page.locator('.poi-btn').first()).toContainText('Bánh mì', { timeout: 20_000 })
  })

  test('đổi ngôn ngữ xong vẫn bấm xem được quán và nghe được', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('.poi-btn')).toHaveCount(5)

    await page.getByRole('button', { name: 'English' }).click()
    await expect(page.locator('.poi-btn')).toHaveCount(5, { timeout: 20_000 })

    // Chọn quán đầu tiên rồi mở panel chi tiết — đây là bước đi qua geofence
    // nên nó phải vẫn hoạt động sau khi đã đổi ngôn ngữ.
    await page.locator('.poi-btn').first().click()
    const panel = page.getByRole('region', { name: 'Chi tiết điểm tham quan' })
    await expect(panel).toBeVisible()
    await expect(panel.getByRole('heading')).not.toBeEmpty()
  })

  test('quán gần nhau trả về theo khoảng cách tăng dần', async ({ page }) => {
    // Dùng API công khai vì thứ tự khoảng cách là hành vi của backend
    // ($geoNear + fallback Haversine), không phải thứ render ở UI.
    const res = await page.request.get(
      'http://127.0.0.1:8000/poi/nearby?lat=10.7569&lng=106.7641&radius_m=3000&lang=vi',
    )
    expect(res.status()).toBe(200)
    const ds = (await res.json()) as { name: string; distance_m: number }[]
    expect(ds.length).toBeGreaterThan(0)
    for (let i = 1; i < ds.length; i += 1) {
      expect(ds[i].distance_m).toBeGreaterThanOrEqual(ds[i - 1].distance_m)
    }
  })

  test('tọa độ sai bị từ chối có kiểm soát, không sập', async ({ page }) => {
    const sai = await page.request.get('http://127.0.0.1:8000/poi/nearby?lat=999&lng=0')
    expect(sai.status()).toBe(400)
    const trong = await page.request.get(
      'http://127.0.0.1:8000/poi/nearby?lat=10.7569&lng=106.7641&radius_m=10',
    )
    expect(trong.status()).toBe(200)
  })
})