# Overall_Testing_17_11

Thư mục tổng hợp phần việc kiểm thử của Tân cho Solo Travelling Assistant, gồm báo cáo, bảng T01–T15, log và công cụ chạy API với Gemini thật.

## Nội dung

| File | Mục đích |
|---|---|
| [reports.md](reports.md) | Báo cáo chi tiết 11 task đã thực hiện, kết quả và phần còn chờ xác minh |
| [doi-chieu-17-11.md](doi-chieu-17-11.md) | Đối chiếu code với phân công, các lỗi cần sửa và kiểm tra lại |
| [T01-T15.csv](T01-T15.csv) | Bảng ghi thao tác, mong đợi, thực tế, trạng thái và bằng chứng nghiệm thu |
| [backend-tests.log](backend-tests.log) | Log 123 bài backend, gồm 121 bài đạt và 2 lỗi môi trường |
| [plan-f03-tests.log](plan-f03-tests.log) | Log 16 bài API/SQLite đã đạt |
| [test_t01_t15_gemini.py](test_t01_t15_gemini.py) | Điểm chạy đủ T01–T15 qua API/TestClient với Gemini thật |
| [test_t01_t05_gemini.py](test_t01_t05_gemini.py) | Phần chạy T01–T05 được bộ đầy đủ sử dụng |
| [geminiAPI-testing-tutorial.md](geminiAPI-testing-tutorial.md) | Hướng dẫn cấu hình, phạm vi từng ca và cách đọc kết quả |

## Kết quả kiểm thử đã ghi nhận

| Bộ kiểm thử | Đạt | Tổng |
|---|---|---|
| Backend chính | 121 | 123 |
| PLAN/F03/F06 API và SQLite | 16 | 16 |
| Mobile F01 | 9 | 9 |
| Mobile ADAPT contract | 4 | 4 |
| **Tổng** | **150** | **152** |

Hai bài backend gặp `WinError 1314` khi tạo symbolic link và cần chạy lại trên môi trường có quyền tương ứng. Kết quả JavaScript được ghi trong báo cáo, log JavaScript riêng chưa được lưu ở đợt chạy đó.

Bản kiểm thử được sao chép từ working tree có HEAD đọc được là `ac35605cff7e35d491c2950b89358ce5cf1e92bb`, nhánh `17_11_vndt/OvrTest`. Độ khớp working tree với HEAD chưa xác định đầy đủ do lỗi quyền Git. Dataset ghi nhận là `bao04-mvp-2026-11-16-v1`.

Bộ chạy T01–T15 đã được kiểm tra hoạt động với phản hồi AI giả lập trước khi bàn giao. Thư mục hiện có thêm bằng chứng chạy Gemini thật, được ghi nhận riêng dưới đây. Kiểm thử Expo Go còn cần bổ sung.

## Lượt Gemini thật đã có bằng chứng

Lượt `20261118T044352245175Z` kết thúc lúc 11:44 ngày 18/11/2026 theo giờ Việt Nam, dùng model `gemini-3.5-flash-lite`, ghi nhận **13/15 ca PASS** và **10 lượt gọi model**, gồm 8 lượt nhận kết quả hợp lệ và 2 lượt lỗi.

| Ca | Kết quả | Chi tiết |
|---|---|---|
| T01–T06, T08, T10–T15 | PASS | Đạt các kiểm tra API/SQLite trong runner |
| T07 | FAIL | Tạo đề xuất trả HTTP 502, `AI_INVALID_OUTPUT` |
| T09 | FAIL | Tạo đề xuất trả HTTP 503, `AI_UNAVAILABLE`, chưa đến bước kiểm REJECT |

Cần kiểm tra lại hai ca lỗi trên trước khi xác nhận đủ T01–T15. Với T07, lỗi xảy ra ở bước tạo đề xuất nên phần đánh giá ưu tiên chưa hoàn thành. Nguyên nhân chi tiết phía nhà cung cấp của T09 chưa được xác định trong dữ liệu audit đã lưu.

