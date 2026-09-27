# 09. Xác Thực & Phân Quyền — LinhUngGuide

## 1. Hai cơ chế xác thực song song

Hệ thống có hai cơ chế xác thực tách biệt, phục vụ hai nhóm người dùng khác nhau:

1. **Access token ẩn danh cho khách tham quan** — không gắn với tài khoản cá nhân, chỉ chứng minh "phiên này đã thanh toán hợp lệ".
2. **Tài khoản đăng nhập (username/password) cho nhân viên và quản trị viên** — gắn với danh tính cụ thể và vai trò (role) rõ ràng.

Việc tách hai cơ chế này giúp trải nghiệm của khách tham quan không bị làm phiền bởi bước tạo tài khoản/đăng nhập, đồng thời vẫn đảm bảo các chức năng quản trị nhạy cảm được bảo vệ chặt chẽ.

## 2. Xác thực khách tham quan (Access Token)

### 2.1. Cách cấp token
Như mô tả trong UC-01 và UC-02, sau khi thanh toán được xác nhận (qua Payoo hoặc qua nhân viên), backend cấp một **access token dạng JWT**, ký bằng khoá bí mật của hệ thống (thuật toán HS256). Token chứa tối thiểu các thông tin: `session_id`, thời điểm hết hạn (`exp`), và một cờ xác nhận `paid = true`. Token **không** chứa bất kỳ thông tin định danh cá nhân nào của khách (không tên, không số điện thoại), vì hệ thống không yêu cầu khách cung cấp thông tin cá nhân để sử dụng.

### 2.2. Lưu trữ token phía client
Token được lưu trong bộ nhớ cục bộ của trình duyệt (localStorage), vì đây là một phiên sử dụng ngắn hạn trên một thiết bị, không cần cơ chế "đăng nhập lại nhiều thiết bị" phức tạp.

### 2.3. Kiểm tra token
Mọi API dành cho khách tham quan (lấy danh sách POI, hỏi chatbot, tải audio) đều yêu cầu header `Authorization: Bearer <access_token>`. Backend kiểm tra chữ ký, thời hạn, và cờ `paid` trước khi xử lý; nếu bất kỳ điều kiện nào không thoả, trả về `401 Unauthorized`, buộc frontend điều hướng khách quay lại màn hình thanh toán.

### 2.4. Thời hạn sử dụng
Token có thời hạn tương ứng với một lượt tham quan hợp lý trong ngày (ví dụ hết hạn vào cuối giờ mở cửa của chùa trong ngày khách thanh toán), tránh trường hợp một lượt thanh toán bị chia sẻ để dùng lại vào các ngày khác.

## 3. Xác thực nhân viên/quản trị viên (Tài khoản)

### 3.1. Đăng ký/khởi tạo tài khoản
Tài khoản admin/staff **không** được tự đăng ký công khai. Tài khoản admin đầu tiên được khởi tạo thủ công khi triển khai hệ thống (seed script); từ đó, admin tạo thêm tài khoản staff (và admin khác nếu cần) thông qua `POST /admin/users` như mô tả trong `07_API_Specification.md`.

### 3.2. Lưu trữ mật khẩu
Mật khẩu không bao giờ được lưu dạng văn bản thuần. Khi tạo/đổi mật khẩu, backend băm mật khẩu bằng **bcrypt** (có salt tự động) trước khi lưu vào trường `password_hash` trong collection `admin_users`.

### 3.3. Đăng nhập
Nhân viên/quản trị viên đăng nhập bằng `username` + `password` tại `POST /admin/login`. Backend so khớp mật khẩu bằng bcrypt; nếu đúng, sinh một JWT chứa `user_id`, `role` (`admin` hoặc `staff`), và thời hạn ngắn hơn access token của khách (ví dụ 8 giờ, tương đương một ca làm việc), vì đây là tài khoản có quyền truy cập dữ liệu nhạy cảm hơn.

### 3.4. Vai trò (Role) và phạm vi quyền hạn

| Vai trò | Mô tả | Quyền hạn chính |
|---|---|---|
| **Khách (Guest/Visitor)** | Không có tài khoản, chỉ có access token ẩn danh sau khi thanh toán | Xem POI, dùng chatbot, xem lộ trình gợi ý — không có quyền ghi/sửa bất kỳ dữ liệu hệ thống nào |
| **Nhân viên (Staff)** — còn gọi là "Quản lý ca/quầy" trong một số ngữ cảnh vận hành | Tài khoản có `role = staff` | Chỉ được: xem danh sách phiên đang chờ thanh toán tiền mặt, xác nhận thanh toán tiền mặt. Không có quyền tạo/sửa/xoá POI, không xem được dashboard giám sát toàn hệ thống, không tạo được tài khoản khác |
| **Quản trị viên (Admin)** | Tài khoản có `role = admin` | Toàn quyền: quản lý POI (bao gồm kích hoạt lại pipeline dịch/TTS), xem toàn bộ dashboard giám sát và số liệu thống kê, quản lý tài khoản nhân viên/quản trị viên khác, cũng có thể thực hiện mọi thao tác mà vai trò Staff được phép |

> Ghi chú: PRD gốc chỉ đề cập "Admin/Staff" trong luồng nghiệp vụ; đồ án bổ sung rõ hai vai trò này (thay vì gộp chung một vai trò "manager") để đảm bảo nguyên tắc phân quyền tối thiểu (principle of least privilege) — nhân viên trực quầy không cần và không nên có quyền chỉnh sửa dữ liệu POI hay xem toàn bộ số liệu kinh doanh.

### 3.5. Kiểm tra phân quyền tại backend
Backend triển khai kiểm tra vai trò tại tầng middleware/dependency dùng chung (không lặp lại logic ở từng endpoint riêng lẻ):
- Middleware giải mã JWT, xác định `role`.
- Mỗi route được gắn một yêu cầu vai trò tối thiểu (ví dụ route quản lý POI yêu cầu `role = admin`).
- Nếu vai trò trong token không đáp ứng yêu cầu của route, backend trả `403 Forbidden` (khác với `401` — nghĩa là đã xác thực được danh tính nhưng không đủ quyền).

### 3.6. Bảo vệ chống tấn công cơ bản
- Giới hạn số lần đăng nhập sai liên tiếp cho một `username` trong một khoảng thời gian (khoá tạm tài khoản hoặc yêu cầu chờ) để chống dò mật khẩu (brute-force).
- Toàn bộ giao tiếp API bắt buộc qua HTTPS, không hỗ trợ HTTP thuần, để tránh lộ token trên đường truyền.
- Webhook từ Payoo được xác thực bằng chữ ký ký số riêng do Payoo cấp (secret key), hoàn toàn tách biệt khỏi cơ chế JWT nội bộ, để tránh giả mạo xác nhận thanh toán.

## 4. Tóm tắt khác biệt giữa hai cơ chế

| Tiêu chí | Access token (Khách) | JWT tài khoản (Staff/Admin) |
|---|---|---|
| Gắn với danh tính cá nhân | Không | Có (username) |
| Cách cấp | Tự động sau khi thanh toán | Qua đăng nhập username/password |
| Thời hạn | Theo lượt tham quan (thường vài giờ tới hết ngày) | Theo ca làm việc (ví dụ 8 giờ) |
| Phạm vi quyền | Chỉ tính năng tham quan | Theo vai trò (`staff` giới hạn, `admin` toàn quyền) |
| Cơ chế lưu trữ phía client | localStorage | localStorage hoặc httpOnly cookie (khuyến nghị dùng httpOnly cookie cho admin dashboard để giảm rủi ro XSS đánh cắp token quản trị) |
