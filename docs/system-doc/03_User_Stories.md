# 03 — User Stories (Góc nhìn người dùng)

Định dạng: **Là một [vai trò], tôi muốn [việc], để [lợi ích].** Mỗi story có tiêu chí chấp nhận (AC).
Vai trò: **Du khách** (khách, không cần đăng nhập), **Chủ quán** (poi_owner), **Admin**, **Super Admin**.

## Epic 1 — Khởi động và ngôn ngữ (Du khách)

**US-01.** Là du khách, tôi muốn chọn ngôn ngữ ngay khi mở app, để mọi nội dung hiển thị bằng ngôn ngữ tôi hiểu.
- AC: Sau splash, có màn chọn ngôn ngữ; các ngôn ngữ chính vi, en, zh, ja, ko luôn có.
- AC: Chọn xong, giao diện đổi sang ngôn ngữ đó.

**US-02.** Là du khách, tôi muốn app mở nhanh dù mạng chậm, để không phải chờ lâu.
- AC: Nếu đã có dữ liệu lưu trong máy, app hiển thị ngay từ dữ liệu đó trong lúc cập nhật nền.
- AC: App có thể bắt đầu bằng tiếng Anh rồi tự chuyển sang ngôn ngữ đích khi sẵn sàng.

**US-03.** Là du khách, tôi muốn đổi ngôn ngữ giữa chừng mà không bị lỗi nội dung nửa vời, để trải nghiệm liền mạch.
- AC: Chỉ khi cả nội dung các POI gần nhất và giao diện đều sẵn sàng thì app mới coi là đã đổi xong.

## Epic 2 — Khám phá bản đồ (Du khách)

**US-10.** Là du khách, tôi muốn xem bản đồ các quán ăn quanh mình, để chọn nơi muốn ghé.
- AC: Bản đồ hiển thị các POI đang hoạt động; bấm vào POI thấy tên, mô tả, ảnh, thực đơn.

**US-11.** Là du khách, tôi muốn bấm nút định vị để biết mình đang ở đâu, để dễ so với các quán xung quanh.
- AC: App dùng vị trí gần nhất còn đủ tốt nếu có; nếu không, chờ tối đa 15 giây rồi thông báo.

**US-12.** Là du khách, tôi muốn chọn kiểu bản đồ (online, offline, kết hợp), để dùng được cả khi không có mạng.
- AC: Chế độ kết hợp tự chuyển sang bản đồ đã tải khi mất mạng và quay lại online sau một độ trễ ngắn.

## Epic 3 — Thuyết minh tự động (Du khách)

**US-20.** Là du khách, tôi muốn khi đi đến gần một quán thì app tự đọc giới thiệu, để tôi không phải nhìn màn hình.
- AC: Khi vào bán kính (mặc định 30 m) và ở lại đủ 3 giây, thuyết minh bắt đầu phát.
- AC: Cùng một quán không phát lại trong 5 phút.

**US-21.** Là du khách, tôi muốn app chọn quán phù hợp nhất khi đứng gần nhiều quán, để không bị nghe lẫn lộn.
- AC: Quán có độ ưu tiên audio cao hơn được chọn trước; nếu bằng nhau chọn quán gần hơn; chỉ phát một nội dung một lúc.

**US-22.** Là du khách, tôi muốn vẫn nghe được thuyết minh khi chưa có file âm thanh sẵn, để không bỏ lỡ thông tin.
- AC: App thử lần lượt: file sinh sẵn, dịch và đọc theo yêu cầu, đọc trực tuyến, đọc bằng giọng của thiết bị.

**US-23.** Là du khách, tôi muốn nếu đổi ngôn ngữ giữa lúc đang chờ thì không nghe nhầm ngôn ngữ cũ.
- AC: Kết quả âm thanh của ngôn ngữ cũ bị bỏ khi đã đổi sang ngôn ngữ mới.

## Epic 4 — Dùng offline (Du khách)

**US-30.** Là du khách, tôi muốn tải trước gói dữ liệu cho chuyến đi, để dùng khi không có sóng.
- AC: Gói gồm bản đồ, nội dung POI, hình ảnh và audio của ngôn ngữ đang chọn, được cài lần lượt và kiểm tra toàn vẹn trước khi dùng.
- AC: Có hiển thị trạng thái "có bản cập nhật" hoặc "cần sửa gói".

**US-31.** Là du khách, tôi muốn app không bị hỏng khi điện thoại hết dung lượng, để vẫn tải được gói quan trọng.
- AC: Khi hết chỗ, app tự xóa bộ nhớ đệm tạm (audio/ảnh lẻ) để nhường chỗ cho gói.

**US-32.** Là du khách, tôi muốn không bao giờ thấy màn hình trống khi mất mạng.
- AC: Nếu thiếu dữ liệu ngôn ngữ đã chọn, app dùng tiếng Anh, rồi tiếng Việt.

## Epic 5 — Quyền riêng tư (Du khách)

**US-40.** Là du khách, tôi muốn được hỏi trước khi bị thu thập dữ liệu sử dụng, để kiểm soát thông tin của mình.
- AC: Chưa đồng ý thì không gửi dữ liệu analytics.
- AC: Dữ liệu analytics gắn với thiết bị ẩn danh, không gắn danh tính.

