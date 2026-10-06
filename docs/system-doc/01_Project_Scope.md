# 01 — Project Scope (Phạm vi đồ án)

> Nguồn: file `system-presentation-standalone.html` (phân tích từ mã nguồn).
> Quy ước: nội dung lấy trực tiếp từ tài liệu gốc; mục đánh dấu **[Đề xuất]** là phần bổ sung do người viết suy ra, cần nhóm xác nhận.

## 1. Tên và mô tả đề tài

**Tên đề tài:** Hệ thống Du lịch Ẩm thực Quận 4 (Quan4 Culinary Tourism).

**Mô tả ngắn:** Ứng dụng web tiến bộ (PWA) full-stack giúp du khách khám phá ẩm thực đường phố Quận 4, TP.HCM. Ứng dụng hiển thị bản đồ tương tác, tự động phát thuyết minh âm thanh khi người dùng đi vào vùng quanh một điểm quan tâm (POI), hỗ trợ đa ngôn ngữ và hoạt động được khi không có mạng.

## 2. Bối cảnh và vấn đề cần giải quyết

- Du khách quốc tế khó tiếp cận thông tin về quán ăn đường phố vì rào cản ngôn ngữ.
- Khu vực du lịch thường có sóng yếu hoặc du khách không có data roaming, nên ứng dụng phải chạy được offline.
- Chủ quán nhỏ cần một kênh tự đăng tải và cập nhật thông tin quán của mình mà không tốn chi phí cao.
- Chi phí vận hành phải thấp: ưu tiên công nghệ mã nguồn mở và dịch vụ miễn phí.

## 3. Mục tiêu

1. Cung cấp bản đồ POI ẩm thực Quận 4 với nội dung mô tả, hình ảnh, thực đơn.
2. Tự động thuyết minh bằng giọng nói theo vị trí GPS (geofence) và theo ngôn ngữ người dùng chọn.
3. Hỗ trợ tối thiểu 5 ngôn ngữ chính (vi, en, zh, ja, ko) và dịch nền cho các ngôn ngữ ít dùng hơn.
4. Hoạt động offline thông qua Service Worker, IndexedDB, gói bản đồ PMTiles và gói âm thanh.
5. Cho phép chủ quán đăng ký, gửi POI và chờ duyệt; cho phép quản trị viên vận hành toàn hệ thống.
6. Hỗ trợ chủ quán nâng cấp mô tả bằng AI (Gemini 2.5 Flash / ProxyPal) trong hạn mức.
7. Giữ chi phí lõi gần như bằng 0 (Edge-TTS, deep-translator, MapLibre, PMTiles đều miễn phí).

## 4. Đối tượng sử dụng

| Nhóm | Mô tả |
|---|---|
| Khách du lịch (user / guest) | Dùng app công khai để xem bản đồ, nghe thuyết minh. Không bắt buộc đăng nhập. |
| Chủ quán (poi_owner) | Đăng ký, được duyệt, quản lý quán của mình, gửi nội dung chờ duyệt, dùng AI Advisor. |
| Quản trị viên (admin) | Quản lý POI, menu, người dùng, duyệt đơn, xem analytics và audit log. |
| Siêu quản trị (super_admin) | Có toàn bộ 32 quyền, quản lý role và cấu hình hệ thống. |

## 5. Phạm vi — TRONG đồ án (In scope)

### 5.1 Ứng dụng công khai (PWA)
- Màn hình khởi động, chọn ngôn ngữ, bản đồ POI.
- Định vị GPS, geofence, tự động phát thuyết minh.
- Audio 4 tầng (pre-generated, on-demand, cloud TTS, local speech synthesis).
- Nội dung đa ngôn ngữ với 3 tầng fallback (ngôn ngữ yêu cầu, tiếng Anh, tiếng Việt gốc).
- UI i18n theo bundle.
- Offline: Service Worker, IndexedDB, Offline Pack (map, POI, images, audio).
- Ba chế độ bản đồ: Cloud, Offline Pack, Hybrid.
- Đồng ý (consent) trước khi thu thập analytics.

### 5.2 Backend (FastAPI + MongoDB)
- Mười router: content, audio, admin, owner, ai_advisor, analytics, localization, maps, runtime_observability, ui_i18n.
- Xác thực cookie httpOnly (JWT access 30 phút, refresh 7 ngày), RBAC động với 32 quyền.
- Sinh audio nền bằng Edge-TTS với tiến độ thời gian thực qua SSE.
- Mã hóa PII (số CCCD chủ quán) bằng Fernet, tự động che sau 180 ngày.
- Audit log, thông báo cho chủ quán, giới hạn tần suất (rate limit).

