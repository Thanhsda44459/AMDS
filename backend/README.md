# Backend API

FastAPI service của dự án. Chạy **native** trên máy (không Docker hoá) để hot-reload nhanh; MongoDB và Redis chạy bằng Docker Compose.

> Xem [`../README.md`](../README.md) để hiểu tổng quan. Tài liệu đặc tả nằm ở `docs/` (không commit vào git theo chủ ý).

---

## 1. Yêu cầu cài đặt

| Công cụ | Phiên bản | Bắt buộc | Ghi chú |
|---|---|---|---|
| Python | 3.12.x | Có | `pyproject.toml` đặt `target-version = "py312"` |
| pip | đi kèm Python | Có | dùng `python -m pip` cho chắc |
| Docker Desktop | 29.x hoặc mới hơn | Có | chỉ dùng để chạy MongoDB + Redis |

Kiểm tra trước khi bắt đầu:

```powershell
python --version
docker --version
docker compose version
```

Cài Docker Desktop tại <https://www.docker.com/products/docker-desktop/> (Windows cần bật WSL 2).

---

## 2. Cài đặt lần đầu

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Trên **macOS / Linux**:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Nếu PowerShell báo lỗi *"running scripts is disabled"*, chạy lệnh này một lần rồi thử activate lại:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Thư mục `.venv` có được commit không?

Không. `.gitignore` ở thư mục gốc đã loại `.venv/`, `__pycache__/` và `*.pyc`. Mỗi người tự tạo `.venv` riêng trên máy, không cần copy.

### Kiểm tra cài đặt thành công

```powershell
python -c "import fastapi, motor, pymongo; print('OK')"
ruff --version
```

---

## 3. Cấu hình biến môi trường

```powershell
Copy-Item .env.example .env          # PowerShell
# cp .env.example .env               # macOS / Linux
```

Nội dung `.env.example`:

| Biến | Bắt buộc | Ví dụ | Ý nghĩa |
|---|---|---|---|
| `MONGODB_URI` | Có | `mongodb://localhost:27017` | chuỗi kết nối MongoDB |
| `MONGODB_DB_NAME` | Có | `amds` | tên database sẽ dùng |
| `REDIS_URL` | Chưa dùng | `redis://localhost:6379` | để sẵn cho session/cache |
| `JWT_SECRET` | Chưa dùng | *(để trống)* | sẽ dùng ở task auth |

### ⚠️ Giới hạn quan trọng ở Phase 0

**`.env` hiện chưa được nạp vào ứng dụng.** Code đọc biến môi trường bằng `os.getenv()` với giá trị mặc định hardcode, và chưa có lệnh `load_dotenv()` nào được gọi. Hệ quả:

