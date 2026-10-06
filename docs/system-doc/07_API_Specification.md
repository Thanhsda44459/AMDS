# 07 — API Specification (Giao tiếp Frontend ↔ Backend)

## 0. Quy ước chung

- **Base URL:** `/api/v1` (tiền tố của các route nêu trong tài liệu gốc). Tệp tĩnh ở `/static`. Kiểm tra sức khỏe ở `/health`, `/health/ready`.
- **Định dạng:** JSON (trừ MP3 và tệp bản đồ).
- **Xác thực:** cookie httpOnly (`access_token`, `refresh_token`); có thể dùng `Authorization: Bearer <token>` cho client không phải trình duyệt.
- **Lỗi chuẩn:** 400 dữ liệu sai; 401 chưa đăng nhập; 403 thiếu quyền hoặc owner chưa xác minh; 404 không tồn tại; 429 vượt giới hạn (kèm `Retry-After`); 5xx lỗi máy chủ.
- **Phân loại truy cập:** Công khai (P), Cần đăng nhập (A), Cần quyền cụ thể (quyền trong ngoặc).

> **Lưu ý quan trọng:** Tài liệu gốc nêu chắc chắn một số endpoint; nhiều endpoint admin/owner (tổng 40 admin + 12 owner) chỉ được tóm tắt theo nhóm. Các dòng ghi **[Đề xuất]** là đường dẫn dự kiến theo quy ước REST, cần đối chiếu với mã nguồn (Swagger `/docs` của FastAPI) trước khi chốt.

## 1. Content (POI)

| Method | Đường dẫn | Truy cập | Mô tả |
|---|---|---|---|
| GET | `/poi/load-all` | P | Tải toàn bộ POI. Tham số: `lang`, `updated_after`; header `If-None-Match`. Trả `dataset_version`, `sync_mode` (full/delta), `removed_poi_ids`, `sync_cursor`, danh sách POI. 304 nếu không đổi. Chỉ trả POI đã sẵn sàng tiếng Anh. |
| GET | `/poi/nearby` | P | POI gần vị trí (`lat`, `lng`, `radius`, `lang`). Dùng `$geoNear`, fallback Haversine. |
| GET | `/poi/{id}` [Đề xuất] | P | Chi tiết một POI. |
| GET | `/poi/{id}/menu` [Đề xuất] | P | Thực đơn của POI. |

**Hình dạng một POI trả về (rút gọn):**
`id`, `name`, `description`, `location {lat,lng}`, `trigger_radius`, `audio_priority`, `images[]`, `audio_url` (đã gắn `?v={updated_at}&l={lang}`), `is_fallback`, `updated_at`.

**Quy tắc fallback ngôn ngữ trong phản hồi:** ngôn ngữ yêu cầu, rồi English, rồi Vietnamese gốc (khi đó `audio_url = null`).

## 2. Localization

| Method | Đường dẫn | Truy cập | Mô tả |
|---|---|---|---|
| POST | `/localizations/on-demand` | P | Dịch và sinh audio cho một POI/ngôn ngữ ngay. Body: `poi_id`, `lang`. Trả `audio_url` mới. Giới hạn 30 yêu cầu/10 phút; 429 kèm `Retry-After`. |
| POST | `/localizations/prepare-hotset` | P | Làm nóng tối đa 10 POI gần nhất trong 1,5 km. Body: vị trí, `lang`. |
| POST | `/localizations/warmup` | P | Chạy dịch toàn bộ corpus ở nền. |

## 3. UI i18n

| Method | Đường dẫn | Truy cập | Mô tả |
|---|---|---|---|
| GET | `/ui-bundles/{locale}` | P | Bundle UI namespace `public-ui`. Locale chính (en, vi, zh, ja, ko) trả bundle tĩnh. Locale khác trả tiếng Anh với `status: pending` và `source_hash` trong lúc dịch nền; khi xong `status: ready`. |

