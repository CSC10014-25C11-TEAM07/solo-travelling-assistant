# Solo Travelling Assistant

App hỗ trợ lập và điều chỉnh lịch trình du lịch một mình.

## Công cụ cần có

- Git
- Node.js LTS và npm
- Python 3.10 trở lên
- Expo Go trên điện thoại
## Chuẩn bị môi trường trên Windows

Mỗi thành viên thực hiện một lần trên máy của mình.

### 1. Cài công cụ

- Cài Git từ https://git-scm.com/install/windows.
- Cài Node.js bản LTS từ https://nodejs.org/en/download.
  Bộ cài Node.js đi kèm npm và npx.
- Cài Python từ https://www.python.org/downloads/windows/.
- Cài Expo Go trên điện thoại từ Google Play hoặc App Store.

Bộ khung đã chạy thử trên máy Leader với Node.js 26.13.0,
npm 11.20.0 và Python 3.14.7.

Sau khi cài, đóng và mở lại VS Code để Terminal nhận công cụ mới.

### 2. Kiểm tra cài đặt

Mở Terminal trong VS Code và chạy:

```powershell
git --version
node --version
npm.cmd --version
py --version
```

Mỗi lệnh cần hiện số phiên bản. Nếu máy chỉ nhận lệnh `python`,
dùng `python` thay cho `py` trong bước tạo môi trường backend.

Nếu lệnh nào báo `not recognized`, kiểm tra lại công cụ đó đã
được cài và đã mở lại VS Code chưa.

### 3. Clone và mở đúng thư mục

Chấp nhận lời mời vào repo Private của nhóm.

Trên GitHub, chọn Code → HTTPS và sao chép URL repo.
Trong VS Code, nhấn Ctrl + Shift + P, chọn Git: Clone,
dán URL và chọn thư mục lưu.

Sau khi clone, mở thư mục `solo-travelling-assistant`.
Trong thư mục này cần có `mobile/`, `backend/` và `README.md`.

### 4. Hiểu các lệnh chạy mobile

- `npm.cmd ci` cài các thư viện theo `package-lock.json` của nhóm.
  Chạy lần đầu sau khi clone hoặc khi thư viện của dự án thay đổi.
- `npx.cmd expo start` khởi động Expo và hiện mã QR để mở app.
  Chạy lệnh này tại thư mục `mobile/`.

### 5. Mở app trên Android hoặc iPhone

Giữ backend đang chạy. Mở Terminal khác tại thư mục `mobile/`:

```powershell
npx.cmd expo start
```

Khi mã QR xuất hiện, thực hiện theo loại điện thoại.

#### Android

1. Cài Expo Go từ Google Play.
2. Kết nối điện thoại và máy tính cùng Wi-Fi.
3. Mở Expo Go, chọn Scan QR code và quét mã trong Terminal.
4. Chờ tải app, sau đó bấm Kiểm tra backend.

#### iPhone

1. Cài Expo Go từ App Store.
2. Trong Terminal tại thư mục `mobile/`, chạy:

```powershell
npx.cmd expo login
npx.cmd expo whoami
```

3. Hoàn tất đăng nhập và kiểm tra `whoami` hiện đúng tài khoản.
4. Đăng nhập cùng tài khoản đó trong Expo Go trên iPhone.
5. Kết nối iPhone và máy tính cùng Wi-Fi.
6. Dùng Camera mặc định quét mã QR, bấm mở trong Expo Go.
7. Chờ tải app, sau đó bấm Kiểm tra backend.

#### Kết quả mong đợi

App hiển thị:
“Kết nối backend thành công! Status: ok”.

Nếu chưa kết nối được, mở trình duyệt trên điện thoại và thử:
`http://IPV4_CUA_MAY_TINH:8000/health`.

Kiểm tra backend đang chạy, hai thiết bị cùng Wi-Fi
và IPv4 trong `mobile/.env` đúng với máy chạy backend.
Sau khi sửa `.env`, khởi động lại Expo và mở lại app.

### 6. Kiểm tra cấu hình kết nối

- Điện thoại và máy tính kết nối cùng Wi-Fi.
- Tạo `mobile/.env` từ `mobile/.env.example`.
- Dùng `ipconfig` để tìm IPv4 Wi-Fi của máy tính.
- Đặt `EXPO_PUBLIC_API_URL=http://IPV4_CUA_MAY_TINH:8000`.
- Giữ Terminal FastAPI và Terminal Expo chạy song song.

Mở địa chỉ `/health` trên Safari hoặc Chrome điện thoại trước.
Khi thấy `{"status":"ok"}`, mở app Expo và bấm Kiểm tra backend.

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

## Dữ liệu địa điểm và API gợi ý F01

- [Hướng dẫn phần việc Bảo 04, chạy thử trên Mac và các bước bàn giao](docs/F01-HUONG-DAN-BAO04.md).
- [Hợp đồng F01 và các chi tiết dữ liệu còn là đề xuất](docs/api/f01.md).
- [Nguồn, trạng thái dữ liệu và bộ kiểm thử MOCK](backend/data/README.md).

## Quy tắc làm việc

Mỗi việc có nhánh riêng và mở Pull Request vào main.
PR ghi đầu ra, cách thử và kết quả, có một người review trước khi ghép.
