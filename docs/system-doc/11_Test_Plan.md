# 11 — Test Plan (Kế hoạch kiểm thử)

> Tài liệu gốc không có kế hoạch kiểm thử. Toàn bộ tài liệu này là **[Đề xuất]**, xây từ các hành vi, hằng số và ràng buộc đã mô tả trong hệ thống. Công cụ nêu tên là gợi ý.

## 1. Mục tiêu và phạm vi

- Xác nhận hệ thống đáp ứng `02_Requirements.md`.
- Tập trung vào các rủi ro lớn: geofence và audio, offline, phân quyền, đa ngôn ngữ, bảo mật dữ liệu.
- Phạm vi: backend (10 router), frontend PWA, cổng owner, admin dashboard.
- Ngoài phạm vi: kiểm thử tải quy mô lớn, kiểm thử hạ tầng nhà cung cấp, bản thân các dịch vụ ngoài.

## 2. Các tầng kiểm thử

| Tầng | Mục tiêu | Công cụ gợi ý |
|---|---|---|
| Unit backend | Hàm service, tiện ích, quyền | pytest, pytest-asyncio |
| Unit frontend | Geofence, hàng đợi audio, store, fallback | Vitest |
| Tích hợp API | Router với MongoDB/Redis thật hoặc test container | pytest + httpx, MongoDB test (replica set) |
| Thành phần frontend | Màn hình, trạng thái | React Testing Library |
| End-to-end | Luồng người dùng trên trình duyệt | Playwright |
| PWA/Offline | Service Worker, cache, mất mạng | Playwright (offline mode), Lighthouse |
| Bảo mật | Xác thực, phân quyền, path traversal | Kiểm thử thủ công + OWASP ZAP |
| Hiệu năng | Thời gian phản hồi API chính | k6 hoặc Locust (quy mô nhỏ) |
| Thực địa | GPS thật ngoài trời | Thử trên điện thoại tại Quận 4 |
| Chấp nhận (UAT) | Người dùng thật | Kịch bản có hướng dẫn |

## 3. Môi trường kiểm thử

- **Dev:** máy cá nhân, MongoDB replica set đơn nút, Redis cục bộ, dịch vụ ngoài giả lập.
- **Staging:** giống production, dữ liệu mẫu, khóa API thử.
- **Thiết bị:** ít nhất một Android (Chrome), một iPhone (Safari), một máy tính (Chrome/Edge/Firefox).
- **Mạng:** bình thường, chậm (3G giả lập), mất mạng hoàn toàn, mạng chập chờn.
- **Giả lập dịch vụ ngoài:** mock Edge-TTS, dịch, AI để kiểm thử tất định; một vòng kiểm thử với dịch vụ thật.

## 4. Dữ liệu kiểm thử

- Bộ POI mẫu (ít nhất 15 quán) gồm: có đủ bản dịch 5 ngôn ngữ; chỉ có tiếng Anh; chỉ có tiếng Việt; không có audio; hai POI cách nhau dưới 30 m (kiểm thử chọn ưu tiên); POI có đủ 8 ảnh.
- Tài khoản: super_admin, admin, owner đã xác minh, owner chưa xác minh, owner bị từ chối, user thường.
- Tập tọa độ GPS mô phỏng: đi vào vùng, đứng sát biên, nhiễu ra vào liên tục, rời vùng rồi quay lại trong và sau 5 phút.

## 5. Các ca kiểm thử chính

### 5.1 Khởi động và ngôn ngữ

| ID | Ca kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC-001 | Mở app lần đầu, chọn ngôn ngữ | Vào được bản đồ, UI đúng ngôn ngữ |
| TC-002 | Mở app lần hai khi có dữ liệu cũ | Hiển thị ngay từ IndexedDB, cập nhật nền |
| TC-003 | Backend không phản hồi lúc mở app | Sau 2 lần thăm dò (timeout 2,5 s, cửa sổ 8 s) app dùng dữ liệu offline, không màn hình trống |
| TC-004 | Chọn ngôn ngữ chưa có UI bundle | Tạm dùng tiếng Anh, `status: pending`, sau đó chuyển sang ngôn ngữ đích |
| TC-005 | Đổi ngôn ngữ | Chỉ coi hoàn tất khi hotset (3 POI bắt buộc) và UI bundle đều sẵn sàng |

### 5.2 Đồng bộ POI