- Sửa `.env` **không có tác dụng** lúc này.
- `MONGODB_URI` mặc định `mongodb://localhost:27017` — trùng với Docker Compose nên vẫn chạy được.
- `MONGODB_DB_NAME` mặc định **`AMSD`** (khác với giá trị `quan4_culinary` trong `.env.example`). Xem [Mục 9](#9-giới-hạn-và-nợ-kỹ-thuật).
- `JWT_SECRET` và `REDIS_URL` chưa có code đọc tới.

Việc gom cấu hình vào `backend/app/config.py` (dùng `pydantic-settings`) là task kế tiếp trong backlog. Sau khi task đó hoàn thành, mục này sẽ được cập nhật lại.

### Không bao giờ commit `.env`

`.env` chứa giá trị thật. Chỉ `.env.example` được commit. Nếu lỡ commit nhầm:

```powershell
git rm --cached .env
```

rồi thêm `.env` vào `.gitignore` (xem [Mục 9](#9-giới-hạn-và-nợ-kỹ-thuật)).

---

## 4. Chạy MongoDB và Redis bằng Docker Compose

Compose nằm ở **thư mục gốc**, không phải trong `backend/`:

```powershell
cd ..                 # về thư mục gốc
docker compose up -d --wait
docker compose ps
```

Kết quả mong đợi — cả hai service đều `running` (hoặc `healthy`):

```
NAME              IMAGE                STATUS
quan4-mongodb     mongo:7.0            running
quan4-redis       redis:7.2-alpine     running
```

Cổng được mở ra máy host:

| Service | Cổng host | Cổng trong container |
|---|---|---|
| MongoDB | `27017` | `27017` |
| Redis | `6379` | `6379` |

Dữ liệu được lưu bằng named volume nên **không mất khi `docker compose down`**. Xoá vĩnh viễn (kèm dữ liệu) thì dùng `docker compose down -v`.

### Lệnh Docker thường dùng

```powershell
docker compose up -d --wait     # khởi động, chờ healthcheck pass
docker compose ps               # xem trạng thái
docker compose logs -f mongodb  # theo dõi log MongoDB
docker compose stop             # dừng, giữ container
docker compose down             # xoá container, giữ volume
docker compose down -v          # xoá container VÀ volume (mất dữ liệu)
```

### Kết nối thử trực tiếp

```powershell
docker compose exec mongodb mongosh --quiet --eval "db.runCommand({ ping: 1 })"
docker compose exec redis redis-cli ping
```

Cả hai lệnh trả về `1` và `PONG` là được.

---

## 5. Chạy backend

Giữ terminal `docker compose` đã chạy, mở terminal mới:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Output mong đợi:

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
[startup] MongoDB connected ✅
INFO:     Uvicorn running on http://127.0.0.1:8000
```

| Địa chỉ | Nội dung |
|---|---|
| <http://127.0.0.1:8000> | endpoint gốc, trả tên service |
| <http://127.0.0.1:8000/health> | health-check |
| <http://127.0.0.1:8000/docs> | Swagger UI — giao diện test API |

Dừng server bằng `Ctrl+C`.

### Về chế độ fail-soft

`app/main.py` cố tình **không crash** nếu MongoDB chưa sẵn sàng. Nếu kết nối thất bại, backend vẫn khởi động và in cảnh báo `[startup] MongoDB chưa sẵn sàng`. Điều này giúp bạn sửa code frontend khi chưa bật Docker. Nhưng `/health` vẫn trả **503** cho tới khi Mongo lên — dùng endpoint đó làm tín hiệu sẵn sàng.

---

## 6. Kiểm tra hoạt động

Health-check trả `200` khi MongoDB kết nối được, `503` khi không.

```powershell
curl.exe -i http://127.0.0.1:8000/health
```

> Trên Windows dùng `curl.exe` (không phải `curl`) — trong PowerShell, `curl` là alias của `Invoke-WebRequest` và sẽ không hiện status code. Trên macOS/Linux dùng `curl` bình thường.

Kết quả đúng (HTTP/1.1 200 OK):

```json
{
  "status": "ok",
  "mongo": "connected",
  "timestamp": "2026-09-27T08:00:00+00:00"
}
```

MongoDB chưa chạy (HTTP/1.1 503 Service Unavailable):

```json
{
  "status": "degraded",
  "mongo": "disconnected",
  "timestamp": "2026-09-27T08:00:00+00:00",
  "mongo_error": "ServerSelectionTimeoutError: ..."
}
```

Cách đọc nhanh trong PowerShell:

```powershell
(Invoke-WebRequest http://127.0.0.1:8000/health).StatusCode   # 200 hoặc 503
Invoke-RestMethod http://127.0.0.1:8000/                       # tên service
```

---

## 7. Cấu trúc thư mục

```text
backend/
├── .env.example              # mẫu biến môi trường — được commit
├── .env                      # biến thật — KHÔNG commit (tạo tay)
├── .venv/                    # môi trường ảo Python — KHÔNG commit
├── pyproject.toml            # cấu hình ruff (lint + format)
├── requirements.txt          # dependency đã ghim phiên bản
└── app/
    ├── main.py               # tạo FastAPI app, lifespan, gắn router
    ├── database.py           # kết nối Motor/MongoDB + close
    └── routers/
        ├── __init__.py
        └── health.py         # GET /health
```

`app/` là *namespace package* — cố ý không có `__init__.py` ở đó. Nếu thêm file Python mới trong `app/`, không cần tạo `__init__.py` trừ khi bạn muốn dùng `__init__.py` để export code.

### Endpoint hiện có

| Method | Path | Mô tả | Response |
|---|---|---|---|
| `GET` | `/` | endpoint gốc | `200` — `{"status": "ok", "service": ...}` |
| `GET` | `/health` | ping backend + MongoDB | `200` nếu Mongo kết nối, `503` nếu không |

---

## 8. Lint và format

Dùng `ruff` (đã nằm trong `requirements.txt`):

```powershell
cd backend
.\.venv\Scripts\Activate.ps1

ruff check .            # phát hiện lỗi: import thừa, biến chưa dùng, style
ruff check --fix .      # tự sửa phần lớn lỗi
ruff format .           # áp dụng format chuẩn (giống black)
ruff format --check .   # chỉ kiểm tra, không ghi file
```

Cấu hình nằm trong `pyproject.toml`:

- `line-length = 100`
- Rule bật: `E` (pycodestyle), `F` (pyflakes), `I` (isort), `B` (bugbear), `UP` (pyupgrade)
- Bỏ qua: `E501` (để formatter lo)

**Chạy `ruff check .` và `ruff format .` trước khi commit.** Import được sắp xếp tự động theo `I` (isort).

---

## 9. Giới hạn và nợ kỹ thuật

Những thứ **chưa** có ở Phase 0, để bạn không tìm nhầm:

| Vấn đề | Chi tiết | Nên sửa ở |
|---|---|---|
| `.env` chưa được nạp | xem [Mục 3](#3-cấu-hình-biến-môi-trường) | task `config.py` |
| Tên DB không nhất quán | `database.py` hardcode `AMSD`, còn `.env.example` ghi `quan4_culinary` | task `config.py` |
| `.env` chưa nằm trong `.gitignore` | `.gitignore` chỉ có `.env.local` và `.env.docker`; nếu bạn tạo `.env` thật thì file đó **sẽ bị commit** | nên sửa ngay — thêm dòng `.env` |
| Chưa có test | không có thư mục `tests/`, chưa cài `pytest` | task test đầu tiên |
| Chưa có CORS | không có middleware CORS; frontend gọi `localhost:5173` sẽ bị chặn trình duyệt | khi frontend bắt đầu gọi API |
| Chưa dùng Redis | service chạy nhưng code chưa import `redis` | khi làm session/cache |
| `ruff` nằm trong `requirements.txt` | công cụ dev lẫn vào dependency runtime | tách `requirements-dev.txt` |
| `health.py` trả chi tiết lỗi | trường `mongo_error` có thể lộ host/port; xem lại khi lên production | task hardening |

---

## 10. Xử lý sự cố

<details>
<summary><b>PowerShell: "running scripts is disabled"</b></summary>

Chính sách thực thi script chặn file `.ps1`. Chạy:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Rồi activate lại. Lệnh này chỉ đổi thiết lập cho user hiện tại, không đụng hệ thống.
</details>

<details>
<summary><b><code>uvicorn: command not found</b></summary>

Chưa activate venv, hoặc cài thiếu dependency. Kiểm tra:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Thay vì gọi `uvicorn` trực tiếp, có thể dùng `python -m uvicorn app.main:app --reload` — cách này không phụ thuộc PATH.
</details>

<details>
<summary><b><code>ModuleNotFoundError: No module named 'app'</b></summary>

Chạy uvicorn sai thư mục. Phải đứng trong `backend/`, không phải thư mục gốc:

```powershell
cd backend
uvicorn app.main:app --reload
```
</details>

<details>
<summary><b><code>/health</code> trả 503, MongoDB chưa kết nối</b></summary>

Kiểm tra container có chạy không:

```powershell
docker compose ps
docker compose logs --tail 30 mongodb
```

Nếu container không chạy: `docker compose up -d --wait`.
Nếu cổng 27017 bị chiếm bởi MongoDB cài trực tiếp trên máy: dừng dịch vụ đó, hoặc sửa cổng trong `docker-compose.yml` và `MONGODB_URI` cho khớp.
</details>

<details>
<summary><b>Cổng 8000 hoặc 5173 đã bị chiếm</b></summary>

Đổi cổng khi chạy:

```powershell
uvicorn app.main:app --reload --port 8001
```
</details>

<details>
<summary><b>Cài lại từ đầu môi trường ảo</b></summary>

```powershell
cd backend
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```
</details>

---

## 11. Quy trình làm việc hằng ngày

Mỗi lần bắt đầu làm việc, cần đúng 2 terminal:

```powershell
# Terminal 1 — hạ tầng
cd <thư mục gốc repo>
docker compose up -d --wait

# Terminal 2 — API
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Trước khi commit:

```powershell
ruff check .
ruff format .
git status
git add backend/ && git commit
```
