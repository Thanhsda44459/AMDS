# 08. Đặc Tả UI/UX — LinhUngGuide

Tài liệu mô tả từng màn hình và luồng chuyển màn hình bằng lời, cho ba nhóm giao diện: Web app khách tham quan, giao diện nhân viên, và admin dashboard.

## 1. Web App — Khách tham quan

### 1.1. Màn hình "Cổng vào" (Entry / Paywall)
Là màn hình đầu tiên khách nhìn thấy ngay sau khi quét QR, khi chưa có access token hợp lệ. Bố cục đơn giản, gồm: logo/tên chùa ở trên cùng, một đoạn giới thiệu ngắn về app, và hai nút lớn dễ bấm bằng ngón tay cái: **"Thanh toán trực tuyến"** và **"Thanh toán tiền mặt"**. Không có menu điều hướng nào khác ở màn hình này, để tránh khách thoát ra ngoài luồng thanh toán bắt buộc.

### 1.2. Màn hình "Đang chờ thanh toán" (Payment Pending)
Xuất hiện sau khi khách chọn thanh toán online và quay lại từ Payoo, hoặc sau khi khách chọn tiền mặt và đang chờ nhân viên xác nhận. Hiển thị một biểu tượng đang tải (spinner), thông báo trạng thái rõ ràng ("Đang xác nhận thanh toán, vui lòng chờ trong giây lát" hoặc "Vui lòng đưa mã số phiên cho nhân viên tại quầy"), và với luồng tiền mặt có hiển thị to, rõ `session_id`/mã ngắn để khách dễ đọc và đưa cho nhân viên. Với luồng online, màn hình tự động kiểm tra lại trạng thái theo chu kỳ ngắn mà không cần khách thao tác gì thêm.

### 1.3. Màn hình chính — Bản đồ tham quan (Map Home)
Màn hình trung tâm của app sau khi xác thực thành công. Gồm:
- Bản đồ chiếm phần lớn diện tích màn hình, hiển thị: chấm định vị vị trí hiện tại của khách, các icon POI (icon POI trong bán kính gần được làm nổi bật bằng màu sắc/kích thước khác biệt so với POI ở xa).
- Góc trên bên phải: biểu tượng hình tròn nhỏ để chọn ngôn ngữ — bấm vào mở ra danh sách cuộn dọc gồm tối thiểu 15 ngôn ngữ, mỗi ngôn ngữ hiển thị kèm quốc kỳ/tên bản ngữ để dễ nhận diện.
- Góc dưới bên phải: nút nổi (floating action button) mở khung chat với chatbot.
- Thanh điều hướng dưới cùng (tuỳ chọn): chuyển nhanh giữa "Bản đồ", "Lộ trình gợi ý", "Chat".

### 1.4. Thẻ thông tin POI (POI Detail Card)
Xuất hiện dạng bottom sheet (trượt lên từ dưới) khi khách chạm vào một icon POI trên bản đồ, hoặc tự động mở khi khách bước vào phạm vi geofence của POI đó (theo UC-04). Nội dung gồm: tên POI theo ngôn ngữ đang chọn, ảnh minh hoạ, đoạn mô tả văn bản có thể cuộn nếu dài, và một nút phát/tạm dừng audio lớn, dễ thấy. Khi khách đổi ngôn ngữ trong lúc thẻ này đang mở, toàn bộ nội dung (văn bản + audio) cập nhật ngay lập tức mà không đóng thẻ lại.

### 1.5. Màn hình Lộ trình gợi ý (Route Suggestion)
Hiển thị danh sách các POI theo thứ tự đề xuất dưới dạng các thẻ xếp dọc, mỗi thẻ có số thứ tự, tên POI, ảnh thu nhỏ, và khoảng cách ước tính tới điểm tiếp theo. Khách có thể chạm vào một thẻ để nhảy thẳng tới vị trí POI đó trên bản đồ. Có một điều khiển (ví dụ thanh trượt hoặc bộ chọn số) để khách tự tuỳ chỉnh số lượng POI muốn có trong lộ trình.

### 1.6. Khung Chat (Chatbot)
Mở dạng cửa sổ trượt lên chiếm khoảng 2/3 màn hình (để khách vẫn thấy một phần bản đồ phía sau, tạo cảm giác liền mạch). Gồm: lịch sử hội thoại trong phiên hiện tại (không cần đăng nhập lưu lại giữa các lượt tham quan khác nhau), ô nhập văn bản ở dưới cùng, và biểu tượng gửi. Câu trả lời của chatbot xuất hiện dạng bong bóng chat, kèm ảnh minh hoạ (nếu có) hiển thị ngay bên dưới đoạn text trả lời. Trong lúc chờ phản hồi, hiển thị hiệu ứng "đang gõ..." (typing indicator) để khách biết hệ thống đang xử lý.