| ID | Ca kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC-010 | `load-all` lần đầu | Full sync, có `dataset_version` |
| TC-011 | `load-all` với `If-None-Match` khớp | 304 |
| TC-012 | Admin sửa 1 POI rồi gọi `load-all` với `updated_after` | Delta chỉ chứa POI đã đổi |
| TC-013 | Admin xóa POI | `removed_poi_ids` chứa POI đó; client xóa khỏi IndexedDB |
| TC-014 | POI chưa sẵn sàng tiếng Anh | Không xuất hiện ở lane công khai |
| TC-015 | `nearby` khi truy vấn không gian lỗi | Fallback Haversine vẫn trả kết quả đúng |
| TC-016 | Ảnh vượt 5 MB hoặc quá 8 ảnh | Bị từ chối kèm thông báo |

### 5.3 Geofence và thuyết minh

| ID | Ca kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC-020 | Vào bán kính 30 m và ở lại hơn 3 s | Phát thuyết minh |
| TC-021 | Chạm biên rồi ra trong dưới 3 s | Không phát (debounce) |
| TC-022 | Cập nhật GPS dồn dập | Xử lý theo throttle 5 s |
| TC-023 | Vào lại POI trong 5 phút | Không phát lại (cooldown) |
| TC-024 | Vào lại sau hơn 5 phút | Phát lại |
| TC-025 | Hai POI cùng đủ điều kiện | Chọn `audio_priority` cao hơn; bằng nhau thì gần hơn |
| TC-026 | Đang phát POI A, vào POI B | Hàng đợi một ô xử lý đúng, không phát chồng |
| TC-027 | Độ chính xác GPS trên 100 m | Không dùng làm định vị tốt |
| TC-028 | Bấm định vị khi có cache vị trí dưới 30 s và đủ tốt | Dùng ngay, không chờ |
| TC-029 | Không có vị trí sau 15 s | Thông báo, không treo |

### 5.4 Audio 4 tầng

| ID | Ca kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC-030 | POI có `audio_url`, không fallback | Tầng 1: phát từ cache |
| TC-031 | POI `is_fallback=true` | Tầng 1.5: gọi on-demand, phát `audio_url` mới |
| TC-032 | On-demand lỗi | Tầng 2: stream `/audio/tts`, header `X-Cache` |
| TC-033 | Tầng 2 lỗi hoặc offline | Tầng 3: `speechSynthesis` |
| TC-034 | Đổi ngôn ngữ khi on-demand đang chờ | Kết quả cũ bị bỏ |
| TC-035 | Vượt 30 yêu cầu/10 phút | 429 kèm `Retry-After`; client backoff 30 s, 60 s, 120 s... tối đa 10 phút |
| TC-036 | Prefetch nền | Tối đa 3 POI/đợt, đợt cách nhau tối thiểu 30 s, trong 500 m |
| TC-037 | Cùng văn bản và ngôn ngữ sinh hai lần | Lần hai Cache HIT, không gọi Edge-TTS |
| TC-038 | Sửa mô tả POI | `audio_url` cũ bị xóa, `audio_status=processing`, `is_active=false` tạm thời, sau đó tự bật lại nếu có `activation_requested` |

### 5.5 Tác vụ audio (admin)

| ID | Ca kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC-040 | Tạo POI mới | 5 ngôn ngữ ưu tiên vào hàng đợi, chạy tối đa 3 song song |
| TC-041 | Theo dõi SSE | Tiến độ cập nhật thời gian thực |
| TC-042 | Pause, Resume, Cancel | Trạng thái chuyển đúng |
| TC-043 | Khởi động lại backend giữa chừng | Tác vụ phục hồi từ snapshot; tác vụ quá 5 phút không heartbeat được xử lý lại |
| TC-044 | Bật công khai POI chưa có tiếng Anh/audio | Bị chặn và phải sinh lại trước |

### 5.6 Offline

