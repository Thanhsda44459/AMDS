# 04 — Use Cases (Luồng sử dụng chính)

Các luồng được mô tả bằng lời, theo từng bước đánh số. Mỗi use case gồm: tác nhân, điều kiện trước, luồng chính, luồng thay thế/ngoại lệ, kết quả.

## Danh mục

| Mã | Tên | Tác nhân chính |
|---|---|---|
| UC-01 | Khởi động app và chọn ngôn ngữ | Du khách |
| UC-02 | Xem bản đồ và chi tiết POI | Du khách |
| UC-03 | Nghe thuyết minh tự động theo vị trí | Du khách |
| UC-04 | Đổi ngôn ngữ | Du khách |
| UC-05 | Tải gói offline | Du khách |
| UC-06 | Đồng ý hoặc từ chối analytics | Du khách |
| UC-07 | Đăng ký chủ quán | Chủ quán |
| UC-08 | Duyệt đăng ký chủ quán | Admin |
| UC-09 | Chủ quán gửi tạo/sửa POI | Chủ quán |
| UC-10 | Admin duyệt submission POI | Admin |
| UC-11 | Admin quản lý POI và sinh audio | Admin |
| UC-12 | Chủ quán dùng AI Advisor | Chủ quán |
| UC-13 | Đăng nhập, làm mới phiên, đăng xuất | Admin/Owner |
| UC-14 | Quản lý role và quyền | Super Admin |

---

## UC-01. Khởi động app và chọn ngôn ngữ

- **Tác nhân:** Du khách.
- **Điều kiện trước:** Đã mở đường dẫn của app (lần đầu hoặc đã cài PWA).
- **Luồng chính:**
  1. Trình duyệt đăng ký Service Worker.
  2. Bộ định tuyến chuyển mọi đường dẫn vào ứng dụng bản đồ; hiển thị màn splash.
  3. Du khách chọn ngôn ngữ.
  4. App chạy song song năm việc: (a) định vị tốt nhất có thể; (b) đọc snapshot POI và UI bundle trong IndexedDB; (c) đồng bộ nội dung POI (full hoặc delta); (d) chuẩn bị hotset gồm tối đa 10 POI gần nhất trong 1,5 km; (e) tải UI bundle và warmup nền.
  5. Khi nội dung cần thiết sẵn sàng, splash ẩn đi và bản đồ hiển thị.
- **Luồng thay thế:**
  - 4a. Backend không phản hồi: app thử thăm dò 2 lần trong cửa sổ 8 giây (timeout 2,5 giây mỗi lần) rồi dùng dữ liệu offline.
  - 4b. UI bundle của ngôn ngữ chưa sẵn: app dùng tiếng Anh trước (quick-start), chuyển sang ngôn ngữ đích khi xong.
- **Kết quả:** Bản đồ hiển thị với dữ liệu mới nhất có thể, hoặc dữ liệu lưu sẵn.

## UC-02. Xem bản đồ và chi tiết POI

- **Điều kiện trước:** Đã hoàn tất UC-01.
- **Luồng chính:**
  1. Bản đồ hiển thị theo chế độ hiện hành (Cloud, Offline, Hybrid).
  2. Du khách chạm vào một POI.
  3. App mở thẻ chi tiết: tên, mô tả theo ngôn ngữ, ảnh, thực đơn, nút nghe thuyết minh.
- **Luồng thay thế:**
  - 2a. POI chưa có bản dịch ngôn ngữ đã chọn: hiển thị tiếng Anh; nếu cũng không có, hiển thị tiếng Việt; POI được đánh dấu `is_fallback`.
  - 1a. Chế độ Hybrid và mất mạng: tự chuyển sang bản đồ offline đã kích hoạt.
- **Kết quả:** Du khách xem được thông tin POI.

## UC-03. Nghe thuyết minh tự động theo vị trí

- **Điều kiện trước:** Đã cấp quyền định vị; app đang theo dõi vị trí.
- **Luồng chính:**
  1. Cứ mỗi 5 giây (throttle), app nhận một vị trí GPS mới.
  2. Bộ máy geofence tính khoảng cách tới từng POI bằng Turf; POI nào trong bán kính (mặc định 30 m) được đưa vào danh sách "chờ vào".
  3. Nếu POI vẫn ở trong vùng sau 3 giây (debounce), sự kiện ENTER được xác nhận.
  4. Nếu có nhiều POI, chọn theo `audio_priority` rồi đến khoảng cách.
  5. POI được chọn đưa vào hàng đợi thuyết minh (một ô).
  6. Bộ phát audio thử các tầng theo thứ tự (xem luồng thay thế) cho đến khi phát được.
  7. Khi phát xong, đóng cửa sổ thông tin.
  8. POI vào trạng thái cooldown 5 phút sau khi du khách rời vùng.
