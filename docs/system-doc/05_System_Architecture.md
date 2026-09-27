# 05. Kiến Trúc Hệ Thống — LinhUngGuide

Tài liệu mô tả kiến trúc bằng lời, giải thích vai trò từng thành phần và cách chúng giao tiếp với nhau, thay cho sơ đồ trực quan.

## 1. Tổng quan lựa chọn công nghệ

| Lớp | Công nghệ được chọn | Lý do chọn |
|---|---|---|
| Frontend (Web app khách) | ReactJS 18 + TypeScript, Vite, TailwindCSS, Zustand, React Router, react-leaflet (Leaflet.js) | Hệ sinh thái phổ biến, cộng đồng lớn, dễ triển khai PWA, Leaflet nhẹ và đủ dùng cho bản đồ khuôn viên một địa điểm (không cần bộ máy vector-tile phức tạp) |
| Bản đồ nền | OpenStreetMap / MapTiler (gói miễn phí) | Miễn phí hoặc chi phí rất thấp so với Google Maps, đủ chi tiết cho khu vực Đà Nẵng |
| Admin & Staff dashboard | Cùng codebase React, tách route riêng (`/admin`, `/staff`), UI dùng thêm thư viện component (ví dụ Ant Design/MUI) | Tận dụng lại hạ tầng frontend, giảm chi phí bảo trì hai codebase riêng biệt |
| Backend API | Python FastAPI (bất đồng bộ) | Hiệu năng tốt với I/O bất đồng bộ (gọi AI, dịch thuật, TTS song song), tài liệu tự sinh (OpenAPI/Swagger) hỗ trợ tài liệu API, hệ sinh thái Python phù hợp để tích hợp AI |
| Giao tiếp Backend ↔ CSDL | Motor (driver MongoDB bất đồng bộ) | Khớp với mô hình async của FastAPI |
| CSDL chính | MongoDB Atlas | Lưu dữ liệu dạng tài liệu (document) linh hoạt, phù hợp với cấu trúc POI có nhiều bản dịch lồng nhau; có gói miễn phí cho môi trường đồ án |
| CSDL vector (cho chatbot RAG) | Azure AI Search (chỉ mục vector) | Tách biệt tìm kiếm ngữ nghĩa khỏi CSDL vận hành chính, tối ưu cho truy vấn tương đồng vector ở quy mô lớn |
| Cache & phiên tạm | Redis (Azure Cache for Redis) | Lưu mã ngắn (shortened_code) cho luồng thanh toán tiền mặt với thời gian sống ngắn, đúng theo luồng đã mô tả trong PRD gốc |
| Dịch vụ AI sinh câu trả lời | Azure OpenAI Service — GPT-4o mini | Cân bằng giữa chi phí và chất lượng, đủ tốt cho tác vụ hỏi đáp có ngữ cảnh (RAG), tương thích hệ sinh thái Azure |
| Dịch vụ embedding | Azure OpenAI — text-embedding-3-small | Dùng chung nhà cung cấp với mô hình sinh câu trả lời, đơn giản hoá việc quản lý khoá API |
| Dịch thuật tự động | Azure AI Translator | Hỗ trợ hơn 100 ngôn ngữ, chất lượng ổn định, có SDK/REST API dễ tích hợp vào pipeline bất đồng bộ |
| Chuyển văn bản thành giọng nói (TTS) | Azure Cognitive Services Speech (Neural TTS) | Giọng đọc tự nhiên, hỗ trợ đa ngôn ngữ tương ứng với danh sách ngôn ngữ dịch thuật, cùng hệ sinh thái Azure giúp giảm độ phức tạp tích hợp |
| Lưu trữ file (audio, ảnh) | Azure Blob Storage | Lưu trữ đối tượng chi phí thấp, có CDN đi kèm để phục vụ file tĩnh nhanh |
| Cổng thanh toán | Payoo Payment Gateway | Được chỉ định trong PRD gốc, phù hợp thanh toán nội địa Việt Nam (QR, thẻ ATM, ví điện tử) |
| Xác thực | JWT (access token), mật khẩu tài khoản quản trị băm bằng bcrypt | Không trạng thái (stateless), dễ xác thực phân tán giữa các service backend |
| Sinh mã QR | Thư viện `qrcode` (Python) | Đơn giản, không tốn chi phí, đủ dùng để sinh QR tại cổng vào |
| Hosting Backend | Azure App Service / Azure Container Apps | Tự động scale, tích hợp tốt với các dịch vụ Azure khác đã chọn (OpenAI, Translator, Speech, Blob Storage) |
| Hosting Frontend | Azure Static Web Apps | Phù hợp ứng dụng SPA/PWA tĩnh, có CDN toàn cầu, tích hợp CI/CD sẵn |
| CI/CD | GitHub Actions | Miễn phí cho repo cá nhân/đồ án, tích hợp tốt với Azure |
| Giám sát | Azure Application Insights + Grafana (tuỳ chọn cho biểu đồ tuỳ biến) | Theo dõi log tập trung, cảnh báo tự động, đủ cho quy mô một đồ án pilot |