### 5.3 Cổng quản trị
- Admin Dashboard (CRUD POI, user, role, menu; duyệt đăng ký và submission; analytics; audit log; theo dõi tác vụ audio).
- Owner Portal (đăng ký, trạng thái xác minh, quản lý quán, submission, thông báo, AI Advisor).

## 6. Phạm vi — NGOÀI đồ án (Out of scope)

- Ứng dụng native iOS/Android (chỉ có PWA).
- Thanh toán, đặt món, đặt bàn, giao hàng.
- Đánh giá/bình luận của người dùng, mạng xã hội.
- Đăng nhập khách bằng Google hoặc mạng xã hội. **Tài liệu gốc không đề cập tính năng này**; khách dùng app ẩn danh. (Xem mục chú thích trong `10_External_Services.md`.)
- Mở rộng ra ngoài Quận 4 (kiến trúc có hỗ trợ scope nhiều pack bản đồ nhưng dữ liệu chính là Quận 4 và TP.HCM).
- Tính năng định tuyến/dẫn đường turn-by-turn **[Đề xuất: không nằm trong tài liệu gốc]**.
- Hạ tầng microservice; hệ thống là modular monolith.

## 7. Ràng buộc và giả định

| Loại | Nội dung |
|---|---|
| Công nghệ | Backend FastAPI + Motor (MongoDB), Redis; frontend React 19.2, Vite 7, Zustand, MapLibre GL JS, Turf.js, Workbox, idb. |
| Chi phí | Lõi mã nguồn mở. Gemini/ProxyPal cần API key; MapTiler chỉ cần cho chế độ cloud/hybrid; OpenWeather chỉ khi bật ngữ cảnh thời tiết cho AI. |
| Trình duyệt | Cần hỗ trợ Service Worker, Cache API, IndexedDB, Geolocation, Web Speech Synthesis. |
| Quyền riêng tư | Analytics chỉ chạy sau khi người dùng đồng ý; PII mã hóa và hết hạn sau 180 ngày. |
| Ngôn ngữ nội dung gốc | Tiếng Việt; bản dịch sinh bằng máy. |
| Giả định | Dữ liệu POI nhập qua admin/owner; chất lượng dịch máy chấp nhận được cho thuyết minh. |

## 8. Sản phẩm bàn giao (Deliverables)

1. Mã nguồn backend và frontend.
2. Bộ tài liệu 12 file (thư mục này).
3. Gói bản đồ PMTiles cho Quận 4 (và TP.HCM nếu có).
4. Dữ liệu mẫu POI và tài khoản siêu quản trị khởi tạo.
5. Hướng dẫn triển khai (`12_Deployment.md`).

## 9. Tiêu chí hoàn thành

- Người dùng mở app, chọn ngôn ngữ, thấy bản đồ và POI trong thời gian hợp lý.
- Đi vào bán kính POI (mặc định 30 m) thì nghe được thuyết minh đúng ngôn ngữ, không phát lặp trong 5 phút.
- Tắt mạng sau khi cài Offline Pack vẫn xem được bản đồ, POI và nghe được audio đã tải.
- Chủ quán đăng ký, được admin duyệt, gửi POI, nhận thông báo kết quả.
- Admin quản lý được toàn bộ dữ liệu và xem được audit log.
- Các ca kiểm thử trong `11_Test_Plan.md` đạt.

## 10. Rủi ro chính

| Rủi ro | Hướng xử lý |
|---|---|
| GPS nhiễu, sai lệch trong khu dân cư đông | Debounce 3 giây, throttle 5 giây, cooldown 5 phút, chấp nhận độ chính xác tới 100 m. |
| Dịch vụ miễn phí (Edge-TTS, Google Translate wrapper) bị giới hạn hoặc thay đổi | Cache MD5 trên đĩa, rate limit, fallback sang speechSynthesis của trình duyệt. |
| Hết dung lượng thiết bị khi tải Offline Pack | Workbox tự xóa runtime cache để nhường chỗ cho pack. |
| Lạm dụng AI/dịch on-demand | Quota 10/ngày cho owner; giới hạn 30 yêu cầu/10 phút cho on-demand. |
| Lộ thông tin cá nhân chủ quán | Mã hóa Fernet, che sau 180 ngày, không trả PII khi giải mã lỗi. |
