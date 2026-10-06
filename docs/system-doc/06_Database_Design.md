# 06 — Database Design (Thiết kế cơ sở dữ liệu)

CSDL: **MongoDB** (driver Motor). Dữ liệu dạng tài liệu; quan hệ biểu diễn bằng khóa tham chiếu (`poi_id`, `user_id`...).

> **Lưu ý:** Tài liệu gốc liệt kê tên collection, vai trò và một số trường chính. Các trường đánh dấu **[Đề xuất]** là bổ sung hợp lý, cần đối chiếu với mã nguồn thực tế.

## 1. Danh sách collection

| Collection | Module | Mục đích |
|---|---|---|
| `POI` | content | POI gốc tiếng Việt, ảnh, tọa độ, bán kính kích hoạt |
| `MenuItem` | content | Món trong thực đơn của POI |
| `poi_localizations` | localization | Bản dịch và `audio_url` theo cặp (poi_id, lang) |
| `content_dataset_versions` | content | Token phiên bản cho `/poi/load-all`, ETag, con trỏ delta sync |
| `audio_tasks` | audio | Snapshot và trạng thái điều khiển tác vụ audio, phục hồi, heartbeat, TTL |
| `admin_users` | admin | Tài khoản admin/owner, mật khẩu băm, role, cờ xác minh, PII mã hóa |
| `roles` | admin | Role động và mảng quyền; có 4 role mặc định |
| `audit_logs` | admin | Nhật ký hành động |
| `poi_owner_registrations` | admin | Đơn đăng ký chủ quán |
| `poi_submissions` | admin | POI do owner tạo/sửa chờ duyệt |
| `owner_notifications` | admin | Thông báo cho owner |
| `ai_usage_limits` | ai_advisor | Hạn mức AI theo ngày |
| `analytics_*` | analytics | Thiết bị, phiên, sự kiện, số liệu theo giờ/ngày, job, read model dashboard |
| `localization_rate_limits` | localization | Giới hạn tần suất dùng chung cho dịch/TTS on-demand (TTL) |
| `ui_translation_bundles` | ui_i18n | Cache bundle UI theo namespace + locale + source_hash |
| `runtime_location_hourly` | runtime_observability | Read model vị trí theo giờ, tách khỏi analytics |

## 2. Mô tả chi tiết từng collection

### 2.1 `POI`
Dữ liệu gốc tiếng Việt của điểm ăn uống.

| Trường | Kiểu | Mô tả |
|---|---|---|
| `_id` / `id` | ObjectId/string | Khóa chính |
| `name`, `description` | string | Tên và mô tả gốc (tiếng Việt) |
| `location` | GeoJSON Point [lng, lat] | Tọa độ; có chỉ mục không gian để `$geoNear` |
| `trigger_radius` | number (m) | Bán kính kích hoạt; mặc định 30 |
| `audio_priority` | number | Độ ưu tiên khi nhiều POI cùng kích hoạt |
| `images` | array | Tối đa 8 ảnh, mỗi ảnh ≤ 5 MB |
| `is_active` | bool | Có hiển thị công khai không |
| `activation_requested` | bool | Ghi nhớ yêu cầu bật khi audio đang sinh |
| `audio_status` | string | Ví dụ `processing`, `ready` |
| `owner_id` | ref | Chủ quán sở hữu [Đề xuất] |
| `created_at`, `updated_at` | datetime | `updated_at` dùng để gắn `?v=` vào `audio_url` và cho delta sync |

### 2.2 `MenuItem`
`poi_id` (tham chiếu POI), `name`, `price`, `description`, `image` [Đề xuất], `created_at`, `updated_at`.

### 2.3 `poi_localizations`
Bản dịch cho từng POI theo ngôn ngữ.

| Trường | Mô tả |
|---|---|
| `poi_id` | Tham chiếu POI |
| `lang` | Mã ngôn ngữ (vi, en, zh, ja, ko, ...) |
| `name`, `description` | Bản dịch |
| `audio_url` | Đường dẫn MP3; `null` nếu chưa có |
| `is_fallback` | Đánh dấu nội dung thay thế (dùng tiếng Anh hoặc Việt) [mô tả ở gốc: frontend dựa vào cờ này] |
| `updated_at` | Thời điểm cập nhật |

