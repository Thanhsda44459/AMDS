# AMDS

Hệ thống hướng dẫn tham quan thông minh tại Chùa Linh Ứng, tích hợp bản đồ GPS, thuyết minh đa ngôn ngữ và chatbot AI.

## Tổng quan

LinhUngGuide là một web app/PWA dành cho khách tham quan tự do. Người dùng có thể truy cập hệ thống bằng cách quét mã QR tại cổng chùa, hoàn tất thanh toán, sau đó sử dụng bản đồ số để xem các điểm tham quan (POI), nghe thuyết minh và đặt câu hỏi bằng ngôn ngữ tự nhiên.

Dự án cũng cung cấp giao diện quản trị cho admin/staff để quản lý POI, phiên tham quan, thanh toán tiền mặt và theo dõi tình trạng vận hành của hệ thống.

## Chức năng chính

- Thanh toán trực tuyến qua Payoo hoặc thanh toán tiền mặt tại quầy.
- Cấp và xác thực access token theo từng phiên tham quan.
- Hiển thị vị trí khách và các POI lân cận trên bản đồ.
- Tự động gợi ý thuyết minh khi khách đi vào vùng lân cận POI.
- Xem mô tả và nghe audio thuyết minh theo ngôn ngữ lựa chọn.
- Hỗ trợ tối thiểu 15 ngôn ngữ cho nội dung POI và giao diện.
- Tự động dịch nội dung POI và sinh audio TTS sau khi admin cập nhật nội dung.
- Gợi ý lộ trình tham quan.
- Chatbot AI dạng RAG trả lời dựa trên tri thức của chùa, có thể đính kèm hình ảnh liên quan.
- Dashboard admin/staff và monitoring dashboard.

## Kiến trúc dự kiến

```text
Trình duyệt di động / PWA
	|
	| REST/JSON over HTTPS
	v
Frontend: React + TypeScript + Vite
	|
	v
Backend API: Python + FastAPI
	|
	+-- MongoDB Atlas       Dữ liệu POI, session, user, metrics
	+-- Redis                Mã thanh toán tiền mặt có TTL
	+-- Azure AI Search      Vector search cho chatbot RAG
	+-- Azure Blob Storage   Audio và hình ảnh
	+-- Payoo               Thanh toán trực tuyến
	+-- Azure AI Services    OpenAI, Translator và Speech
```

## Công nghệ

| Thành phần | Công nghệ dự kiến |
|---|---|
| Frontend | React 18, TypeScript, Vite, TailwindCSS, Zustand, React Router |
| Bản đồ | Leaflet và React-Leaflet, OpenStreetMap/MapTiler |
| Backend | Python, FastAPI, Motor |
| Cơ sở dữ liệu | MongoDB Atlas |
| Cache và phiên tạm | Redis |
| Chatbot | Azure OpenAI và Azure AI Search |
| Dịch thuật/TTS | Azure AI Translator và Azure Speech |
| Lưu trữ media | Azure Blob Storage |
| Thanh toán | Payoo |
| Triển khai | Azure App Service/Container Apps, Azure Static Web Apps, GitHub Actions |

## Cấu trúc repository

```text
AMDS/
├── backend/                 # API và xử lý nghiệp vụ FastAPI
├── frontend/                # Web app khách tham quan và dashboard React
├── docs/
│   ├── system-doc/          # Đặc tả yêu cầu, kiến trúc, API, dữ liệu, kiểm thử...
│   └── plan-task/           # Kế hoạch và backlog phát triển
└── README.md
```

## Trạng thái hiện tại

Repository hiện đang ở giai đoạn khởi tạo và hoàn thiện tài liệu thiết kế. Backend và frontend chưa có bản triển khai chức năng hoàn chỉnh. Các công nghệ, endpoint và dịch vụ bên ngoài trong tài liệu là kiến trúc mục tiêu của đồ án.

## Bắt đầu phát triển

### Backend

Yêu cầu Python 3.11 trở lên.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi "uvicorn[standard]"
```

Khi API đầu tiên được triển khai, có thể chạy development server bằng:

```powershell
uvicorn app.main:app --reload
```

### Frontend

Frontend sẽ được khởi tạo bằng Vite/React theo kế hoạch phát triển. Các biến môi trường chứa secret của Azure, MongoDB, Redis hoặc Payoo không được commit vào repository; sử dụng file `.env` cục bộ hoặc secret manager của môi trường triển khai.

## Tài liệu

- [Phạm vi đồ án](docs/system-doc/01_Project_Scope.md)
- [Yêu cầu hệ thống](docs/system-doc/02_Requirements.md)
- [User stories](docs/system-doc/03_User_Stories.md)
- [Use cases](docs/system-doc/04_Use_Cases.md)
- [Kiến trúc hệ thống](docs/system-doc/05_System_Architecture.md)
- [Thiết kế cơ sở dữ liệu](docs/system-doc/06_Database_Design.md)
- [Đặc tả API](docs/system-doc/07_API_Specification.md)
- [Đặc tả UI/UX](docs/system-doc/08_UI_UX_Specification.md)
- [Kế hoạch kiểm thử](docs/system-doc/11_Test_Plan.md)
- [Kế hoạch triển khai](docs/system-doc/12_Deployment.md)
- [Master development plan](docs/plan-task/00_Master_Development_Plan.md)
- [Backlog Phase 0-4](docs/plan-task/01_Task_Backlog_Phase0-4.md)
- [Backlog Phase 5-13](docs/plan-task/02_Task_Backlog_Phase5-13.md)

## Lộ trình phát triển

1. Khởi tạo backend, frontend, cấu hình môi trường và kết nối cơ sở dữ liệu.
2. Xây dựng CRUD POI và API xác thực cơ bản.
3. Xây dựng bản đồ, GPS và hiển thị POI trên frontend.
4. Tích hợp thanh toán tiền mặt và thanh toán trực tuyến.
5. Hoàn thiện pipeline dịch thuật, TTS và nội dung đa ngôn ngữ.
6. Tích hợp chatbot RAG, dashboard quản trị và monitoring.
7. Bổ sung kiểm thử, bảo mật, tối ưu hiệu năng và triển khai pilot.

## Bảo mật

- Chỉ truyền access token và dữ liệu thanh toán qua HTTPS.
- Không lưu thông tin thẻ hoặc tài khoản ngân hàng của khách.
- Mật khẩu admin/staff phải được băm trước khi lưu.
- Secret và connection string phải được quản lý bằng biến môi trường hoặc secret manager.
- Webhook Payoo phải được xác thực bằng chữ ký riêng của cổng thanh toán.

## Giấy phép

Dự án được thực hiện trong phạm vi đồ án học tập. Thông tin về giấy phép phát hành sẽ được bổ sung khi dự án xác định chính sách phân phối mã nguồn.