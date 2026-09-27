# 02. Yêu Cầu Hệ Thống — LinhUngGuide

## 1. Yêu cầu chức năng (Functional Requirements)

### 1.1. Nhóm: Truy cập & Thanh toán
| Mã | Yêu cầu | Mô tả chi tiết |
|---|---|---|
| FR-01 | Quét QR vào cổng | Khách quét mã QR đặt tại cổng chùa để mở web app trên trình duyệt di động |
| FR-02 | Thanh toán trực tuyến | Khách chọn "Pay Now (Online)", hệ thống tạo liên kết thanh toán qua Payoo, khách hoàn tất thanh toán và được cấp quyền truy cập |
| FR-03 | Thanh toán tiền mặt | Khách chọn "Pay with Cash", nhận mã ngắn (shortened code), đưa mã cho nhân viên, nhân viên xác nhận đã thu tiền, hệ thống đổi mã lấy access token cho khách |
| FR-04 | Cấp và xác thực access token | Sau khi thanh toán thành công (bằng bất kỳ hình thức nào), hệ thống cấp access token; mọi tính năng trong app chỉ hoạt động khi token hợp lệ |
| FR-05 | Hết hạn phiên | Access token có thời hạn sử dụng tương ứng với một lượt tham quan (ví dụ theo ngày); hệ thống từ chối truy cập khi token hết hạn |

### 1.2. Nhóm: Bản đồ & Định vị
| Mã | Yêu cầu | Mô tả chi tiết |
|---|---|---|
| FR-06 | Hiển thị vị trí khách | App lấy toạ độ GPS của thiết bị và hiển thị vị trí khách trên bản đồ số của khuôn viên chùa |
| FR-07 | Hiển thị POI lân cận | Hệ thống làm nổi bật các POI nằm trong bán kính cấu hình sẵn quanh vị trí hiện tại |
| FR-08 | Tự động phát nội dung theo vị trí | Khi khách bước vào phạm vi (range of proximity) của một POI, nội dung thuyết minh tương ứng được gợi ý/tự phát mà không cần thao tác thủ công |
| FR-09 | Gợi ý lộ trình tham quan | Hệ thống đề xuất một chuỗi POI theo thứ tự hợp lý kèm chỉ đường giữa các điểm; số lượng và thứ tự POI trong lộ trình có thể tuỳ chỉnh |

### 1.3. Nhóm: Nội dung đa ngôn ngữ
| Mã | Yêu cầu | Mô tả chi tiết |
|---|---|---|
| FR-10 | Xem thông tin POI | Khách chạm vào một POI trên bản đồ để xem mô tả dạng văn bản và nghe audio thuyết minh |
| FR-11 | Chuyển đổi ngôn ngữ | Khách chọn ngôn ngữ ưa thích qua biểu tượng ở góc trên bên phải; toàn bộ nội dung văn bản/audio đang hiển thị cập nhật theo ngôn ngữ mới ngay lập tức |
| FR-12 | Hỗ trợ tối thiểu 15 ngôn ngữ | Toàn bộ mô tả POI phải có sẵn bản dịch cho tối thiểu 15 ngôn ngữ, bao gồm tiếng Việt |
| FR-13 | Data pipeline dịch & TTS tự động | Khi nội dung một POI được tạo mới hoặc chỉnh sửa trong admin dashboard, hệ thống tự động dịch văn bản sang toàn bộ ngôn ngữ được hỗ trợ và sinh file audio tương ứng, không cần thao tác thủ công cho từng ngôn ngữ |

### 1.4. Nhóm: Chatbot AI (RAG)
| Mã | Yêu cầu | Mô tả chi tiết |
|---|---|---|
| FR-14 | Đặt câu hỏi tự do | Khách nhập câu hỏi bằng ngôn ngữ tự nhiên (ngôn ngữ bất kỳ trong danh sách hỗ trợ) vào khung chat |
| FR-15 | Trả lời dựa trên tri thức của chùa | Chatbot tìm kiếm thông tin liên quan trong kho tri thức (mô tả POI và tài liệu bổ sung), tổng hợp và trả lời bằng ngôn ngữ mà khách đã dùng để hỏi |
| FR-16 | Đính kèm hình ảnh minh hoạ | Câu trả lời của chatbot có thể kèm hình ảnh liên quan đến POI được nhắc tới, nếu có |
| FR-17 (tương lai) | Lưu cache câu hỏi thường gặp | Lưu lại các cặp hỏi-đáp gần đây để tăng tốc độ phản hồi cho câu hỏi lặp lại (ghi nhận trong PRD là "Future considerations", không bắt buộc ở bản MVP) |

### 1.5. Nhóm: Quản trị (Admin/Staff)
| Mã | Yêu cầu | Mô tả chi tiết |
|---|---|---|
| FR-18 | Đăng nhập quản trị | Nhân viên/quản trị viên đăng nhập bằng tài khoản riêng, phân quyền theo vai trò |
| FR-19 | Quản lý POI | Tạo, sửa, xoá (hoặc vô hiệu hoá) thông tin POI: toạ độ, bán kính, mô tả gốc, hình ảnh thumbnail |
| FR-20 | Quản lý phiên tham quan | Tạo phiên (session) khi khách thanh toán tiền mặt, sinh mã claim code, theo dõi trạng thái thanh toán |
| FR-21 | Quản lý dữ liệu chung | Chỉnh sửa thông tin cấu hình hệ thống liên quan tới nội dung (không bao gồm cấu hình hạ tầng) |

