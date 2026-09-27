# 10. Dịch Vụ Bên Ngoài Tích Hợp — LinhUngGuide

Tài liệu liệt kê toàn bộ dịch vụ/API bên thứ ba mà hệ thống phụ thuộc, lý do lựa chọn, cách tích hợp, và phương án dự phòng nếu có.

## 1. Bản đồ số — OpenStreetMap / MapTiler + Leaflet.js

**Vai trò**: Cung cấp nền bản đồ (tile) để hiển thị vị trí khách và các POI trong khuôn viên chùa.

**Lý do chọn thay vì Google Maps**: Google Maps Platform tính phí theo lượt tải bản đồ (map load) khá cao khi lượng khách tăng vào mùa cao điểm; OpenStreetMap là dữ liệu bản đồ mở, miễn phí, đủ chi tiết cho khu vực Đà Nẵng, kết hợp với MapTiler (gói miễn phí cho ứng dụng có lượng truy cập vừa phải) để có tile chất lượng tốt và ổn định hơn tile OSM công cộng thuần tuý. Thư viện hiển thị bản đồ phía frontend là **Leaflet.js** (qua `react-leaflet`) — nhẹ, đơn giản, phù hợp vì khu vực bản đồ chỉ giới hạn trong khuôn viên một địa điểm, không cần các tính năng vector-tile phức tạp của MapLibre GL.

**Cách tích hợp**: Frontend gọi trực tiếp tile server của MapTiler bằng API key công khai (giới hạn theo domain); không đi qua backend, vì đây là tài nguyên tĩnh không nhạy cảm.

**Dự phòng**: Nếu vượt hạn mức miễn phí của MapTiler, hệ thống chuyển sang dùng tile OpenStreetMap công cộng (yêu cầu tuân thủ chính sách sử dụng công bằng — usage policy — của OSM) hoặc tự host tile server bằng dữ liệu OSM tải sẵn cho khu vực Đà Nẵng.

## 2. Cổng thanh toán — Payoo Payment Gateway

**Vai trò**: Xử lý thanh toán trực tuyến (QR, thẻ ATM nội địa, ví điện tử liên kết) cho luồng "Pay Now (Online)".

**Lý do chọn**: Được chỉ định trực tiếp trong PRD gốc; Payoo là cổng thanh toán phổ biến tại Việt Nam, hỗ trợ đa dạng phương thức thanh toán nội địa phù hợp với đối tượng khách trong nước, đồng thời cũng hỗ trợ thanh toán quốc tế cơ bản cho khách du lịch nước ngoài.

**Cách tích hợp**: Backend gọi API tạo liên kết thanh toán của Payoo (REST), truyền kèm `auth_code` làm tham số tham chiếu; Payoo gọi lại (webhook) tới một endpoint nội bộ khi giao dịch hoàn tất, được xác thực bằng chữ ký riêng do Payoo cấp cho tài khoản merchant. Trong môi trường phát triển/demo của đồ án, dùng **môi trường sandbox** do Payoo cung cấp cho merchant thử nghiệm.

**Lưu ý bảo mật**: Hệ thống không bao giờ lưu trữ trực tiếp số thẻ hay thông tin tài khoản ngân hàng của khách; toàn bộ bước nhập thông tin thanh toán diễn ra trên giao diện của Payoo, hệ thống chỉ nhận kết quả thành công/thất bại.

## 3. Dịch thuật tự động — Azure AI Translator

**Vai trò**: Tự động dịch mô tả gốc (tiếng Việt) của mỗi POI sang tối thiểu 15 ngôn ngữ khác, phục vụ FR-13.

**Lý do chọn**: Hỗ trợ hơn 100 ngôn ngữ (thừa đủ so với yêu cầu 15+), chất lượng dịch ổn định cho văn bản mô tả mang tính thông tin (không phải văn học phức tạp), có REST API/SDK dễ gọi bất đồng bộ theo lô (batch), và nằm trong cùng hệ sinh thái Azure với các dịch vụ AI khác đã chọn — giảm số nhà cung cấp cần quản lý.

