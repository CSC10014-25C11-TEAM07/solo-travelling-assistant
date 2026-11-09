# Hân — phạm vi và trạng thái nghiệm thu

## Phạm vi
- Đăng ký/đăng nhập, S01 chọn ngày/sở thích (F01 tối đa 3 gợi ý), S02 xem/xác nhận JSON mẫu, S03 xem/đánh dấu hoàn thành/tải lại.
- Đã loại bỏ S04–S06. `src/features/plan/adapt-handoff.ts` chỉ chuẩn bị dữ liệu `itinerary_id`, `version`, `activity_id` cho Linh; không tự mở màn ADAPT khi chưa có mã Linh.
- Chế độ demo khi không cấu hình API: lịch CURRENT được lưu trong SecureStore và có thể mở lại sau khi tắt ứng dụng; không đồng bộ máy chủ.

## Backend
- EXPO_PUBLIC_API_URL phải trỏ tới địa chỉ IP LAN của máy tính, ví dụ `http://192.168.1.10:8000` (không dùng localhost trên điện thoại).
- Auth, F01, PATCH DONE dùng các endpoint trong tài liệu đã trao đổi.
- Tạo lịch `/api/v1/itineraries/draft`, xác nhận `.../confirm`, lấy lịch `/api/v1/itineraries/current` vẫn là endpoint dự kiến: cần đối chiếu hợp đồng backend nhóm.
- Không được tuyên bố T01–T05 đạt nếu chưa kiểm thử với backend thật và Expo Go.

## Chạy
```powershell
cd .\solo-travelling-assistant\mobile
npm install
npx expo start --go --lan -c
```

## Kiểm tra thủ công
1. Không cấu hình API: chọn Xem thử lịch trình, nhập ngày đi/về 3–4 ngày, mở S02, xác nhận, S03 đánh dấu DONE, đóng mở lại ứng dụng và xem lịch.
2. Có API: đăng ký, đăng nhập, F01, tạo nháp, xác nhận, DONE, tải CURRENT; kiểm tra 401/409 và mạng lỗi.
3. Bàn giao Linh: gọi `buildAdaptHandoff(trip, activityId)` từ màn S03 sau khi tích hợp route của Linh.
