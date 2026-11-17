# Bàn giao F02 và F05 - Nhật

Yêu cầu hiện hành: [TASK 17/11](https://docs.google.com/document/d/13kcGW3jPT2ZJW0jKIH7XDr8WDmpFnEq5AyzFXzAhDNs/edit), hạn 18/11. PR #27 đã merge. Lần cập nhật này dựa trên main `ac35605`, đã đọc các PR mở #29, #30, #31, #32 trước khi sửa. Không PR nào sửa module F02/F05 của Nhật. PR #31 về dữ liệu nối tiếp #30, chưa thuộc main khi kiểm tra.

Trên main tại mốc này, API F02 vẫn dùng `mock_plan`, F05 vẫn dùng xếp hạng bằng luật. Kiểm thử trực tiếp provider dưới đây không chứng minh ứng dụng đã dùng Gemini. Bảo 06 phụ trách nối provider, router, cấu hình catalog và SQLite; Nhật không sửa các file dùng chung ấy. Hân/Linh phụ trách mobile, Tân tổng hợp T01–T15. Không thay dataset để làm test qua.

## F02

`PlanProvider(catalog, templates)` trả một callable nhận `DraftInput` và trả `list[day]`. Mỗi ngày có `date`, `end_deadline`, `activities`. Mỗi activity có `type`, `name`, `place_id`, `start_time`, `end_time`, `is_optional`. Hàm lưu hiện tại cấp ID và trạng thái.

```python
provider = PlanProvider(catalog, templates)  # GeminiRanker, 60 s, lỗi trả APIError
app = create_app(plan_provider=provider)
```

`templates` là dictionary theo số ngày. Mỗi tuyến có `route_id`, `data_status`, `days`. Mỗi ngày cần `start_place_id`, `end_place_id`, `start_time`, `end_deadline`, `stops`. Một stop VISIT có `type`, `place_id`, `is_optional`. Một stop REST có `type`, `place_id`, `duration_minutes`. Các REST giữ vị trí trong tuyến. Một nhóm VISIT liên tiếp được đổi thứ tự tối đa bốn điểm; tối đa 24 cách mỗi ngày và tám lịch hoàn chỉnh được đưa cho model. Giới hạn này nghĩa là không tìm hết mọi lịch có thể có.

Code chỉ lấy địa điểm và chặng trong catalog cùng chế độ MOCK hoặc VERIFIED. Python tính đường đi, giờ mở cửa, tổng nghỉ và hạn ngày, rồi Gemini chỉ xếp hạng ID các lịch hợp lệ. Khi không có tuyến, chặng hoặc dữ liệu đã xác minh, provider trả lỗi thay vì tự tạo số liệu. Khi model timeout hoặc trả cấu trúc sai, provider trả APIError; không tự dùng MOCK. Tuyến nguồn của PR #24 hiện UNVERIFIED, không đủ để chạy lịch thật.

Cập nhật TASK17: `buffer_minutes` ở cấp route là số nguyên từ 0 đến 1439, mặc định 0 nếu không có. Phải thỏa `giờ đến cuối ngày + buffer <= end_deadline`; buffer không được cộng thành REST. REST phải nằm trọn trong một khoảng mở cửa; nếu đến sớm thì có thể đợi, thời gian đợi không tính vào tổng nghỉ. Giờ mở cửa chưa biết là thiếu dữ liệu, danh sách rỗng là đóng cửa. Điểm đầu phải tiếp cận được lúc xuất phát; PLAN có thể dời giờ xuất phát đến lúc mở. Điểm cuối phải mở lúc đến nếu có chặng trở về. Trong MOCK hiện có, điểm đầu mở 07:00 dù mẫu ghi 06:00, nên lịch mới bắt đầu 07:00; không sửa fixture để giấu khác biệt này.

Để kiểm tra với dữ liệu MOCK của Bảo 04, đọc `backend/data/handoff/routes_mock.json`, đọc từng `snapshot` tương ứng, gọi `mock_templates(routes, snapshots)`, trong đó snapshots ánh xạ `route_id` sang JSON của snapshot. Tạo `Catalog` từ `data/fixtures/mock`, mode MOCK và RouteDay tương ứng. Test `backend/tests/test_plan_f02_provider.py` là ví dụ chạy đầy đủ cả API tạo nháp, xác nhận và đọc lại SQLite tạm. Fixture là mô phỏng.

Trước khi dùng VERIFIED, Bảo 04 cần cung cấp tuyến đủ trường trên, địa điểm và chặng có cùng nhãn VERIFIED. `Catalog.version` và mode phụ thuộc nội dung cấu hình; không trộn chặng MOCK vào tuyến thật.

## F05

```python
public, stored = create_proposal(itinerary, payload.model_dump(), catalog_provider)
save_proposal(stored, user_id)  # Bảo 06 gọi trước khi trả public
validator = make_option_validator(catalog_provider)
```

`catalog_provider = make_catalog_provider(data_directory, routes_by_days, mode="MOCK")` tạo catalog mới mỗi lần từ JSON, ánh xạ theo thứ tự ngày sang `day_id` thực và từ chối hạn giờ khác cấu hình. `routes_by_days` ánh xạ số ngày sang cấu hình tuyến đã chọn. Với VERIFIED dùng `mode="VERIFIED"` và chỉ cấu hình tuyến đã xác minh. Mỗi số ngày cần được nhóm chốt một cấu hình, nếu có nhiều tuyến thì cần chọn tuyến lưu cùng lịch thay vì đoán theo số ngày.

`validator(itinerary, option)` khớp chữ ký đã bàn giao trong PR #25 và kiểm tra bản option do server lưu. API F05 trên main tại mốc kiểm tra gọi `AdaptEngine(catalog)` theo mặc định dùng luật. Để nghiệm thu AI thật cần Bảo 06 gọi `create_proposal` ở trên, giữ nguyên bước xác thực và lưu đề xuất. Không truyền nội dung option do mobile gửi vào validator.

`create_proposal` chỉ gọi Gemini khi có phương án hợp lệ và không chuyển sang RuleRanker khi AI lỗi. Nếu không có phương án thì trả options rỗng cùng lý do, không gọi AI.

ADAPT kiểm lại các dòng PENDING của ngày đang điều chỉnh, kể cả REST kéo dài và phần trước được giữ nguyên; không áp giờ mở cửa mới lên lịch sử DONE. Giữ nguyên các ngày khác. `make_catalog_provider` ánh xạ buffer cấp route vào `Catalog.buffer_minutes_by_day` theo ID ngày thực. Nếu tạo Catalog thủ công, truyền `buffer_minutes_by_day={day_id: minutes, ...}`; không cần thêm trường vào `RouteDay` hay đổi schema database. Buffer tham gia fingerprint catalog. Sau nâng cấp validator, đề xuất cũ có fingerprint khác phải tạo lại, không áp dụng cưỡng ép. Bảo 06 phải dùng cùng cấu hình buffer cho F02/F05.

## Kiểm thử: ba mức khác nhau

1. **Unit/regression test:** cố ý đưa dữ liệu sai, timeout hoặc phản hồi AI sai vào hàm. Dùng AI giả lập, không mạng, không cần key. Chứng minh code giữ ràng buộc và báo lỗi đúng. Không cố tình làm Gemini thật quá hạn hoặc hết quota để kiểm thử các ca này.
2. **Provider với Gemini thật:** gọi dịch vụ Google để xếp hạng phương án Python đã tính. Dataset vẫn MOCK. Chứng minh kết nối AI, kiểm tra JSON, chọn phương án và bảo toàn ràng buộc. Không có tài khoản, HTTP app hay SQLite trong lần chạy này.
3. **Tích hợp toàn ứng dụng:** sau Bảo 06 nối provider, Đăng/Tân chạy Expo → API → Gemini → xác nhận/SQLite → mở lại. Kiểm tra ACCEPT, REJECT, gửi lặp, version cũ, quyền sở hữu và khởi động lại. Mức 2 đạt chưa có nghĩa mức 3 đạt.

`MOCK` của **dữ liệu** và `MOCK_AI` của **AI** là hai nhãn độc lập. Lần gọi Google thật trên địa điểm giả có nhãn `data_mode=MOCK`, `ai_mode=GEMINI`; không gọi đó là dữ liệu du lịch thật.

## Bắt đầu trong VS Code trên Windows

### 1. Đúng repo, nhánh và môi trường Python

Terminal phải ở thư mục có `requirements.txt`, `backend`, `mobile`:

```powershell
git status --short --branch
git fetch origin
```

Đọc PR mở trước mỗi lần sửa code. Nếu chỉ chạy kiểm thử, không tự merge nhánh của người khác. Nếu checkout cũ chưa có `backend/nhat_ai_check.py`, lấy nhánh PR của Nhật vào checkout sạch hoặc mở đúng worktree được bàn giao; giữ nguyên file chưa commit của bạn.

Dùng Python 3.10 trở lên. Nếu chưa có môi trường Python của repo:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nếu `py` không được nhận diện, cài Python từ python.org rồi mở lại terminal, hoặc dùng đường dẫn Python đã cài để chạy `-m venv .venv`. Không bắt buộc activate venv; gọi trực tiếp `.\.venv\Scripts\python.exe` tránh lỗi chính sách PowerShell. Nếu nhóm đã có venv khác, thay đường dẫn Python trong các lệnh sau bằng venv đó.

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Kết quả mong đợi là `OK`. Nếu test tạo symbolic link gặp `WinError 1314`, đó là quyền Windows của test dataset; ghi nhận nguyên lỗi, không báo toàn suite đạt hoặc xóa test. Các test riêng của Nhật vẫn chạy được bằng `-p 'test_plan_f02_provider.py'`, `-p 'test_f02_f05_constraints.py'`, `-p 'test_gemini_ranking_errors.py'`, `-p 'test_nhat_ai_check.py'`, `-p 'test_adapt_f05.py'`.

### 2. Tạo và lưu khóa cục bộ

Mở [Google AI Studio](https://aistudio.google.com/api-keys), tạo API key cho project của bạn. Chưa cần bật thanh toán. Tạo file `backend/.env` trong VS Code:

```dotenv
GEMINI_API_KEY=dan_khoa_cua_ban_vao_day
GEMINI_MODEL=gemini-3.1-flash-lite
```

Thay giá trị khóa ngay trong editor rồi lưu file. Không gửi khóa vào chat, ảnh, issue, PR hoặc terminal command. Tên model trên là ứng viên thử, không phải cam kết project của bạn được quyền truy cập hay luôn còn quota. [API key](https://ai.google.dev/gemini-api/docs/api-key), [model](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite), [giá và free tier](https://ai.google.dev/gemini-api/docs/pricing) được kiểm tra ngày 17/11/2026; xác nhận hạn mức của project trong AI Studio.

```powershell
git check-ignore backend/.env
git ls-files -- backend/.env
```

Lệnh thứ nhất phải in `backend/.env`; lệnh thứ hai không được in đường dẫn nào. `.gitignore` hiện có chặn `.env`. Nếu file đã bị theo dõi, dừng push; nếu khóa từng xuất hiện trên GitHub phải thu hồi và tạo lại khóa, xóa file ở commit mới không xóa được lịch sử cũ.

Python không tự đọc `.env`. Công cụ dưới đây đọc trực tiếp bằng `--env-file`, chỉ lấy hai biến Gemini; file chỉ dùng cho lần chạy đó. Nếu không truyền `--env-file`, công cụ lấy hai biến từ môi trường của tiến trình. Không cần đặt key vào mobile hoặc biến `EXPO_PUBLIC_*`. Mỗi thành viên chạy backend có thể dùng key riêng; chỉ thành viên chạy mobile qua backend chung không cần key.

### 3. Chạy trước bằng AI giả lập

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
.\.venv\Scripts\python.exe backend/nhat_ai_check.py --mode mock --output "docs/testing/nhat-mock-$stamp.json"
```

Chạy 10 ca: PLAN 3/4 ngày, REST/RAIN có phương án và REST/RAIN không có phương án cho cả 3/4 ngày. Mong đợi 10 `PASS`, `ai_mode=MOCK_AI`, 6 lần gọi **hàm giả lập**, 4 ca không gọi AI. Không phát sinh yêu cầu Google. File kết quả được ghi mới, không đè bằng chứng cũ.

### 4. Thử một lần Gemini thật trước

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
.\.venv\Scripts\python.exe backend/nhat_ai_check.py --mode gemini --env-file backend/.env --case F02_3D --output "docs/testing/nhat-gemini-smoke-$stamp.json"
```

Lệnh này gọi API `generateContent` của Google một lần, timeout tối đa 60 giây, không tự retry. `PASS (GEMINI, ... ms)` cùng `ai_audit.outcome=SUCCESS` chứng minh model trả JSON hợp lệ và lịch đã qua kiểm tra. Khi thiếu key, thoát mã 2, không gọi AI và không tạo bằng chứng PASS. Không cần chạy Uvicorn hay Expo cho bước này.

### 5. Chạy bộ nghiệm thu provider

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
.\.venv\Scripts\python.exe backend/nhat_ai_check.py --mode gemini --env-file backend/.env --output "docs/testing/nhat-gemini-$stamp.json"
```

| Ca | Số lần gọi Google | Điều kiện cần đạt |
|---|---:|---|
| `F02_3D`, `F02_4D` | 1 mỗi ca | Đúng số ngày, đủ TRAVEL/REST/VISIT, tuyến có hướng, giờ/nhịp nghỉ/hạn ngày hợp lệ |
| `F05_REST_3D`, `F05_REST_4D` | 1 mỗi ca | Hai phương án, giữ DONE và lịch sử, không sửa snapshot đầu vào |
| `F05_RAIN_3D`, `F05_RAIN_4D` | 1 mỗi ca | Một phương án trong nhà, kiểm cả chặng đến và chặng đi tiếp |
| `F05_NO_REST_OPTION_3D/4D` | 0 | Không có phương án, có lý do, không gọi model |
| `F05_NO_RAIN_OPTION_3D/4D` | 0 | Không có điểm thay hợp lệ, có lý do, không gọi model |

Một lượt `all` tối đa 6 lần gọi AI, cộng 1 nếu đã chạy smoke trước đó. Dừng ở lỗi đầu tiên; ca sau ghi `NOT_RUN`, không tự thử lại tốn quota. Dùng `--case` với mã ca cụ thể để kiểm tra lại sau khi sửa. Đổi `--output` để giữ bằng chứng cũ. Không đánh giá AI bằng việc câu chữ giống hệt giữa các lần chạy: kiểm tra lựa chọn có hợp lệ và dựa trên dữ kiện được cấp hay không.

Kiểm tra JSON đầu ra có: thời điểm UTC, `commit`, `worktree_dirty`, hash code, `dataset_version`, hash fixture, `catalog_fingerprint`, model, `prompt_version`, `usage`, thời gian và trạng thái từng ca. `ai_calls` đếm lần thử gọi provider; `ai_used=GEMINI` trên ca lỗi chỉ nói đã thử gọi, cần `ai_succeeded=true` và `ai_audit.outcome=SUCCESS` để xác nhận trả kết quả hợp lệ. Ca không có phương án ghi kiểm tra snapshot/option là `null` (không áp dụng), không báo đã kiểm tra một option không tồn tại. File không chứa key, header Authorization, `.env`, tài khoản hoặc phản hồi lỗi Google nguyên văn. Chỉ commit báo cáo sau khi đọc lại. `worktree_dirty=true` phải được ghi nhận; không gán kết quả ấy cho commit như thể chưa có sửa đổi cục bộ.

### 6. Đọc lỗi và xử lý

| Kết quả | Ý nghĩa | Cách xử lý |
|---|---|---|
| `AI_UNAVAILABLE`, HTTP 400/403 | Khóa/quyền/cấu hình không được chấp nhận | Kiểm tra project, hạn chế key và model; không in key |
| `AI_UNAVAILABLE`, HTTP 404 | Model/đường gọi không truy cập được | Đối chiếu tên model có quyền dùng; sửa `GEMINI_MODEL` rồi chạy đúng một ca |
| `AI_UNAVAILABLE`, HTTP 429 | Hết quota hoặc bị giới hạn tốc độ | Xem quota AI Studio; chờ theo hướng dẫn dịch vụ, không chạy vòng lặp retry, không tự bật billing |
| `AI_UNAVAILABLE`, HTTP 5xx hoặc lỗi mạng | Nhà cung cấp/kết nối tạm lỗi | Ghi kết quả, kiểm tra mạng rồi thử lại một ca |
| `AI_TIMEOUT` | Không nhận kết quả trong hạn chờ | Lịch không đổi; ghi lỗi, chỉ thử lại có chủ đích |
| `AI_INVALID_OUTPUT` | JSON sai, thiếu/trùng/bịa ID, mã giải thích không hợp lệ hoặc phản hồi bị cắt | Không dùng kết quả, lưu mã lỗi và model; sửa prompt/adapter trong phạm vi Nhật |
| `DATA_INCOMPLETE` | Thiếu dữ liệu/chặng/giờ mở cửa/nhãn xác minh | Gửi mã điểm/chặng cho Bảo 04; không tự bịa số liệu |
| `NO_FEASIBLE_ITINERARY` hoặc options rỗng | Không xếp được lịch trong phạm vi hỗ trợ | Giữ ràng buộc và lý do; không nới deadline để test qua |
| `CHECK_FAILED` | Công cụ gặp lỗi chưa phân loại | Dùng `exception_type`, chạy unit test và ca riêng để tái hiện; không coi là PASS |

Các test lỗi dùng transport giả để tạo timeout, HTTP 429/5xx, dữ liệu không phải JSON, nội dung sai và ID bịa. Không cần gửi yêu cầu lỗi ra Google để nghiệm thu xử lý lỗi. Không có fallback âm thầm sang MOCK khi dùng `create_proposal`/`PlanProvider` với Gemini.

## Ghép API và chạy dữ liệu thực sau đó

Bảo 06 nối F02/F05 theo các callable ở trên, dùng cùng catalog/route cho tạo nháp và validator quyết định. Giữ nguyên endpoint `/api/v1/itinerary-drafts`, `/api/v1/itineraries/{id}/adapt-proposals`, `/api/v1/adapt-proposals/{id}/decision`. Backend phải nạp môi trường khi khởi động; `--env-file` của công cụ kiểm thử không cấu hình cho một Uvicorn khác đang chạy. Sau thay key/model cần khởi động lại tiến trình backend theo hướng dẫn cấu hình của Bảo.

Khi API đã nối: đăng nhập → tạo PLAN 3/4 ngày → xác nhận → đọc lại → DONE → REST hoặc RAIN → xem → REJECT, rồi tạo mới → ACCEPT → đọc lại; kiểm tra quyền sở hữu, version cũ, gửi lại cùng quyết định, tắt/mở backend. Tân ghi T01–T15; Đăng xác nhận Expo Go. Chỉ khi có bằng chứng những bước này mới ghi ứng dụng tích hợp AI đạt.

Dữ liệu nguồn trong PR #30/#31 còn chưa đủ điều kiện tại mốc kiểm tra. Công cụ `nhat_ai_check.py` cố ý chỉ nhận bộ MOCK đóng băng hiện có. Khi Bảo 04 bàn giao nguồn VERIFIED và Đăng chốt tuyến, chạy lại audit nguồn, dùng các `stops` nguồn cho `PlanProvider`, cấu hình catalog `mode="VERIFIED"`, rồi kiểm thử provider/API theo cùng bốn luồng. Không đưa fixture MOCK vào catalog VERIFIED hoặc sửa nhãn để gọi đó là chuyến thật. Việc mở rộng công cụ để nhận fixture nguồn phải dựa vào bản bàn giao đã chốt, không đoán dữ liệu khi chưa có.

Kết quả thực tế của lượt cập nhật được ghi trong báo cáo kèm PR. Không thay các mục tiêu ở đây thành kết quả đã đạt. Gemini thật chỉ được ghi PASS khi có model, commit/digest và bằng chứng phản hồi thực.
