# Kết quả kiểm tra Gemini trên backend đã tích hợp — 18/11/2026

## Phạm vi

- Code đã chạy: main `c5d7aca898037b075ee4473fb5e95800a6e137e1`, sau khi merge #33 và #34. Dữ liệu **MOCK**: `bao04-mvp-2026-11-17-v2`.
- Backend được khởi tạo qua `main.configured_app()`, `ADAPT_MODE=MOCK`, `STA_RANKER=GEMINI`; model thật `gemini-3.1-flash-lite`, prompt `adapt-rank-v2`. Trong kiểm thử chỉ chọn model này cho tiến trình; file `.env` của người dùng không bị thay đổi.
- Yêu cầu HTTP đi qua FastAPI TestClient/ASGI, các router thật và SQLite thử mới trong thư mục tạm. Đây không phải máy chủ TCP/Uvicorn, Expo Go hay điện thoại. Không đụng database của app. Audit bọc `GeminiRanker.rank` để ghi metadata, vẫn gọi phương thức gốc và Gemini thật, không thay kết quả.
- Mỗi ca PLAN gọi API tạo nháp, xác nhận và đọc CURRENT. Đánh dấu hoạt động đầu ngày 2 là DONE qua API, lấy version mới; gửi REST và RAIN riêng để xem đề xuất. REST kéo dài thêm 15 phút; RAIN chọn điểm ngoài trời MOCK-A03. Hai yêu cầu ADAPT cùng dựa trên CURRENT, chỉ xem đề xuất, không ACCEPT/REJECT.
- Với mỗi phương án, đối chiếu snapshot độc lập bằng `data_handoff.mock_snapshot`: thứ tự giờ, giờ mở cửa, chặng có hướng và thời gian chặng, tổng nghỉ, hạn ngày và tuyến về. Kiểm tra thêm REST được kéo dài đúng; điểm mưa chuyển sang INDOOR, liên kết hoạt động cũ; DONE giữ nguyên từng trường, GET CURRENT không đổi khi chỉ xem.

## Kết quả

Lượt thứ hai lúc 16:57–16:58 ngày 18/11, giờ Việt Nam, bổ sung kiểm tra đúng thay đổi REST/RAIN. Thời gian là từ lúc gửi đến lúc nhận response của endpoint tương ứng, không bao gồm đăng nhập, xác nhận, đánh dấu DONE hoặc kiểm tra độc lập.

| Ca | Kết quả | API response | Số phương án | Hoạt động DONE được giữ |
|---|---|---:|---:|---:|
| F02, 3 ngày | Đạt | 1.265 ms | — | — |
| F05, nghỉ thêm, 3 ngày | Đạt | 1.953 ms | 1 | 1 |
| F05, đổi điểm vì mưa, 3 ngày | Đạt | 1.844 ms | 1 | 1 |
| F02, 4 ngày | Đạt | 2.375 ms | — | — |
| F05, nghỉ thêm, 4 ngày | Đạt | 2.375 ms | 1 | 1 |
| F05, đổi điểm vì mưa, 4 ngày | Đạt | 4.172 ms | 1 | 1 |

Mỗi ca có đúng một lần gọi Gemini thật và outcome SUCCESS, tổng sáu lần cho lượt này. Response API không công bố audit AI; bằng chứng model/token/thời gian Gemini được lấy từ adapter tại thời điểm gọi, không phải suy ra từ cấu hình. JSON chứa tên model, phiên bản prompt, token được nhà cung cấp báo, thời gian, hash fixture và trạng thái từng ca:

- [Lượt 1](nhat-integrated-gemini-20261118.json): 6/6 đạt. Kiểm tra độc lập lịch và DONE.
- [Lượt 2](nhat-integrated-gemini-20261118-v2.json): 6/6 đạt, thêm xác nhận REST/RAIN. Bảng trên dùng lượt này.

Hai file được kiểm tra không chứa khóa trước khi lưu. Không ghi token đăng nhập hoặc mật khẩu vào kết quả. Các con số thời gian chỉ phản ánh hai lần chạy, không phải cam kết tốc độ.

