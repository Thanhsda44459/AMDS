# Quy tắc trình bày câu trả lời

## 1. Ngôn ngữ
- Luôn trả lời bằng **tiếng Việt**, kể cả khi câu hỏi bằng tiếng Anh.
- Comment trong code cũng viết bằng **tiếng Việt**.
- Giữ nguyên tiếng Anh cho: tên biến, tên hàm, tên class, keyword, tên thư viện, và thuật ngữ kỹ thuật không có bản dịch chuẩn.

## 2. Khi gặp thuật ngữ mới
- Thêm giải thích ngắn **trong ngoặc đơn ngay cạnh thuật ngữ**, tối đa 1 câu.
- Ví dụ: `event loop (vòng lặp sự kiện xử lý tác vụ bất đồng bộ)`, `singleton (một instance duy nhất dùng chung toàn ứng dụng)`.
- Chỉ giải thích lần đầu xuất hiện, các lần sau không lặp lại.

## 3. Cấu trúc câu trả lời cho một task kỹ thuật
Trình bày theo đúng thứ tự sau:

1. **Giải thích lý do** — ví dụ tiêu đề: "Giải thích: Tại sao dùng Motor (Async) thay vì pymongo (Sync)?". Viết văn xuôi, ngắn gọn, tập trung vào "tại sao". **Không dùng bảng ASCII/box-drawing**. Nếu cần so sánh, viết thành câu hoặc bullet đơn giản.
2. **Code implementation** — đặt trong file/module cụ thể, kèm đường dẫn (ví dụ `backend/app/db.py`).
3. **Các bước thực hiện** — trình bày dạng sơ đồ cây ASCII đơn giản (xem mẫu bên dưới), **không dùng bảng**.
4. **Code sử dụng** — ví dụ cách gọi trong file khác (như `main.py`).
5. **Checklist** — dạng `- [x]` hoặc `- [ ]`, mỗi dòng một việc, không dùng bảng.
6. **Chạy thử (Verification)** — luôn có, dạng khối `bash` với comment giải thích từng bước và "Expected output" (kết quả mong đợi).

## 4. Mẫu "Các bước thực hiện" (bắt buộc theo format này)
