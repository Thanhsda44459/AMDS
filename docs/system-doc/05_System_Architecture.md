# 05 — System Architecture (Kiến trúc hệ thống)

> Sơ đồ được thay bằng mô tả lời theo từng tầng và từng luồng dữ liệu.

## 1. Tổng quan

Hệ thống là **modular monolith** ở phía backend và **PWA offline-first** ở phía frontend.

Hình dung theo chiều từ người dùng vào trong:

1. **Trình duyệt/PWA của người dùng** chạy ứng dụng React. Giữa ứng dụng và mạng có **Service Worker** làm lớp chặn yêu cầu và cache. Dữ liệu lâu dài nằm trong **IndexedDB** và **Cache API**.
2. Yêu cầu đi qua mạng tới **một tiến trình backend FastAPI** duy nhất, trong đó mười router chia ranh giới theo nghiệp vụ.
3. Backend dùng chung **MongoDB** (dữ liệu chính), **Redis** (trạng thái tạm thời, phối hợp), và **kho tệp tĩnh/runtime** (audio, ảnh, bản đồ), có thể thay bằng kho tương thích S3.
4. Backend gọi ra **dịch vụ ngoài** khi cần: Edge-TTS, Google Translate (qua deep-translator), Gemini/ProxyPal, MapTiler, OpenWeather (tùy chọn).

## 2. Các thành phần

### 2.1 Frontend (PWA)

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| Khung UI | React 19.2, React Router (catch-all) | Hiển thị màn hình, định tuyến |
| Build | Vite 7 + plugin PWA, Workbox `injectManifest` | Đóng gói, sinh Service Worker |
| State | Zustand (ví dụ `poiStore`) | Lưu trạng thái ứng dụng |
| Bản đồ | MapLibre GL JS, giao thức `pmtiles://` | Hiển thị vector map cloud/offline |
| Địa lý | Turf.js | Tính khoảng cách cho geofence |
| Offline | Service Worker, `idb` (IndexedDB), Cache API | 4 lớp phòng thủ offline |

Các module logic chính trong frontend:

- **LocationService**: theo dõi vị trí liên tục, throttle 5 giây, hàm lấy vị trí tốt nhất có thể.
- **GeofenceEngine**: phát hiện vào/ra vùng POI, debounce 3 giây, cooldown 5 phút, vòng reconcile 5 giây.
- **NarrationEngine + AudioQueueManager**: hàng đợi một ô, phát có fallback 4 tầng.
- **useGeofence**: gắn geofence vào React, điều phối prefetch nền.
- **LanguageHotsetService**: chuẩn bị hotset theo ngôn ngữ (10 POI, 1,5 km, 3 POI bắt buộc).
- **Startup coordinator và startupNetworkProbe**: tách trạng thái sẵn sàng giữa nội dung và UI bundle; thăm dò mạng.
- **AudioPackService, MapPackService**: tải, xác thực, kích hoạt gói offline.
- **mapConfig**: chọn chế độ bản đồ Cloud, Offline hoặc Hybrid.
- **db.js**: truy cập IndexedDB `Quan4DB v2`.

### 2.2 Backend (FastAPI)

Công nghệ: FastAPI (async), Motor (MongoDB async), PyJWT (HS256), bcrypt, cryptography (Fernet), Redis client, Edge-TTS, deep-translator, SDK Gemini hoặc cổng ProxyPal.

Mười router được mount:

| Router | Trách nhiệm |
|---|---|
| content | CRUD POI, đồng bộ delta, nearby, hydrate bản địa hóa, cổng kích hoạt, menu |
| audio | Edge-TTS, GoogleTranslator, task manager, danh sách giọng, pack manifest, SSE tác vụ |
| admin | Xác thực cookie, RBAC, người dùng, role, duyệt đăng ký/submission, audit log |
| owner | Cổng chủ quán: POI của mình, submission, thông báo, trạng thái đăng ký |
| ai_advisor | Cải thiện mô tả bằng AI, quota theo ngày |
| analytics | API thu thập có consent, hiện diện qua Redis, read model trong Mongo |
| localization | On-demand, hotset, warmup, cổng "sẵn sàng tiếng Anh công khai" |
| maps | Manifest tĩnh-first, PMTiles, glyph, sprite, chống path traversal |
| runtime_observability | Ingest vị trí công khai (tách riêng), rate limit, cửa sổ quan sát cho admin |
| ui_i18n | UI bundle theo locale, `source_hash`, trạng thái pending/ready, dịch long-tail |

