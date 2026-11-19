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
4. Chờ tải app rồi mở màn hình đăng nhập.

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
7. Chờ tải app rồi mở màn hình đăng nhập.

#### Kết quả mong đợi

Mở Safari hoặc Chrome trên điện thoại tại `http://IPV4_CUA_MAY_TINH:8002/health`.
Khi thấy `{"status":"ok"}`, đăng ký tài khoản thử, đăng nhập và chọn một sở thích để xem gợi ý.
Nếu dùng cổng khác, thay `8002` bằng cổng Uvicorn in ra ở cả địa chỉ kiểm tra và `mobile/.env`.
Sau khi đổi cấu hình, tải lại app trong Expo Go.

### 6. Kiểm tra cấu hình kết nối

- Điện thoại và máy tính kết nối cùng Wi-Fi.
- Tạo `mobile/.env` từ `mobile/.env.example`.
- Dùng `ipconfig` để tìm IPv4 Wi-Fi của máy tính.
- Đặt `EXPO_PUBLIC_API_URL=http://IPV4_CUA_MAY_TINH:8002`.
- Giữ Terminal FastAPI và Terminal Expo chạy song song.

Nếu chạy Expo trên trình duyệt, xem [cấu hình cho Expo Web](mobile/README.md#expo-web).

## Chạy backend trên Windows

Mở Terminal tại thư mục gốc repo:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

Mở http://127.0.0.1:8002/health trên máy tính.
Kết quả mong đợi là {"status":"ok"}.

## Chạy mobile

Mở Terminal khác tại thư mục gốc repo:

```powershell
cd mobile
npm.cmd ci
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Dùng `ipconfig` để tìm IPv4 của máy tính.
Sửa `EXPO_PUBLIC_API_URL` trong `mobile/.env` thành
`http://IPV4_CUA_MAY_TINH:8002`, rồi chạy:

```powershell
npx.cmd expo start
```

Điện thoại và máy tính kết nối cùng Wi-Fi.
Mở Expo Go để quét mã QR. Với iPhone, dùng Camera quét mã,
đồng thời đăng nhập cùng tài khoản trên Expo Go và Expo CLI.

Giữ backend chạy trong suốt buổi thử.

## Dữ liệu địa điểm và API gợi ý F01

- [Bộ bàn giao 10/11: tuyến 3/4 ngày, ba ca MOCK, nguồn và phần còn thiếu](docs/DATASET-HANDOFF-BAO04.md).
- [Hướng dẫn phần việc Bảo 04, chạy thử trên Mac và các bước bàn giao](docs/F01-HUONG-DAN-BAO04.md).
- [Hợp đồng F01 và các chi tiết dữ liệu còn là đề xuất](docs/api/f01.md).
- [Nguồn, trạng thái dữ liệu và bộ kiểm thử MOCK](backend/data/README.md).

## Nạp lại lịch MOCK cho kiểm thử tích hợp

Từ thư mục gốc, dùng Python trong môi trường backend đã cài thư viện:

```bash
python -X utf8 backend/scripts/reset_demo.py
```

Lệnh khôi phục CURRENT v1 bốn ngày vào SQLite kiểm thử riêng, không dùng database
app mặc định. Xem [hướng dẫn](docs/testing/demo-reset-guide.md) để chọn lịch
3/4 ngày, catalog T15, tài khoản thử và cách đọc bằng chứng chạy lại hai lần.

## Quy tắc làm việc

Mỗi việc có nhánh riêng và mở Pull Request vào main.
PR ghi đầu ra, cách thử và kết quả, có một người review trước khi ghép.