## Cách chạy lại thủ công với server trên máy

Các bước sau giúp nhóm tái hiện đường API thật qua Uvicorn; đây là hướng dẫn chạy lại, không phải bằng chứng máy chủ TCP đã được kiểm tra ở trên. Cần checkout chứa commit đã ghi và Python/requirements đã cài. Bắt đầu trong terminal PowerShell tại thư mục gốc repo:

```powershell
$env:PYTHONUTF8 = '1'
$env:ADAPT_MODE = 'MOCK'
$env:STA_RANKER = 'GEMINI'
$env:GEMINI_MODEL = 'gemini-3.1-flash-lite'
$env:ADAPT_MOCK_DAYS = '3'
$env:ADAPT_MOCK_SCENARIO = 'T06'
$runId = Get-Date -Format 'yyyyMMdd-HHmmss'
$env:ADAPT_MOCK_DB = Join-Path $env:TEMP "nhat-api-$runId.test.sqlite3"
.\.venv\Scripts\python.exe backend/scripts/reset_demo.py --database $env:ADAPT_MOCK_DB --days 3 --scenario T06
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --env-file backend/.env --host 127.0.0.1 --port 8000
```

Thay đường dẫn Python nếu venv có tên khác. Mỗi lần reset chọn file thử **mới**; không dùng database app hay file của thành viên khác. `.env` chứa khóa cục bộ; không đưa vào Git. Biến model ở terminal ưu tiên model trong `.env` cho phiên chạy này. Stop server bằng Ctrl+C sau khi thử.

Mở `http://127.0.0.1:8000/docs` trên cùng máy. Dùng tài khoản demo có trong `backend/demo_reset.py` để đăng nhập `/api/v1/auth/login`, nhập bearer token vào Authorize mà không chụp hay chia sẻ token. Tiếp theo:

1. Tạo nháp qua `POST /api/v1/itinerary-drafts` với `departure_date=2026-11-12`, `return_date=2026-11-14`, `departure_time=06:00`, `interests=["nature","coffee"]`, `min_rest_minutes=60`. Xác nhận nháp, đọc `/api/v1/itineraries/current`. Đổi ngày về thành `2026-11-15` để thử chuyến 4 ngày.
2. Trong ngày 2, đánh dấu hoạt động đầu là DONE bằng PATCH; dùng `version` mới trả về. Lấy activity ID trực tiếp từ CURRENT, vì ID và thứ tự có thể khác mỗi lần.
3. Gửi `POST /api/v1/itineraries/{itinerary_id}/adapt-proposals` cho REST với `type=EXTEND_REST`, `base_version`, `rest_activity_id` của REST, và `rest_until` sau giờ kết thúc REST 15 phút. Xem `options` và đối chiếu giờ, DONE, thời điểm đến cuối ngày.
4. Từ CURRENT chưa đổi, gửi thêm yêu cầu RAIN với `type=REPLACE_LOCATION`, `base_version`, `activity_id` của VISIT MOCK-A03, `reason=RAIN`. Kiểm tra điểm thay trong nhà, hai chặng liên quan, DONE và giờ kết thúc.
5. Ghi mã HTTP, thời gian, kết quả thực tế, commit, model, dataset và mọi lỗi. Kiểm tra ACTIVE gồm PENDING/DONE khi đọc timeline; DROPPED/REPLACED là lịch sử. Để xác minh gọi Gemini, chỉ cấu hình model chưa đủ: cần audit an toàn từ backend hoặc quan sát có kiểm soát tại adapter. Không ghi key, bearer token hoặc dữ liệu tài khoản thật.

## Giới hạn và phần bàn giao

Chưa kiểm tra ACCEPT/REJECT, gửi lặp, khởi động lại hay Expo trong lượt này. Phần kiểm thử tự động API/lưu lịch thuộc Bảo 06. Dữ liệu tuyến VERIFIED chưa đủ điều kiện; không chuyển nhãn MOCK thành dữ liệu thật. Không sửa module AI trong lượt này vì sáu ca đều đạt. PR của Hân #32 đang mở chỉ sửa mobile, không trùng file báo cáo.