> Nguyên tắc chọn công nghệ: ưu tiên một hệ sinh thái đám mây thống nhất (Azure) để giảm số lượng nhà cung cấp cần quản lý khoá/billing riêng lẻ, đồng thời giữ các thành phần mã nguồn mở, chi phí thấp ở tầng frontend/bản đồ để tối ưu ngân sách đồ án.

## 2. Các thành phần chính và vai trò

### 2.1. Web App (Client)
Là một Progressive Web App (PWA) chạy hoàn toàn trên trình duyệt di động. Sau khi khách xác thực thành công (có access token), toàn bộ dữ liệu POI (mô tả đa ngôn ngữ, toạ độ, bán kính, đường dẫn audio) được tải về một lần duy nhất và lưu trong bộ nhớ của ứng dụng. Từ thời điểm đó, mọi thao tác xem POI, đổi ngôn ngữ, xem lộ trình diễn ra hoàn toàn phía client mà không cần gọi lại server — đúng theo nguyên tắc "Key Logic" trong PRD gốc. Chỉ có hai loại yêu cầu tiếp tục được gửi lên server sau khi xác thực: (1) câu hỏi gửi tới chatbot, và (2) file audio được tải theo yêu cầu (khi khách thực sự bấm nghe) thay vì tải toàn bộ audio ngay từ đầu, nhằm giảm dung lượng tải ban đầu.

### 2.2. Authorization Service (Dịch vụ xác thực & thanh toán)
Thành phần trong backend chịu trách nhiệm: sinh và xác minh auth_code, giao tiếp với Payoo cho luồng online, phối hợp với nhân viên cho luồng tiền mặt (lưu mã ngắn vào Redis), và cấp/kiểm tra access token (JWT) cho mọi yêu cầu tiếp theo từ client.

### 2.3. Admin Dashboard & Staff Dashboard
Hai giao diện quản trị (có thể tách route trong cùng một ứng dụng React hoặc build riêng), giao tiếp với backend qua các API riêng có phân quyền:
- Admin: toàn quyền quản lý POI, xem giám sát hệ thống, quản lý tài khoản nhân viên.
- Staff: chỉ có quyền xác nhận thanh toán tiền mặt và xem danh sách phiên đang chờ.

### 2.4. Cloud Backend
Là lớp API trung tâm (FastAPI), điều phối toàn bộ logic nghiệp vụ: xác thực, quản lý POI, điều phối chatbot, kích hoạt data pipeline dịch/TTS, và cung cấp số liệu cho dashboard giám sát. Backend giao tiếp với các dịch vụ AI của Azure OpenAI (sinh câu trả lời, embedding), Azure AI Translator, Azure Speech, và với CSDL/Storage.

### 2.5. Data Pipeline (Dịch thuật & TTS tự động)
Một tiến trình chạy bất đồng bộ (dưới dạng background task hoặc hàng đợi công việc nhẹ trong nội bộ backend), được kích hoạt mỗi khi một POI được tạo mới hoặc mô tả gốc được chỉnh sửa. Pipeline thực hiện tuần tự: dịch văn bản sang toàn bộ ngôn ngữ hỗ trợ → sinh audio cho từng bản dịch → lưu audio vào Blob Storage → cập nhật bản ghi POI trong CSDL với các đường dẫn tương ứng → cập nhật chỉ mục vector để nội dung mới khả dụng cho chatbot.

