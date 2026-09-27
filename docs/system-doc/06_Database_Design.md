# 06. Thiết Kế Cơ Sở Dữ Liệu — LinhUngGuide

Hệ thống dùng MongoDB (dạng tài liệu/document) làm CSDL chính và Redis làm bộ nhớ tạm. Vì MongoDB không có khái niệm "bảng" cứng nhắc như CSDL quan hệ, tài liệu này mô tả từng **collection**, cấu trúc các trường dữ liệu, và mối quan hệ (tham chiếu) giữa chúng bằng lời thay vì sơ đồ ER.

## 1. Collection `pois`
Lưu thông tin từng điểm tham quan.

| Trường | Kiểu dữ liệu | Mô tả |
|---|---|---|
| `_id` | ObjectId | Khoá chính, định danh duy nhất của POI |
| `code` | String | Mã ngắn gọn, dễ đọc cho nội bộ (ví dụ `LU-001`) |
| `name_original` | String | Tên POI bằng ngôn ngữ gốc (tiếng Việt) |
| `description_original` | String | Mô tả gốc bằng tiếng Việt, do quản trị viên nhập |
| `translations` | Mảng các đối tượng con | Danh sách bản dịch, mỗi phần tử gồm: `language_code` (ví dụ `en`, `ja`, `ko`, `fr`...), `name`, `description`, `audio_url`, `status` (đã sẵn sàng/đang xử lý/lỗi) |
| `location` | Đối tượng GeoJSON dạng `Point` | Toạ độ (kinh độ, vĩ độ) của POI, dùng chỉ mục địa lý `2dsphere` để truy vấn khoảng cách nhanh |
| `proximity_radius_m` | Number | Bán kính (mét) để xác định khi nào khách được coi là "vào vùng" POI |
| `thumbnail_url` | String | Đường dẫn ảnh đại diện trên Blob Storage |
| `gallery_urls` | Mảng String | Các ảnh minh hoạ bổ sung |
| `order_hint` | Number | Gợi ý thứ tự khi xuất hiện trong lộ trình mặc định |
| `is_active` | Boolean | Cho phép ẩn POI khỏi app mà không xoá dữ liệu |
| `created_by`, `updated_by` | ObjectId (tham chiếu `admin_users`) | Người tạo/sửa gần nhất |
| `created_at`, `updated_at` | Date | Mốc thời gian |

**Chỉ mục đề xuất**: chỉ mục địa lý `2dsphere` trên `location`; chỉ mục thường trên `code` (unique) và `is_active`.

## 2. Collection `visit_sessions`
Lưu một lượt tham quan của một khách (một access token tương ứng một session).

| Trường | Kiểu dữ liệu | Mô tả |
|---|---|---|
| `_id` | ObjectId | Khoá chính |
| `session_id` | String (UUID) | Định danh phiên, dùng trong luồng thanh toán tiền mặt (khách đưa cho nhân viên) |
| `payment_method` | String enum | `online` hoặc `cash` |
| `payment_status` | String enum | `pending`, `paid`, `expired`, `failed` |
| `auth_code` | String | Mã xác thực tạm thời dùng để đổi lấy access token |
| `payoo_transaction_id` | String (nullable) | Mã giao dịch bên Payoo, chỉ có khi `payment_method = online` |
| `confirmed_by_staff_id` | ObjectId (tham chiếu `admin_users`, nullable) | Nhân viên đã xác nhận, chỉ có khi `payment_method = cash` |
| `access_token_issued_at` | Date | Thời điểm cấp access token |
| `access_token_expires_at` | Date | Thời điểm hết hạn quyền truy cập |
| `preferred_language` | String | Ngôn ngữ khách chọn gần nhất (tham khảo cho thống kê, không bắt buộc dùng để hiển thị vì frontend tự quản lý) |
| `created_at` | Date | Thời điểm khách bắt đầu phiên (trước cả khi thanh toán) |

**Chỉ mục đề xuất**: unique trên `session_id`; chỉ mục trên `payment_status` để dashboard truy vấn nhanh danh sách đang chờ.

## 3. Collection `admin_users`
Lưu tài khoản quản trị viên và nhân viên (không có tài khoản cho khách tham quan, vì khách chỉ định danh bằng access token ẩn danh).

| Trường | Kiểu dữ liệu | Mô tả |
|---|---|---|
| `_id` | ObjectId | Khoá chính |
| `username` | String | Tên đăng nhập, duy nhất |
| `password_hash` | String | Mật khẩu đã băm bằng bcrypt |
| `full_name` | String | Họ tên hiển thị |
| `role` | String enum | `admin` hoặc `staff` |
| `is_active` | Boolean | Cho phép khoá tài khoản mà không xoá |
| `created_at`, `last_login_at` | Date | Mốc thời gian |

## 4. Collection `chat_logs`
Lưu lịch sử hỏi đáp với chatbot, phục vụ thống kê và (trong tương lai) làm cache câu hỏi thường gặp.

