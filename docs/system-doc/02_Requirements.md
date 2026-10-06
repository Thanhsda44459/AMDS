# 02 — Requirements (Yêu cầu hệ thống)

> Mã yêu cầu: **FR-xx** (chức năng), **NFR-xx** (phi chức năng). Mức ưu tiên: **M** = bắt buộc, **S** = nên có, **C** = có thể có.

## A. Yêu cầu chức năng

### A1. Khởi động và ngôn ngữ

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-01 | Khi mở app, hiển thị màn hình splash và cho người dùng chọn ngôn ngữ. | M |
| FR-02 | Sau khi chọn ngôn ngữ, app tải song song: vị trí tốt nhất có thể, snapshot offline, nội dung POI (delta sync), hotset và UI bundle. | M |
| FR-03 | App có thể khởi động nhanh bằng tiếng Anh trong lúc ngôn ngữ đích đang được chuẩn bị. | S |
| FR-04 | Trước khi kết luận lỗi mạng, app thử thăm dò (`/audio/languages`, `/maps/offline-options`) với timeout 2,5 giây, tối đa 2 lần trong cửa sổ 8 giây. | S |
| FR-05 | Chuyển ngôn ngữ chỉ được xem là hoàn tất khi cả nội dung (hotset: 3 POI bắt buộc) và UI bundle đều sẵn sàng. | M |

### A2. Bản đồ và POI

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-10 | Hiển thị bản đồ vector với các POI đang hoạt động. | M |
| FR-11 | Hiển thị chi tiết POI: tên, mô tả, hình ảnh (tối đa 8, mỗi ảnh tối đa 5 MB), thực đơn (menu item), tọa độ, bán kính kích hoạt. | M |
| FR-12 | Lấy danh sách POI gần vị trí người dùng (`/poi/nearby`), ưu tiên truy vấn không gian `$geoNear`, fallback Haversine nếu lỗi. | M |
| FR-13 | Tải toàn bộ POI bằng full sync hoặc delta sync (ETag, `If-None-Match`, `updated_after`), trả về `dataset_version`, `sync_mode`, `removed_poi_ids`, `sync_cursor`. | M |
| FR-14 | Nút định vị: dùng `requestBestEffortPosition()` ưu tiên vị trí cache còn tốt (tuổi tối đa 30 giây, sai số chấp nhận tới 100 m, ngân sách 15 giây). | M |
| FR-15 | Ba chế độ bản đồ: Cloud, Offline Pack, Hybrid (cloud trước, tự chuyển sang pack khi mất mạng; quay lại cloud có độ trễ để tránh nhấp nháy). | M |

### A3. Geofence và thuyết minh

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-20 | Theo dõi vị trí liên tục (`watchPosition`) với throttle 5 giây. | M |
| FR-21 | Phát hiện vào vùng POI khi khoảng cách ≤ bán kính (mặc định 30 m); xác nhận sau debounce 3 giây. | M |
| FR-22 | Sau khi kích hoạt một POI, không kích hoạt lại trong cooldown 5 phút khi người dùng rời vùng. | M |
| FR-23 | Khi nhiều POI cùng đủ điều kiện, chọn theo `audio_priority` rồi đến khoảng cách. | M |
| FR-24 | Có vòng reconcile an toàn mỗi 5 giây. | S |
| FR-25 | Hàng đợi thuyết minh một ô (single-slot priority queue). | M |
| FR-26 | Nếu người dùng đổi ngôn ngữ trong lúc chờ audio on-demand, kết quả cũ bị bỏ. | M |
| FR-27 | Prefetch nền: quét POI `is_fallback=true` trong 500 m, tối đa 3 POI mỗi đợt, cách nhau tối thiểu 30 giây, backoff khi gặp 429 (30 s, 60 s, 120 s, tối đa 10 phút). | S |

### A4. Audio và dịch

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-30 | Phát audio theo 4 tầng: (1) file đã sinh sẵn, (1.5) dịch và TTS theo yêu cầu, (2) TTS đám mây dạng stream, (3) `speechSynthesis` cục bộ. | M |
| FR-31 | Sinh audio bằng Edge-TTS; giọng ưu tiên: vi HoaiMy, en Jenny, zh Xiaoxiao, ja Nanami, ko SunHi. | M |
| FR-32 | Cache audio theo khóa MD5 của `text:lang`; trùng khóa thì không sinh lại. | M |
| FR-33 | Khi tạo/sửa POI, tự đưa vào hàng đợi sinh audio cho 5 ngôn ngữ ưu tiên (song song tối đa 3). | M |
| FR-34 | Khi mô tả đổi: xóa `audio_url` cũ, đặt `audio_status="processing"`, tạm đặt `is_active=false` và ghi nhớ `activation_requested`. | M |
| FR-35 | Backend gắn `?v={updated_at}&l={lang}` vào `audio_url` để chống cache cũ và phân shard cache theo ngôn ngữ. | S |
| FR-36 | Admin theo dõi tác vụ audio thời gian thực (SSE), có thể tạm dừng, tiếp tục, hủy. | M |
| FR-37 | Cung cấp `pack-manifest` cho từng ngôn ngữ (danh sách file, SHA-256, tổng dung lượng, phiên bản). | M |
| FR-38 | Nội dung POI có 3 tầng fallback: ngôn ngữ yêu cầu, tiếng Anh, tiếng Việt gốc (với `audio_url = null`). | M |
| FR-39 | UI bundle theo locale; 5 ngôn ngữ chính có bundle tĩnh; ngôn ngữ ít dùng trả tiếng Anh với `status: pending` và `source_hash` trong lúc dịch nền. | M |

