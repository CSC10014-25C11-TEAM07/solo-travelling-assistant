# Solo Travelling Assistant

App hỗ trợ lập và điều chỉnh lịch trình du lịch một mình.

## Công cụ cần có

- Git
- Node.js LTS và npm
- Python 3.10 trở lên
- Expo Go trên điện thoại

## Chạy backend trên Windows

Mở Terminal tại thư mục gốc repo:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0
```

Mở http://127.0.0.1:8000/health trên máy tính.
Kết quả mong đợi là {"status":"ok"}.

## Chạy mobile

Mở Terminal khác tại thư mục gốc repo:

```powershell
cd mobile
npm.cmd ci
Copy-Item .env.example .env
```

Dùng `ipconfig` để tìm IPv4 của máy tính.
Sửa `EXPO_PUBLIC_API_URL` trong `mobile/.env` thành
`http://IPV4_CUA_MAY_TINH:8000`, rồi chạy:

```powershell
npx.cmd expo start
```

Điện thoại và máy tính kết nối cùng Wi-Fi.
Mở Expo Go để quét mã QR. Với iPhone, dùng Camera quét mã,
đồng thời đăng nhập cùng tài khoản trên Expo Go và Expo CLI.

Giữ backend chạy và bấm **Kiểm tra backend** trên app.
Kết quả mong đợi là **Kết nối backend thành công! Status: ok**.

## Quy tắc làm việc

Mỗi việc có nhánh riêng và mở Pull Request vào main.
PR ghi đầu ra, cách thử và kết quả, có một người review trước khi ghép.