### 2.6. Chatbot Service (RAG)
Thành phần backend xử lý câu hỏi của khách: chuyển câu hỏi thành vector embedding, tìm kiếm ngữ cảnh liên quan trong Azure AI Search, gửi ngữ cảnh cùng câu hỏi tới mô hình GPT-4o mini để sinh câu trả lời, rồi trả kết quả về cho client.

### 2.7. Cơ sở dữ liệu
- **MongoDB Atlas**: lưu trữ dữ liệu vận hành — POI (toạ độ, bán kính, mô tả theo từng ngôn ngữ, đường dẫn audio, thumbnail), phiên tham quan (session), tài khoản quản trị/nhân viên, nhật ký giao dịch thanh toán.
- **Azure AI Search (vector index)**: lưu chỉ mục vector của nội dung POI và tài liệu bổ sung, phục vụ riêng cho việc tìm kiếm ngữ nghĩa của chatbot, tách biệt khỏi CSDL vận hành để không ảnh hưởng hiệu năng đọc/ghi thông thường.
- **Redis**: lưu tạm mã ngắn (shortened_code) trong luồng thanh toán tiền mặt, với thời gian sống (TTL) ngắn để tự động dọn dẹp.

### 2.8. Lưu trữ đối tượng (Blob Storage)
Lưu toàn bộ file audio đã sinh (theo từng ngôn ngữ, từng POI) và hình ảnh thumbnail/minh hoạ. Các file này được phục vụ qua CDN để tải nhanh trên thiết bị di động.

### 2.9. Cổng thanh toán Payoo
Dịch vụ bên thứ ba xử lý thanh toán trực tuyến. Backend chỉ gửi yêu cầu tạo liên kết thanh toán và nhận webhook xác nhận, không xử lý trực tiếp thông tin nhạy cảm của thẻ/tài khoản khách hàng.

### 2.10. Monitoring Stack
Azure Application Insights thu thập log và số liệu hiệu năng từ backend (thời gian phản hồi API, tỉ lệ lỗi, số request). Dữ liệu này được tổng hợp và hiển thị trong Monitoring Dashboard của admin, kết hợp thêm số liệu nghiệp vụ (lượt xem POI, số câu hỏi chatbot) được backend tự tính toán và lưu định kỳ vào MongoDB.

## 3. Nguyên tắc thiết kế xuyên suốt

1. **Nạp dữ liệu một lần (load-once)**: Toàn bộ dữ liệu văn bản/POI được nạp về frontend ngay sau xác thực; chỉ audio được tải theo yêu cầu nhằm cân bằng giữa nguyên tắc "không gọi lại API" của PRD gốc và việc kiểm soát dung lượng tải ban đầu.
2. **Bất đồng bộ hoá các tác vụ nặng**: Dịch thuật, sinh TTS, cập nhật chỉ mục vector đều chạy nền, không chặn thao tác của quản trị viên.
3. **Tách bạch quyền hạn theo vai trò**: Mọi endpoint quản trị đều kiểm tra vai trò (role) được mã hoá trong JWT trước khi xử lý, hạn chế nhân viên truy cập chức năng vượt phạm vi công việc.
4. **Một hệ sinh thái đám mây thống nhất**: Việc dùng Azure cho AI, dịch thuật, TTS, lưu trữ và hosting giúp đơn giản hoá cấu hình bảo mật (dùng chung managed identity/khoá quản lý tập trung) và giảm số lượng nhà cung cấp cần theo dõi chi phí.
5. **Khả năng mở rộng cho tương lai**: Kiến trúc tách rõ Chatbot Service, Authorization Service và Data Pipeline thành các module độc lập trong backend, để có thể tách thành các service riêng biệt (microservices) nếu hệ thống được nhân rộng ra nhiều địa điểm tham quan khác trong tương lai, dù điều này nằm ngoài phạm vi hiện thực hoá của đồ án.