- **Luồng thay thế (chọn tầng audio):**
  - Tầng 1: POI có `audio_url` và không phải `is_fallback`: phát từ cache Service Worker.
  - Tầng 1.5: POI là `is_fallback=true`: gọi `POST /localizations/on-demand`, backend dịch và sinh audio, trả `audio_url` mới (2–5 giây).
  - Tầng 2: Nếu tầng trên lỗi: gọi `POST /audio/tts` để nhận MP3 dạng stream (3–8 giây).
  - Tầng 3: Nếu vẫn lỗi hoặc offline: dùng `window.speechSynthesis` của thiết bị.
- **Ngoại lệ:**
  - 6a. Người dùng đổi ngôn ngữ trong lúc chờ: bỏ kết quả cũ.
  - 6b. Backend trả 429 hoặc `Retry-After`: dừng gọi, chờ theo thời gian được yêu cầu.
- **Song song:** Prefetch nền quét POI `is_fallback` trong 500 m, tối đa 3 POI mỗi đợt, cách nhau ít nhất 30 giây.
- **Kết quả:** Du khách nghe thuyết minh đúng ngôn ngữ, không lặp trong 5 phút.

## UC-04. Đổi ngôn ngữ

- **Luồng chính:**
  1. Du khách chọn ngôn ngữ mới trong cài đặt.
  2. App ghim ngôn ngữ mới cho Service Worker (`SET_ACTIVE_LANGUAGE`).
  3. Hai làn chạy độc lập: làn nội dung (hotset 10 POI gần nhất, cần 3 POI bắt buộc, on-demand và warmup) và làn giao diện (UI bundle).
  4. Chỉ khi cả hai làn xong, app đánh dấu hoàn tất và đổi giao diện sang ngôn ngữ mới.
- **Luồng thay thế:** Ngôn ngữ ít dùng: UI bundle trả tiếng Anh với `status: pending`; app kiểm tra lại sau khi server dịch xong.
- **Kết quả:** Giao diện và nội dung đồng nhất theo ngôn ngữ mới.

## UC-05. Tải gói offline

- **Điều kiện trước:** Có mạng; còn dung lượng.
- **Luồng chính:**
  1. Du khách mở màn hình gói offline, thấy danh sách pack bản đồ (Quận 4, TP.HCM) và gói của ngôn ngữ hiện tại.
  2. Bấm tải; app cài tuần tự: bản đồ, POI, ảnh, audio.
  3. Mỗi tài sản được kiểm tra SHA-256 theo manifest.
  4. Khi tất cả đạt, app gửi thông điệp kích hoạt cho Service Worker (`MAP_PACK_ACTIVATE`, `AUDIO_PACK_ACTIVATE`).
  5. Bản đồ chuyển sang đọc từ cache cục bộ qua `pmtiles://`.
- **Luồng thay thế:**
  - 2a. Hết dung lượng (`QuotaExceededError`): Workbox xóa cache audio lẻ và ảnh, rồi thử lại.
  - 3a. Sai checksum: không kích hoạt, đánh dấu `repairRequired`.
  - 4a. Đã có pack khác scope đang dùng: yêu cầu cập nhật dạng thay thế (`replace_update`).
  - Xóa gói: gửi `MAP_PACK_DEACTIVATE` hoặc `AUDIO_PACK_REMOVE_LANG`, app quay về chế độ cloud.
- **Kết quả:** App dùng được hoàn toàn offline cho ngôn ngữ đã chọn.

## UC-06. Đồng ý hoặc từ chối analytics

- **Luồng chính:** App hỏi sự đồng ý; nếu đồng ý, gửi sự kiện ẩn danh qua API thu thập có kiểm soát consent; thiết bị được tính vào số online trong cửa sổ trượt.
- **Luồng thay thế:** Từ chối: không gửi gì; app vẫn dùng bình thường.
- **Ghi chú:** Kênh quan sát vị trí runtime là kênh riêng, có rate limit, không phụ thuộc consent analytics.

## UC-07. Đăng ký chủ quán

- **Tác nhân:** Chủ quán (chưa có tài khoản).
- **Luồng chính:**
  1. Chủ quán mở trang đăng ký và nhập thông tin, kể cả số CCCD.
  2. Gọi `POST /admin/auth/register-owner`.
  3. Hệ thống tạo user role `poi_owner` (chưa xác minh), mã hóa CCCD và tạo đơn `poi_owner_registrations` trạng thái `pending`.
  4. Chủ quán đăng nhập thì chỉ thấy màn trạng thái đăng ký (`/owner/registration-status`).
- **Ngoại lệ:** Dữ liệu trùng hoặc không hợp lệ: trả lỗi và yêu cầu nhập lại.

## UC-08. Duyệt đăng ký chủ quán

- **Tác nhân:** Admin có quyền phù hợp.
- **Luồng chính:**
  1. Admin mở danh sách đơn đang chờ.
  2. Xem chi tiết và quyết định duyệt hoặc từ chối.
  3. Duyệt: đặt `is_verified=true` và `is_poi_owner_verified=true`. Từ chối: ghi `admin_note`.
  4. Hệ thống ghi audit log và tạo thông báo cho chủ quán.
