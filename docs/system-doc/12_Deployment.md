# 12 — Deployment (Chạy và triển khai hệ thống)

> Tài liệu gốc mô tả kiến trúc, trình tự khởi động và cấu hình chính nhưng **không có hướng dẫn triển khai đầy đủ**. Các lệnh và cấu hình cụ thể dưới đây là **[Đề xuất]**, cần đối chiếu với `README`, `requirements.txt`, `package.json` và tệp mẫu `.env` thực tế của dự án.

## 1. Thành phần cần chạy

| Thành phần | Mô tả | Bắt buộc |
|---|---|---|
| Backend FastAPI | Một tiến trình ASGI (uvicorn/gunicorn+uvicorn workers) | Có |
| MongoDB | Cần hỗ trợ transaction (replica set, kể cả một nút) | Có |
| Redis | Hiện diện, rate limit, phối hợp | Có |
| Frontend PWA | Tệp tĩnh sau khi build bằng Vite | Có |
| Kho media/tĩnh | Thư mục trên đĩa hoặc S3-compatible | Có |
| Reverse proxy + HTTPS | Nginx/Caddy | Có (production) |
| Gói bản đồ PMTiles | Tệp trong thư mục maps | Có nếu dùng offline |

**Vì sao cần HTTPS:** Service Worker, định vị (Geolocation) và cookie `Secure` chỉ hoạt động đầy đủ trên HTTPS (trừ `localhost`).

## 2. Yêu cầu phần mềm

- Python 3.11 trở lên [Đề xuất], Node.js 20 trở lên [Đề xuất], MongoDB 6 trở lên, Redis 6 trở lên.
- Tài nguyên tối thiểu gợi ý cho demo/đồ án: 2 vCPU, 4 GB RAM, 20 GB đĩa (audio và pack bản đồ chiếm nhiều nhất).

## 3. Cấu hình môi trường

### 3.1 Backend (biến môi trường — tên tham khảo)

| Nhóm | Biến | Ghi chú |
|---|---|---|
| Bảo mật bắt buộc (non-dev) | `JWT_SECRET`, `REFRESH_TOKEN_SECRET`, `SECRET_KEY` | Chuỗi ngẫu nhiên dài; thiếu thì backend không chạy |
| Khởi tạo admin | `SUPERADMIN_BOOTSTRAP_MODE` + thông tin tài khoản | Sai chế độ thì dừng ngay |
| PII | Khóa Fernet | Giữ bí mật, sao lưu an toàn |
| CSDL | Chuỗi kết nối MongoDB, tên DB | Cần replica set |
| Cache | Địa chỉ Redis | |
| Bản đồ | `MAP_PACK_DATA_DIR` | Mặc định `backend/app/static/maps/` |
| Media | Cấu hình S3-compatible (nếu dùng) | Khởi động có kiểm tra sức khỏe |
| AI | Khóa Gemini hoặc cấu hình ProxyPal | Tùy chọn |
| Thời tiết | Khóa OpenWeather | Tùy chọn |
| CORS/Cookie | Tên miền cho phép, cờ Secure | |

### 3.2 Frontend (lúc build)

| Biến | Ghi chú |
|---|---|
| `VITE_MAPTILER_KEY` | Cần cho Cloud/Hybrid; giới hạn khóa theo tên miền |
| Địa chỉ API | Thường dùng cùng nguồn gốc (proxy `/api`) để cookie hoạt động |

Không đưa bí mật phía server vào biến `VITE_*` vì chúng bị lộ cho trình duyệt.

## 4. Chạy trên máy phát triển (đề xuất)

1. Khởi động MongoDB dạng replica set một nút và Redis (khuyên dùng Docker).
2. Backend: tạo môi trường ảo, cài phụ thuộc, tạo `.env` với `JWT_SECRET` v.v. (môi trường dev có thể nới lỏng), chạy uvicorn với chế độ tự tải lại.
3. Frontend: cài phụ thuộc, tạo `.env` với `VITE_MAPTILER_KEY`, chạy máy chủ dev của Vite.
4. Mở trình duyệt, kiểm tra `/health` và `/health/ready` của backend.
5. Đăng nhập tài khoản super admin được tạo khi khởi động; thêm POI mẫu.
6. Lưu ý: Service Worker và PWA chỉ thật sự được thử nghiệm đúng ở bản build (`vite build` rồi `vite preview`), không phải ở chế độ dev.