## Epic 6 — Chủ quán

**US-50.** Là chủ quán, tôi muốn đăng ký tài khoản chủ quán, để đưa quán lên ứng dụng.
- AC: Điền thông tin đăng ký, hệ thống tạo tài khoản chưa xác minh và đơn trạng thái "chờ duyệt".
- AC: Số CCCD được lưu dạng mã hóa.

**US-51.** Là chủ quán, tôi muốn biết khi nào đơn đăng ký được duyệt hay bị từ chối, để biết bước tiếp theo.
- AC: Chưa được xác minh thì chỉ thấy màn hình trạng thái đăng ký; bị từ chối thì thấy ghi chú của admin.
- AC: Được duyệt thì đăng nhập vào được khu vực chủ quán.

**US-52.** Là chủ quán, tôi muốn thêm hoặc sửa thông tin quán của mình, để khách thấy thông tin đúng.
- AC: Chỉ sửa được quán của mình.
- AC: Thay đổi không lên app ngay mà chờ admin duyệt.

**US-53.** Là chủ quán, tôi muốn nhận thông báo kết quả duyệt trong app, để không phải hỏi lại admin.
- AC: Có chuông thông báo, phân biệt đã đọc/chưa đọc, bấm vào xem chi tiết kèm ghi chú.

**US-54.** Là chủ quán, tôi muốn AI giúp viết lại mô tả hấp dẫn hơn, để thu hút khách.
- AC: AI chỉ làm đẹp văn phong, không bịa thông tin; độ dài khoảng 200–300 từ.
- AC: Mỗi ngày dùng tối đa 10 lần và thấy được số lần còn lại.

**US-55.** Là chủ quán, tôi muốn quản lý thực đơn của quán, để khách xem món và giá.
- AC: Chủ quán có quyền đọc, tạo, sửa menu; không có quyền xóa.

## Epic 7 — Admin

**US-60.** Là admin, tôi muốn thêm, sửa, ẩn, xóa POI, để dữ liệu luôn đúng.
- AC: Khi sửa mô tả, hệ thống tự sinh lại audio cho 5 ngôn ngữ ưu tiên và tạm ẩn POI đến khi sẵn sàng.
- AC: Không thể bật hiển thị công khai nếu chưa sẵn sàng tiếng Anh/audio.

**US-61.** Là admin, tôi muốn theo dõi tiến độ sinh audio theo thời gian thực và có thể tạm dừng hoặc hủy, để kiểm soát tải hệ thống.
- AC: Có thanh tiến độ cập nhật tự động; có nút Pause, Resume, Cancel.

**US-62.** Là admin, tôi muốn duyệt đăng ký chủ quán và bài gửi POI, kèm ghi chú, để kiểm soát chất lượng nội dung.
- AC: Duyệt thì tài khoản được xác minh; từ chối phải kèm `admin_note`.

**US-63.** Là admin, tôi muốn xem nhật ký hành động, để truy vết khi có sự cố.
- AC: Mỗi dòng có hành động, người thực hiện, tài nguyên và thời gian.

**US-64.** Là admin, tôi muốn xem số liệu sử dụng ứng dụng, để hiểu hành vi du khách.
- AC: Có số thiết bị online ẩn danh, thống kê theo giờ/ngày.

**US-65.** Là admin, tôi muốn quản lý người dùng, để cấp hoặc thu hồi quyền.
- AC: CRUD user; gán role.

## Epic 8 — Super Admin

**US-70.** Là super admin, tôi muốn tạo và chỉnh role, để phân quyền linh hoạt mà không sửa mã.
- AC: Role lưu trong DB, gồm danh sách quyền; thay đổi có hiệu lực cho token mới.

**US-71.** Là super admin, tôi muốn có tài khoản siêu quản trị được tạo an toàn khi cài hệ thống.
- AC: Khi khởi động, hệ thống tạo role mặc định và super admin theo chế độ bootstrap cấu hình sẵn; cấu hình sai hoặc thiếu bí mật thì hệ thống từ chối chạy.

## Epic 9 — Vận hành

**US-80.** Là người vận hành, tôi muốn có endpoint kiểm tra sức khỏe, để giám sát và triển khai an toàn.
- AC: `/health` cho biết tiến trình sống; `/health/ready` cho biết đã sẵn sàng nhận tải.

**US-81.** Là người vận hành, tôi muốn khi server khởi động lại, các tác vụ audio dở dang được khôi phục, để không mất việc.
- AC: Tác vụ được lưu snapshot; tác vụ quá 5 phút không có heartbeat được xử lý lại.

## Ma trận truy vết (Story → Yêu cầu)

| User Story | Yêu cầu liên quan |
|---|---|
| US-01..03 | FR-01..05, FR-39 |
| US-10..12 | FR-10..15 |
| US-20..23 | FR-20..27, FR-30..38 |
| US-30..32 | FR-40..48 |
| US-40 | FR-80..83 |
| US-50..55 | FR-55, FR-60..66 |
| US-60..65 | FR-33..36, FR-70..75 |
| US-70..71 | FR-53..54 |
| US-80..81 | NFR-11..13 |
