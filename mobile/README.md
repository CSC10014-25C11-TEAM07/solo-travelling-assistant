# Solo Travelling Assistant

App hỗ trợ lập và điều chỉnh lịch trình du lịch một mình.

## Công nghệ

- Mobile dùng React Native, Expo và TypeScript.
- Backend dùng Python và FastAPI.

## Chạy backend trên Windows

Mở Terminal tại thư mục gốc của repo:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

Kiểm tra trên máy tính tại http://127.0.0.1:8002/health.

## Chạy mobile

Cần Node.js LTS và Expo Go trên điện thoại.
Mở một Terminal khác tại thư mục gốc của repo:

```powershell
cd mobile
npm.cmd ci
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Chạy `ipconfig` để tìm IPv4 của máy tính.
Sửa `EXPO_PUBLIC_API_URL` trong `mobile/.env` thành
`http://IPV4_CUA_MAY_TINH:8002`.

Sau đó chạy:

```powershell
npx.cmd expo start
```

Điện thoại và máy tính dùng cùng Wi-Fi.
Quét mã QR bằng Expo Go. Với iPhone, dùng Camera để quét
và đăng nhập Expo Go cùng tài khoản với Expo CLI.

Mở `http://IPV4_CUA_MAY_TINH:8002/health` trên trình duyệt của điện thoại.
Khi thấy `{"status":"ok"}`, quay lại Expo Go, đăng ký tài khoản thử, đăng nhập và chọn sở thích để xem gợi ý.
Nếu Uvicorn chạy cổng khác, dùng đúng cổng đó cho cả `/health` và `EXPO_PUBLIC_API_URL`.
Sau khi sửa `.env`, tải lại app. Nếu vẫn thấy địa chỉ cũ, khởi động lại Expo bằng `npx.cmd expo start --lan --clear`.

## Expo Web

Trên máy chạy Expo, mở `http://localhost:8081` sau khi nhấn **w** trong Terminal Expo.
Backend mặc định cho phép hai địa chỉ web `http://localhost:8081` và `http://127.0.0.1:8081`.
Nếu mở web bằng IP Wi-Fi hoặc cổng Expo khác, đặt danh sách địa chỉ web trong **Terminal backend** trước khi khởi động Uvicorn. Ví dụ, thay IP và cổng theo thanh địa chỉ trình duyệt:

```powershell
$env:EXPO_WEB_ORIGINS = 'http://localhost:8081,http://192.168.1.20:8081'
```

`EXPO_WEB_ORIGINS` là địa chỉ của **trang web**. `EXPO_PUBLIC_API_URL` là địa chỉ của **backend**. Expo Go trên điện thoại chỉ cần địa chỉ backend.

## Cách làm việc

Tạo nhánh riêng cho từng việc và mở Pull Request vào main.
Ghi mã Issue, cách thử và kết quả trong PR.
Người review kiểm tra trước khi ghép.