### 1.7. Nguyên tắc thiết kế UI/UX chung cho khách
- Ưu tiên thao tác một tay: các nút quan trọng (chọn ngôn ngữ, mở chat, phát audio) đặt trong tầm với của ngón tay cái trên màn hình lớn.
- Tương phản màu sắc rõ ràng, cỡ chữ đủ lớn để đọc ngoài trời nắng — phù hợp bối cảnh tham quan ngoài trời tại chùa.
- Giao diện tối giản, hạn chế văn bản hướng dẫn dài dòng, ưu tiên biểu tượng (icon) trực quan để giảm rào cản ngôn ngữ ngay cả trước khi khách chọn được ngôn ngữ ưa thích.
- Trạng thái tải (loading state) luôn được thể hiện rõ ràng ở mọi thao tác gọi mạng (phát audio, gửi câu hỏi chatbot) để khách không nhầm tưởng app bị treo.

## 2. Giao diện Nhân viên (Staff)

### 2.1. Màn hình Đăng nhập
Form đơn giản gồm ô tên đăng nhập, mật khẩu, nút đăng nhập — dùng chung layout với màn hình đăng nhập admin nhưng sau khi đăng nhập sẽ điều hướng theo `role` được trả về.

### 2.2. Màn hình Xác nhận thanh toán tiền mặt
Danh sách các phiên đang ở trạng thái chờ (`pending`), mỗi dòng hiển thị `session_id`, thời gian khách bắt đầu chờ, và một nút "Xác nhận đã thu tiền". Khi nhân viên bấm xác nhận, hệ thống hiển thị ngay mã ngắn (shortened_code) to, rõ ràng trên màn hình để nhân viên đọc/đưa cho khách, kèm nút "Sao chép" để tiện thao tác nếu có màn hình phụ hiển thị cho khách xem trực tiếp.

## 3. Admin Dashboard

### 3.1. Màn hình Đăng nhập
Tương tự staff, nhưng chỉ tài khoản có `role = admin` mới được điều hướng vào các trang quản trị đầy đủ.

### 3.2. Trang Tổng quan (Overview / Monitoring Dashboard)
Trang mặc định sau khi admin đăng nhập. Bố cục dạng lưới các thẻ số liệu (cards): số phiên đang hoạt động, doanh thu hôm nay theo từng hình thức thanh toán, tình trạng hoạt động của backend (biểu tượng xanh/vàng/đỏ), số câu hỏi chatbot đã xử lý. Bên dưới là các biểu đồ đơn giản (dạng cột/đường) thể hiện xu hướng lượt khách theo giờ trong ngày và danh sách top POI được xem nhiều nhất. Toàn bộ số liệu tự làm mới theo chu kỳ ngắn mà không cần admin bấm tải lại trang.

### 3.3. Trang Quản lý POI
Danh sách POI dạng bảng, mỗi dòng gồm: tên, trạng thái hoạt động (đang hiển thị/đã ẩn), trạng thái pipeline dịch/TTS (một cụm chấm màu nhỏ thể hiện số ngôn ngữ đã hoàn tất trên tổng số ngôn ngữ). Có nút "Thêm POI mới" mở ra một form chi tiết gồm: tên, mô tả gốc (khung nhập văn bản dài), vị trí (nhập toạ độ trực tiếp hoặc chọn điểm trên một bản đồ nhỏ nhúng trong form), bán kính phạm vi, tải ảnh thumbnail. Sau khi lưu, dòng POI đó hiển thị trạng thái "Đang xử lý dịch/TTS" và tự cập nhật thành "Sẵn sàng" khi pipeline hoàn tất, không cần admin tải lại trang thủ công.

### 3.4. Trang Quản lý tài khoản
Danh sách tài khoản nhân viên/quản trị viên, kèm nút tạo tài khoản mới với việc chọn vai trò (`admin`/`staff`) và khả năng khoá/mở khoá một tài khoản.

### 3.5. Nguyên tắc thiết kế UI/UX cho admin/staff
- Ưu tiên hiển thị dữ liệu dạng bảng, số liệu rõ ràng, phù hợp thao tác trên máy tính để bàn/laptop (khác với web app khách vốn ưu tiên di động).
- Mọi hành động có tác động dữ liệu quan trọng (xoá/ẩn POI, xác nhận thanh toán) đều có bước xác nhận lại (confirm dialog) để tránh thao tác nhầm.
- Trạng thái xử lý bất đồng bộ (pipeline dịch/TTS) luôn được phản ánh trực quan để admin không cần đoán hệ thống có đang chạy hay không.