Ngoài ra: `/static` (tệp tĩnh), `/health`, `/health/ready`.

Mỗi domain tổ chức theo mẫu **router → service → store**, dùng chung tiến trình, DB và Redis nhưng ranh giới rõ ràng.

### 2.3 Cơ sở dữ liệu và lưu trữ

- **MongoDB**: kho dữ liệu chính (chi tiết ở `06_Database_Design.md`). Yêu cầu hỗ trợ transaction (kiểm tra khi khởi động bằng `assert_transaction_capability()`, tức cần replica set).
- **Redis**: hiện diện người dùng ẩn danh (sliding window), rate limit analytics, khóa phối hợp.
- **Kho media/runtime**: thư mục tĩnh chứa audio MP3, ảnh, gói bản đồ (`backend/app/static/maps/`, đổi bằng biến môi trường `MAP_PACK_DATA_DIR`). Có thể dùng backend tương thích S3, khi đó khi khởi động có kiểm tra sức khỏe kho (`media_storage.check_backend_health()`).

### 2.4 Dịch vụ ngoài

Xem `10_External_Services.md`.

## 3. Trình tự khởi động backend (theo tầng)

1. **Bảo mật và bootstrap guard:** kiểm tra `JWT_SECRET`, `REFRESH_TOKEN_SECRET`, `SECRET_KEY` ở môi trường không phải dev; kiểm tra `SUPERADMIN_BOOTSTRAP_MODE`. Sai hoặc thiếu thì dừng ngay.
2. **Sẵn sàng DB, cache, media:** kết nối MongoDB, xác nhận có transaction, nếu dùng S3 thì kiểm tra sức khỏe.
3. **Seeding và chuẩn bị runtime:** tạo role mặc định, tạo super admin, kiểm tra hoặc tạo thư mục lưu trữ.
4. **Phục hồi và worker nền:** làm mới trạng thái transaction, bật vòng kiểm tra sẵn sàng, khôi phục tác vụ audio sau restart, nạp tác vụ gần đây, bật vòng bảo trì, tạo index cho quan sát runtime, rồi bật worker analytics và worker dọn media.
5. **Gắn router:** mount 10 router, `/static`, `/health`, `/health/ready`.

## 4. Luồng dữ liệu chính (mô tả bằng lời)

### 4.1 Mở app và tải dữ liệu
Trình duyệt tải trang, Service Worker được đăng ký. Giao diện đọc ngay snapshot từ IndexedDB để hiển thị. Cùng lúc, frontend gọi `GET /poi/load-all` kèm ETag; backend so khớp phiên bản dataset, trả đầy đủ hoặc chỉ phần thay đổi và danh sách POI bị xóa. Frontend ghi lại vào IndexedDB. Service Worker cache phản hồi này theo chiến lược NetworkFirst (chờ mạng 8 giây, TTL 15 phút).

### 4.2 Thuyết minh theo vị trí
Dịch vụ vị trí đẩy tọa độ mỗi 5 giây vào bộ máy geofence. Bộ máy xác nhận ENTER, chọn POI tốt nhất, chuyển cho bộ phát. Bộ phát hỏi Service Worker audio đã có sẵn chưa; nếu chưa, gọi backend on-demand, rồi TTS stream, rồi cuối cùng dùng giọng của thiết bị.

### 4.3 Sinh audio phía backend
Khi admin lưu POI, router content ghi bản gốc tiếng Việt, rồi giao cho trình quản lý tác vụ audio. Trình quản lý chạy tối đa 3 tác vụ song song: dịch văn bản, kiểm tra cache MD5 trên đĩa, nếu chưa có thì gọi Edge-TTS, lưu MP3, upsert bản địa hóa vào MongoDB, cập nhật trạng thái và đẩy tiến độ qua SSE tới trang admin. Trạng thái tác vụ được lưu vào MongoDB để phục hồi.

