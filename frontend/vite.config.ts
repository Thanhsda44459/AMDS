import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'sw.ts',
      manifest: {
        name: 'Du lịch ẩm thực Quận 4',
        short_name: 'Quan4',
        start_url: '/',
        display: 'standalone',
        background_color: '#ffffff',
        theme_color: '#2563eb',
        icons: [],
      },
      injectManifest: {
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
      },
    }),
  ],
  // Test cần DOM thật cho localStorage/sessionStorage (consentStore đọc lúc
  // import) và Blob/sendBeacon của lane vị trí runtime.
  //
  // Phải ghim include về src/: mặc định vitest quét cả e2e/*.spec.ts của
  // Playwright và sập với "did not expect test.describe() to be called here" —
  // hai runner dùng cùng đuôi .spec.ts nên không tách nhau được bằng tên.
  test: {
    environment: 'jsdom',
    include: ['src/**/*.test.{ts,tsx}'],
  },
})
