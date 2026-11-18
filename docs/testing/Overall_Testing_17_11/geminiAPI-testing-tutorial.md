# Chạy T01–T15 với Gemini thật

Bộ chạy gọi các API bằng FastAPI TestClient và dùng SQLite tạm. F02 chạy Gemini cho lịch 3/4 ngày. F05 chạy Gemini để xếp hạng các phương án khả thi cho nghỉ thêm và đổi điểm vì mưa. Catalog PLAN/ADAPT là MOCK có nhãn từ bộ bàn giao. F01 sử dụng catalog backend/data với nhãn gốc.

Hai script cần nằm cùng thư mục

- `test_t01_t15_gemini.py` là điểm chạy đủ 15 ca.
- `test_t01_t05_gemini.py` cung cấp phần PLAN được runner đầy đủ sử dụng.

## Chuẩn bị

Tạo key mới thay key đã đưa vào chat. Nhập key trực tiếp trên máy và chọn model mà tài khoản có quyền gọi. Cần có các thư viện backend hiện có, gồm fastapi, httpx, pydantic và argon2-cffi. Adapter Gemini dùng REST qua thư viện chuẩn Python.

Mở PowerShell ở gốc repo

```powershell
cd "\...\solo-travelling-assistant"

$secret = Read-Host "Nhap Gemini key moi" -AsSecureString
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new("", $secret).Password
$env:GEMINI_MODEL = Read-Host "Nhap ten model"
$env:PYTHONUTF8 = "1"
```

Nếu môi trường Python đang dùng chưa có thư viện backend, cài bằng chính Python đó

```powershell
python -m pip install -r requirements.txt
```

## Chạy toàn bộ

```powershell
python docs/testing/Overall_Testing_17_11/test_t01_t15_gemini.py --repo ".../solo-travelling-assistant"
```

Mỗi lần gọi Gemini có giới hạn 60 giây. Cả bộ có nhiều lượt gọi model, có thể mất vài phút và sử dụng quota hoặc phát sinh phí theo tài khoản. Nếu một ca báo FAIL/ERROR, runner ghi nhận và tiếp tục các ca còn độc lập. Mã thoát 0 tương ứng tất cả kiểm tra trong script đạt, mã 1 tương ứng có ca chưa đạt.

## Phạm vi từng ca

| Ca | Thao tác kiểm tra | Vai trò Gemini |
|---|---|---|
| T01 | Đăng ký, trùng tài khoản, sai mật khẩu, đăng nhập | API tài khoản |
| T02 | Đổi coffee/nature, kiểm tối đa 3 gợi ý và nhãn sở thích | API F01 |
| T03 | Tạo nháp 3 ngày và 4 ngày, kiểm lịch và ràng buộc | Hai lượt gọi Gemini thật |
| T04 | Thiếu ngày về, ngày về trước ngày đi | Chặn trước khi gọi model |
| T05 | Xác nhận hai lịch, DONE, tăng version, đọc lại sau tạo app instance mới | Dùng lịch do F02 đã gọi Gemini tạo ra |
| T06 | Nghỉ đến 15:00, có DROP và giữ hạn kết thúc | Gemini xếp hạng phương án khả thi |
| T07 | Hai ưu tiên giữ khác nhau, kiểm phương án đầu giữ hoạt động ưu tiên | Hai lượt gọi Gemini |
| T08 | Nghỉ đến 16:30, cần thêm chặng đi nên không khả thi | Bộ kiểm ràng buộc trả options rỗng trước model |
| T09 | REJECT nghỉ thêm, gửi lại REJECT và giữ lịch | Gemini tạo đề xuất trước quyết định |
| T10 | ACCEPT nghỉ thêm, gửi lại, kiểm bảo toàn DONE và đọc lại | Gemini tạo đề xuất trước quyết định |
| T11 | Tạo đề xuất rồi cập nhật lịch, chặn ACCEPT đề xuất cũ | Gemini tạo đề xuất trước khi version thay đổi |
| T12 | Mô phỏng timeout AI, lỗi SQLite sau ghi, kiểm rollback và thử ACCEPT lại | Timeout được mô phỏng có nhãn; đề xuất dùng kiểm lỗi lưu gọi Gemini thật |
| T13 | Đổi điểm khi mưa, kiểm INDOOR, lịch sử, ACCEPT và đọc lại | Gemini xếp hạng phương án |
| T14 | REJECT đổi điểm và giữ lịch | Gemini tạo đề xuất trước quyết định |
| T15 | Catalog không có điểm trong nhà phù hợp, trả lý do | Không gọi model khi thiếu phương án hợp lệ |

T06–T15 dùng reset fixture 4 ngày độc lập để tái lập các kịch bản. T01–T05 kiểm cả 3/4 ngày. T10 chọn phương án đầu của model và so sánh lịch đã lưu với chính phương án đó.

## Đọc kết quả

Thư mục `runs/<mốc UTC>/` được tạo mới cho mỗi lần chạy

| File | Nội dung |
|---|---|
| `summary.json` | Trạng thái T01–T15 và tổng số lần gọi model |
| `plan/T01-T05-results.json` | Kết quả PLAN, SHA256 các file tham chiếu, dataset_version, model, latency và token |
| `adapt/T06-T15-results.json` | Đề xuất, quyết định, kết quả ADAPT và các lần gọi model theo ca |

`gemini_calls` có `status=PASS` cùng thông tin audit từ adapter khi nhận phản hồi hợp lệ. Lỗi HTTP phía Gemini được phản ánh qua lỗi API. Key, mật khẩu và access token được giữ trong bộ nhớ của runner và được loại khỏi dữ liệu báo cáo. Tránh tự thêm lệnh in biến môi trường hoặc token vào log.

## Cách diễn giải kết quả

Runner cấu hình provider F02 và chèn GeminiRanker vào engine F05 trong tiến trình kiểm thử. Việc cấu hình này cho phép kiểm API, SQLite và logic với model thật khi backend mặc định còn chờ tích hợp. Kết quả cần được ghi rõ là kiểm thử với cấu hình tích hợp riêng của runner.

Các thao tác trên app, thông báo UI, thao tác thử lại, SecureStore, timeout mobile và kết nối điện thoại cần được kiểm tiếp qua Expo Go trên bản backend chạy chung. T05 khởi tạo lại app instance, chưa kiểm khởi động lại tiến trình hệ điều hành. Các kết quả trong bảng nghiệm thu cần ghi đúng phạm vi bằng chứng.

Trước bàn giao, script đã được kiểm cú pháp và chạy kiểm tra 15 ca với phản hồi AI giả lập trong workspace. Lượt đó có mục đích xác minh script, chưa phải kết quả Gemini thật. Kết quả xác minh giả lập được giữ trong work và không đưa vào thư mục runs của repo.
