# 04. Use Cases — LinhUngGuide

Tài liệu mô tả các luồng sử dụng chính bằng lời (không dùng sơ đồ), theo cấu trúc: Tác nhân — Điều kiện tiên quyết — Luồng chính — Luồng phụ/ngoại lệ — Kết quả.

---

## UC-01: Thanh toán trực tuyến để vào tham quan

**Tác nhân chính**: Khách tham quan
**Tác nhân phụ**: Cổng thanh toán Payoo, hệ thống Backend

**Điều kiện tiên quyết**: Khách đã quét mã QR và mở web app; khách chưa có access token hợp lệ.

**Luồng chính**:
1. App hiển thị màn hình "Pay to Access Features" với hai lựa chọn: thanh toán online hoặc tiền mặt.
2. Khách chọn "Pay Now (Online)".
3. Frontend gửi yêu cầu tới backend để lấy liên kết thanh toán.
4. Backend sinh một mã xác thực tạm thời (auth_code) gắn với phiên hiện tại, gọi sang Payoo để tạo một liên kết thanh toán có chứa mã này, rồi trả liên kết đó về cho frontend.
5. Frontend chuyển hướng khách sang trang thanh toán của Payoo.
6. Khách hoàn tất thanh toán trên giao diện Payoo (ví điện tử, ngân hàng, thẻ nội địa...).
7. Payoo gửi thông báo thanh toán thành công về backend (dưới dạng webhook) kèm theo auth_code tương ứng.
8. Backend đánh dấu giao dịch là đã thanh toán và chuyển hướng khách trở lại web app, mang theo auth_code.
9. Frontend dùng auth_code gọi backend để đổi lấy access token; vì có độ trễ giữa bước 7 và bước 9, frontend sẽ thử lại một vài lần theo chu kỳ ngắn cho tới khi backend xác nhận thanh toán đã ghi nhận hoặc đạt số lần thử tối đa.
10. Khi backend xác nhận thanh toán hợp lệ, backend trả về access token; frontend lưu token này lại trên thiết bị và mở khoá toàn bộ tính năng tham quan.

**Luồng phụ**:
- 6a. Khách rời trang thanh toán mà không hoàn tất: ở bước 9, backend trả trạng thái "đang chờ thanh toán"; frontend hiển thị thông báo và cho phép khách thử lại.
- 9a. Vượt quá số lần thử lại tối đa mà vẫn chưa nhận được xác nhận: app hiển thị hướng dẫn liên hệ nhân viên hỗ trợ.

**Kết quả**: Khách có access token hợp lệ và được phép sử dụng toàn bộ tính năng của app trong thời hạn phiên.

---

## UC-02: Thanh toán tiền mặt để vào tham quan

**Tác nhân chính**: Khách tham quan
**Tác nhân phụ**: Nhân viên, hệ thống Backend, Redis

**Điều kiện tiên quyết**: Khách đã mở web app, chưa có access token hợp lệ.

**Luồng chính**:
1. Khách chọn "Pay with Cash" trên màn hình thanh toán.
2. App hiển thị hướng dẫn "vui lòng thanh toán tiền mặt tại quầy, đưa mã số phiên (session_id) cho nhân viên".
3. Khách đến quầy, đưa tiền mặt và mã số phiên cho nhân viên.
4. Nhân viên xác nhận đã thu tiền trên giao diện quản trị dành cho nhân viên.
5. Backend ghi nhận giao dịch là đã thanh toán, tạo một phiên (session) và sinh một mã xác thực tạm thời (auth_code).
6. Backend rút gọn mã xác thực này thành một mã ngắn, dễ đọc (shortened_code) và lưu tạm vào Redis kèm thời hạn sử dụng.
7. Backend hiển thị mã ngắn này trên giao diện của nhân viên.
8. Nhân viên đọc/đưa mã ngắn lại cho khách.
9. Khách nhập mã ngắn vào app.
10. Frontend gửi mã ngắn lên backend để đổi lấy access token; backend kiểm tra mã trong Redis, nếu hợp lệ sẽ sinh access token và trả về cho khách.
11. Frontend lưu access token và mở khoá các tính năng của app.

**Luồng phụ**:
- 9a. Khách nhập sai mã hoặc mã đã hết hạn trong Redis: backend trả lỗi, app yêu cầu khách quay lại quầy để lấy mã mới.

