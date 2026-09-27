# 11. Kế Hoạch Kiểm Thử — LinhUngGuide

## 1. Mục tiêu kiểm thử
Đảm bảo hệ thống đáp ứng đầy đủ các yêu cầu chức năng và phi chức năng đã nêu ở `02_Requirements.md`, đặc biệt tập trung vào ba luồng có rủi ro cao nhất: (1) thanh toán (online và tiền mặt), (2) độ chính xác của nội dung đa ngôn ngữ, và (3) chất lượng câu trả lời của chatbot AI.

## 2. Các cấp độ kiểm thử

### 2.1. Unit Test (Kiểm thử đơn vị)
Kiểm thử từng hàm/module riêng lẻ ở backend, tách biệt khỏi các dịch vụ bên ngoài thật (dùng mock/stub thay cho Payoo, Azure OpenAI, Azure Translator, Azure Speech).
- Phạm vi: logic sinh và xác minh JWT, logic tính khoảng cách geofence (khách có nằm trong bán kính POI hay không), logic rút gọn mã (auth_code → shortened_code), logic ghép ngữ cảnh cho prompt gửi tới mô hình AI.
- Công cụ: `pytest` cho backend Python; `Vitest`/`Jest` + `React Testing Library` cho các component/logic xử lý ở frontend (ví dụ logic chuyển đổi ngôn ngữ, logic tính khoảng cách hiển thị).
- Tiêu chí đạt: độ phủ (coverage) tối thiểu 70% cho các module nghiệp vụ cốt lõi (auth, geofence, pipeline điều phối).

### 2.2. Integration Test (Kiểm thử tích hợp)
Kiểm thử sự phối hợp giữa các thành phần thật trong môi trường staging (không dùng mock), ví dụ:
- Backend thật ↔ MongoDB thật (instance riêng cho môi trường test).
- Backend thật ↔ Redis thật — kiểm tra mã ngắn được lưu và hết hạn đúng theo TTL cấu hình.
- Backend thật ↔ Payoo sandbox — kiểm tra toàn bộ vòng đời một giao dịch thử nghiệm, từ tạo liên kết thanh toán tới nhận webhook.
- Data pipeline thật ↔ Azure Translator/Speech (dùng key môi trường test) — kiểm tra một POI mẫu được dịch và sinh audio đúng cho toàn bộ 15+ ngôn ngữ mà không có ngôn ngữ nào bị bỏ sót.
- Chatbot Service thật ↔ Azure AI Search ↔ Azure OpenAI — kiểm tra một câu hỏi mẫu trả về ngữ cảnh đúng và câu trả lời hợp lý.

### 2.3. End-to-End Test (E2E)
Mô phỏng hành vi thật của người dùng trên trình duyệt, chạy tự động bằng công cụ như **Playwright**.
- Kịch bản 1: Khách quét QR (giả lập bằng cách mở thẳng URL) → chọn thanh toán online (dùng Payoo sandbox) → hoàn tất thanh toán → xác nhận được cấp access token và thấy bản đồ.
- Kịch bản 2: Khách chọn thanh toán tiền mặt → nhân viên (tài khoản test) xác nhận trên giao diện staff → khách nhập mã ngắn → xác nhận được cấp access token.
- Kịch bản 3: Khách chạm vào một POI → đổi ngôn ngữ → xác nhận nội dung văn bản và audio cập nhật đúng ngôn ngữ mới mà không tải lại trang.
- Kịch bản 4: Khách gửi một câu hỏi cho chatbot → xác nhận nhận được câu trả lời trong thời gian chấp nhận được và câu trả lời không rỗng.
- Kịch bản 5: Admin thêm một POI mới → chờ pipeline chạy xong → xác nhận POI đó xuất hiện đầy đủ (đủ ngôn ngữ) trên web app khách.

### 2.4. Kiểm thử hiệu năng (Performance/Load Test)
- Công cụ: `k6` hoặc `Locust`.
- Kịch bản: mô phỏng đồng thời một lượng lớn khách (ví dụ tương đương mùa lễ hội cao điểm) cùng gọi `GET /pois` và `POST /chatbot/ask` trong một khoảng thời gian ngắn.
- Chỉ tiêu cần đạt: thời gian phản hồi trung bình của `GET /pois` dưới 1 giây ở tải cao điểm; tỉ lệ lỗi (5xx) dưới 1%; đáp ứng đúng NFR-01, NFR-02, NFR-04.

