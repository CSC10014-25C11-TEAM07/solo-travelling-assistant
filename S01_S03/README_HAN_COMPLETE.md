# Solo Travelling Assistant — Hân (Auth + PLAN S01–S03)

## Scope
- Đăng ký, đăng nhập, kiểm tra phiên và đăng xuất qua FastAPI cục bộ.
- S01 nhập ngày, giờ, nhóm sở thích; F01 tối đa 3 gợi ý; tạo lịch DRAFT 3–4 ngày.
- S02 xem lịch nháp, xác nhận CURRENT. Chỉnh giờ trực tiếp chỉ khả dụng ở chế độ demo chưa nối backend; cần endpoint cập nhật lịch nháp của nhóm để chỉnh giờ thật.
- S03 mở lại lịch CURRENT, đánh dấu DONE, xử lý 409 khi phiên bản thay đổi.
- Điểm bàn giao dữ liệu ADAPT: `mobile/src/features/plan/adapt-handoff.ts` (`itinerary_id`, `version`, `activity_id`). Không có S04–S06.
- Giữ ảnh nền Đà Lạt.

## Cách chạy trên Windows / Expo Go
1. Cài Node.js LTS và Python 3.11+; cài ứng dụng Expo Go trên điện thoại.
2. Giải nén ZIP. Mở PowerShell tại thư mục `solo-travelling-assistant`.
3. Chạy `./START_BACKEND.ps1` (hoặc `cd backend; py -m pip install -r requirements.txt; py -m uvicorn main:app --host 0.0.0.0 --port 8000`). Giữ cửa sổ này mở.
4. Dùng `ipconfig` để tìm **IPv4 Address** của Wi-Fi laptop. Ví dụ `192.168.1.10`.
5. Tạo `mobile/.env` với dòng `EXPO_PUBLIC_API_URL=http://IP_LAPTOP:8000` (thay IP thực tế, không dùng localhost).
6. Trong PowerShell khác chạy `./START_EXPO.ps1` (hoặc `cd mobile; npm install; npx expo start --go --lan -c`).
7. Laptop và điện thoại phải cùng Wi-Fi. Truy cập `http://IP_LAPTOP:8000/health` từ trình duyệt điện thoại, cần thấy `{"status":"ok"}`. Sau đó quét QR bằng Expo Go.
8. Nếu điện thoại không truy cập được API: kiểm tra Windows Firewall cho Python, cùng mạng Wi-Fi, và IP đúng. Nếu Expo báo không tương thích SDK, cập nhật Expo Go và đối chiếu phiên bản Expo SDK với Expo Go trên thiết bị.

## Kiểm thử API tự động
`cd backend; py test_flow.py`

## Giới hạn
- Backend trong ZIP là **backend tích hợp cục bộ để kiểm thử**, không phải API chính thức đã được nhóm phê duyệt.
- Bộ sinh lịch tạo lịch tham khảo theo sở thích, chưa dùng Gemini AI, chưa tính tuyến đường/thời gian di chuyển thực tế.
- Chưa thể bảo đảm Expo Go chạy trên mọi thiết bị vì môi trường đóng gói chưa cài đủ npm dependencies để chạy Metro thực tế.
- T01–T05 của nhóm cần đối chiếu tiêu chí gốc và kiểm thử trên thiết bị thật; bài test trong ZIP là kiểm thử luồng API, không thay thế T01–T05.
- Các lựa chọn bổ sung (ngân sách, lưu trú, v.v.) hiện là tùy chọn giao diện, chưa tham gia tạo lịch từ API.