**Kết quả**: Khách có access token hợp lệ tương đương với luồng thanh toán online.

---

## UC-03: Xem thông tin và nghe thuyết minh một điểm tham quan (POI)

**Tác nhân chính**: Khách tham quan (đã có access token hợp lệ)

**Điều kiện tiên quyết**: Toàn bộ dữ liệu POI (mô tả đa ngôn ngữ, audio, toạ độ) đã được nạp về frontend ngay sau khi xác thực thành công, theo đúng nguyên tắc "nạp một lần, không gọi lại" được quy định trong PRD gốc.

**Luồng chính**:
1. Khách nhìn thấy các icon POI trên bản đồ, trong đó POI nằm gần vị trí hiện tại được làm nổi bật.
2. Khách chạm vào một icon POI.
3. App mở một thẻ thông tin chứa: tên POI, mô tả văn bản theo ngôn ngữ đang chọn, hình ảnh minh hoạ, và nút phát audio.
4. Khách bấm phát audio; app phát file âm thanh thuyết minh tương ứng với ngôn ngữ hiện tại.
5. Nếu khách đổi ngôn ngữ ngay trong lúc xem, nội dung văn bản và audio cập nhật theo ngôn ngữ mới mà không cần tải lại trang, vì toàn bộ bản dịch của tất cả ngôn ngữ đã có sẵn ở frontend.

**Luồng phụ**:
- 4a. Thiết bị đang ở chế độ im lặng hoặc không hỗ trợ phát audio tự động: app hiển thị nút phát thủ công và cảnh báo nhẹ.

**Kết quả**: Khách hiểu được nội dung của POI bằng ngôn ngữ mình lựa chọn.

---

## UC-04: Tự động gợi ý nội dung khi khách đến gần một POI (Geofencing)

**Tác nhân chính**: Khách tham quan
**Tác nhân phụ**: Module định vị trên frontend

**Luồng chính**:
1. App liên tục theo dõi toạ độ GPS của thiết bị (khi được cấp quyền).
2. App tính khoảng cách giữa vị trí hiện tại và toạ độ của từng POI đã nạp sẵn.
3. Khi khoảng cách nhỏ hơn hoặc bằng bán kính (range of proximity) được cấu hình cho một POI cụ thể, app coi như khách đã "vào vùng" của POI đó.
4. App hiển thị một thông báo nổi (hoặc rung nhẹ nếu thiết bị hỗ trợ) mời khách nghe thuyết minh, đồng thời tự mở thẻ thông tin của POI.
5. Nếu khách không thao tác trong vài giây, hệ thống có thể tự phát audio ở chế độ nền (tuỳ theo cấu hình bật/tắt tự động phát mà khách đã chọn).

**Luồng phụ**:
- 1a. Khách từ chối quyền truy cập vị trí: tính năng tự động gợi ý bị vô hiệu hoá; khách vẫn có thể chạm thủ công vào từng POI để xem nội dung (rơi về luồng UC-03).

**Kết quả**: Khách nhận được trải nghiệm thuyết minh liền mạch như có hướng dẫn viên đi cùng, không cần thao tác tìm kiếm thủ công.

---

## UC-05: Hỏi đáp với Chatbot AI (RAG)

**Tác nhân chính**: Khách tham quan
**Tác nhân phụ**: Dịch vụ AI (Azure OpenAI — mô hình sinh câu trả lời và mô hình embedding), CSDL vector

**Luồng chính**:
1. Khách mở khung chat và nhập câu hỏi bằng ngôn ngữ tự nhiên, ở bất kỳ ngôn ngữ nào trong danh sách hỗ trợ.
2. Frontend gửi câu hỏi kèm access token tới dịch vụ chatbot ở backend.
3. Backend chuyển câu hỏi của khách thành một vector embedding bằng mô hình embedding.
4. Backend dùng vector này để tìm kiếm những đoạn nội dung liên quan nhất trong kho tri thức đã được lập chỉ mục trước đó (mô tả các POI và tài liệu bổ sung về chùa).
5. Backend gửi câu hỏi gốc cùng với các đoạn nội dung liên quan tìm được (ngữ cảnh) tới mô hình sinh câu trả lời (ví dụ GPT-4o mini), kèm hướng dẫn chỉ trả lời dựa trên ngữ cảnh được cung cấp và trả lời đúng ngôn ngữ của câu hỏi.
6. Mô hình sinh ra câu trả lời; backend trả câu trả lời này về cho frontend, kèm theo hình ảnh minh hoạ nếu có POI liên quan được xác định.
7. Frontend hiển thị câu trả lời và hình ảnh (nếu có) trong khung chat.