| Trường | Kiểu dữ liệu | Mô tả |
|---|---|---|
| `_id` | ObjectId | Khoá chính |
| `session_id` | String (tham chiếu `visit_sessions.session_id`) | Phiên đặt câu hỏi |
| `question` | String | Câu hỏi gốc của khách |
| `detected_language` | String | Ngôn ngữ được xác định cho câu hỏi |
| `answer` | String | Câu trả lời đã sinh |
| `related_poi_ids` | Mảng ObjectId (tham chiếu `pois`) | Các POI được xác định có liên quan tới câu trả lời |
| `response_time_ms` | Number | Thời gian xử lý, phục vụ số liệu giám sát hiệu năng |
| `created_at` | Date | Thời điểm đặt câu hỏi |

**Chỉ mục đề xuất**: chỉ mục trên `created_at` (giảm dần) để truy vấn nhanh các câu hỏi gần nhất cho dashboard; có thể cân nhắc TTL index nếu muốn tự động xoá log cũ sau một khoảng thời gian.

## 5. Collection `system_metrics` (tổng hợp định kỳ)
Lưu số liệu đã tổng hợp theo khoảng thời gian (ví dụ mỗi giờ), tránh việc dashboard phải quét toàn bộ dữ liệu thô mỗi lần tải.

| Trường | Kiểu dữ liệu | Mô tả |
|---|---|---|
| `_id` | ObjectId | Khoá chính |
| `period_start`, `period_end` | Date | Khoảng thời gian tổng hợp |
| `total_visits` | Number | Số phiên đã thanh toán thành công trong khoảng thời gian |
| `revenue_online`, `revenue_cash` | Number | Doanh thu theo từng hình thức thanh toán |
| `top_pois` | Mảng đối tượng `{ poi_id, view_count }` | Các POI được xem nhiều nhất |
| `chatbot_question_count` | Number | Số câu hỏi chatbot đã xử lý |
| `avg_chatbot_response_time_ms` | Number | Thời gian phản hồi trung bình của chatbot |
| `error_count` | Number | Số lỗi hệ thống ghi nhận được |

## 6. Chỉ mục vector — Azure AI Search (ngoài MongoDB)
Không lưu trong MongoDB mà trong chỉ mục riêng của Azure AI Search, gồm các "document" tìm kiếm với cấu trúc: đoạn nội dung văn bản (chunk mô tả POI hoặc tài liệu bổ sung), vector embedding tương ứng, `poi_id` liên kết ngược về collection `pois` trong MongoDB, và `language_code`. Việc tách chỉ mục vector ra khỏi MongoDB giúp tối ưu tốc độ tìm kiếm ngữ nghĩa mà không ảnh hưởng tới hiệu năng đọc/ghi dữ liệu vận hành.

## 7. Redis — cấu trúc dữ liệu tạm
Redis không phải CSDL bền vững mà dùng như bộ nhớ tạm có thời hạn (TTL):
- Khoá dạng `cash_code:{shortened_code}` → giá trị là `auth_code` tương ứng, thời gian sống ngắn (ví dụ 15 phút) đúng theo luồng thanh toán tiền mặt mô tả trong PRD gốc.
- (Tuỳ chọn mở rộng) Khoá dạng `rate_limit:{ip}` để giới hạn tần suất gọi API chatbot, tránh lạm dụng.

## 8. Quan hệ giữa các collection (mô tả bằng lời)
- Một `visit_session` không sở hữu trực tiếp POI nào, nhưng có thể tham chiếu tới nhiều `chat_logs` (một phiên có thể hỏi nhiều câu).
- Một `admin_user` có vai trò `staff` có thể là người xác nhận (`confirmed_by_staff_id`) của nhiều `visit_sessions` thuộc luồng thanh toán tiền mặt.
- Một `poi` có thể xuất hiện trong `related_poi_ids` của nhiều `chat_logs` khác nhau (quan hệ nhiều–nhiều mềm, không cần bảng trung gian vì MongoDB cho phép lưu mảng tham chiếu trực tiếp).
- `system_metrics` là dữ liệu phái sinh (derived), được backend tính toán định kỳ từ `visit_sessions`, `chat_logs`, và log giám sát — không có quan hệ tham chiếu ngược lại.

## 9. Lý do chọn mô hình phi quan hệ (NoSQL)
Dữ liệu POI có cấu trúc lồng nhau tự nhiên (một POI có nhiều bản dịch, mỗi bản dịch có nhiều trường) — mô hình tài liệu của MongoDB biểu diễn trực tiếp cấu trúc này mà không cần nhiều bảng liên kết như CSDL quan hệ. Ngoài ra, việc đọc dữ liệu POI diễn ra rất thường xuyên (mỗi khách tải toàn bộ danh sách POI một lần) trong khi việc ghi chỉ xảy ra khi quản trị viên chỉnh sửa — mô hình tài liệu tối ưu cho khối lượng đọc lớn, ghi ít này.
