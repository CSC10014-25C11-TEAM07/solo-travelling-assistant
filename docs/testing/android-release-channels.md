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

## Bản thử theo pull request

Mỗi PR trong repo có thay đổi ứng dụng hoặc backend sẽ nhận hai link khi workflow `Android PR preview` chạy thành công. Link cài ứng dụng thử chỉ dùng lúc chưa cài bản thử tương thích. Link còn lại mở bản của PR trong ứng dụng thử. Bản thử mang tên **Solo Travelling · Bản thử** và có thể cài song song với bản chính.

1. Tạo GitHub Environment `android-preview` và lưu token Expo của dự án trong secret `EXPO_TOKEN`. Chỉ cho phép thành viên tin cậy của nhóm chạy nhánh kiểm thử với token này. PR từ fork và PR nháp bị bỏ qua.
2. Thiết lập chứng chỉ ký cho package `vn.team07.solotravellingassistant.preview` trong EAS trước khi chạy build không tương tác lần đầu.
3. Với PR sửa backend hoặc dữ liệu, đặt biến `ANDROID_QA_API_URL` trong environment thành URL HTTPS của máy chủ thử. Triển khai commit cần test vào máy chủ đó và trả SHA đầy đủ trong header `X-STA-Release` tại `/health`. Mỗi lần dùng một backend QA chung, kiểm tra lại SHA trước khi thử một PR khác.
4. Với PR chỉ sửa ứng dụng, dùng tài khoản QA riêng khi thử trên backend hiện tại.

## Phát hành từ main

Workflow **Android main release** chạy test trước. Nếu phần Android còn tương thích, EAS gửi cập nhật qua kênh `main`. Khi phần Android đổi, workflow tạo APK và cập nhật file tại link cố định. Người dùng Android cần xác nhận cài APK mới khi cập nhật phần Android. Lịch do backend lưu trong SQLite ngoài thư mục chứa mã.

### Thiết lập một lần

1. Trong GitHub, tạo environment `android-main` chỉ cho nhánh `main` triển khai. Thêm secret `EXPO_TOKEN` của Expo và `PYTHONANYWHERE_API_TOKEN` của tài khoản lưu backend. Giữ URL API công khai trong EAS production và cấu hình workflow giống nhau.
2. Trên PythonAnywhere, sao lưu file SQLite hiện hành bằng SQLite backup và giữ bản sao của `~/solo-start.sh`. Đặt `backend/scripts/pythonanywhere_start.py` của PR ở `~/solo-pythonanywhere-start.py`. Trong `~/solo-start.sh`, giữ các dòng cấu hình hiện hành và thay lệnh cuối gọi Uvicorn bằng:

   ```sh
   exec "$HOME/solo-venv/bin/python" "$HOME/solo-pythonanywhere-start.py" "$HOME/solo-backend"
   ```

3. Reload bằng PythonAnywhere và kiểm tra trang `/health`. Startup trên tiếp tục dùng backend cũ cho tới khi có bản được gửi lên. Xác nhận `STA_DATABASE_PATH` đang trỏ vào chính file SQLite hiện hành và môi trường đã cài thư viện của `requirements.txt`.
4. Sau khi nghiệm thu các bản Android và cho phép tự phát hành, đặt biến cấp repository `ANDROID_MAIN_RELEASE_ENABLED=true` rồi chạy workflow thủ công từ `main` lần đầu. Nếu repo đã bật GitHub Immutable Releases, ghi nhận cấu hình này trước khi phát hành và chọn cơ chế cho phép cập nhật asset tại cùng URL.

Mỗi lượt triển khai gói đúng thư mục backend và dữ liệu theo commit, thử startup trên SQLite tạm, rồi xác nhận SHA trên `/health` sau khi reload. Nếu bước xác nhận thất bại, workflow đặt lại bản trước và reload để kiểm tra phục hồi. Trước khi cập nhật thư viện Python hoặc đổi schema theo cách làm bản cũ không còn đọc được SQLite, chuẩn bị môi trường và kế hoạch chuyển dữ liệu riêng. Có thể lưu bản phát hành trước để khôi phục. Giữ đủ dung lượng của tài khoản PythonAnywhere khi lưu các bản cũ.