## 5. Triển khai production (đề xuất)

### 5.1 Mô hình đơn giản (một máy chủ)

Mô tả theo lớp từ ngoài vào trong:
1. **Tên miền + chứng chỉ TLS** (Let's Encrypt qua Caddy hoặc Certbot).
2. **Reverse proxy (Nginx/Caddy)** nhận mọi yêu cầu:
   - Đường dẫn `/api/` chuyển tới backend.
   - Đường dẫn `/static/` chuyển tới backend (hoặc phục vụ trực tiếp từ đĩa để nhanh hơn, nhưng phải giữ nguyên header cache và hỗ trợ Range Request cho PMTiles).
   - Mọi đường dẫn còn lại phục vụ tệp frontend đã build, với quy tắc quay về trang chính (catch-all) cho định tuyến phía client.
3. **Backend** chạy bằng trình quản lý tiến trình (systemd hoặc Docker) với vài worker uvicorn.
4. **MongoDB và Redis** chạy cùng máy (Docker) hoặc dịch vụ quản lý; chỉ lắng nghe trong mạng nội bộ.
5. **Ổ đĩa dữ liệu** gắn riêng cho thư mục media và maps, có sao lưu.

### 5.2 Docker Compose (đề xuất cấu trúc)

Các dịch vụ: `mongo` (replica set, có volume), `redis`, `backend` (phụ thuộc mongo, redis; mount volume static), `frontend` hoặc `nginx` (phục vụ bản build + proxy). Mỗi dịch vụ có `healthcheck`; backend dùng `/health/ready` làm điều kiện sẵn sàng. Bí mật truyền qua tệp `.env` không commit hoặc secrets của Docker.

### 5.3 Lưu ý riêng cho PWA và cache

- **`sw.js` và `index.html` không được cache lâu** ở lớp proxy/CDN; nếu bị cache, người dùng sẽ kẹt bản cũ.
- Tệp có băm tên (chunk, asset) có thể cache dài hạn.
- Manifest bản đồ: `no-cache`; pack `.pmtiles`, glyph: `immutable`.
- Sau mỗi bản phát hành, `APP_BUILD_SYNC` dọn chunk tùy chọn cũ để không lẫn asset giữa hai build.
- Bật nén (gzip/brotli) cho JS/CSS/JSON; **không** nén lại tệp PMTiles/MP3 và phải bảo toàn Range Request.

## 6. Trình tự khởi động mong đợi của backend

Khi triển khai, kỳ vọng thấy theo thứ tự:
1. Kiểm tra bí mật và chế độ bootstrap (sai thì dừng).
2. Kết nối MongoDB, xác nhận transaction; nếu dùng S3 thì kiểm tra sức khỏe.
3. Tạo role mặc định và super admin; kiểm tra hoặc tạo thư mục lưu trữ.
4. Phục hồi tác vụ audio, bật vòng bảo trì, tạo index, bật worker analytics và dọn media.
5. Gắn router; `/health/ready` trả sẵn sàng.

Nếu khởi động lỗi, đọc log theo đúng trình tự trên để xác định tầng hỏng.

## 7. Khởi tạo dữ liệu lần đầu

1. Đăng nhập super admin.
2. Kiểm tra 4 role mặc định đã có.
3. Đặt gói bản đồ vào `MAP_PACK_DATA_DIR` (hoặc `backend/app/static/maps/`) theo cấu trúc `packs/{version}/*.pmtiles`, `packs/current/manifest.json`, `styles/`, `fonts/`.
4. Nhập POI; hệ thống tự xếp việc sinh audio cho 5 ngôn ngữ ưu tiên; theo dõi ở màn hình tác vụ audio.
5. Chạy warmup để dịch toàn bộ corpus nếu cần.
6. Kiểm tra `/audio/pack-manifest?lang=...` và `/maps/offline-options`.

## 8. Quy trình phát hành (đề xuất)

1. Chạy kiểm thử tự động (CI): unit, tích hợp, E2E.
2. Build frontend (`vite build`); build ảnh Docker backend.
3. Triển khai lên staging, chạy kiểm thử khói: `/health`, `/health/ready`, mở app, tải POI, phát một audio.
4. Triển khai production theo kiểu cuốn chiếu hoặc thay thế nhanh; không xóa tệp asset cũ ngay để người dùng đang giữ bản cũ không gặp lỗi 404.
5. Xác nhận Service Worker mới được kích hoạt và `APP_BUILD_SYNC` chạy.
6. Theo dõi log và số liệu trong 24 giờ đầu.
7. **Quay lui:** giữ ảnh/bản build trước; khôi phục và xóa cache proxy cho `sw.js`/`index.html`.

## 9. Sao lưu và khôi phục

| Dữ liệu | Cách sao lưu | Tần suất đề xuất |
|---|---|---|
| MongoDB | `mongodump` hoặc snapshot đĩa | Hằng ngày |
| Media (audio, ảnh) | Đồng bộ thư mục hoặc phiên bản hóa S3 | Hằng ngày/tăng dần |
| Gói bản đồ | Lưu bản gốc ngoài máy chủ | Khi cập nhật |
| Khóa và `.env` | Kho bí mật an toàn | Khi đổi |

Khôi phục: dựng MongoDB, nạp bản sao lưu, đặt lại media, khởi động backend. Audio có thể **sinh lại** từ văn bản nếu mất (tốn thời gian nhưng không tốn tiền nhờ Edge-TTS).

Lưu ý: mất khóa Fernet thì không giải mã được CCCD đã lưu; mất `JWT_SECRET` chỉ khiến mọi người phải đăng nhập lại.

## 10. Giám sát và vận hành

- **Kiểm tra sống/sẵn sàng:** `/health`, `/health/ready` cho giám sát và bộ cân bằng tải.
- **Log:** log ứng dụng backend, log proxy; audit log nghiệp vụ trong MongoDB.
- **Số liệu nghiệp vụ:** dashboard analytics và cửa sổ quan sát vị trí runtime của admin.
- **Cảnh báo nên có:** `/health/ready` thất bại, đĩa trên 80%, tác vụ audio thất bại liên tục, lỗi 5xx tăng, MongoDB/Redis ngắt.
- **Bảo trì định kỳ:** worker dọn media chạy nền; `audio_tasks` tự hết hạn 14 ngày; theo dõi dung lượng thư mục audio.

## 11. Bảo mật khi triển khai

- Bắt buộc HTTPS; bật HSTS.
- Không mở cổng MongoDB và Redis ra Internet; bật xác thực.
- Bí mật chỉ nằm trong biến môi trường hoặc kho bí mật, không nằm trong mã.
- Giới hạn khóa MapTiler theo tên miền.
- Đặt tên miền cho CORS/cookie chính xác; cookie `Secure`, `httpOnly`, `SameSite=Lax`.
- Tường lửa chỉ mở 80/443 (và SSH hạn chế).
- Cập nhật phụ thuộc định kỳ.

## 12. Chi phí dự kiến

| Hạng mục | Ghi chú |
|---|---|
| Phần mềm lõi | $0 (mã nguồn mở) |
| TTS, dịch | $0 (mức miễn phí; có rủi ro giới hạn) |
| Máy chủ/VPS, tên miền | Chi phí duy nhất chắc chắn phát sinh |
| MapTiler | Tùy gói; có thể bỏ nếu chỉ dùng Offline/pack |
| Gemini/ProxyPal | Tùy mức dùng; có hạn mức 10/ngày/owner |
| S3 | Tùy dung lượng nếu chọn |

## 13. Danh sách kiểm tra trước khi go-live

- [ ] HTTPS hoạt động, chứng chỉ tự gia hạn.
- [ ] Đã đặt `JWT_SECRET`, `REFRESH_TOKEN_SECRET`, `SECRET_KEY`, khóa Fernet, chế độ bootstrap đúng.
- [ ] MongoDB là replica set; backend qua bước kiểm tra transaction.
- [ ] `/health/ready` trả sẵn sàng.
- [ ] Gói bản đồ và manifest đã có; `offline-options` trả đúng.
- [ ] POI mẫu đã có audio đủ 5 ngôn ngữ.
- [ ] `sw.js`, `index.html` không bị cache lâu.
- [ ] Range Request cho PMTiles hoạt động qua proxy.
- [ ] Kiểm thử khói trên điện thoại thật: cài PWA, định vị, nghe thuyết minh, dùng offline.
- [ ] Đã có sao lưu tự động và đã thử khôi phục.
- [ ] Đã đổi mật khẩu super admin mặc định.
