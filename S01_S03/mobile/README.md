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
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0
```

Kiểm tra trên máy tính tại http://127.0.0.1:8000/health.

## Chạy mobile

Cần Node.js LTS và Expo Go trên điện thoại.
Mở một Terminal khác tại thư mục gốc của repo:

```powershell
cd mobile
npm.cmd ci
Copy-Item .env.example .env
```

Chạy `ipconfig` để tìm IPv4 của máy tính.
Sửa `EXPO_PUBLIC_API_URL` trong `mobile/.env` thành
`http://IPV4_CUA_MAY_TINH:8000`.

Sau đó chạy:

```powershell
npx.cmd expo start
```

Điện thoại và máy tính dùng cùng Wi-Fi.
Quét mã QR bằng Expo Go. Với iPhone, dùng Camera để quét
và đăng nhập Expo Go cùng tài khoản với Expo CLI.

Bấm **Kiểm tra backend** trên app.
Kết quả mong đợi là **Kết nối backend thành công! Status: ok**.

## Cách làm việc

Tạo nhánh riêng cho từng việc và mở Pull Request vào main.
Ghi mã Issue, cách thử và kết quả trong PR.
Người review kiểm tra trước khi ghép.