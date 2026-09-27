# 07. Đặc Tả API — LinhUngGuide

Backend cung cấp REST API (JSON qua HTTPS), theo chuẩn FastAPI/OpenAPI. Mọi endpoint yêu cầu xác thực đều dùng header `Authorization: Bearer <access_token>`. Tài liệu mô tả từng nhóm endpoint bằng lời: mục đích, đầu vào, đầu ra, và các mã lỗi chính — không vẽ sơ đồ luồng (đã có ở tài liệu 04).

## 1. Quy ước chung
- Base URL: `https://api.linhungguide.vn/v1` (môi trường sản xuất) — trong đồ án dùng domain tạm cấp bởi Azure App Service.
- Định dạng phản hồi lỗi thống nhất: đối tượng JSON gồm `error_code`, `message`, `details` (tuỳ chọn).
- Mã trạng thái HTTP dùng đúng ngữ nghĩa chuẩn: `200` thành công, `201` tạo mới thành công, `400` dữ liệu đầu vào sai, `401` chưa xác thực/token không hợp lệ, `403` không đủ quyền, `404` không tìm thấy, `409` xung đột trạng thái (ví dụ thanh toán đã được xác nhận trước đó), `429` vượt giới hạn tần suất, `500` lỗi hệ thống.

## 2. Nhóm: Xác thực & Thanh toán

### `POST /auth/payment/online/init`
Khởi tạo luồng thanh toán trực tuyến. Không cần access token (khách chưa có).
- Đầu vào: không bắt buộc trường nào, backend tự sinh một phiên mới nếu client chưa gửi `session_id` tạm.
- Đầu ra: `payment_url` (liên kết Payoo để chuyển hướng khách), `session_id`.
- Lỗi: `500` nếu Payoo không phản hồi khi tạo liên kết.

### `POST /auth/payment/webhook/payoo`
Endpoint nội bộ, chỉ được gọi bởi hệ thống Payoo (xác thực bằng chữ ký/secret riêng của Payoo, không dùng access token của khách).
- Đầu vào: thông tin giao dịch từ Payoo, gồm `auth_code`, trạng thái thanh toán, mã giao dịch Payoo.
- Đầu ra: `200 OK` xác nhận đã nhận; backend cập nhật trạng thái phiên tương ứng trong nội bộ.

### `POST /auth/token/exchange`
Đổi `auth_code` (luồng online) hoặc `shortened_code` (luồng tiền mặt) lấy access token.
- Đầu vào: `code` (một trong hai loại mã trên), `code_type` (`auth_code` hoặc `shortened_code`).
- Đầu ra khi thành công: `access_token`, `expires_at`.
- Đầu ra khi thanh toán chưa hoàn tất: mã trạng thái `202 Accepted` kèm `status: pending`, để frontend biết cần thử lại.
- Lỗi: `404` nếu mã không tồn tại/đã hết hạn trong Redis.

### `POST /auth/payment/cash/confirm` *(yêu cầu vai trò staff hoặc admin)*
Nhân viên xác nhận đã thu tiền mặt cho một `session_id`.
- Đầu vào: `session_id`, `amount_received`.
- Đầu ra: `shortened_code` được sinh ra để đưa cho khách.
- Lỗi: `404` nếu `session_id` không tồn tại, `409` nếu phiên đã được xác nhận thanh toán trước đó.

## 3. Nhóm: Dữ liệu điểm tham quan (POI) — phía khách

### `GET /pois`
Trả về toàn bộ danh sách POI cùng bản dịch của tất cả ngôn ngữ hỗ trợ, phục vụ nguyên tắc "nạp một lần" của frontend. *(yêu cầu access token hợp lệ)*
- Đầu ra: mảng đối tượng POI, mỗi đối tượng gồm toạ độ, bán kính, và mảng `translations` như mô tả trong `06_Database_Design.md` — nhưng **không** bao gồm nội dung audio dạng nhị phân, chỉ trả về `audio_url` để client tải riêng khi cần.
- Lỗi: `401` nếu token không hợp lệ/hết hạn.

### `GET /pois/{poi_id}/audio/{language_code}`
Trả về (hoặc chuyển hướng 302 tới) file audio đã lưu trên Blob Storage/CDN cho một POI và một ngôn ngữ cụ thể. Được gọi theo yêu cầu (khi khách thực sự bấm nghe), không gọi hàng loạt.

### `GET /pois/route-suggestion`
Trả về một lộ trình tham quan gợi ý.
- Tham số truy vấn tuỳ chọn: `poi_count` (số lượng POI mong muốn trong lộ trình).
- Đầu ra: mảng `poi_id` theo thứ tự đề xuất.