### 2.5. Kiểm thử bảo mật (Security Test)
- Kiểm tra không thể truy cập bất kỳ endpoint `/admin/*` nào nếu không có JWT hợp lệ với vai trò phù hợp (kiểm thử cả trường hợp thiếu token, token hết hạn, token đúng định dạng nhưng sai vai trò).
- Kiểm tra webhook Payoo từ chối yêu cầu không có chữ ký hợp lệ (giả lập một request giả mạo không có secret đúng).
- Kiểm tra mật khẩu tài khoản admin/staff không bao giờ xuất hiện dạng văn bản thuần trong log hệ thống hoặc trong phản hồi API.
- Kiểm tra giới hạn tần suất (`rate limit`) trên `POST /chatbot/ask` hoạt động đúng khi gọi liên tục vượt ngưỡng.
- Rà soát cơ bản theo danh sách OWASP Top 10 cho ứng dụng web (đặc biệt: injection, broken authentication, sensitive data exposure) ở mức phù hợp quy mô đồ án.

### 2.6. Kiểm thử khả năng tương thích (Compatibility Test)
- Kiểm thử thủ công web app trên tối thiểu: Chrome (Android), Safari (iOS), Samsung Internet, để đáp ứng NFR-03.
- Kiểm thử trên các kích thước màn hình phổ biến (điện thoại nhỏ, điện thoại lớn) đảm bảo bố cục UI/UX như mô tả ở `08_UI_UX_Specification.md` không bị vỡ layout.

### 2.7. Kiểm thử chấp nhận người dùng (UAT — User Acceptance Test)
Thực hiện tại hiện trường (on-site) trong giai đoạn Pilot theo Launch Plan của PRD gốc:
- Mời một nhóm người dùng thật (bao gồm cả người Việt và người nước ngoài nếu có thể) trực tiếp trải nghiệm toàn bộ luồng: quét QR → thanh toán → tham quan có GPS thật → hỏi chatbot → đánh giá chất lượng bản dịch và giọng đọc.
- Thu thập phản hồi định tính về: độ chính xác geofence ngoài thực địa (do GPS ngoài trời có thể khác với môi trường giả lập), độ tự nhiên của giọng đọc TTS, độ hữu ích của câu trả lời chatbot.
- Ghi nhận và phân loại lỗi phát hiện theo mức độ nghiêm trọng (Critical/Major/Minor) để ưu tiên xử lý trước khi vận hành chính thức.

## 3. Kiểm thử riêng cho chất lượng nội dung AI
Vì chatbot dựa trên mô hình sinh ngôn ngữ, tài liệu kiểm thử bổ sung một bộ câu hỏi mẫu (test set) khoảng 30–50 câu, bao phủ:
- Câu hỏi có câu trả lời rõ ràng trong dữ liệu POI (kỳ vọng: trả lời đúng, có căn cứ).
- Câu hỏi không liên quan tới chùa (ví dụ hỏi về thời tiết, chính trị) — kỳ vọng: chatbot từ chối lịch sự hoặc điều hướng lại chủ đề tham quan.
- Câu hỏi cố tình đánh lừa (ví dụ hỏi thông tin không có thật để kiểm tra "ảo giác") — kỳ vọng: chatbot thừa nhận không có đủ thông tin thay vì bịa đặt.
- Câu hỏi bằng nhiều ngôn ngữ khác nhau cho cùng một nội dung — kỳ vọng: câu trả lời nhất quán về nội dung, đúng ngôn ngữ đã hỏi.

Bộ câu hỏi này được chạy lại (regression) mỗi khi có thay đổi lớn về prompt hệ thống hoặc dữ liệu tri thức, để đảm bảo chất lượng không suy giảm theo thời gian.

## 4. Môi trường kiểm thử
| Môi trường | Mục đích | Dữ liệu |
|---|---|---|
| Local/Dev | Nhà phát triển tự kiểm thử trong lúc code | Dữ liệu giả lập (seed data), dùng mock cho dịch vụ AI để tiết kiệm chi phí gọi API thật |
| Staging | Chạy Integration Test, E2E Test, Performance Test | Dữ liệu gần giống thật, dùng tài khoản sandbox thật của Payoo và Azure (giới hạn quota) |
| Pilot (hiện trường) | UAT thực tế tại Chùa Linh Ứng | Dữ liệu thật, nhưng giới hạn số lượng người tham gia thử nghiệm ban đầu |

## 5. Tiêu chí hoàn thành kiểm thử (Exit Criteria)
- 100% các kịch bản E2E ở mục 2.3 chạy thành công.
- Không còn lỗi mức Critical nào tồn đọng từ UAT trước khi chuyển sang vận hành chính thức.
- Các chỉ tiêu hiệu năng ở mục 2.4 đạt yêu cầu.
- Bộ câu hỏi kiểm thử chatbot ở mục 3 đạt tỉ lệ trả lời chấp nhận được (được đánh giá thủ công bởi nhóm thực hiện đồ án, ví dụ tối thiểu 80% câu trả lời được đánh giá là chính xác/hợp lý).