**Cách tích hợp**: Data pipeline ở backend gọi API Translator theo lô cho toàn bộ danh sách ngôn ngữ mục tiêu mỗi khi một POI được tạo/sửa; kết quả được lưu vào mảng `translations` của bản ghi POI trong MongoDB.

**Kiểm soát chất lượng**: Với nội dung mang ý nghĩa tôn giáo/văn hoá quan trọng, quy trình vận hành khuyến nghị có bước admin xem lại bản dịch tiếng Anh (ngôn ngữ phổ biến nhất) trước khi công bố chính thức, dù bước này không bắt buộc về mặt kỹ thuật để hệ thống hoạt động.

## 4. Chuyển văn bản thành giọng nói — Azure Cognitive Services Speech (Neural TTS)

**Vai trò**: Sinh file audio thuyết minh cho từng bản dịch của mỗi POI.

**Lý do chọn**: Cung cấp giọng đọc neural tự nhiên cho đa số ngôn ngữ trong danh sách hỗ trợ (bao gồm tiếng Việt với giọng đọc chất lượng tốt), có thể tuỳ chỉnh tốc độ đọc/ngữ điệu cơ bản qua SSML, và tích hợp liền mạch với hệ sinh thái Azure.

**Cách tích hợp**: Data pipeline gọi API Speech Synthesis cho từng bản dịch, nhận về file audio (định dạng nén, ví dụ MP3), sau đó tải file này lên Azure Blob Storage và lưu đường dẫn (`audio_url`) vào bản ghi POI tương ứng.

**Dự phòng**: Với các ngôn ngữ hiếm không được Azure Speech hỗ trợ giọng neural chất lượng cao, hệ thống có thể tạm dùng giọng standard hoặc loại bỏ tuỳ chọn audio cho ngôn ngữ đó trong khi vẫn giữ bản dịch văn bản.

## 5. Mô hình AI cho Chatbot RAG — Azure OpenAI Service

**Vai trò**: (a) Sinh vector embedding cho nội dung tri thức và cho câu hỏi của khách; (b) sinh câu trả lời tự nhiên dựa trên ngữ cảnh tìm được.

**Mô hình cụ thể**:
- **text-embedding-3-small** — chuyển văn bản thành vector, dùng cho cả bước lập chỉ mục nội dung và bước xử lý câu hỏi.
- **GPT-4o mini** — mô hình sinh câu trả lời, được chọn vì cân bằng tốt giữa chi phí, tốc độ phản hồi, và chất lượng — phù hợp cho tác vụ hỏi đáp có ngữ cảnh (RAG) với độ phức tạp vừa phải, thay vì cần mô hình cỡ lớn tốn kém hơn.

**Cách tích hợp**: Backend gọi Azure OpenAI qua REST API/SDK chính thức, dùng khoá API được cấp qua Azure resource riêng cho dự án, có thể giới hạn theo quota để kiểm soát chi phí.

**Kiểm soát rủi ro "ảo giác" (hallucination)**: Prompt hệ thống gửi kèm mỗi câu hỏi luôn bao gồm chỉ dẫn rõ ràng: chỉ trả lời dựa trên ngữ cảnh được cung cấp (các đoạn nội dung tìm được từ Azure AI Search); nếu ngữ cảnh không đủ, trả lời trung thực là chưa có đủ thông tin thay vì suy đoán.

## 6. Tìm kiếm ngữ nghĩa (Vector Search) — Azure AI Search

**Vai trò**: Lưu trữ và truy vấn chỉ mục vector phục vụ bước "truy hồi" (retrieval) trong kiến trúc RAG.

**Lý do chọn**: Là dịch vụ vector search được quản lý hoàn toàn (managed) trong cùng hệ sinh thái Azure, hỗ trợ tìm kiếm tương đồng (similarity search) hiệu quả ở quy mô vừa và lớn, giảm gánh nặng tự vận hành một CSDL vector riêng (ví dụ tự triển khai Qdrant/FAISS).

