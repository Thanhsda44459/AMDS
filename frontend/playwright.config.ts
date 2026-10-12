import { defineConfig, devices } from '@playwright/test'

// TEST-006/007/008/009.
//
// Vì sao có `channel`: máy dev đã có Chrome nên test chạy được ngay mà không
// cần tải browser. CI để trống channel và dùng chromium đi kèm Playwright.
// Đặt PW_CHANNEL=chrome để ép dùng Chrome đã cài.
const channel = process.env.PW_CHANNEL

// Đường dẫn python trong venv khác nhau giữa Windows và Linux.
const pythonBackend =
  process.platform === 'win32' ? '.venv\\Scripts\\python.exe' : '.venv/bin/python'

export default defineConfig({
  testDir: './e2e',
  // E2E đụng nhau DB và cổng nên chạy tuần tự; song song chỉ làm khó chẩn đoán.
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: process.env.CI ? [['github'], ['list']] : [['list']],
  use: {
    // PHẢI dùng 127.0.0.1 chứ không phải localhost. Cookie phiên được đặt
    // `SameSite=Lax`, nên trình duyệt coi `localhost:5173` và `127.0.0.1:8000`
    // là hai site khác nhau và KHÔNG gửi cookie khi fetch chéo → mọi endpoint
    // cần đăng nhập trả 401. Cổng không ảnh hưởng "site", nhưng tên host thì có.
    // Đây cũng là ràng buộc thật của cookie phiên ở môi trường thật (xem ADR-017).
    baseURL: 'http://127.0.0.1:5173',
    channel,
    locale: 'vi-VN',
    timezoneId: 'Asia/Ho_Chi_Minh',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  globalSetup: './e2e/global-setup.ts',
  webServer: [
    {
      // DB riêng cho E2E để không đụng dữ liệu dev (app, admin).
      command: `${pythonBackend} -m uvicorn app.main:app --port 8000`,
      cwd: '../backend',
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        MONGODB_DB_NAME: 'amds_e2e',
        // Không có key thì `ma_hoa_pii` trả None và POST /owner/register trả
        // 500 "Chưa cấu hình mã hóa PII" → luồng chủ quán không test được.
        // Đây là key tạm cho test, không phải bí mật thật.
        PII_KEY: process.env.E2E_PII_KEY ?? 'tUjud1BMSHU5ySrA-KdMGkbRLKn503M3lS6JlFQlEmk=',
      },
    },
    {
      // Ép Vite nghe 127.0.0.1 (mặc định nó chỉ nghe ::1) để trang và API cùng
      // một site → cookie SameSite=Lax mới được gửi.
      command: 'npm run dev -- --port 5173 --strictPort --host 127.0.0.1',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
})