## 4. Audio

| Method | Đường dẫn | Truy cập | Mô tả |
|---|---|---|---|
| GET | `/audio/languages` | P | Danh sách ngôn ngữ/giọng khả dụng (cache danh mục giọng 6 giờ). Cũng dùng làm probe khởi động. |
| POST | `/audio/tts` | P | Tầng 2: văn bản thành MP3 stream. Body: `text`, `lang`. Header phản hồi: `X-Cache: HIT/MISS`, `X-Static-Url` (URL có phiên bản cho Service Worker). |
| GET | `/audio/pack-manifest` | P | Manifest gói audio theo ngôn ngữ (`?lang=`). Trả `{lang, pack_version, total_files, total_bytes, files[]}`, mỗi tệp có SHA-256. |
| GET | `/admin/audio-tasks/stream` | A (quyền admin) | **SSE** tiến độ tác vụ audio thời gian thực. |
| POST | `/admin/audio-tasks/{id}/pause\|resume\|cancel` [Đề xuất] | A | Điều khiển tác vụ. |

## 5. Maps

| Method | Đường dẫn | Truy cập | Cache | Mô tả |
|---|---|---|---|---|
| GET | `/static/maps/packs/current/manifest.json` | P | no-cache | Manifest chính |
| GET | `/maps/offline-manifest` | P | no-cache | Manifest tương thích |
| GET | `/maps/offline-options` | P | no-cache | Danh sách pack theo scope, nhãn, phiên bản, ngày nguồn, kích thước. Cũng dùng làm probe khởi động. |
| GET | `/static/maps/packs/{version}/{file}.pmtiles` | P | immutable | PMTiles, hỗ trợ Range Request |
| GET | `/static/maps/styles/*.json` | P | revalidate/immutable | Style và sprite |
| GET | `/static/maps/fonts/{fontstack}/{range}.pbf` | P | immutable | Glyph |

Mọi đường dẫn tệp qua `resolve_safe_path` để chống Path Traversal.

## 6. Authentication (admin/owner)

| Method | Đường dẫn | Truy cập | Mô tả |
|---|---|---|---|
| POST | `/admin/auth/login` [Đề xuất] | P | Đăng nhập, đặt 2 cookie. |
| POST | `/admin/auth/refresh` [Đề xuất] | Cookie refresh | Cấp lại access token. |
| POST | `/admin/auth/logout` [Đề xuất] | A | Xóa cookie. |
| GET | `/admin/auth/me` | A | Thông tin người dùng hiện tại, role, quyền, cờ xác minh. |
| POST | `/admin/auth/change-password` | A | Đổi mật khẩu. |
| POST | `/admin/auth/register-owner` | P | Đăng ký chủ quán; tạo user chưa xác minh và đơn `pending`. |

## 7. Admin (nhóm chức năng, tổng 40 route)

| Nhóm | Hành động | Quyền |
|---|---|---|
| POI | Liệt kê, tạo, sửa, xóa, bật/tắt, duyệt | `poi:read/create/update/delete/toggle/approve` |
| Menu | CRUD | `menu:*` |
| User | CRUD, gán role | `user:*` |
| Role | CRUD | `role:*` |
| Đăng ký chủ quán | Liệt kê, duyệt, từ chối (kèm `admin_note`) | `content:moderate` hoặc `user:update` [cần đối chiếu] |
| Submission POI | Liệt kê, duyệt, từ chối | `poi:approve` |
| Audit | Xem log | `audit:read` |
| Analytics | Xem dashboard, xuất | `analytics:view/export` |
| Quan sát runtime | Xem cửa sổ vị trí | `analytics:view` [cần đối chiếu] |
| Audio tasks | Danh sách, SSE, pause/resume/cancel | Quyền POI/system |

