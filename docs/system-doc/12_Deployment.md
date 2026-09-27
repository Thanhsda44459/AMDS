# 12. Triển Khai Hệ Thống — LinhUngGuide

## 1. Tổng quan chiến lược triển khai
Hệ thống được triển khai hoàn toàn trên nền tảng Azure để tận dụng việc quản lý tập trung các dịch vụ AI/dịch thuật/TTS/lưu trữ đã chọn ở `05_System_Architecture.md`. Quy trình triển khai được tự động hoá qua GitHub Actions, với ba môi trường tách biệt: Development, Staging, Production (pilot).

## 2. Thành phần hạ tầng và nơi lưu trú

| Thành phần | Dịch vụ Azure / bên thứ ba | Ghi chú |
|---|---|---|
| Backend API (FastAPI) | Azure App Service (Linux, container) hoặc Azure Container Apps | Chọn Container Apps nếu cần auto-scale linh hoạt hơn theo lượng traffic biến động mạnh vào mùa lễ hội |
| Frontend (React PWA) | Azure Static Web Apps | Build tĩnh (Vite build), phân phối qua CDN toàn cầu tích hợp sẵn |
| CSDL chính | MongoDB Atlas (cụm M0/M10 tuỳ giai đoạn) | M0 (free tier) dùng cho môi trường Dev/Staging, nâng cấp M10 trả phí cho Production khi vận hành thật |
| Chỉ mục vector | Azure AI Search | Tier Free/Basic tuỳ dung lượng chỉ mục thực tế |
| Cache | Azure Cache for Redis (Basic tier) | Dùng cho luồng mã ngắn thanh toán tiền mặt |
| Lưu trữ đối tượng | Azure Blob Storage + Azure CDN | Container riêng cho `audio/` và `images/` |
| Dịch vụ AI | Azure OpenAI Service | Resource riêng theo từng môi trường để tách quota/chi phí |
| Dịch thuật & TTS | Azure AI Translator, Azure Speech | Cùng resource group với các dịch vụ Azure khác |
| Thanh toán | Payoo (sandbox cho Dev/Staging, production merchant cho Production) | Cấu hình webhook URL riêng cho từng môi trường |
| Giám sát | Azure Application Insights | Gắn trực tiếp vào App Service/Container Apps |

## 3. Quy trình CI/CD (GitHub Actions)

### 3.1. Luồng cho Backend
1. Khi có commit/merge vào nhánh `develop`: pipeline tự động chạy lint (`ruff`/`flake8`), chạy Unit Test (`pytest`), build image Docker, và deploy tự động lên môi trường Staging.
2. Khi có merge vào nhánh `main` (đã được duyệt qua Pull Request): pipeline chạy lại toàn bộ kiểm thử, sau đó yêu cầu một bước phê duyệt thủ công (manual approval) trước khi deploy lên Production, nhằm tránh sự cố ngoài ý muốn ảnh hưởng tới khách đang tham quan thực tế.
3. Biến môi trường nhạy cảm (khoá API Azure OpenAI, secret webhook Payoo, chuỗi kết nối MongoDB) được lưu trong GitHub Secrets, không bao giờ commit trực tiếp vào mã nguồn.

### 3.2. Luồng cho Frontend
1. Tương tự backend: lint, build, chạy Unit Test/E2E test cơ bản trên môi trường Staging trước.
2. Azure Static Web Apps hỗ trợ sẵn cơ chế "preview deployment" cho mỗi Pull Request, giúp nhóm phát triển xem trước giao diện trước khi merge.
3. Sau khi merge vào `main`, bản build production được xuất bản tự động lên CDN.

### 3.3. Quản lý phiên bản cơ sở dữ liệu
Các thay đổi cấu trúc dữ liệu (ví dụ thêm trường mới vào collection `pois`) được viết dưới dạng script migration nhỏ, chạy thủ công có kiểm soát bởi người triển khai (không tự động chạy trong CI/CD) để tránh rủi ro với dữ liệu thật đang phục vụ khách.

