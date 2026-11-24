# Bản Android chính và bản thử

Bản cài chính dùng kênh Expo Update `main`. Bản nghiệm thu ban đầu dùng kênh `main-qa`, nên cập nhật thử không tới bản chính. Hai bản đầu này dùng cùng mã định danh và chữ ký Android của nhóm. Dùng một thiết bị thử hoặc sao lưu lịch thử trước khi thay bản cài.

## Thử nhận cập nhật qua mạng

1. Cài APK từ lượt build `main-qa` được gắn trong PR. Người đang dùng APK trước Giai đoạn 1 cần cài bản hỗ trợ Expo Update một lần.
2. Đăng nhập tài khoản thử, tạo và lưu một lịch.
3. Khi người triển khai báo đã phát bản cập nhật thử trên `main-qa`, mở app khi có mạng. Chờ app tải cập nhật, đóng rồi mở lại.
4. Kiểm tra thay đổi mà người triển khai mô tả đã hiện và lịch đã lưu vẫn mở được. Nếu thay đổi phần Android, hệ thống phải đóng APK tương thích trước.

## Link cài của bản chính

Link cố định sau lần phát hành chính thức đầu tiên:
https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/releases/download/android-main/solo-travelling-assistant.apk

Chỉ gắn file cài đã kiểm thử và có kênh `main` vào GitHub Release mang tag `android-main`. Đặt tên file là `solo-travelling-assistant.apk`. Các cập nhật qua mạng không cần đổi file tải. Khi có APK chính thức mới, thay file tại đúng release đó và kiểm tra lại link. Giữ lượt build hoặc APK trước để khôi phục khi cần.

Mỗi lượt phát hành cập nhật phải trỏ vào kênh đã định, dùng cùng môi trường API với bản cài và có phiên bản tương thích của phần Android. Khi chưa nghiệm thu trên điện thoại, dùng kênh `main-qa` và link build riêng trong PR.