| ID | Ca kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC-050 | Tắt mạng sau khi đã dùng app | Bản đồ (pack hoặc cache), POI, UI vẫn hoạt động |
| TC-051 | Offline, ngôn ngữ chọn thiếu dữ liệu | Fallback chọn, en, vi; không màn hình trống |
| TC-052 | Cài Offline Pack | Tuần tự map, POI, ảnh, audio; kiểm tra SHA-256 |
| TC-053 | Làm hỏng một tệp (sai checksum) | Không kích hoạt, trạng thái `repairRequired` |
| TC-054 | Hết dung lượng khi tải pack | `QuotaExceededError` thì xóa cache audio/ảnh runtime rồi tiếp tục |
| TC-055 | Có phiên bản pack mới | Hiển thị `updateAvailable` |
| TC-056 | Cài pack khác scope khi đã có pack | Yêu cầu `replace_update` |
| TC-057 | Xóa gói | `MAP_PACK_DEACTIVATE` hoặc `AUDIO_PACK_REMOVE_LANG`, quay về cloud |
| TC-058 | Dùng 4 ngôn ngữ liên tiếp | Tối đa 3 cache ngôn ngữ; LRU xóa ngôn ngữ ít dùng nhất, giữ ngôn ngữ đang dùng |
| TC-059 | Vượt 300 tệp một ngôn ngữ | Loại bớt theo LRU |
| TC-060 | Triển khai bản mới | `APP_BUILD_SYNC` dọn chunk cũ, không lẫn asset hai build |
| TC-061 | Kiểm tra manifest từ xa lỗi liên tiếp | Vào cooldown, không spam mạng |
| TC-062 | Hybrid: mất mạng rồi có lại | Chuyển sang pack; quay lại cloud có độ trễ, không nhấp nháy |

### 5.7 Xác thực và phân quyền

| ID | Ca kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC-070 | Đăng nhập đúng | Hai cookie httpOnly, Secure, SameSite=Lax |
| TC-071 | Đăng nhập sai | 401, không lộ chi tiết |
| TC-072 | JS đọc `document.cookie` | Không thấy token |
| TC-073 | Access hết hạn, còn refresh | Tự cấp lại, yêu cầu tiếp tục |
| TC-074 | Cả hai hết hạn | Về trang đăng nhập |
| TC-075 | Gọi API bằng Bearer | Được chấp nhận |
| TC-076 | Route thiếu quyền (ví dụ `poi:delete`) | 403 |
| TC-077 | Owner chưa xác minh gọi API nghiệp vụ | 403; frontend chỉ vào trang trạng thái |
| TC-078 | Owner sửa POI không phải của mình | Bị từ chối |
| TC-079 | Admin duyệt đơn, owner đăng nhập lại | Vào được `/owner` |
| TC-080 | Đổi mật khẩu | Mật khẩu mới có hiệu lực; cũ vô hiệu |
| TC-081 | Tạo role mới và gán user | Quyền đúng sau khi cấp token mới |
| TC-082 | Khởi động non-dev thiếu `JWT_SECRET` | Backend không chạy |
| TC-083 | Ma trận role: gọi lần lượt mọi route nhóm admin bằng 4 role | Kết quả khớp ma trận ở `09` |

### 5.8 Chủ quán và AI

| ID | Ca kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC-090 | Đăng ký chủ quán | User chưa xác minh, đơn `pending`, CCCD mã hóa (`v1:` trong DB) |
| TC-091 | Admin từ chối không ghi chú | Bị yêu cầu nhập `admin_note` |
| TC-092 | Gửi submission | Chưa ảnh hưởng dữ liệu công khai |
| TC-093 | Admin duyệt submission | POI cập nhật, tăng phiên bản dataset, owner nhận thông báo |
| TC-094 | Thông báo | Đã/chưa đọc, trang chi tiết |
| TC-095 | AI: lượt 1–10 | Thành công; `/ai/usage` giảm đúng |
| TC-096 | AI: lượt 11 trong ngày | Bị từ chối; hôm sau hoạt động lại |
| TC-097 | AI: admin | Không giới hạn |
| TC-098 | AI: quá 30 s | Timeout, thông báo rõ nhà cung cấp |
| TC-099 | Chất lượng AI | 200–300 từ, không thêm thông tin không có trong bản gốc (đánh giá thủ công) |

### 5.9 Analytics và riêng tư

| ID | Ca kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC-100 | Từ chối consent | Không có yêu cầu analytics nào được gửi |
| TC-101 | Đồng ý consent | Sự kiện được ghi |
| TC-102 | Hiện diện | `tracked_online_users` đúng theo cửa sổ trượt, đếm thiết bị chứ không phải số tab |
| TC-103 | Kênh vị trí runtime | Hoạt động độc lập với consent, có rate limit |
| TC-104 | PII quá 180 ngày | Tự che |
| TC-105 | Giải mã PII lỗi | Trả `None`, không rò rỉ |

### 5.10 Bản đồ và bảo mật tệp