### A5. Offline

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-40 | Service Worker cache theo chiến lược: POI NetworkFirst (8 giây, TTL 15 phút), audio CacheFirst theo ngôn ngữ, ảnh CacheFirst có purge khi đầy quota. | M |
| FR-41 | Lưu POI theo ngôn ngữ và UI bundle trong IndexedDB (`Quan4DB v2`); offline fallback theo thứ tự ngôn ngữ chọn, en, vi. | M |
| FR-42 | Giới hạn cache audio: tối đa 300 file mỗi ngôn ngữ, tối đa 3 ngôn ngữ đồng thời, loại bỏ theo LRU (ghim ngôn ngữ đang dùng). | M |
| FR-43 | Offline Pack theo ngôn ngữ gồm 4 phần cài tuần tự: map, POI, images, audio; kiểm tra SHA-256 từng tài sản trước khi kích hoạt. | M |
| FR-44 | Hiển thị trạng thái pack: `updateAvailable`, `repairRequired`, `poiMissing`. | S |
| FR-45 | Khi tải pack gặp `QuotaExceededError`, tự xóa runtime cache audio/ảnh để nhường chỗ. | M |
| FR-46 | Khi kiểm tra bản cập nhật từ xa lỗi liên tiếp, vào cooldown thay vì gọi lặp. | S |
| FR-47 | Gói bản đồ PMTiles: tải, xác thực, kích hoạt; cho phép nhiều pack theo scope (Quận 4, TP.HCM) và `replace_update` khi trùng scope. | M |
| FR-48 | Đồng bộ build: khi phiên bản app đổi, xóa cache chunk tùy chọn cũ (`APP_BUILD_SYNC`). | S |

### A6. Xác thực và phân quyền

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-50 | Đăng nhập admin/owner bằng cookie httpOnly: access token 30 phút, refresh token 7 ngày. | M |
| FR-51 | Hỗ trợ thêm Bearer header cho API/mobile fallback. | S |
| FR-52 | Đăng xuất, đổi mật khẩu, lấy thông tin tài khoản hiện tại. | M |
| FR-53 | RBAC động: 32 quyền thuộc 9 nhóm; role lưu trong MongoDB; bảo vệ route bằng `require_permission`. | M |
| FR-54 | Bốn role mặc định: super_admin, admin, poi_owner, user. | M |
| FR-55 | Owner chỉ được vào các chức năng nghiệp vụ khi `is_poi_owner_verified = true`. | M |
| FR-56 | Mật khẩu băm bằng bcrypt. | M |

### A7. Chủ quán

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-60 | Đăng ký chủ quán công khai (`POST /admin/auth/register-owner`), tạo user poi_owner chưa xác minh và đơn `pending`. | M |
| FR-61 | Admin duyệt hoặc từ chối đơn kèm `admin_note`; khi duyệt đặt `is_verified` và `is_poi_owner_verified`. | M |
| FR-62 | Owner gửi tạo/cập nhật POI dưới dạng submission chờ duyệt; chỉ sửa được quán của mình. | M |
| FR-63 | Owner nhận thông báo kết quả duyệt, có trạng thái đã đọc/chưa đọc và trang chi tiết. | M |
| FR-64 | Số CCCD của chủ quán được mã hóa, tự che sau 180 ngày. | M |
| FR-65 | Owner dùng AI Advisor để cải thiện mô tả (200–300 từ, không bịa thông tin), tối đa 10 lần/ngày; admin không giới hạn. | S |
| FR-66 | Hiển thị hạn mức AI còn lại (`GET /ai/usage`). | S |

### A8. Quản trị

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-70 | CRUD POI, menu, user, role. | M |
| FR-71 | Bật/tắt công khai POI; không cho bật khi chưa sẵn sàng tiếng Anh/audio (phải sinh lại trước). | M |
| FR-72 | Xóa POI theo transaction khi có thể, cascade sang `poi_localizations`, đưa dọn media vào hàng đợi, cập nhật dataset version. | M |
| FR-73 | Xem audit log (hành động, người thực hiện, tài nguyên, thời gian). | M |
| FR-74 | Xem dashboard analytics và cửa sổ quan sát vị trí runtime. | S |
| FR-75 | Quản lý duyệt đăng ký chủ quán và submission POI. | M |