### 4.4 Gói offline
Frontend gọi manifest (audio, map) để biết danh sách tệp, kích thước và SHA-256. Tải từng tệp, kiểm tra hash, lưu vào cache riêng của pack, rồi nhắn Service Worker kích hoạt để ưu tiên đọc từ pack.

### 4.5 Duyệt nội dung chủ quán
Chủ quán gửi submission vào `poi_submissions`; admin duyệt; hệ thống cập nhật `poi`, tăng phiên bản dataset, xếp việc sinh audio, tạo `owner_notifications`. Thiết bị của du khách thấy thay đổi ở lần đồng bộ delta kế tiếp.

## 5. Chiến lược cache và offline (4 lớp)

1. **Service Worker (Workbox):** POI NetworkFirst; audio CacheFirst theo từng ngôn ngữ; ảnh và chunk tùy chọn CacheFirst có dọn khi hết quota; gói bản đồ có cache bất biến riêng.
2. **Phân mảnh ngôn ngữ và đồng bộ build:** mỗi ngôn ngữ một cache, tối đa 300 tệp, tối đa 3 ngôn ngữ, LRU, ghim ngôn ngữ đang dùng; xóa chunk cũ khi build đổi.
3. **IndexedDB:** `pois_by_lang` và UI bundle; thứ tự dự phòng chọn, en, vi.
4. **Offline Pack:** bản đồ, POI, ảnh, audio; cài tuần tự, kiểm tra SHA-256, cache tách biệt, hy sinh runtime cache khi đầy.

Thông điệp giữa frontend và Service Worker: `SET_ACTIVE_LANGUAGE`, `APP_BUILD_SYNC`, `AUDIO_PACK_ACTIVATE`, `AUDIO_PACK_REMOVE_LANG`, `MAP_PACK_ACTIVATE`, `MAP_PACK_DEACTIVATE`.

## 6. Ba chế độ bản đồ (chuỗi bốn tầng)

1. **Chọn chế độ:** `mapConfig` quyết định Cloud, Offline hoặc Hybrid theo trạng thái mạng và pack đã kích hoạt.
2. **Công bố pack:** backend phục vụ `/static/maps/*` và lớp tương thích `/api/v1/maps/*`; manifest nêu phiên bản, checksum, scope, ngày nguồn, bbox, URL tuyệt đối.
3. **Kích hoạt pack:** frontend tải, kiểm tra SHA-256, kích hoạt; cập nhật an toàn hoặc thay thế khi khác scope.
4. **Hiển thị:** MapLibre đọc từ cache cục bộ qua `pmtiles://`; hybrid giữ cloud làm dự phòng và thăm dò dựa trên style cloud đang dùng.

## 7. Ranh giới tin cậy và bảo mật kiến trúc

- Trình duyệt không đọc được token (cookie httpOnly).
- Backend là nơi duy nhất thực thi quyền; JWT mang danh sách quyền.
- PII chỉ giải mã khi cần và không rò rỉ khi lỗi.
- Đường dẫn tệp bản đồ phải nằm trong thư mục gốc cho phép.
- Kênh analytics (cần consent) tách khỏi kênh quan sát vị trí runtime.

## 8. Các mẫu thiết kế được áp dụng

Modular Monolith; Audio lai 4 tầng; Fallback nội dung 3 tầng (chọn, en, vi); Quốc tế hóa hai làn (nội dung và UI); Phân mảnh cache theo ngôn ngữ; Geofence reconcile; RBAC động; Analytics có consent; Cookie httpOnly; PWA offline-first; Theo dõi tiến độ bằng SSE; Mã hóa PII khi lưu.

## 9. Thuộc tính chất lượng và cách đạt được

| Thuộc tính | Cách đạt |
|---|---|
| Chạy offline | 4 lớp cache, pack, IndexedDB |
| Chi phí thấp | Công cụ miễn phí, cache MD5 chống sinh lại |
| Chịu lỗi | Fallback nhiều tầng, backoff, phục hồi tác vụ |
| Mở rộng | Ranh giới router/service/store cho phép tách service sau này |
| Bảo mật | Cookie httpOnly, RBAC, mã hóa PII, rate limit, path guard |
