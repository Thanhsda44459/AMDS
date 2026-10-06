# 08 — UI/UX Specification (Màn hình và luồng giao diện)

> Sơ đồ luồng được thay bằng mô tả theo trình tự. Tài liệu gốc không có wireframe; phần bố cục chi tiết là **[Đề xuất]** dựa trên chức năng đã mô tả.

## 1. Nguyên tắc thiết kế

1. **Mobile-first:** du khách dùng điện thoại, vừa đi vừa xem.
2. **Không bao giờ trống:** luôn có nội dung dự phòng; hiển thị dữ liệu cũ trong lúc tải mới.
3. **Hạn chế thao tác:** thuyết minh tự động, không bắt buộc đăng nhập.
4. **Trạng thái rõ ràng:** đang tải, đang dùng offline, nội dung thay thế, đã đạt hạn mức.
5. **Đa ngôn ngữ:** mọi nhãn qua UI bundle; bố cục chịu được chuỗi dài (tiếng Đức/Việt) và chữ CJK **[Đề xuất]**.
6. **Tôn trọng riêng tư:** hỏi consent rõ ràng, có lựa chọn từ chối.

## 2. Danh sách màn hình

### A. Ứng dụng công khai (Du khách)

| Mã | Màn hình | Mục đích |
|---|---|---|
| P-01 | Splash | Hiển thị logo, tiến trình tải ban đầu |
| P-02 | Chọn ngôn ngữ | Chọn vi, en, zh, ja, ko hoặc ngôn ngữ khác |
| P-03 | Hỏi đồng ý analytics | Cho phép hoặc từ chối thu thập |
| P-04 | Bản đồ chính | Bản đồ, POI, vị trí người dùng, nút định vị |
| P-05 | Thẻ chi tiết POI | Tên, mô tả, ảnh, thực đơn, nghe/dừng thuyết minh |
| P-06 | Bộ phát thuyết minh | Thanh/popup hiển thị POI đang đọc, dừng, đóng |
| P-07 | Cài đặt | Ngôn ngữ, chế độ bản đồ, quyền riêng tư |
| P-08 | Gói offline | Danh sách pack bản đồ và gói ngôn ngữ, tải, cập nhật, xóa, trạng thái |
| P-09 | Trạng thái mạng/lỗi | Thông báo offline, thử lại, hết quota |

### B. Cổng chủ quán

| Mã | Màn hình | Mục đích |
|---|---|---|
| O-01 | Đăng ký chủ quán | Form đăng ký kèm CCCD |
| O-02 | Đăng nhập | Đăng nhập chung với admin |
| O-03 | Trạng thái đăng ký | Chờ duyệt, đã duyệt, bị từ chối kèm ghi chú |
| O-04 | Dashboard chủ quán | Tổng quan quán, số liệu của mình |
| O-05 | Danh sách POI của tôi | Các quán đang sở hữu |
| O-06 | Form POI | Sửa thông tin, ảnh, nút AI cải thiện mô tả, số lượt còn lại |
| O-07 | Thực đơn | Thêm, sửa món |
| O-08 | Submissions | Danh sách bài gửi và trạng thái duyệt |
| O-09 | Thông báo | Chuông, danh sách, trang chi tiết |

### C. Admin Dashboard

| Mã | Màn hình | Mục đích |
|---|---|---|
| A-01 | Đăng nhập | Cookie httpOnly |
| A-02 | Tổng quan | Số liệu chính, cảnh báo |
| A-03 | Quản lý POI | Bảng, lọc, tạo, sửa, bật/tắt, xóa |
| A-04 | Chi tiết/Form POI | Văn bản, ảnh, tọa độ, bán kính, độ ưu tiên |
| A-05 | Tác vụ audio | Thanh tiến độ SSE, Pause, Resume, Cancel |
| A-06 | Quản lý menu | CRUD món |
| A-07 | Quản lý người dùng | CRUD, gán role |
| A-08 | Quản lý role | Chọn tập quyền |
| A-09 | Duyệt đăng ký chủ quán | Danh sách, chi tiết, duyệt/từ chối kèm ghi chú |
| A-10 | Duyệt submission | So sánh đề xuất, duyệt/từ chối |
| A-11 | Analytics | Biểu đồ giờ/ngày, số online ẩn danh |
| A-12 | Quan sát vị trí runtime | Cửa sổ quan sát |
| A-13 | Audit log | Bảng nhật ký |
| A-14 | Hồ sơ/Đổi mật khẩu | Tài khoản cá nhân |

## 3. Mô tả luồng giao diện

### 3.1 Luồng khách lần đầu
Mở app, hiện **Splash** (P-01). Sau đó hiện **Chọn ngôn ngữ** (P-02). Chọn xong, nếu chưa từng trả lời, hiện **Hỏi đồng ý** (P-03). Trong lúc này app tải dữ liệu nền. Khi đủ dữ liệu, vào **Bản đồ chính** (P-04). Từ đây du khách có thể chạm POI để mở **Thẻ chi tiết** (P-05), hoặc đi bộ để **Bộ phát thuyết minh** (P-06) tự bật lên khi vào vùng POI.

### 3.2 Luồng khách quay lại
Mở app, Splash rất ngắn vì dữ liệu cũ đã có trong máy, vào thẳng Bản đồ. Ngôn ngữ đã chọn được nhớ nên bỏ qua bước chọn.