Chỉ mục: **compound unique (`poi_id`, `lang`)**. Khóa cache audio: `MD5(text + ":" + lang)`.

### 2.4 `content_dataset_versions`
Lưu token phiên bản hiện tại của bộ dữ liệu POI, phục vụ ETag và con trỏ delta (`sync_cursor`). Mỗi lần thay đổi/xóa POI sẽ "chạm" (cập nhật) phiên bản này.

### 2.5 `audio_tasks`
Trạng thái: `queued`, `running`, `paused`, `completed`, `failed`, `cancelled`. Các trường: id tác vụ, POI, ngôn ngữ, tiến độ, thông báo lỗi, `heartbeat_at` (mỗi 5 giây), thời điểm tạo/cập nhật. Tác vụ không có heartbeat quá 5 phút bị coi là treo; tự xóa sau 14 ngày (chỉ mục TTL).

### 2.6 `admin_users`
| Trường | Mô tả |
|---|---|
| `username`/`email` | Định danh đăng nhập (duy nhất) |
| `password_hash` | bcrypt |
| `role` | Tên role (khóa sang `roles`) |
| `is_verified` | Tài khoản đã được xác minh |
| `is_poi_owner_verified` | Chủ quán đã được duyệt |
| `cccd_encrypted` (tên tham khảo) | Chuỗi `"v1:" + Fernet` |
| `pii_redacted_at` [Đề xuất] | Thời điểm che PII (sau 180 ngày) |
| `created_at`, `last_login_at` [Đề xuất] | Thời gian |

### 2.7 `roles`
`name` (duy nhất), `priority` (số nhỏ = quyền cao), `permissions` (mảng chuỗi dạng `domain:action`), cờ role hệ thống [Đề xuất]. Bốn role mặc định được seed khi khởi động.

### 2.8 `audit_logs`
`action`, `user_id`, `resource`, `timestamp`, chi tiết bổ sung [Đề xuất].

### 2.9 `poi_owner_registrations`
`user_id`, thông tin chủ quán, `status` (`pending` thành `approved` hoặc `rejected`), `admin_note`, thời gian gửi và duyệt.

### 2.10 `poi_submissions`
`owner_id`, `poi_id` (rỗng nếu tạo mới), nội dung đề xuất, `status` (chờ duyệt, được duyệt, từ chối), `admin_note`, thời gian.

### 2.11 `owner_notifications`
`owner_id`, tiêu đề/nội dung, liên kết tới submission hoặc đơn, `read` (bool), `created_at`.

### 2.12 `ai_usage_limits`
`{user_id, date, count}`. Mỗi ngày một bản ghi cho mỗi người dùng; reset theo ngày. Giới hạn owner 10 lượt/ngày.

### 2.13 `analytics_*`
Nhóm collection gồm thiết bị ẩn danh, phiên, sự kiện, số liệu theo giờ và ngày, job và read model cho dashboard. Chỉ ghi khi có consent. Tên cụ thể từng collection xem mã nguồn.

### 2.14 `localization_rate_limits`
Khóa giới hạn theo người/thiết bị và cửa sổ thời gian; TTL để tự dọn. Ngưỡng: 30 yêu cầu/10 phút.

### 2.15 `ui_translation_bundles`
Khóa: (`namespace`, `locale`, `source_hash`). Trường: `status` (pending/ready), `payload`. Khi `source_hash` đổi (văn bản gốc UI đổi), bundle cũ không còn khớp.

### 2.16 `runtime_location_hourly`
Tổng hợp vị trí theo cửa sổ giờ, phục vụ màn hình quan sát của admin. Độc lập với analytics.

## 3. Quan hệ giữa các dữ liệu (mô tả bằng lời)