Mẫu đường dẫn **[Đề xuất]**: `GET/POST /admin/pois`, `PUT/DELETE /admin/pois/{id}`, `PATCH /admin/pois/{id}/toggle`, `GET /admin/users`, `GET /admin/roles`, `GET /admin/registrations`, `POST /admin/registrations/{id}/approve|reject`, `GET /admin/submissions`, `GET /admin/audit-logs`.

## 8. Owner (nhóm chức năng, 12 route)

Điều kiện chung: đăng nhập, role `poi_owner`, `is_poi_owner_verified = true` (trừ route trạng thái đăng ký).

| Method | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/owner/registration-status` | Trạng thái đơn đăng ký (dùng khi chưa xác minh). |
| PUT | `/owner/pois/{id}` | Sửa POI của mình (tạo submission chờ duyệt). |
| POST | `/owner/pois` [Đề xuất] | Gửi POI mới. |
| GET | `/owner/pois` [Đề xuất] | Danh sách POI của mình. |
| GET | `/owner/submissions` [Đề xuất] | Danh sách submission và trạng thái. |
| GET | `/owner/notifications` | Danh sách thông báo (`/owner/notifications*` gồm chi tiết và đánh dấu đã đọc). |
| GET | `/owner/notifications/{id}` [Đề xuất] | Chi tiết thông báo. |
| POST | `/owner/notifications/{id}/read` [Đề xuất] | Đánh dấu đã đọc. |
| GET | `/owner/dashboard` [Đề xuất] | Tổng quan (quyền `analytics:view_own`). |
| CRUD | Menu của quán mình [Đề xuất] | Quyền `menu:read/create/update`. |

## 9. AI Advisor

| Method | Đường dẫn | Truy cập | Mô tả |
|---|---|---|---|
| GET | `/ai/usage` | A | Trả `{limit, used, remaining}`. Admin không giới hạn. |
| POST | `/ai/enhance-description` | A | Body: mô tả gốc (và tùy chọn ngữ cảnh, thời tiết nếu bật). Trả bản mô tả cải thiện 200–300 từ. Timeout 30 giây. Lỗi nêu rõ nhà cung cấp. Hết quota: lỗi 429. |

## 10. Analytics và quan sát runtime

| Nhóm | Mô tả |
|---|---|
| API thu thập analytics | Công khai nhưng chỉ ghi khi client gửi đủ thông tin consent; có rate limit. Gửi sự kiện, phiên, thiết bị ẩn danh. Đường dẫn cụ thể: xem mã nguồn. |
| Ingest vị trí runtime | Kênh công khai riêng, rate limit, không phụ thuộc consent analytics. |
| Đọc số liệu | Chỉ admin; dựa trên read model. `tracked_online_users` là số thiết bị ẩn danh đã đồng ý còn trong cửa sổ trượt. |

## 11. Hệ thống

| Method | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/health` | Tiến trình còn sống. |
| GET | `/health/ready` | Đã sẵn sàng (DB, transaction, lưu trữ). |

## 12. Hợp đồng quan trọng giữa frontend và backend

1. **ETag và delta sync:** frontend gửi `If-None-Match` và `updated_after`; backend trả 304 hoặc phần thay đổi cùng `removed_poi_ids`.
2. **Phiên bản audio:** `audio_url` có `?v=...&l=...`; frontend không tự bỏ tham số này vì Service Worker dùng để phân shard.
3. **Cờ `is_fallback`:** frontend dùng để quyết định gọi on-demand thay vì phát ngay.
4. **429 và `Retry-After`:** frontend phải dừng và backoff đúng thời gian (prefetch: 30 s, 60 s, 120 s, tối đa 10 phút).
5. **Trạng thái UI bundle:** `pending` thì dùng tiếng Anh tạm; sẽ kiểm tra lại để chuyển sang `ready`.
6. **Cookie:** mọi gọi API admin/owner dùng `credentials: include`.
7. **Phiên hết hạn:** 401 thì thử refresh một lần, thất bại thì về trang đăng nhập.