### A9. Analytics và quyền riêng tư

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-80 | Chỉ thu thập analytics sau khi người dùng đồng ý (consent). | M |
| FR-81 | Thống kê số thiết bị ẩn danh đang online trong cửa sổ trượt (`tracked_online_users`). | S |
| FR-82 | Kênh quan sát vị trí runtime tách riêng, có rate limit, không trộn với analytics. | S |
| FR-83 | Tổng hợp số liệu theo giờ/ngày thành read model. | S |

## B. Yêu cầu phi chức năng

### B1. Hiệu năng

| ID | Yêu cầu |
|---|---|
| NFR-01 | Audio tầng 1 phát từ cache gần như tức thì (~0 ms mạng). |
| NFR-02 | Audio tầng 1.5 hoàn tất trong khoảng 2–5 giây; tầng 2 khoảng 3–8 giây. |
| NFR-03 | GPS xử lý throttle 5 giây để tránh render/sắp xếp liên tục. |
| NFR-04 | `/poi/load-all` hỗ trợ ETag và delta sync để giảm băng thông. |
| NFR-05 | Giới hạn tải tạo audio nền: tối đa 3 tác vụ TTS song song. |
| NFR-06 | PMTiles phục vụ bằng Range Request; file bất biến cache dài hạn. |

### B2. Độ tin cậy và khả dụng

| ID | Yêu cầu |
|---|---|
| NFR-10 | Người dùng không bao giờ thấy màn hình trống: có chuỗi fallback ngôn ngữ và 4 lớp phòng thủ offline. |
| NFR-11 | Backend kiểm tra bí mật bắt buộc khi khởi động ở môi trường không phải dev và dừng ngay nếu thiếu (fail-fast). |
| NFR-12 | Có `/health` và `/health/ready` (kiểm tra sẵn sàng DB/transaction/storage). |
| NFR-13 | Tác vụ audio phục hồi sau khi backend khởi động lại (snapshot Mongo, heartbeat 5 giây, coi là treo sau 5 phút, lưu 14 ngày). |
| NFR-14 | Giới hạn tần suất dùng trạng thái chung (Mongo/Redis) để hoạt động đúng khi chạy nhiều tiến trình. |

### B3. Bảo mật

| ID | Yêu cầu |
|---|---|
| NFR-20 | Token nằm trong cookie httpOnly, SameSite=Lax, Secure (chống XSS và CSRF cơ bản). |
| NFR-21 | Mật khẩu bcrypt; JWT ký HS256. |
| NFR-22 | PII mã hóa Fernet (tiền tố `v1:`), che sau 180 ngày, giải mã lỗi trả `None`. |
| NFR-23 | Chặn Path Traversal ở dịch vụ bản đồ (`resolve_safe_path`). |
| NFR-24 | Giới hạn: on-demand 30 yêu cầu/10 phút; AI owner 10/ngày; kích thước ảnh tối đa 5 MB. |
| NFR-25 | Mọi hành động quản trị quan trọng ghi audit log. |

### B4. Quyền riêng tư

| ID | Yêu cầu |
|---|---|
| NFR-30 | Privacy-by-design: analytics chỉ khi có consent. |
| NFR-31 | Tối thiểu hóa dữ liệu: PII tự hết hạn sau 180 ngày. |

### B5. Khả năng sử dụng và quốc tế hóa

| ID | Yêu cầu |
|---|---|
| NFR-40 | Hỗ trợ tối thiểu vi, en, zh, ja, ko; ngôn ngữ khác dịch nền. |
| NFR-41 | Giao diện responsive cho điện thoại là ưu tiên **[Đề xuất]**. |
| NFR-42 | Khi dùng nội dung thay thế (fallback) phải báo cho frontend biết qua `is_fallback`. |

### B6. Khả năng bảo trì và chi phí

| ID | Yêu cầu |
|---|---|
| NFR-50 | Kiến trúc modular monolith, tách ranh giới theo router/service/store. |
| NFR-51 | Lõi dùng phần mềm mã nguồn mở/miễn phí; phần có API key là tùy chọn. |
| NFR-52 | Cache an toàn khi triển khai bản mới (không lẫn asset giữa hai build). |

### B7. Tương thích

| ID | Yêu cầu |
|---|---|
| NFR-60 | Trình duyệt hiện đại có Service Worker, Cache API, IndexedDB, Geolocation. |
| NFR-61 | Có thể cài đặt như PWA lên màn hình chính. |
