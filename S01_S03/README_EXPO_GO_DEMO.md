# Chạy S01–S03 khi chưa có backend

Bản này cho phép dùng luồng Đăng ký/Đăng nhập (giao diện) → S01 → S02 → S03 ở chế độ trải nghiệm mà không cần API. Không tạo tài khoản thật, không gửi hoặc lưu mật khẩu demo. Nếu cấu hình EXPO_PUBLIC_API_URL, ứng dụng chuyển sang dùng API xác thực và PLAN như mã nguồn hiện có.

- S01: chọn ngày 3–4 ngày, sở thích, địa điểm; tạo lịch JSON mẫu.
- S02: xem lịch, chỉnh giờ, xác nhận.
- S03: đánh dấu hoàn thành, lưu lịch demo bằng SecureStore và mở lại sau khi khởi động lại app.
- Chưa xác nhận API thật và chưa kiểm thử trên điện thoại trong môi trường này.

Chạy: cd mobile; npm install; npx expo start --go --lan -c
Điện thoại và máy tính dùng chung Wi-Fi.

Lưu ý: Nếu muốn đăng ký/đăng nhập thật, cần backend đang chạy và EXPO_PUBLIC_API_URL trỏ đến IP LAN máy tính (không dùng localhost trên điện thoại).