## 4. Nhóm: Chatbot

### `POST /chatbot/ask`
Gửi một câu hỏi tới chatbot RAG. *(yêu cầu access token hợp lệ)*
- Đầu vào: `question` (chuỗi văn bản câu hỏi của khách).
- Đầu ra: `answer` (câu trả lời), `related_poi_ids` (mảng, có thể rỗng), `related_images` (mảng đường dẫn ảnh minh hoạ, có thể rỗng).
- Lỗi: `429` nếu vượt giới hạn số câu hỏi trong khoảng thời gian ngắn (chống lạm dụng); `500` nếu dịch vụ AI tạm thời không phản hồi.

## 5. Nhóm: Quản trị POI (Admin)

### `GET /admin/pois` *(yêu cầu vai trò admin)*
Trả về danh sách POI kèm trạng thái xử lý của pipeline dịch/TTS cho từng ngôn ngữ (`ready`, `processing`, `failed`), phục vụ màn hình quản lý.

### `POST /admin/pois` *(yêu cầu vai trò admin)*
Tạo mới một POI.
- Đầu vào: `name_original`, `description_original`, `location` (kinh độ, vĩ độ), `proximity_radius_m`, `thumbnail` (upload file hoặc URL đã upload trước).
- Đầu ra: đối tượng POI vừa tạo, trạng thái dịch/TTS ban đầu là `processing` cho toàn bộ ngôn ngữ.
- Hiệu ứng phụ: backend kích hoạt data pipeline dịch & TTS chạy nền (mô tả ở `05_System_Architecture.md`, mục 2.5).

### `PUT /admin/pois/{poi_id}` *(yêu cầu vai trò admin)*
Cập nhật thông tin một POI. Nếu `description_original` thay đổi, backend kích hoạt lại pipeline dịch/TTS cho toàn bộ ngôn ngữ (ghi đè bản dịch cũ).

### `DELETE /admin/pois/{poi_id}` *(yêu cầu vai trò admin)*
Thực hiện xoá mềm (đặt `is_active = false`) thay vì xoá vĩnh viễn, để giữ lịch sử dữ liệu và tránh phá vỡ tham chiếu từ `chat_logs`.

### `POST /admin/pois/{poi_id}/retry-pipeline` *(yêu cầu vai trò admin)*
Kích hoạt lại pipeline dịch/TTS cho một POI khi lần chạy trước gặp lỗi.

## 6. Nhóm: Quản trị phiên & tài khoản (Admin/Staff)

### `GET /admin/sessions?status=pending_cash` *(yêu cầu vai trò staff hoặc admin)*
Trả về danh sách các phiên đang chờ xác nhận thanh toán tiền mặt, phục vụ US-11.

### `POST /admin/users` *(yêu cầu vai trò admin)*
Tạo tài khoản mới cho nhân viên hoặc quản trị viên khác.
- Đầu vào: `username`, `password`, `full_name`, `role`.
- Đầu ra: đối tượng người dùng vừa tạo (không trả về `password_hash`).

### `POST /admin/login`
Đăng nhập cho admin/staff, trả về JWT chứa `user_id` và `role`.

## 7. Nhóm: Giám sát (Monitoring)

### `GET /admin/metrics/realtime` *(yêu cầu vai trò admin)*
Trả về các chỉ số hiện tại: số phiên đang hoạt động, độ trễ trung bình API gần nhất, tỉ lệ lỗi trong 5 phút gần nhất.

### `GET /admin/metrics/summary?from=&to=` *(yêu cầu vai trò admin)*
Trả về số liệu tổng hợp theo khoảng thời gian, lấy từ collection `system_metrics`: tổng lượt khách, doanh thu theo hình thức thanh toán, top POI, số câu hỏi chatbot.

## 8. Bảo mật & giới hạn tần suất
- Toàn bộ endpoint dưới `/admin/*` bắt buộc JWT có `role` phù hợp; backend kiểm tra vai trò ở tầng middleware chung, không lặp lại logic kiểm tra ở từng endpoint.
- Endpoint `/chatbot/ask` áp dụng giới hạn tần suất theo access token (ví dụ tối đa N câu hỏi/phút) để tránh chi phí gọi mô hình AI tăng đột biến do lạm dụng.
- Endpoint webhook của Payoo được xác thực bằng chữ ký riêng do Payoo cung cấp, tách biệt hoàn toàn khỏi cơ chế JWT dùng cho người dùng thông thường.