**Cách tích hợp**: Sau mỗi lần data pipeline cập nhật nội dung một POI, backend gửi đoạn văn bản (chunk) cùng vector embedding tương ứng tới Azure AI Search để cập nhật chỉ mục; khi xử lý câu hỏi chatbot, backend gửi vector của câu hỏi tới Azure AI Search để lấy về các đoạn nội dung liên quan nhất.

## 7. Lưu trữ đối tượng — Azure Blob Storage

**Vai trò**: Lưu trữ file audio đã sinh và hình ảnh (thumbnail, ảnh minh hoạ) của các POI.

**Lý do chọn**: Chi phí lưu trữ thấp, có thể kết hợp Azure CDN để phục vụ file tĩnh với độ trễ thấp cho khách truy cập trên di động, tích hợp tốt với các dịch vụ Azure khác đã chọn (ví dụ đầu ra trực tiếp từ Speech Service có thể tải thẳng lên Blob Storage).

**Cách tích hợp**: Data pipeline dùng Azure SDK để tải file lên container riêng cho từng loại tài nguyên (`audio/`, `images/`); các URL công khai (hoặc URL có chữ ký tạm thời — SAS token — nếu cần kiểm soát truy cập chặt hơn) được lưu vào bản ghi POI.

## 8. Sinh mã QR — thư viện `qrcode` (Python)

**Vai trò**: Sinh mã QR đặt tại cổng vào chùa để khách quét mở web app.

**Lý do chọn**: Thư viện mã nguồn mở, miễn phí, đơn giản, chạy hoàn toàn nội bộ không cần gọi dịch vụ bên ngoài — mã QR chỉ cần chứa một đường dẫn URL cố định tới trang chủ web app nên không cần dịch vụ sinh QR động phức tạp.

## 9. Giám sát & log tập trung — Azure Application Insights

**Vai trò**: Thu thập log, độ trễ, tỉ lệ lỗi của các API backend theo thời gian thực, phục vụ Monitoring Dashboard (FR-22).

**Lý do chọn**: Tích hợp sẵn với Azure App Service/Container Apps mà không cần cấu hình phức tạp, cung cấp cảnh báo (alert) tự động khi chỉ số vượt ngưỡng, và có thể xuất dữ liệu ra để hiển thị lại trong admin dashboard tự xây dựng.

## 10. Tổng hợp chi phí và mức độ phụ thuộc

| Dịch vụ | Có gói miễn phí/dùng thử? | Mức độ quan trọng |
|---|---|---|
| MapTiler / OpenStreetMap | Có (MapTiler free tier; OSM luôn miễn phí) | Cao — không có bản đồ thì app không hoạt động được |
| Payoo | Có môi trường sandbox miễn phí cho thử nghiệm | Cao — bắt buộc cho luồng thanh toán online |
| Azure AI Translator | Có (free tier giới hạn số ký tự/tháng) | Cao — cốt lõi của trải nghiệm đa ngôn ngữ |
| Azure Speech (TTS) | Có (free tier giới hạn) | Cao — cốt lõi của trải nghiệm thuyết minh audio |
| Azure OpenAI | Trả phí theo lượng sử dụng (pay-as-you-go), không có free tier lớn | Cao — cốt lõi của chatbot |
| Azure AI Search | Có (tier miễn phí giới hạn dung lượng chỉ mục) | Trung bình — có thể tạm thay bằng tìm kiếm vector nội bộ đơn giản nếu vượt ngân sách |
| Azure Blob Storage | Có (free tier trong 12 tháng đầu của tài khoản Azure mới) | Cao — lưu toàn bộ audio/ảnh |
| Azure Application Insights | Có (free tier giới hạn dữ liệu/tháng) | Trung bình — hệ thống vẫn hoạt động được nếu tạm thời thiếu giám sát, nhưng mất khả năng phát hiện sự cố sớm |
