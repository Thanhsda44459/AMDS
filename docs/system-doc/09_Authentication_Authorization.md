# 09 — Authentication & Authorization (Đăng nhập, phân quyền)

## 1. Đối chiếu vai trò: yêu cầu đề bài và hệ thống thực tế

Đề bài nêu ba nhóm: **khách / manager / admin**. Hệ thống trong tài liệu gốc có bốn role. Quy đổi:

| Nhóm theo đề bài | Role trong hệ thống | Ghi chú |
|---|---|---|
| Khách | Không đăng nhập (ẩn danh) và role `user` (ưu tiên 100) | Du khách dùng app công khai không cần tài khoản. Role `user` dùng cho tài khoản người dùng cơ bản, có quyền đăng ký làm chủ quán. |
| Manager | `poi_owner` (ưu tiên 10) | Chủ quán, chỉ quản lý quán của mình, cần được xác minh. |
| Admin | `admin` (ưu tiên 1) và `super_admin` (ưu tiên 0) | `super_admin` có toàn bộ 32 quyền. |

> **Đăng nhập Google:** tài liệu gốc **không** có đăng nhập bằng Google; xác thực dùng tên đăng nhập và mật khẩu cho admin/owner. Nếu đồ án yêu cầu Google Login, xem mục 9 (đề xuất mở rộng) và `10_External_Services.md`.

## 2. Cơ chế xác thực

### 2.1 Cookie httpOnly (chính)
- **`access_token`**: JWT, hiệu lực 30 phút, cookie `httpOnly`, `SameSite=Lax`, `Secure`.
- **`refresh_token`**: JWT, hiệu lực 7 ngày, `httpOnly`.
- JavaScript phía trình duyệt không đọc được token (chống XSS lấy token). `SameSite=Lax` giảm rủi ro CSRF.
- Thuật toán ký: HS256 (PyJWT). Bí mật: `JWT_SECRET`, `REFRESH_TOKEN_SECRET`.

### 2.2 Chế độ kép
Ngoài cookie còn chấp nhận `Authorization: Bearer` cho API hoặc client di động.

### 2.3 Mật khẩu
Băm bằng **bcrypt**; không lưu mật khẩu thô.

### 2.4 Nội dung JWT
Chứa định danh, role, **danh sách quyền**, nên đa số yêu cầu không cần truy vấn DB để kiểm tra quyền. Hệ quả: thay đổi quyền chỉ có hiệu lực khi token mới được cấp (tối đa 30 phút hoặc khi refresh).

## 3. Luồng xác thực (mô tả bằng lời)

**Đăng nhập:** người dùng gửi thông tin; server so khớp bcrypt; thành công thì tạo access và refresh, đặt hai cookie, trả thông tin cơ bản. Sai thì trả 401, không tiết lộ là sai tên hay sai mật khẩu.

**Gọi API:** trình duyệt tự đính cookie. Server giải mã JWT, kiểm tra chữ ký và hạn, rồi kiểm tra quyền của route.

**Làm mới:** khi nhận 401 vì access hết hạn, frontend gọi refresh một lần; thành công thì thử lại yêu cầu ban đầu; thất bại thì chuyển về trang đăng nhập.

**Đăng xuất:** xóa hai cookie.

**Đổi mật khẩu:** `POST /admin/auth/change-password` cho người đã đăng nhập.

## 4. Mô hình phân quyền (RBAC động)

- **Quyền (permission)** định nghĩa tĩnh trong mã: 32 quyền thuộc 9 nhóm, dạng `domain:action`.
- **Role** lưu động trong MongoDB (`roles`), mỗi role là một tập quyền; có thể tạo role mới không cần sửa mã.
- **Bảo vệ route:** `require_permission("poi:delete")`. Thiếu quyền trả 403.

### 4.1 Chín nhóm quyền

| Nhóm | Quyền |
|---|---|
| poi | read, create, update, delete, approve, toggle |
| menu | read, create, update, delete |
| user | read, create, update, delete |
| role | read, create, update, delete |
| analytics | view, export, view_own |
| audit | read, manage |
| system | config, logs, backup |
| owner | register, access, submit_poi, manage_own_poi |
| content | moderate, publish |

### 4.2 Bốn role mặc định

| Role | Ưu tiên | Quyền |
|---|---|---|
| super_admin | 0 | Toàn bộ 32 quyền |
| admin | 1 | POI, Menu, User, Analytics, Audit, Content |
| poi_owner | 10 | `poi:read`; `owner:access`, `owner:submit_poi`, `owner:manage_own_poi`; `menu:read/create/update`; `analytics:view_own` |
| user | 100 | `poi:read`, `menu:read`, `owner:register` |

(Số ưu tiên càng nhỏ thì quyền càng cao.)

## 5. Ma trận quyền theo chức năng