- **Kết quả:** Chủ quán được vào khu vực `/owner` hoặc biết lý do bị từ chối.

## UC-09. Chủ quán gửi tạo/sửa POI

- **Điều kiện trước:** Đã đăng nhập và `is_poi_owner_verified = true`.
- **Luồng chính:**
  1. Chủ quán tạo POI mới hoặc sửa POI của mình (`PUT /owner/pois/{id}`).
  2. Hệ thống lưu thành một submission trạng thái chờ duyệt (`poi_submissions`), chưa ảnh hưởng dữ liệu công khai.
  3. Chủ quán theo dõi trạng thái trong trang submissions và thông báo.
- **Ngoại lệ:** Sửa POI không thuộc mình: bị từ chối (403). Chưa xác minh: bị chặn ở mọi lane nghiệp vụ.

## UC-10. Admin duyệt submission POI

- **Luồng chính:**
  1. Admin xem submission kèm nội dung đề xuất.
  2. Duyệt hoặc từ chối kèm `admin_note`.
  3. Khi duyệt: POI được tạo/cập nhật, hệ thống đưa việc sinh audio vào hàng đợi, tăng phiên bản dataset để các thiết bị đồng bộ delta.
  4. Gửi thông báo kết quả cho chủ quán (`owner_notifications`).
- **Kết quả:** POI xuất hiện công khai sau khi bản tiếng Anh và audio sẵn sàng.

## UC-11. Admin quản lý POI và sinh audio

- **Luồng chính (tạo/sửa):**
  1. Admin lưu văn bản POI.
  2. Hệ thống đưa vào hàng đợi sinh audio cho 5 ngôn ngữ ưu tiên.
  3. Nếu mô tả thay đổi: xóa `audio_url` cũ, đặt `audio_status="processing"`, tạm `is_active=false`, ghi nhớ `activation_requested`.
  4. Trình quản lý tác vụ chạy tối đa 3 tác vụ song song: dịch, đọc bằng Edge-TTS, lưu MP3, ghi bản địa hóa.
  5. Admin xem tiến độ qua luồng SSE; có thể Pause, Resume, Cancel.
  6. Khi xong, POI được bật lại nếu đã yêu cầu kích hoạt.
- **Luồng chính (xóa):** Xóa theo transaction khi có thể, xóa cascade bản địa hóa, xếp việc dọn media, cập nhật phiên bản dataset.
- **Luồng thay thế:** Bật công khai khi chưa sẵn sàng tiếng Anh/audio: hệ thống buộc sinh lại trước.
- **Ngoại lệ:** Server khởi động lại giữa chừng: tác vụ được khôi phục từ snapshot.

## UC-12. Chủ quán dùng AI Advisor

- **Luồng chính:**
  1. Chủ quán mở form POI và bấm "Cải thiện mô tả".
  2. Giao diện gọi `GET /ai/usage` để hiển thị số lượt còn lại, sau đó `POST /ai/enhance-description`.
  3. Hệ thống kiểm tra hạn mức 10 lượt/ngày; nếu còn, gọi Gemini 2.5 Flash hoặc ProxyPal với yêu cầu không bịa, có thể thêm tính từ tích cực, 200–300 từ.
  4. Trả bản đề xuất; chủ quán chọn dùng hay không.
- **Ngoại lệ:** Hết hạn mức: báo lỗi. Quá 30 giây: hết thời gian chờ, giao diện nhận lỗi theo nhà cung cấp.
- **Ghi chú:** Admin không bị giới hạn.

## UC-13. Đăng nhập, làm mới phiên, đăng xuất

- **Luồng chính:**
  1. Người dùng gửi tên đăng nhập và mật khẩu.
  2. Hệ thống xác thực (bcrypt) và đặt hai cookie httpOnly: access (30 phút), refresh (7 ngày); JWT chứa danh sách quyền.
  3. Mỗi yêu cầu kế tiếp mang cookie; route kiểm tra quyền từ JWT, không cần truy vấn DB cho hầu hết yêu cầu.
  4. Access hết hạn: dùng refresh để cấp lại.
  5. Đăng xuất xóa cookie.
- **Thay thế:** Client không phải trình duyệt có thể dùng Bearer header.
- **Ngoại lệ:** Sai thông tin: 401. Thiếu quyền: 403.

## UC-14. Quản lý role và quyền

- **Tác nhân:** Super Admin (hoặc người có quyền `role:*`).
- **Luồng chính:** Xem danh sách role; tạo role mới với tập quyền chọn từ 32 quyền; sửa hoặc xóa; gán role cho user. Thay đổi ghi audit log.
- **Ghi chú:** Quyền định nghĩa tĩnh trong mã; role lưu động trong DB.
