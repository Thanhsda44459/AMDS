# 01. Phạm Vi Đồ Án — Hệ Thống Hướng Dẫn Tham Quan Thông Minh Chùa Linh Ứng

## 1. Tên đồ án
**Hệ thống hướng dẫn tham quan thông minh tích hợp GPS và trợ lý ảo AI tại Chùa Linh Ứng** (tên gọi tắt trong tài liệu: **LinhUngGuide**).

## 2. Bối cảnh và lý do thực hiện
Chùa Linh Ứng (Đà Nẵng) đón lượng lớn du khách trong và ngoài nước mỗi năm, nhưng phần lớn khách tham quan độc lập (không đi theo tour có hướng dẫn viên) hiện gặp hai vấn đề chính:

1. Không có hướng dẫn đa ngôn ngữ tại chỗ — khách nước ngoài khó hiểu ý nghĩa lịch sử, kiến trúc, tôn giáo của từng điểm tham quan (POI — Point of Interest).
2. Không có kênh hỏi đáp tức thời — khi có thắc mắc, khách phải tìm nhân viên hoặc tra cứu thủ công, gây gián đoạn trải nghiệm.

Đồ án xây dựng một web app (PWA) chạy trên trình duyệt di động, cho phép khách tự định vị bằng GPS, nghe/đọc thuyết minh đa ngôn ngữ tại từng POI, và trò chuyện với một chatbot AI (dạng RAG — Retrieval-Augmented Generation) để được giải đáp thắc mắc bằng ngôn ngữ tự nhiên.

## 3. Mục tiêu của đồ án
- Xây dựng trải nghiệm thuyết minh tự động, sống động, không cần hướng dẫn viên con người.
- Tự động phát nội dung tương ứng với vị trí hiện tại của khách nhờ GPS/geofencing.
- Hỗ trợ tối thiểu 15 ngôn ngữ cho cả văn bản và âm thanh, bao gồm tiếng Việt.
- Tích hợp chatbot RAG trả lời câu hỏi tự do của khách dựa trên kho tri thức của chùa.
- Cho phép thu phí truy cập qua hai kênh: thanh toán trực tuyến (Payoo) và thanh toán tiền mặt tại chỗ (qua nhân viên).
- Cung cấp trang quản trị (admin dashboard) để nhân viên/quản trị viên quản lý dữ liệu POI, phiên tham quan, và một bảng giám sát (monitoring dashboard) theo thời gian thực.

## 4. Phạm vi trong đồ án (In-scope)
| Hạng mục | Mô tả |
|---|---|
| Web app khách tham quan | PWA responsive, chạy trên trình duyệt di động (Android/iOS), không cần cài đặt từ store |
| Bản đồ & định vị GPS | Hiển thị vị trí khách theo thời gian thực, đánh dấu các POI trong bán kính lân cận |
| Thuyết minh đa ngôn ngữ | Văn bản + audio cho từng POI, tối thiểu 15 ngôn ngữ, chuyển ngôn ngữ tức thời qua biểu tượng chọn ngôn ngữ |
| Gợi ý lộ trình | Đề xuất tuyến tham quan gồm nhiều POI theo thứ tự hợp lý |
| Chatbot AI (RAG) | Trả lời câu hỏi tự do bằng ngôn ngữ tự nhiên, dựa trên dữ liệu POI và tài liệu bổ sung của chùa |
| Thanh toán truy cập | Quét mã QR tại cổng vào → thanh toán online (Payoo) hoặc tiền mặt (qua nhân viên) → nhận access token |
| Data pipeline dịch & TTS | Tự động dịch mô tả POI sang 15+ ngôn ngữ và sinh audio tương ứng khi nội dung được tạo/cập nhật |
| Admin dashboard | Tạo/sửa/xoá POI, quản lý phiên (session), quản lý xác nhận thanh toán tiền mặt |
| Monitoring dashboard | Theo dõi tình trạng hệ thống và số liệu sử dụng theo thời gian thực |

## 5. Ngoài phạm vi đồ án (Out-of-scope)
- Ứng dụng native cài đặt qua App Store / Google Play (chỉ làm web app/PWA).
- Chức năng đặt vé theo đoàn, quản lý tour du lịch, CRM khách hàng.
- Thanh toán quốc tế (thẻ Visa/Mastercard nước ngoài) — chỉ dùng cổng Payoo nội địa trong phạm vi đồ án; có thể mở rộng sau.
- Chức năng mạng xã hội (đánh giá, bình luận công khai, chia sẻ ảnh cộng đồng).
- Chế độ hoạt động hoàn toàn ngoại tuyến (offline-first) dài hạn — chỉ triển khai cache cơ bản để tăng tốc độ tải, chưa làm đồng bộ dữ liệu ngoại tuyến đầy đủ (được ghi nhận là "Future considerations" trong PRD gốc).
- Ứng dụng riêng cho hướng dẫn viên chuyên nghiệp hoặc công cụ soạn thảo nội dung nâng cao (rich content editor) ngoài admin dashboard cơ bản.

## 6. Đối tượng người dùng (Stakeholders)
- **Khách tham quan (Visitor/Guest)**: người dùng cuối, dùng web app trên điện thoại cá nhân.
- **Nhân viên (Staff)**: nhân viên tại quầy/cổng, xác nhận thanh toán tiền mặt, hỗ trợ khách.
- **Quản trị viên (Admin)**: quản lý toàn bộ dữ liệu hệ thống, theo dõi vận hành, cấu hình.
- **Ban quản lý chùa Linh Ứng**: chủ đầu tư/đơn vị vận hành, quan tâm đến số liệu sử dụng và doanh thu.

## 7. Ràng buộc của đồ án
- Thời gian thực hiện giới hạn trong khuôn khổ một học kỳ/đồ án tốt nghiệp, do đó công nghệ được chọn ưu tiên tính ổn định, tài liệu phong phú, chi phí vận hành thấp (ưu tiên dịch vụ có gói miễn phí/giá rẻ cho môi trường thử nghiệm).
- Chỉ triển khai thử nghiệm (pilot) tại một địa điểm — Chùa Linh Ứng — chưa tính đến việc nhân rộng sang nhiều địa điểm khác trong phạm vi đồ án (kiến trúc có tính mở rộng nhưng chưa hiện thực hoá đa tenant).
- Cổng thanh toán Payoo yêu cầu đăng ký tài khoản doanh nghiệp; trong môi trường phát triển/demo sẽ dùng môi trường sandbox của Payoo.

## 8. Mốc thời gian tham chiếu
Theo Launch Plan trong PRD gốc: mốc **Pilot** (kiểm thử sơ bộ tại hiện trường) dự kiến **16/05/2025**. Đồ án sẽ bám theo mốc này làm cột mốc bàn giao bản demo có thể kiểm thử thực tế.