Bằng chứng gồm [tổng hợp](runs/20261118T044352245175Z/summary.json), [T01–T05](runs/20261118T044352245175Z/plan/T01-T05-results.json) và [T06–T15](runs/20261118T044352245175Z/adapt/T06-T15-results.json). Dữ liệu tuyến của lượt chạy này là MOCK, cấu hình provider được chèn riêng trong runner.

## Chạy T01–T15 với Gemini thật

Cần Python có các thư viện trong `requirements.txt` tại gốc repo. Hai script Python trong thư mục này phải được đặt cùng nhau. Key và model được đọc từ biến môi trường của terminal.

Mở PowerShell tại gốc repo và nhập key riêng trên máy

```powershell
cd "D:\WORKPLACE\Computational Thinking\solo-travelling-assistant"

$secret = Read-Host "Nhap Gemini API key" -AsSecureString
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new("", $secret).Password
$env:GEMINI_MODEL = Read-Host "Nhap ten model"
$env:PYTHONUTF8 = "1"
```

Chạy trong cùng terminal

```powershell
python docs/testing/Overall_Testing_17_11/test_t01_t15_gemini.py --repo .
```

Nếu đã tạo `venv` trong thư mục kiểm thử, dùng Python của môi trường đó

```powershell
& ".\docs\testing\Overall_Testing_17_11\venv\Scripts\python.exe" ".\docs\testing\Overall_Testing_17_11\test_t01_t15_gemini.py" --repo "$PWD"
```

Tham số `--repo` cần có đường dẫn theo sau. Có thể thay `.` hoặc `$PWD` bằng đường dẫn đầy đủ đến gốc repo, đặt trong dấu ngoặc kép nếu chứa khoảng trắng.

## Phạm vi bộ chạy

- T01/T02/T04 kiểm tài khoản, gợi ý và dữ liệu đầu vào. T03 gọi Gemini để lập lịch 3/4 ngày. T05 xác nhận, đánh dấu DONE và đọc lại lịch đã tạo.
- T06–T15 dùng fixture 4 ngày độc lập để kiểm nghỉ thêm, ưu tiên giữ hoạt động, đổi điểm vì mưa, ACCEPT/REJECT, đề xuất cũ và rollback.
- Gemini thật xếp hạng phương án khả thi ở F02/F05. T08/T15 kiểm trường hợp không có phương án trước khi gọi model. T12 chủ động mô phỏng lỗi AI và lỗi lưu, đồng thời dùng đề xuất từ Gemini thật để kiểm rollback khi lưu.
- Dữ liệu tuyến PLAN/ADAPT mang nhãn MOCK. F01 dùng catalog `backend/data` với nhãn gốc. Các lượt gọi model sử dụng quota và có thể phát sinh phí theo tài khoản.
- Runner cấu hình provider và GeminiRanker trong tiến trình kiểm thử riêng, dùng API/TestClient và SQLite tạm. Kết quả cần được đối chiếu thêm với backend khởi động bằng lệnh chung và thao tác trên Expo Go. Bước đọc lại ở T05/T10/T13 tạo app instance mới, còn kiểm khởi động lại tiến trình backend cần thực hiện bổ sung.

## Kết quả mỗi lần chạy

Thư mục `runs/<mốc UTC>/` được tạo mới cho từng lần chạy

| File | Nội dung |
|---|---|
| `summary.json` | Trạng thái T01–T15 và số lượt gọi Gemini |
| `plan/T01-T05-results.json` | Kết quả PLAN, dataset_version, SHA256 các file tham chiếu và audit model |
| `adapt/T06-T15-results.json` | Đề xuất, quyết định, lỗi được mô phỏng và audit model theo từng ca |

Mã thoát 0 tương ứng tất cả kiểm tra trong script đạt. Mã thoát 1 tương ứng có ca chưa đạt. Xem `reason`, `error_type` và `gemini_calls` trong JSON để xác định bước cần kiểm tra lại.

