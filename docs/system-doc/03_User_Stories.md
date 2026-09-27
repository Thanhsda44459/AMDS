# 03. User Stories — LinhUngGuide

Định dạng: **Là [vai trò], tôi muốn [hành động], để [giá trị/lý do].**
Mỗi story kèm tiêu chí chấp nhận (Acceptance Criteria — AC) và liên kết tới yêu cầu chức năng (FR) tương ứng trong `02_Requirements.md`.

## 1. Vai trò: Khách tham quan (Visitor)

**US-01 — Vào cổng bằng QR**
Là một khách tham quan, tôi muốn quét mã QR tại cổng chùa, để mở ngay web app mà không cần tìm kiếm hay tải ứng dụng.
- AC1: Quét QR mở đúng địa chỉ web app trên trình duyệt mặc định của điện thoại.
- AC2: Nếu khách chưa thanh toán, app hiển thị ngay màn hình yêu cầu thanh toán.
- Liên quan: FR-01.

**US-02 — Thanh toán trực tuyến**
Là một khách tham quan, tôi muốn thanh toán trực tuyến bằng ví điện tử/ngân hàng qua Payoo, để không phải xếp hàng hay mang tiền mặt.
- AC1: Khách được chuyển tới trang thanh toán Payoo trong vòng 2 giây sau khi bấm "Pay Now (Online)".
- AC2: Sau khi thanh toán thành công, khách tự động quay lại app và được cấp quyền sử dụng ngay.
- AC3: Nếu thanh toán chưa hoàn tất, app hiển thị trạng thái "đang chờ" và tự thử lại theo chu kỳ hợp lý.
- Liên quan: FR-02, FR-04.

**US-03 — Thanh toán tiền mặt**
Là một khách tham quan không có phương tiện thanh toán trực tuyến, tôi muốn trả tiền mặt tại quầy, để vẫn sử dụng được app.
- AC1: Khách nhận được một mã ngắn, dễ đọc để đưa cho nhân viên.
- AC2: Sau khi nhân viên xác nhận đã thu tiền, khách nhập mã và được cấp quyền truy cập ngay.
- Liên quan: FR-03, FR-04.

**US-04 — Xem vị trí bản thân trên bản đồ**
Là một khách tham quan, tôi muốn thấy vị trí hiện tại của mình trên bản đồ khuôn viên chùa, để không bị lạc đường.
- AC1: Chấm định vị cập nhật theo thời gian thực khi khách di chuyển.
- AC2: Nếu thiết bị từ chối quyền định vị, app hiển thị thông báo hướng dẫn cấp quyền.
- Liên quan: FR-06.

**US-05 — Khám phá POI lân cận**
Là một khách tham quan, tôi muốn thấy những điểm tham quan gần vị trí của mình được làm nổi bật trên bản đồ, để biết nên ghé đâu tiếp theo.
- AC1: POI trong bán kính cấu hình hiển thị icon nổi bật khác với POI ở xa.
- AC2: Chạm vào icon POI mở ra thẻ thông tin chi tiết.
- Liên quan: FR-07.

**US-06 — Tự động nghe thuyết minh khi đến gần**
Là một khách tham quan, tôi muốn nội dung thuyết minh tự động được gợi ý khi tôi bước vào khu vực của một POI, để có trải nghiệm liền mạch như có hướng dẫn viên đi cùng.
- AC1: Khi khách vào phạm vi bán kính của POI, app hiển thị thông báo/gợi ý phát audio.
- AC2: Khách có thể bỏ qua hoặc tắt tính năng tự phát nếu muốn tự điều khiển.
- Liên quan: FR-08.

**US-07 — Đọc & nghe mô tả POI theo ngôn ngữ ưa thích**
Là một khách tham quan nước ngoài, tôi muốn đọc và nghe mô tả POI bằng ngôn ngữ mẹ đẻ của mình, để hiểu trọn vẹn ý nghĩa văn hoá – lịch sử.
- AC1: Danh sách ngôn ngữ có ít nhất 15 lựa chọn.
- AC2: Khi đổi ngôn ngữ, nội dung văn bản và audio đang mở cập nhật ngay mà không cần tải lại trang.
- Liên quan: FR-10, FR-11, FR-12.