| Chức năng | Khách ẩn danh | user | poi_owner (đã xác minh) | admin | super_admin |
|---|---|---|---|---|---|
| Xem bản đồ, POI, nghe thuyết minh | Có | Có | Có | Có | Có |
| Tải gói offline | Có | Có | Có | Có | Có |
| Đăng ký làm chủ quán | Có (qua endpoint công khai) | Có | Không cần | Không cần | Không cần |
| Xem trạng thái đăng ký | Không | Có | Có | Không | Không |
| Sửa/gửi POI của mình | Không | Không | Có (chờ duyệt) | Không áp dụng | Không áp dụng |
| Quản lý menu quán mình | Không | Không | Đọc/tạo/sửa | Có | Có |
| Dùng AI Advisor | Không | Không | Có (10 lượt/ngày) | Có (không giới hạn) | Có |
| CRUD POI toàn hệ thống | Không | Không | Không | Có | Có |
| Duyệt đăng ký và submission | Không | Không | Không | Có | Có |
| Quản lý user | Không | Không | Không | Có | Có |
| Quản lý role | Không | Không | Không | Theo cấu hình | Có |
| Xem audit log | Không | Không | Không | Có | Có |
| Xem analytics toàn hệ thống | Không | Không | Chỉ của mình | Có | Có |
| Cấu hình, log hệ thống, backup | Không | Không | Không | Không | Có |

> Cột `admin` ở quyền `role` và `system` cần đối chiếu với danh sách quyền thực của role `admin` trong mã nguồn.

## 6. Cổng xác minh chủ quán (Owner Gate)

Role `poi_owner` **chưa đủ**. Mọi chức năng nghiệp vụ của chủ quán còn yêu cầu **`is_poi_owner_verified === true`**.

Quy trình:
1. Chủ quán đăng ký công khai: tạo user `poi_owner` chưa xác minh và đơn `pending`.
2. Admin duyệt thì hệ thống đặt `is_verified=true` và `is_poi_owner_verified=true`.
3. Chưa được duyệt: frontend chỉ truy cập được `/owner/registration-status` và màn thông báo. Các trang dashboard, submissions, notifications, POI đều **không gọi API** khi chưa qua cổng.
4. Backend vẫn chặn (403) nếu client cố gọi, không chỉ dựa vào giao diện.

Ràng buộc sở hữu: chủ quán chỉ sửa được POI của mình; sửa quán khác bị từ chối.

## 7. Bảo vệ dữ liệu cá nhân (PII)

- Số CCCD của chủ quán mã hóa bằng **Fernet** (`encrypt_pii()`), lưu dạng `"v1:" + chuỗi mã hóa`.
- Giải mã chỉ khi thật sự cần; lỗi giải mã trả `None`, không bao giờ lộ dữ liệu.
- Tự động **che sau 180 ngày**.
- Khóa mã hóa là bí mật cấu hình, không lưu trong DB.

## 8. Khởi tạo tài khoản và kiểm soát bí mật

- Khi khởi động: `ensure_roles()` tạo 4 role; `ensure_super_admin()` tạo siêu quản trị theo `SUPERADMIN_BOOTSTRAP_MODE`.
- Ở môi trường không phải dev, thiếu `JWT_SECRET`, `REFRESH_TOKEN_SECRET`, `SECRET_KEY` hoặc sai chế độ bootstrap thì backend **từ chối chạy** (fail-fast).
- Mọi thao tác quản trị quan trọng ghi `audit_logs`.

## 9. Mở rộng đề xuất: Google Login cho khách (không có trong tài liệu gốc)

Chỉ làm nếu đồ án yêu cầu. Phương án gọn:
1. Frontend dùng Google Identity Services lấy ID token.
2. Gửi ID token tới endpoint mới, ví dụ `POST /auth/google`.
3. Backend xác thực ID token với Google, tìm hoặc tạo người dùng role `user` (khóa theo email/`sub`), đặt cookie httpOnly như đăng nhập thường.
4. Cần thêm biến `GOOGLE_CLIENT_ID`, màn hình đồng ý OAuth, và cập nhật collection người dùng (trường `google_sub`, `provider`).
5. Có thể dùng để lưu yêu thích hoặc ngôn ngữ ưa thích; **không** thay thế quy trình xác minh chủ quán.

## 10. Rủi ro và biện pháp

| Rủi ro | Biện pháp |
|---|---|
| Đánh cắp token | httpOnly, Secure; token truy cập ngắn (30 phút) |
| CSRF | SameSite=Lax; cân nhắc thêm CSRF token cho thao tác ghi quan trọng [Đề xuất] |
| Quyền cũ còn trong JWT sau khi bị thu hồi | Hạn ngắn 30 phút; thu hồi refresh khi đổi role [Đề xuất] |
| Dò mật khẩu | Rate limit đăng nhập và khóa tạm sau nhiều lần sai [Đề xuất] |
| Leo thang quyền | `require_permission` ở backend, kiểm tra sở hữu khi sửa POI |
| Rò PII | Fernet, che sau 180 ngày, không ghi PII vào log |
