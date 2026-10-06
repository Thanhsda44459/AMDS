# 10 — External Services (Dịch vụ bên ngoài)

## 1. Tổng quan

Nguyên tắc: **lõi mã nguồn mở/miễn phí**, dịch vụ cần API key là tùy chọn. Bảng dưới liệt kê mọi dịch vụ ngoài theo tài liệu gốc và các dịch vụ trong đề bài mà tài liệu gốc không dùng.

| Dịch vụ | Mục đích | Chi phí | Bắt buộc? | Trạng thái trong hệ thống |
|---|---|---|---|---|
| Edge-TTS (Microsoft Neural Voices) | Chuyển văn bản thành giọng nói | Miễn phí | Có (cho audio sinh sẵn và tầng 2) | Đang dùng |
| deep-translator (GoogleTranslator) | Dịch văn bản | Miễn phí (mức free) | Có (dịch nội dung) | Đang dùng |
| Gemini 2.5 Flash / ProxyPal | AI cải thiện mô tả | Cần API key, có hạn mức | Tùy chọn | Đang dùng |
| MapTiler | Dữ liệu bản đồ cloud | Cần API key | Chỉ cho chế độ Cloud/Hybrid | Đang dùng |
| OpenWeather | Ngữ cảnh thời tiết cho AI | Cần API key | Tùy chọn | Đang dùng (khi bật) |
| MapLibre GL JS + PMTiles | Hiển thị bản đồ và bản đồ offline | Miễn phí | Có | Đang dùng |
| Web Speech Synthesis (trình duyệt) | TTS cục bộ dự phòng | Miễn phí | Dự phòng | Đang dùng |
| Lưu trữ tương thích S3 | Lưu media | Tùy nhà cung cấp | Tùy chọn | Hỗ trợ tùy cấu hình |
| Redis | Hiện diện, rate limit, phối hợp | Tự lưu trữ | Có | Đang dùng (hạ tầng) |
| Google Maps | Bản đồ | — | Không | **Không dùng**; thay bằng MapLibre |
| Google Login | Đăng nhập | — | Không | **Không có trong tài liệu gốc** |

> **Lưu ý đối chiếu đề bài:** Đề bài nhắc Google Maps và Google Login. Tài liệu gốc dùng **MapLibre + MapTiler + PMTiles** thay cho Google Maps, và **không** có Google Login. Nếu đồ án cần cả hai, xem mục 9 và `09_Authentication_Authorization.md` mục 9. Dịch bằng "Google Translate" ở đây là thư viện `deep-translator` gọi dịch vụ dịch miễn phí, không phải Google Cloud Translation có tính phí.

## 2. Edge-TTS (Text-to-Speech)

- **Dùng để:** sinh MP3 thuyết minh (tầng 1 sinh sẵn, tầng 1.5 on-demand, tầng 2 stream).
- **Ưu điểm:** hơn 300 giọng neural, miễn phí.
- **Giọng ưu tiên:** vi `HoaiMyNeural`; en `JennyNeural`; zh `XiaoxiaoNeural`; ja `NanamiNeural`; ko `SunHiNeural`.
- **Cache:** khóa MD5 của `text:lang`, tệp tồn tại thì không gọi lại, chi phí bằng 0.
- **Danh mục giọng:** cache 6 giờ (`VOICE_CATALOG_TTL`).
- **Tải:** tối đa 3 tác vụ song song (Semaphore).
- **Rủi ro:** dịch vụ không chính thức, có thể thay đổi hoặc giới hạn; giảm thiểu bằng cache, rate limit và fallback `speechSynthesis`.
- **Dự phòng:** `window.speechSynthesis` của thiết bị khi mọi tầng trước lỗi.

## 3. Dịch văn bản (deep-translator / GoogleTranslator)

- **Dùng để:** dịch mô tả POI sang ngôn ngữ khác; dịch UI bundle cho ngôn ngữ ít dùng ở nền.
- **Quy trình:** văn bản gốc tiếng Việt, qua deep-translator, thành văn bản dịch, rồi vào TTS.
- **Giới hạn:** chất lượng dịch máy; có thể bị chặn nếu gọi quá nhiều. Biện pháp: giới hạn on-demand 30 yêu cầu/10 phút, backoff khi 429, lưu bản dịch vào `poi_localizations`.
- **Fallback:** nếu dịch lỗi, dùng tiếng Anh rồi tiếng Việt gốc.

## 4. AI Advisor (Gemini 2.5 Flash / ProxyPal)

- **Dùng để:** viết lại mô tả quán 200–300 từ.
- **Quy tắc prompt:** không bịa thông tin; được phép thêm tính từ tích cực.
- **Hạn mức:** owner 10 lượt/ngày (`OWNER_DAILY_LIMIT`, bảng `ai_usage_limits`); admin không giới hạn.
- **Timeout:** 30 giây; lỗi trả về nêu rõ nhà cung cấp.
- **Cấu hình:** API key hoặc địa chỉ và khóa cổng ProxyPal trong biến môi trường (tên biến cụ thể: xem mã nguồn).
- **Thời tiết (tùy chọn):** OpenWeather để thêm ngữ cảnh thời tiết khi bật.
- **Bảo mật:** không gửi PII của chủ quán tới AI [Đề xuất]; không đưa khóa vào mã nguồn.