### 3.3 Luồng thuyết minh tự động
Du khách đang ở Bản đồ chính. Khi vào vùng POI đủ 3 giây, bộ phát xuất hiện ở dưới màn hình và bắt đầu đọc. Có nút dừng/đóng. Khi đọc xong, bộ phát tự đóng. Nếu đang chờ audio phải tạo (2–8 giây), bộ phát hiển thị trạng thái "đang chuẩn bị" thay vì im lặng **[Đề xuất]**.

### 3.4 Luồng đổi ngôn ngữ
Từ Bản đồ, mở **Cài đặt** (P-07), chọn ngôn ngữ khác. Giao diện hiển thị trạng thái đang chuẩn bị, vẫn dùng ngôn ngữ cũ (hoặc tiếng Anh) cho đến khi cả nội dung và nhãn UI đều sẵn sàng, rồi đổi cùng lúc.

### 3.5 Luồng tải gói offline
Từ Cài đặt, mở **Gói offline** (P-08). Thấy hai khối: gói bản đồ (Quận 4, TP.HCM) và gói của ngôn ngữ hiện tại. Bấm tải, hiển thị 4 bước lần lượt: bản đồ, POI, ảnh, audio, mỗi bước có tiến độ. Nếu hết dung lượng, hiển thị thông báo và app tự dọn cache tạm. Xong, hiển thị "đã sẵn sàng offline". Nếu có phiên bản mới hiển thị "có bản cập nhật"; nếu lỗi checksum hiển thị "cần sửa gói".

### 3.6 Luồng chủ quán
**Đăng ký** (O-01), sau đó **Đăng nhập** (O-02). Vì chưa được duyệt, chủ quán được đưa tới **Trạng thái đăng ký** (O-03) và chỉ xem được trang này cùng thông báo. Khi admin duyệt, chủ quán nhận thông báo, lần đăng nhập sau vào **Dashboard** (O-04). Từ đó vào danh sách POI (O-05), mở form (O-06), bấm AI cải thiện mô tả, bấm gửi. Bài gửi hiện ở **Submissions** (O-08) với trạng thái chờ duyệt. Kết quả duyệt xuất hiện ở **Thông báo** (O-09).

### 3.7 Luồng admin duyệt
Đăng nhập (A-01), vào **Tổng quan** (A-02) với số lượng đơn chờ. Mở **Duyệt đăng ký** (A-09) hoặc **Duyệt submission** (A-10), xem chi tiết, chọn duyệt hoặc từ chối (từ chối bắt buộc nhập ghi chú). Quay lại danh sách.

### 3.8 Luồng admin sửa POI
Mở **Quản lý POI** (A-03), chọn POI, vào **Form POI** (A-04), lưu. Giao diện thông báo "đang sinh audio", chuyển sang **Tác vụ audio** (A-05) để xem tiến độ. POI chuyển trạng thái hoạt động trở lại khi xong.

## 4. Bố cục từng màn hình chính (mô tả)

### P-04 Bản đồ chính
- Toàn màn hình là bản đồ.
- Góc trên: thanh nhỏ hiển thị trạng thái (online/offline, chế độ bản đồ) và nút cài đặt.
- Các điểm POI dạng ghim; ghim POI đang thuyết minh được làm nổi bật.
- Góc dưới phải: nút định vị.
- Dưới cùng: vùng dành cho bộ phát thuyết minh (ẩn khi không phát).

### P-05 Thẻ chi tiết POI
- Dạng bảng trượt từ dưới lên.
- Từ trên xuống: dải ảnh, tên, nhãn "nội dung thay thế" nếu `is_fallback`, mô tả, nút nghe, thực đơn (món và giá).

### P-08 Gói offline
- Mỗi gói là một thẻ gồm tên, dung lượng, phiên bản, nút hành động chính (Tải / Cập nhật / Sửa / Xóa) và thanh tiến độ.

### A-05 Tác vụ audio
- Danh sách tác vụ, mỗi dòng có POI, ngôn ngữ, trạng thái (màu theo trạng thái), thanh tiến độ, nút Pause/Resume/Cancel.

## 5. Trạng thái giao diện cần xử lý

| Tình huống | Hiển thị |
|---|---|
| Đang tải lần đầu | Splash với tiến trình |
| Mất mạng | Nhãn "offline", vẫn dùng dữ liệu đã lưu |
| Nội dung dùng ngôn ngữ thay thế | Nhãn nhỏ trên thẻ POI |
| Từ chối quyền định vị | Hướng dẫn bật quyền; vẫn xem bản đồ và chọn POI thủ công |
| Định vị không đạt trong 15 giây | Thông báo, cho thử lại |
| Hạn mức AI hết | Vô hiệu hóa nút, hiển thị thời điểm reset |
| 429 từ on-demand | Chờ và thử lại ngầm, không báo lỗi gắt |
| Hết dung lượng khi tải gói | Thông báo và dọn tự động |
| Owner chưa xác minh | Chỉ thấy O-03 và thông báo |
| Thiếu quyền (admin) | Ẩn mục menu hoặc hiện trang 403 |

## 6. Khả năng tiếp cận và hiển thị (đề xuất)

- Mọi nút có nhãn văn bản hoặc `aria-label`.
- Thuyết minh có thể dừng bằng một chạm; hiển thị phụ đề văn bản mô tả POI.
- Độ tương phản đạt WCAG AA; cỡ chữ tối thiểu 14 px.
- Vùng chạm tối thiểu 44 px.

## 7. Màu sắc và nhận diện (theo tài liệu thuyết trình)

Màu chủ đạo cam đậm (`#e65100`), màu nhấn xanh ngọc (`#00838f`), nền sáng, chữ Segoe UI/hệ thống. Đây là phong cách trang trình bày; có thể dùng làm tham chiếu cho app.