### 1.6. Nhóm: Giám sát hệ thống
| Mã | Yêu cầu | Mô tả chi tiết |
|---|---|---|
| FR-22 | Bảng giám sát thời gian thực | Hiển thị tình trạng hoạt động của các dịch vụ backend (uptime, độ trễ, tỉ lệ lỗi) |
| FR-23 | Thống kê sử dụng | Hiển thị số lượt truy cập, số phiên đang hoạt động, POI được xem nhiều nhất, số câu hỏi chatbot đã xử lý |
| FR-24 (tương lai) | Nhật ký hoạt động thời gian thực | Ghi log chi tiết hành vi người dùng để phục vụ phân tích sau này (ghi nhận là "Future considerations" trong PRD) |

## 2. Yêu cầu phi chức năng (Non-Functional Requirements)

| Mã | Danh mục | Yêu cầu |
|---|---|---|
| NFR-01 | Hiệu năng | Thời gian tải trang lần đầu (sau khi thanh toán) không quá 3 giây trên mạng 4G trung bình; nội dung POI hiển thị tức thời (< 300ms) vì toàn bộ dữ liệu đã được nạp sẵn xuống frontend sau khi xác thực |
| NFR-02 | Hiệu năng chatbot | Thời gian phản hồi trung bình của chatbot (từ lúc gửi câu hỏi đến khi nhận câu trả lời đầy đủ) không quá 5 giây |
| NFR-03 | Khả năng tương thích | Hoạt động ổn định trên các trình duyệt di động phổ biến: Chrome, Safari, Samsung Internet, trên cả Android và iOS, không yêu cầu cài đặt ứng dụng |
| NFR-04 | Khả năng mở rộng | Kiến trúc backend cho phép mở rộng theo chiều ngang (horizontal scaling) để đáp ứng lượng truy cập tăng vào mùa cao điểm lễ hội |
| NFR-05 | Bảo mật dữ liệu | Access token và thông tin thanh toán được truyền qua HTTPS; mật khẩu tài khoản quản trị được băm (hash) trước khi lưu trữ |
| NFR-06 | Bảo mật thanh toán | Không lưu trữ trực tiếp thông tin thẻ/tài khoản ngân hàng của khách trong hệ thống; toàn bộ xử lý nhạy cảm uỷ quyền cho cổng Payoo |
| NFR-07 | Độ chính xác GPS | Sai số định vị hiển thị trên bản đồ không vượt quá phạm vi cho phép của thiết bị di động phổ thông (thường 5–15m ngoài trời); hệ thống có cơ chế làm mượt (smoothing) để tránh vị trí "nhảy" liên tục |
| NFR-08 | Chất lượng dịch thuật & giọng đọc | Bản dịch và giọng đọc tổng hợp phải tự nhiên, dễ hiểu, đúng ngữ cảnh văn hoá – tôn giáo; có bước rà soát thủ công đối với nội dung quan trọng trước khi công bố |
| NFR-09 | Khả dụng (Availability) | Hệ thống đảm bảo tỉ lệ hoạt động tối thiểu 99% trong giờ mở cửa của chùa |
| NFR-10 | Khả năng quan sát (Observability) | Toàn bộ lỗi hệ thống được ghi log tập trung và có cảnh báo khi tỉ lệ lỗi vượt ngưỡng |
| NFR-11 | Đa ngôn ngữ giao diện | Bản thân giao diện người dùng (nút bấm, nhãn, thông báo) cũng được đa ngôn ngữ hoá, không chỉ nội dung thuyết minh POI |
| NFR-12 | Khả năng bảo trì | Mã nguồn tuân theo cấu trúc module rõ ràng, có tài liệu API, để nhóm phát triển hoặc người kế thừa dễ dàng bảo trì sau khi đồ án kết thúc |
| NFR-13 | Chi phí vận hành | Ưu tiên các dịch vụ có gói miễn phí/giá rẻ trong giai đoạn thử nghiệm (pilot), hạn chế chi phí vượt ngân sách đồ án |
| NFR-14 | Khả năng dùng lại dữ liệu | Vì dữ liệu POI được nạp toàn bộ về frontend một lần sau xác thực, hệ thống phải đảm bảo dung lượng payload hợp lý (nén dữ liệu, không nạp toàn bộ audio ngay mà chỉ nạp theo yêu cầu) để tránh tải chậm ban đầu |

## 3. Ma trận truy vết yêu cầu (tóm tắt)
Mỗi yêu cầu chức năng ở trên đều được ánh xạ tới ít nhất một use case trong tài liệu `04_Use_Cases.md` và một hoặc nhiều endpoint API trong `07_API_Specification.md`, đảm bảo không có yêu cầu nào bị "mồ côi" (không được hiện thực hoá) hoặc thiết kế dư thừa không phục vụ yêu cầu nào.
