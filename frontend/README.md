# Frontend Web App

Giao diện React + TypeScript + Vite. Chạy **native** trên máy (không Docker hoá) để hot-reload nhanh.

> Xem [`../README.md`](../README.md) để hiểu tổng quan. Tài liệu đặc tả nằm ở `docs/` (không commit vào git theo chủ ý).

---

## 1. Yêu cầu cài đặt

| Công cụ | Phiên bản | Bắt buộc | Ghi chú |
|---|---|---|---|
| Node.js | `^20.19.0` hoặc `>=22.12.0` | Có | ràng buộc do Vite 8, nâng cao hơn sẽ bị cảnh báo |
| npm | 10 trở lên | Có | đi kèm Node.js |

> **Không dùng Node 18 trở xuống.** Vite 8 sẽ báo lỗi ngay khi chạy. Nếu máy bạn còn Node 18, hãy cài [nvm-windows](https://github.com/coreybutler/nvm-windows) rồi `nvm install 22 && nvm use 22`.

Kiểm tra trước khi bắt đầu:

```powershell
node --version
npm --version
```

Cài Node.js tại <https://nodejs.org/> (bản LTS). Nếu `node` không được nhận, khởi động lại terminal sau khi cài.

---

## 2. Cài đặt lần đầu

```powershell
cd frontend
npm install
```

Lệnh này đọc `package.json` và tạo thư mục `node_modules/`. Mất khoảng 1–3 phút tuỳ tốc độ mạng.

### `node_modules` có được commit không?

Không. `frontend/.gitignore` đã loại `node_modules`, `dist`, `dist-ssr` và các file log. Mỗi người tự `npm install` trên máy.

Dùng `npm ci` thay vì `npm install` khi bạn chỉ muốn cài đúng phiên bản đã ghim trong `package-lock.json` — dùng trong CI hoặc sau khi người khác vừa push lockfile mới.

### Kiểm tra cài đặt thành công

```powershell
npm ls --depth=0
```

---

## 3. Chạy ở chế độ phát triển

```powershell
cd frontend
npm run dev
```

Mở trình duyệt tại <http://localhost:5173>.

Output mong đợi:

```
  VITE v8.x.x  ready in 300 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

| Địa chỉ | Nội dung |
|---|---|
| <http://localhost:5173> | trang đăng nhập dev |

Dừng server bằng `Ctrl+C`.

Sửa bất kỳ file nào trong `src/` và trình duyệt tự cập nhật — không cần reload tay.

---

## 4. Các lệnh npm

| Lệnh | Việc nó làm | Khi nào dùng |
|---|---|---|
| `npm run dev` | chạy dev server + hot reload | hằng ngày |
| `npm run build` | kiểm tra kiểu rồi build ra `dist/` | trước khi commit hoặc deploy |
| `npm run preview` | phục vụ bản build trong `dist/` ở cổng 4173 | kiểm tra bản build |
| `npm run lint` | chạy ESLint trên toàn bộ project | trước khi commit |

### Kiểm tra trước khi commit

```powershell
npm run lint
npm run build
```

`npm run build` chạy `tsc -b` trước — nghĩa là **lỗi TypeScript sẽ chặn build**. Không bỏ qua lệnh này.

### Deploy

`npm run build` tạo ra `dist/` — thư mục tĩnh, có thể đưa lên Azure Static Web Apps hoặc bất kỳ host tĩnh nào. `dist/` không được commit.

---

## 5. Cấu trúc thư mục

```text
frontend/
├── .gitignore               # loại node_modules, dist, file log
├── eslint.config.js         # ESLint flat config
├── index.html               # entrypoint HTML, khai báo <title>
├── package.json             # scripts + dependency
├── package-lock.json        # ghim phiên bản chính xác — ĐƯỢC commit
├── tsconfig.json            # file gốc, tham chiếu 2 file con
├── tsconfig.app.json        # cấu hình TS cho mã nguồn ứng dụng
├── tsconfig.node.json       # cấu hình TS cho mã nguồn build tool
├── vite.config.ts           # cấu hình Vite
└── src/
    ├── main.tsx             # điểm vào: mount React vào #root
    ├── App.tsx              # component gốc
    ├── App.css              # style của App
    └── index.css            # style toàn cục
```

`package-lock.json` **phải** commit — đó là thứ bảo đảm mọi người cài cùng phiên bản. Xoá nó sẽ khiến mỗi máy ra một phiên bản khác nhau.

---

## 6. Công nghệ

| Thành phần | Phiên bản | Vai trò |
|---|---|---|
| React | 19.x | thư viện giao diện |
| TypeScript | ~6.0 | kiểu tĩnh |
| Vite | ^8.3 | dev server + bundler |
| `@vitejs/plugin-react` | ^6.1 | hỗ trợ Fast Refresh |
| ESLint | ^10.x | lint |
| `typescript-eslint` | ^8.x | lint cho TypeScript |
| `eslint-plugin-react-hooks` | ^7.x | luật cho React Hooks |
| `eslint-plugin-react-refresh` | ^0.5 | luật cho Fast Refresh |

Chưa cài: router, state management, CSS framework, thư viện bản đồ, HTTP client. Xem [Mục 8](#8-giới-hạn-và-nợ-kỹ-thuật).

---

## 7. Kết nối với backend

### Trạng thái hiện tại

Frontend **chưa** gọi backend. Ở Phase 0, `src/App.tsx` chỉ render một tiêu đề tĩnh.

Khi bắt đầu tích hợp, cần làm **cả hai** việc sau — nếu thiếu một, trình duyệt sẽ chặn request:

1. **Bật CORS phía backend** — `backend/app/main.py` hiện chưa có middleware CORS.
2. **Thêm proxy phía frontend** trong `vite.config.ts` (khuyến nghị, giúp tránh CORS):

```ts
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
```

Rồi gọi `/api/...` trong code thay vì ghi cứng `http://localhost:8000`.

### Biến môi trường

Hiện **chưa** có biến `VITE_*` nào. Khi cần, tạo file `frontend/.env.local` — file này đã được `.gitignore` loại (dòng `*.local`), nên secret không bị commit.

Quy tắc của Vite: chỉ biến có tiền tố `VITE_` mới được đọc trong mã nguồn, và **giá trị đó được nhúng vào bundle gửi tới trình duyệt** — tức là ai cũng thấy. Không bao giờ đặt secret thật vào biến `VITE_`.

---

## 8. Giới hạn và nợ kỹ thuật

| Vấn đề | Chi tiết | Nên sửa ở |
|---|---|---|
| Chưa có proxy sang backend | xem [Mục 7](#7-kết-nối-với-backend) | task tích hợp API đầu tiên |
| Chưa có test | không có test runner, chưa cài Vitest | task test đầu tiên |
| ESLint chưa bật type-aware rules | đang dùng `tseslint.configs.recommended`; bản nâng cao cần `parserOptions.project` | khi codebase lớn dần |
| Không có prettier | format hiện do ESLint lo phần logic, style chưa thống nhất | khi nhiều người cùng code |
| Không có path alias | đang import tương đối (`../components/...`); dự án lớn sẽ cần alias `@/` | khi cấu trúc thư mục sâu hơn |
| Không có CI | `npm run lint` và `npm run build` phải chạy tay | khi có GitHub Actions |
| Không có router | mới chỉ 1 trang, chưa có định tuyến | khi bắt đầu làm nhiều màn hình |

---

## 9. Xử lý sự cố

<details>
<summary><b><code>npm</code> hoặc <code>node</code> không được nhận</b></summary>

Cài Node.js, mở lại terminal, kiểm tra `node --version`. Kiểm tra Node có nằm trong PATH không:

```powershell
$env:Path -split ';' | Select-String 'nodejs'
```
</details>

<details>
<summary><b>Vite báo lỗi phiên bản Node</b></summary>

Vite 8 cần `^20.19.0 || >=22.12.0`. Kiểm tra:

```powershell
node --version
```

Dùng [nvm-windows](https://github.com/coreybutler/nvm-windows) để cài và chuyển phiên bản:

```powershell
nvm install 22
nvm use 22
```
</details>

<details>
<summary><b>Cổng 5173 đã bị chiếm</b></summary>

Vite tự chọn cổng trống kế tiếp và in ra cổng mới. Ép cổng cụ thể:

```powershell
npm run dev -- --port 5174
```
</details>

<details>
<summary><b><code>npm run build</code> lỗi TypeScript</b></summary>

Báo lỗi kiểu dữ liệu sẽ chặn build. Xem file và dòng lỗi trong output. Kiểm tra nhanh mà không build:

```powershell
npx tsc -b --noEmit
```
</details>

<details>
<summary><b>Dependency lỗi sau khi kéo code mới</b></summary>

Thường là do `package-lock.json` đã cập nhật. Cài lại từ đầu:

```powershell
Remove-Item -Recurse -Force node_modules
npm ci
```

Nếu vẫn lỗi, xoá cache rồi thử lại:

```powershell
npm cache clean --force
npm install
```
</details>

<details>
<summary><b>Sửa <code>eslint.config.js</code> mà ESLint không nhận thay đổi</b></summary>

Kiểm tra đang lint đúng thư mục không:

```powershell
npx eslint src --debug
```
</details>

---

## 10. Quy trình làm việc hằng ngày

```powershell
# Terminal 1 — hạ tầng (chỉ khi backend cần MongoDB/Redis)
cd <thư mục gốc repo>
docker compose up -d --wait

# Terminal 2 — API
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload

# Terminal 3 — web app
cd frontend
npm run dev
```

Trước khi commit:

```powershell
npm run lint
npm run build
git status
git add frontend/ && git commit
```