## 4. Các bước triển khai lần đầu (Initial Setup)
1. Tạo resource group riêng trên Azure cho dự án (ví dụ `rg-linhungguide-prod`).
2. Khởi tạo các resource: App Service/Container Apps, Static Web Apps, Azure OpenAI, Azure AI Translator, Azure Speech, Azure AI Search, Azure Cache for Redis, Azure Blob Storage, Application Insights.
3. Khởi tạo cụm MongoDB Atlas, cấu hình network access chỉ cho phép kết nối từ dải IP của App Service/Container Apps (không mở public rộng rãi).
4. Chạy seed script tạo tài khoản admin đầu tiên trong collection `admin_users`.
5. Đăng ký tài khoản merchant Payoo (sandbox trước, production sau khi kiểm thử ổn định), cấu hình webhook URL trỏ về endpoint `/auth/payment/webhook/payoo` của môi trường tương ứng.
6. Cấu hình biến môi trường backend: chuỗi kết nối MongoDB, Redis, các khoá API Azure, secret Payoo, khoá bí mật ký JWT.
7. Sinh mã QR (dùng script Python với thư viện `qrcode`) trỏ về domain frontend Production, in và đặt tại cổng vào chùa.
8. Nhập dữ liệu POI ban đầu qua admin dashboard, chờ data pipeline hoàn tất dịch/TTS cho toàn bộ POI trước khi công bố chính thức.

## 5. Domain và chứng chỉ bảo mật
- Frontend: domain chính (ví dụ `linhungguide.vn`) trỏ về Azure Static Web Apps, dùng chứng chỉ TLS được Azure tự động cấp và gia hạn.
- Backend API: subdomain riêng (ví dụ `api.linhungguide.vn`) trỏ về App Service/Container Apps, cũng dùng TLS tự động.
- Toàn bộ giao tiếp bắt buộc qua HTTPS; cấu hình chuyển hướng tự động từ HTTP sang HTTPS ở tầng hạ tầng.

## 6. Kế hoạch sao lưu và khôi phục (Backup & Recovery)
- MongoDB Atlas: bật tính năng sao lưu tự động theo lịch hằng ngày (continuous backup nếu ngân sách cho phép ở tier trả phí), lưu giữ tối thiểu 7 ngày gần nhất.
- Azure Blob Storage: bật soft-delete cho container audio/ảnh, tránh mất dữ liệu khi có thao tác xoá nhầm từ pipeline hoặc admin.
- Redis: không cần sao lưu dài hạn vì chỉ chứa dữ liệu tạm có TTL ngắn; nếu Redis gặp sự cố, ảnh hưởng chỉ giới hạn ở các phiên đang chờ đổi mã ngắn, không mất dữ liệu vận hành cốt lõi.

## 7. Giám sát sau triển khai (Post-Deployment Monitoring)
- Azure Application Insights theo dõi tỉ lệ lỗi, độ trễ API theo thời gian thực, tích hợp trực tiếp vào Monitoring Dashboard mô tả ở `08_UI_UX_Specification.md`, mục 3.2.
- Thiết lập cảnh báo tự động (qua email hoặc kênh chat nội bộ của nhóm) khi: tỉ lệ lỗi 5xx vượt ngưỡng trong 5 phút, độ trễ trung bình API vượt ngưỡng, hoặc một trong các dịch vụ Azure phụ thuộc (Translator, Speech, OpenAI) trả về lỗi liên tục.
- Theo dõi định kỳ chi phí sử dụng các dịch vụ trả phí theo lượng dùng (đặc biệt Azure OpenAI) để tránh vượt ngân sách đồ án, có thể cấu hình ngưỡng cảnh báo chi phí (budget alert) trực tiếp trên Azure Cost Management.

## 8. Kế hoạch triển khai theo mốc thời gian (bám theo Launch Plan của PRD)
| Giai đoạn | Mục tiêu | Môi trường |
|---|---|---|
| Phát triển | Hoàn thiện các tính năng theo yêu cầu ở `02_Requirements.md` | Development |
| Kiểm thử nội bộ | Chạy đầy đủ các cấp độ kiểm thử ở `11_Test_Plan.md` | Staging |
| **Pilot (16/05/2025 theo PRD gốc)** | Kiểm thử sơ bộ tại hiện trường với người dùng thật, thu thập phản hồi UAT | Production (giới hạn quy mô) |
| Vận hành chính thức | Mở rộng quy mô, bật đầy đủ giám sát và cảnh báo, hoàn thiện tài liệu bàn giao | Production |

## 9. Kế hoạch bàn giao sau đồ án
Toàn bộ mã nguồn, tài liệu (bao gồm 12 tài liệu trong bộ tài liệu này), script triển khai, và hướng dẫn cấu hình biến môi trường được lưu trong một repository Git duy nhất kèm file `README.md` hướng dẫn khởi chạy nhanh (quick start), nhằm đảm bảo người kế thừa (ban quản lý chùa hoặc nhóm vận hành tiếp theo) có thể tiếp tục bảo trì hệ thống sau khi đồ án kết thúc, đáp ứng NFR-12.
