import { execFileSync } from 'node:child_process'
import path from 'node:path'

// Nạp dữ liệu E2E trước mọi test. Chạy seed (xoá sạch rồi nạp) chứ không đụng
// script seed_poi của dev, để test luôn bắt đầu từ trạng thái đã biết.
//
// `__dirname` không tồn tại trong ES module (package.json đặt "type": "module"),
// nên phải lấy từ import.meta.dirname.
const backendDir = path.resolve(import.meta.dirname, '..', '..', 'backend')
const python =
  process.platform === 'win32' ? '.venv\\Scripts\\python.exe' : '.venv/bin/python'

export default function globalSetup(): void {
  execFileSync(python, ['scripts/seed_e2e.py'], {
    cwd: backendDir,
    env: { ...process.env, MONGODB_DB_NAME: 'amds_e2e' },
    stdio: 'inherit',
  })
}