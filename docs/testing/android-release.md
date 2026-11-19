# Bàn giao bản Android

Nhánh `feat/android-sourced-demo` bắt đầu từ main `26adf63`. PR #37 chứa bản sửa kết nối và biểu mẫu tài khoản. Kiểm tra trạng thái ghép của PR này trước khi đóng bản cuối.

## Chạy backend của bản Android

Chọn Python 3.12 trở lên và cài thư viện từ `requirements.txt` ở gốc repo. Trên alwaysdata chọn loại site **User program**, đặt thư mục làm việc ở gốc repo. Đặt `STA_DATABASE_PATH` thành đường dẫn tuyệt đối tới file SQLite trong thư mục dữ liệu riêng của tài khoản hosting, bên ngoài thư mục triển khai. Tạo thư mục cha trước khi chạy và chỉ cấp quyền ghi cho tài khoản chạy backend.

Đặt `ADAPT_MODE=VERIFIED`, `GEMINI_MODEL` và `GEMINI_API_KEY` trong cấu hình riêng của backend. Khởi động bằng Python của môi trường đã cài thư viện.

```sh
python -m uvicorn main:app --app-dir backend --host "$IP" --port "$PORT"
```

Kiểm tra `/health` từ mạng di động. Tạo tài khoản thử và lịch, khởi động lại backend rồi đọc lại đúng lịch trước khi nghiệm thu.

## Tạo bản cài

Đặt `EXPO_PUBLIC_API_URL` trong môi trường EAS **preview** thành URL HTTPS của backend. Biến này chỉ chứa địa chỉ công khai. Từ `mobile/`, chạy `npx eas-cli build --platform android --profile demo`. Cài APK từ kết quả build rồi thử trên Android qua 4G.

## Tiến độ kiểm chứng

- Đã nối chế độ VERIFIED vào F02 và F05, cấu hình vị trí lưu SQLite và profile APK. Hai chức năng dùng Gemini trong chế độ này. Catalog và tuyến thiếu xác minh sẽ trả lỗi dữ liệu.
- Main tại thời điểm bắt đầu có 16 điểm (1 VERIFIED), 42 chặng có hướng (28 VERIFIED). Hai tuyến nguồn vẫn mang trạng thái UNVERIFIED. Cần kiểm chứng bằng chứng cụ thể trước khi sử dụng trong lịch.
- Còn mở: hoàn thiện dữ liệu nguồn và thao tác hai ca ADAPT từ cùng lịch mẫu riêng cho người thử; chạy Gemini thật, kiểm tra máy chủ công khai, dựng APK, kiểm thử T01–T15 và điện thoại thật. Bản thử chạy RULES trước đây không dùng làm bằng chứng cho bản phát hành.