| ID | Ca kiểm thử | Kết quả mong đợi |
|---|---|---|
| TC-110 | Truy cập `/static/maps/../../etc/passwd` và các biến thể mã hóa | Bị chặn (`resolve_safe_path`) |
| TC-111 | Range Request PMTiles | 206 đúng |
| TC-112 | Header cache | Manifest `no-cache`; pack/glyph `immutable` |
| TC-113 | Ba chế độ bản đồ | Cloud, Offline, Hybrid hoạt động và chuyển được |
| TC-114 | Khóa MapTiler sai hoặc thiếu | Cloud lỗi nhẹ nhàng; Hybrid chuyển sang pack |

## 6. Kiểm thử phi chức năng

| Mục | Phương pháp | Tiêu chí (đề xuất, cần nhóm xác nhận) |
|---|---|---|
| Hiệu năng API | k6: `load-all`, `nearby`, `on-demand` | p95 `nearby` dưới 500 ms; `load-all` 304 dưới 200 ms (trên cấu hình mục tiêu) |
| Thời gian audio | Đo thực tế | Tầng 1.5: 2–5 s; tầng 2: 3–8 s |
| Pin và GPS | Thử thực địa 30 phút | Mức tiêu thụ chấp nhận được, không treo |
| PWA | Lighthouse | Đạt tiêu chí PWA cài đặt; điểm hiệu năng đạt ngưỡng nhóm đặt ra |
| Tương thích | Ma trận thiết bị | Hoạt động trên Chrome Android, Safari iOS, Chrome/Edge/Firefox desktop |
| Chịu lỗi | Tắt Redis, Edge-TTS, AI lần lượt | Hệ thống giảm chất lượng nhưng không sập |
| Bảo mật | OWASP Top 10 cơ bản, quét ZAP | Không có lỗ hổng mức cao |
| Khả năng tiếp cận | Quét tự động và kiểm tra thủ công | Nhãn, tương phản, vùng chạm |

## 7. Kiểm thử thực địa

1. Đi bộ có kế hoạch qua ít nhất 5 POI tại Quận 4, ghi lại: thời điểm vào vùng, thời điểm audio bắt đầu, có phát đúng POI không, có phát lặp không.
2. Thử trong khu đông nhà cao tầng để quan sát nhiễu GPS.
3. Thử khi có mạng yếu và khi mất mạng sau khi đã cài gói.
4. Thử bằng ít nhất 3 ngôn ngữ.

## 8. Quy trình và tiêu chí

- **Tự động hóa:** unit và tích hợp chạy trên mỗi lần đẩy mã (CI); E2E chạy trước mỗi lần phát hành.
- **Mức nghiêm trọng lỗi:** Nghiêm trọng (mất dữ liệu, lỗ hổng bảo mật, app không mở), Cao (chức năng chính hỏng), Trung bình, Thấp.
- **Điều kiện vào kiểm thử chấp nhận:** không còn lỗi Nghiêm trọng/Cao mở; toàn bộ ca mức M của `02` đạt.
- **Điều kiện phát hành:** 100% ca "M" đạt; không lỗ hổng bảo mật mức cao; kịch bản thực địa đạt.
- **Báo cáo lỗi:** mô tả, các bước tái hiện, môi trường, thiết bị, ảnh/video, mức độ.

## 9. Truy vết yêu cầu sang kiểm thử

| Yêu cầu | Ca kiểm thử |
|---|---|
| FR-01..05 | TC-001..005 |
| FR-10..15 | TC-010..016, TC-113 |
| FR-20..27 | TC-020..029, TC-036 |
| FR-30..39 | TC-030..038, TC-004 |
| FR-40..48 | TC-050..062 |
| FR-50..56 | TC-070..083 |
| FR-60..66 | TC-090..099 |
| FR-70..75 | TC-040..044, TC-091..093 |
| FR-80..83 | TC-100..103 |
| NFR-20..25 | TC-072, TC-082, TC-104, TC-105, TC-110 |

## 10. Rủi ro kiểm thử

- Edge-TTS và dịch miễn phí có thể không ổn định khi chạy tự động: dùng mock cho CI.
- Hành vi Service Worker khác nhau giữa trình duyệt, đặc biệt Safari iOS: bắt buộc thử thiết bị thật.
- GPS giả lập không phản ánh nhiễu thật: cần thực địa.
- MongoDB cần replica set để thử transaction: dùng test container.