**US-08 — Nhận gợi ý lộ trình tham quan**
Là một khách tham quan lần đầu đến chùa, tôi muốn được gợi ý một lộ trình tham quan hợp lý, để không bỏ sót điểm quan trọng và không đi lại lộn xộn.
- AC1: Hệ thống đề xuất tối thiểu một lộ trình mặc định.
- AC2: Khách có thể tuỳ chỉnh số lượng POI trong lộ trình.
- Liên quan: FR-09.

**US-09 — Hỏi chatbot AI**
Là một khách tham quan, tôi muốn hỏi chatbot những câu hỏi tự do (ví dụ "Bức tượng này được xây năm nào?"), để nhận câu trả lời ngay lập tức mà không cần tìm nhân viên.
- AC1: Chatbot trả lời đúng ngôn ngữ mà khách dùng để hỏi.
- AC2: Câu trả lời dựa trên thông tin có thật trong kho tri thức của chùa (không bịa thông tin).
- AC3: Nếu câu hỏi có liên quan tới một POI cụ thể, câu trả lời có thể kèm ảnh minh hoạ.
- Liên quan: FR-14, FR-15, FR-16.

## 2. Vai trò: Nhân viên (Staff)

**US-10 — Xác nhận thanh toán tiền mặt**
Là một nhân viên tại quầy, tôi muốn xác nhận nhanh một giao dịch tiền mặt bằng mã ngắn khách đưa, để khách có thể sử dụng app ngay mà không phải chờ đợi lâu.
- AC1: Nhân viên nhập/xác nhận mã trong giao diện quản trị đơn giản.
- AC2: Hệ thống hiển thị rõ trạng thái "đã xác nhận" sau khi thao tác thành công.
- Liên quan: FR-03, FR-20.

**US-11 — Theo dõi trạng thái phiên đang chờ**
Là một nhân viên, tôi muốn thấy danh sách các phiên đang chờ thanh toán tiền mặt, để không bỏ sót khách đang chờ xác nhận.
- Liên quan: FR-20.

## 3. Vai trò: Quản trị viên (Admin)

**US-12 — Quản lý nội dung POI**
Là một quản trị viên, tôi muốn thêm/sửa thông tin một điểm tham quan (toạ độ, bán kính, mô tả gốc, ảnh), để nội dung trên app luôn cập nhật và chính xác.
- AC1: Sau khi lưu, hệ thống tự động kích hoạt pipeline dịch và sinh audio cho tất cả ngôn ngữ hỗ trợ.
- AC2: Quản trị viên nhận được thông báo khi pipeline hoàn tất hoặc gặp lỗi.
- Liên quan: FR-13, FR-19.

**US-13 — Theo dõi tình trạng hệ thống**
Là một quản trị viên, tôi muốn xem bảng giám sát thời gian thực về tình trạng hệ thống (uptime, lỗi, độ trễ) và số liệu sử dụng, để phát hiện sớm sự cố và đánh giá hiệu quả vận hành.
- AC1: Dashboard cập nhật số liệu theo chu kỳ ngắn (ví dụ mỗi 30 giây hoặc theo thời gian thực).
- AC2: Có cảnh báo trực quan khi một dịch vụ backend gặp sự cố.
- Liên quan: FR-22, FR-23.

**US-14 — Phân quyền tài khoản**
Là một quản trị viên, tôi muốn tạo tài khoản cho nhân viên mới với quyền hạn giới hạn (chỉ xác nhận thanh toán), để đảm bảo an toàn dữ liệu hệ thống.
- Liên quan: FR-18.

## 4. Vai trò: Ban quản lý chùa (gián tiếp, không thao tác trực tiếp trên hệ thống)

**US-15 — Xem báo cáo tổng quan**
Là đại diện ban quản lý, tôi muốn xem báo cáo tổng hợp số lượt khách, doanh thu theo hình thức thanh toán, và các POI được quan tâm nhiều nhất, để đánh giá hiệu quả đầu tư hệ thống.
- Liên quan: FR-23 (thực hiện thông qua quyền xem báo cáo trong admin dashboard, không phải vai trò đăng nhập riêng trong phạm vi đồ án).