## 5. Bản đồ

### 5.1 MapLibre GL JS
Thư viện vẽ bản đồ vector mã nguồn mở, miễn phí.

### 5.2 MapTiler (chế độ Cloud/Hybrid)
- Cần biến **`VITE_MAPTILER_KEY`** ở frontend cho dữ liệu cloud.
- Style cloud do dự án sở hữu; glyph tự host.
- **Giới hạn khóa:** nên giới hạn khóa theo tên miền (HTTP referrer) vì khóa nằm ở phía client.

### 5.3 PMTiles (Offline)
- Tệp bản đồ đơn, tự host, không cần máy chủ tile; đọc bằng Range Request.
- Phục vụ qua `/static/maps/*` với cache bất biến; có manifest, checksum SHA-256.
- Có thể có nhiều pack theo scope (Quận 4, TP.HCM).
- Nguồn dữ liệu nền: dữ liệu bản đồ mở (thường OpenStreetMap); cần ghi công theo giấy phép **[Đề xuất: xác nhận nguồn pack]**.

### 5.4 Google Maps (không dùng)
Nếu bắt buộc dùng, phải thay MapLibre bằng Maps JavaScript API, mất khả năng offline PMTiles và phát sinh chi phí; **không khuyến nghị** vì mâu thuẫn mục tiêu offline và chi phí thấp.

## 6. Lưu trữ (Storage)

- **Mặc định:** thư mục tĩnh/runtime của backend chứa MP3, ảnh, gói bản đồ.
- **Tùy chọn S3-compatible:** khi bật, khởi động kiểm tra sức khỏe (`check_backend_health()`); worker nền dọn media.
- **Giới hạn nội dung:** tối đa 8 ảnh mỗi POI, mỗi ảnh ≤ 5 MB.
- **Dọn dẹp:** xóa POI sẽ xếp việc dọn media.

## 7. Hạ tầng dữ liệu

- **MongoDB:** cần chế độ hỗ trợ transaction (replica set). Có thể dùng bản tự host hoặc dịch vụ quản lý.
- **Redis:** hiện diện người dùng ẩn danh, giới hạn tần suất analytics, khóa phối hợp.

## 8. Quản lý khóa và cấu hình

| Biến (tên tham khảo) | Dùng cho | Nơi đặt |
|---|---|---|
| `JWT_SECRET`, `REFRESH_TOKEN_SECRET`, `SECRET_KEY` | Ký token, bí mật ứng dụng | Backend, bắt buộc ở non-dev |
| `SUPERADMIN_BOOTSTRAP_MODE` (+ thông tin tài khoản khởi tạo) | Tạo super admin | Backend |
| Khóa mã hóa PII (Fernet) | Mã hóa CCCD | Backend |
| `MAP_PACK_DATA_DIR` | Thư mục gói bản đồ | Backend |
| `VITE_MAPTILER_KEY` | Bản đồ cloud | Frontend (biến lúc build) |
| API key Gemini/ProxyPal | AI Advisor | Backend |
| Khóa OpenWeather | Thời tiết (tùy chọn) | Backend |
| Chuỗi kết nối MongoDB, Redis, S3 | Hạ tầng | Backend |

Tên chính xác của các biến không nêu hết trong tài liệu gốc; cần lấy từ mã nguồn hoặc tệp mẫu `.env`. Tuyệt đối không commit khóa vào kho mã.

## 9. Các dịch vụ trong đề bài mà hệ thống gốc chưa có (đề xuất nếu cần)

| Yêu cầu | Đánh giá | Hướng làm |
|---|---|---|
| Google Login | Không có sẵn | Google Identity Services + endpoint xác minh ID token (xem `09`, mục 9) |
| Google Maps | Có phương án thay thế tốt hơn đã triển khai | Giữ MapLibre; có thể chỉ thêm liên kết "Chỉ đường bằng Google Maps" mở ứng dụng bản đồ của thiết bị (không cần API key) |
| Translation | Đã có (deep-translator) | Nếu cần chất lượng cao hơn có thể dùng Cloud Translation (có phí) |
| TTS | Đã có (Edge-TTS) | Dự phòng Google Cloud TTS (có phí) |
| Storage | Mặc định đĩa, tùy chọn S3 | Dùng S3-compatible (R2, MinIO, S3) khi triển khai thật |

## 10. Chiến lược chịu lỗi dịch vụ ngoài

| Dịch vụ lỗi | Hành vi |
|---|---|
| Edge-TTS | Dùng `speechSynthesis` của thiết bị; audio đã cache vẫn phát |
| Dịch | Dùng bản đã lưu, rồi tiếng Anh, rồi tiếng Việt |
| AI | Báo lỗi theo nhà cung cấp; không ảnh hưởng chức năng khác |
| MapTiler | Hybrid chuyển sang pack offline nếu có |
| S3 | Phát hiện ở bước khởi động qua `check_backend_health()` |
| Redis | Tính năng hiện diện/rate limit giảm; cần quy định hành vi (fail-open hoặc fail-closed) [Đề xuất: xác nhận] |
