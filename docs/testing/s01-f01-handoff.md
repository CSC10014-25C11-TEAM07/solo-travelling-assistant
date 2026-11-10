# Kiểm tra đổi sở thích trên S01 cùng Hân

Trạng thái: **NOT_RUN trên app/thiết bị**. Chuẩn bị ngày 10/11/2026 cho bộ
bao04-handoff-2026-11-10-v1. PR giao diện #18 đang mở lúc kiểm tra; các bước dưới đây
là tiêu chí cần chạy trên bản ghép, không phải kết quả đã đạt.

## Chuẩn bị

1. Hân và Bảo 04 dùng cùng build có S01 và backend F01 đã ghép. Ghi commit frontend,
   backend, thiết bị/OS và dataset_version trước khi chạy.
2. Khởi động backend theo README; điện thoại cùng Wi-Fi. Đặt EXPO_PUBLIC_API_URL
   thành IP LAN của máy chạy backend, restart Expo sau khi đổi .env; kiểm /health trước.
3. Đăng ký tài khoản thử, đăng nhập và lấy phiên từ luồng thật; không dùng token ghi
   cứng hoặc in token/mật khẩu trong log/ảnh bằng chứng.
4. Bảo đảm backend đang đọc đúng catalog nguồn: coffee trả P006/P010/P011,
   nature+culture ưu tiên P002. Khởi động lại backend sau khi thay JSON vì có cache.

## Các ca cần quan sát

| Thao tác trên S01 | Kỳ vọng | Thực tế/Bằng chứng |
|---|---|---|
| Chọn coffee | Gọi F01 kèm Bearer; tối đa 3 thẻ, bộ này P006/P010/P011; ảnh null dùng ảnh mặc định | Chưa chạy |
| Đổi sang nature | Danh sách cập nhật theo nature, không giữ nguyên toàn bộ thẻ coffee cũ | Chưa chạy |
| Chọn nature + culture | Query interests lặp; P002 khớp hai nhãn được ưu tiên | Chưa chạy |
| Đổi sở thích liên tục khi mạng chậm | Kết quả request cũ không ghi đè lựa chọn mới | Chưa chạy |
| Bỏ hết sở thích | Xóa gợi ý cũ hoặc yêu cầu chọn sở thích rõ ràng; không hiển thị danh sách cũ như mới | Chưa chạy |
| Đăng xuất rồi dùng lại phiên cũ trong kiểm tra API | F01 trả 401; app xử lý phiên không hợp lệ, không báo lấy gợi ý thành công | Chưa chạy |

Khi kiểm tra phản hồi rỗng, dùng catalog test riêng và ghi rõ MOCK; không sửa bộ nguồn
thành dữ liệu giả để chụp một ca PASS. Khả năng API trả 0–3 kết quả đã được kiểm backend;
hiển thị empty/loading/error trên S01 vẫn phải quan sát trên build của Hân.

Lưu ảnh hoặc video cùng request đã che token, HTTP status và giờ thao tác. Chỉ đổi dòng
thực tế thành PASS/FAIL sau khi quan sát. Tân lưu bug có bước tái hiện và chạy lại sau sửa.