**Luồng phụ**:
- 4a. Không tìm thấy nội dung liên quan đủ tin cậy trong kho tri thức: mô hình được hướng dẫn trả lời thành thật rằng chưa có đủ thông tin, thay vì suy đoán, và có thể gợi ý khách hỏi nhân viên tại chỗ.
- 2a. Access token không hợp lệ/hết hạn: backend từ chối yêu cầu, frontend đưa khách quay lại luồng thanh toán.

**Kết quả**: Khách nhận được câu trả lời chính xác, có căn cứ, bằng đúng ngôn ngữ đã hỏi.

---

## UC-06: Quản trị viên thêm/sửa một điểm tham quan (POI) và tự động dịch nội dung

**Tác nhân chính**: Quản trị viên
**Tác nhân phụ**: Data pipeline dịch thuật & TTS, CSDL, Storage

**Điều kiện tiên quyết**: Quản trị viên đã đăng nhập vào admin dashboard.

**Luồng chính**:
1. Quản trị viên mở màn hình quản lý POI, chọn "Thêm mới" hoặc chọn một POI hiện có để chỉnh sửa.
2. Quản trị viên nhập/sửa: tên POI, mô tả gốc (thường bằng tiếng Việt), toạ độ, bán kính phạm vi, hình ảnh thumbnail.
3. Quản trị viên lưu thay đổi.
4. Backend lưu bản ghi POI vào cơ sở dữ liệu chính và kích hoạt data pipeline xử lý bất đồng bộ (không bắt quản trị viên phải chờ).
5. Pipeline lần lượt: (a) dịch mô tả gốc sang toàn bộ ngôn ngữ được hỗ trợ (tối thiểu 15 ngôn ngữ), (b) với mỗi bản dịch, sinh file audio thuyết minh tương ứng bằng dịch vụ chuyển văn bản thành giọng nói, (c) lưu các file audio vào kho lưu trữ đối tượng, (d) cập nhật bản ghi POI trong cơ sở dữ liệu với đường dẫn tới từng bản dịch và file audio, (e) cập nhật chỉ mục vector cho chatbot để nội dung mới cũng có thể được chatbot tham chiếu khi trả lời câu hỏi.
6. Khi pipeline hoàn tất, admin dashboard hiển thị trạng thái "đã sẵn sàng" cho POI đó; nếu có bước nào lỗi (ví dụ dịch vụ dịch thuật tạm thời không phản hồi), dashboard hiển thị trạng thái lỗi kèm khả năng thử lại.

**Kết quả**: POI mới/được cập nhật có đầy đủ nội dung đa ngôn ngữ mà quản trị viên không cần tự dịch hay tự thu âm.

---

## UC-07: Nhân viên xác nhận thanh toán tiền mặt

Đã mô tả chi tiết trong UC-02 (bước 3 đến 8), với tác nhân chính lúc này là Nhân viên: nhân viên thao tác trên một giao diện quản trị đơn giản, nhập/khớp session_id, xác nhận số tiền đã thu, và hệ thống tự sinh mã ngắn để giao lại cho khách. Nhân viên không cần truy cập bất kỳ dữ liệu quản trị nào khác ngoài phạm vi xác nhận thanh toán.

---

## UC-08: Quản trị viên theo dõi tình trạng hệ thống

**Tác nhân chính**: Quản trị viên

**Luồng chính**:
1. Quản trị viên mở màn hình Monitoring Dashboard.
2. Dashboard truy vấn định kỳ các chỉ số vận hành: tình trạng hoạt động của backend, độ trễ trung bình các API chính, tỉ lệ lỗi, số phiên đang hoạt động, số lượt xem theo từng POI, số câu hỏi chatbot đã xử lý trong khoảng thời gian gần nhất.
3. Dashboard hiển thị các chỉ số này dưới dạng số liệu và biểu đồ thời gian thực; nếu một chỉ số vượt ngưỡng cảnh báo (ví dụ tỉ lệ lỗi cao bất thường), dashboard làm nổi bật cảnh báo đó.

**Kết quả**: Quản trị viên nắm được sức khoẻ hệ thống và mức độ sử dụng để ra quyết định vận hành kịp thời.