- **Một POI có nhiều `poi_localizations`** (một bản cho mỗi ngôn ngữ). Xóa POI thì xóa tiếp toàn bộ bản địa hóa (cascade, có transaction khi khả dụng).
- **Một POI có nhiều `MenuItem`.**
- **Một POI thuộc về một chủ quán** (chủ quán là một bản ghi trong `admin_users` có role `poi_owner`) [Đề xuất về tên trường].
- **Một người dùng có đúng một role** (tên role trỏ sang `roles`). Quyền của người dùng là tập quyền của role đó, được nhúng vào JWT khi đăng nhập.
- **Một người dùng owner có thể có một đơn đăng ký** (`poi_owner_registrations`) và **nhiều submission** (`poi_submissions`) và **nhiều thông báo** (`owner_notifications`).
- **Mỗi hành động quản trị tạo một dòng `audit_logs`** gắn với `user_id`.
- **`ai_usage_limits`** gắn mỗi người dùng với mỗi ngày một bản ghi.
- **`audio_tasks`** gắn với cặp (POI, ngôn ngữ) cần sinh âm thanh.
- **`content_dataset_versions`** là điểm tham chiếu chung: mọi thay đổi POI/bản địa hóa cập nhật nó để client biết cần đồng bộ.

MongoDB không ép khóa ngoại; tính toàn vẹn được đảm bảo ở tầng service và bằng transaction.

## 4. Chỉ mục đề xuất

| Collection | Chỉ mục | Mục đích |
|---|---|---|
| `POI` | 2dsphere trên `location` | `$geoNear` cho nearby |
| `POI` | `is_active`, `updated_at` | Delta sync |
| `poi_localizations` | unique (`poi_id`, `lang`) | Truy vấn và upsert theo ngôn ngữ |
| `admin_users` | unique `username` | Đăng nhập |
| `roles` | unique `name` | Tra role |
| `audit_logs` | `timestamp`, `user_id` | Tra cứu |
| `ai_usage_limits` | unique (`user_id`, `date`) | Đếm hạn mức |
| `audio_tasks` | TTL 14 ngày | Dọn tác vụ cũ |
| `localization_rate_limits` | TTL theo cửa sổ | Tự dọn |
| `ui_translation_bundles` | unique (`namespace`, `locale`, `source_hash`) | Tra bundle |

## 5. Dữ liệu phía trình duyệt

**IndexedDB `Quan4DB` phiên bản 2:**
- `pois_by_lang`: bản chụp POI theo từng ngôn ngữ.
- Kho UI bundle đã cache.

**Cache API (do Service Worker quản lý):**
- `poi-load-all-cache` (TTL 15 phút).
- `audio-cache-lang-{lang}` (tối đa 300 tệp mỗi ngôn ngữ, 3 ngôn ngữ).
- Cache ảnh, cache chunk tùy chọn, cache gói bản đồ bất biến, cache gói audio.

## 6. Dữ liệu khởi tạo (seed)

- 4 role mặc định, chạy bởi `ensure_roles()`:

| Role | Ưu tiên | Quyền |
|---|---|---|
| super_admin | 0 | Toàn bộ 32 quyền |
| admin | 1 | POI, Menu, User, Analytics, Audit, Content |
| poi_owner | 10 | `poi:read`, `owner:access`, `owner:submit_poi`, `owner:manage_own_poi`, `menu:read/create/update`, `analytics:view_own` |
| user | 100 | `poi:read`, `menu:read`, `owner:register` |

- Tài khoản super admin: tạo bởi `ensure_super_admin()` theo `SUPERADMIN_BOOTSTRAP_MODE`.

## 7. Vòng đời và lưu giữ dữ liệu

| Dữ liệu | Thời gian lưu |
|---|---|
| CCCD chủ quán | Tự che sau 180 ngày |
| `audio_tasks` | 14 ngày |
| `localization_rate_limits` | Theo cửa sổ quota |
| Cache POI trên client | 15 phút trước khi kiểm tra lại |
| Tác vụ audio treo | Coi là stale sau 5 phút không heartbeat |

## 8. Ràng buộc nghiệp vụ trên dữ liệu

- Chỉ POI có bản tiếng Anh sẵn sàng mới xuất hiện ở "active public lane".
- Khi mô tả đổi: `audio_url` cũ bị xóa, `audio_status` về `processing`, POI tạm `is_active=false`.
- Mỗi POI tối đa 8 ảnh; mỗi ảnh tối đa 5 MB.
- Mỗi người dùng owner tối đa 10 lượt AI mỗi ngày.
