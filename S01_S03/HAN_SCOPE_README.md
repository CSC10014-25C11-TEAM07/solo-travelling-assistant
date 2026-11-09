# Solo Travelling Assistant — Hân (Account + S01–S03)

Màn hình: Đăng nhập, Đăng ký, S01 tạo kế hoạch, S02 lịch nháp, S03 lịch hiện hành. Không chứa S04–S06 hoặc ADAPT.

## Chạy bằng Expo Go
1. Cài Node.js LTS và Expo Go.
2. Mở thư mục `solo-travelling-assistant/mobile` bằng VS Code.
3. Chạy `npm install`.
4. Chạy `npx expo start --go --lan -c`.
5. Điện thoại và laptop cùng Wi-Fi; dùng Expo Go quét QR.

Nếu cần tunnel, đăng nhập `npx expo login` trước khi chạy `npx expo start --go --tunnel -c`.

## Tình trạng tính năng
- Nếu chưa có `EXPO_PUBLIC_API_URL`, màn hình hiển thị dữ liệu minh họa; đăng ký và đăng nhập không tạo tài khoản thật.
- Để kiểm thử API thật cần backend triển khai theo hợp đồng nhóm.
- F01 chỉ hiển thị tối đa 3 địa điểm; các lựa chọn mở rộng khác là UI/demo.
