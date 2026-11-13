# ADAPT F05 - cơ chế, kiểm thử và bàn giao

Solo Travelling Assistant | Nhật | Cập nhật 10/11/2026

## 1. Phần đã thực hiện

Đã viết logic ADAPT cho hai tình huống: kéo dài khoảng nghỉ và thay điểm tham quan ngoài trời vì người dùng báo mưa. Python tạo, tính giờ và kiểm tra các phương án. AI chỉ chọn thứ tự và mã lý do từ những phương án đã hợp lệ.

Module tạo bản xem trước nội bộ `F05_DOMAIN_PREVIEW_V1` và xuất dữ liệu F05 theo quy tắc lưu chặng ngày 10/11. F05 tính và kiểm tra phương án. Bảo 06 tích hợp lưu đề xuất và áp dụng quyết định F06 trong SQLite.

| Nội dung | Trạng thái thực tế |
|---|---|
| Hai ca ADAPT, tính lại giờ và chặng | Đã code và test bằng dữ liệu MOCK |
| Xuất chặng đổi giờ, chặng cũ REPLACED và chặng mới PENDING | Đã chạy trên snapshot 3/4 ngày của PR #19 |
| Bảo toàn DONE, lịch ngày khác và lịch nguồn | Đã test |
| AI xếp ưu tiên, kiểm tra đầu ra, fallback | Đã test bằng AI giả lập |
| Adapter gọi Gemini | Đã viết; kiểm tra HTTP bằng transport giả lập |
| Gemini thật, bằng chứng token/latency thật | Chưa chạy vì nhóm chưa có key |
| Lưu đề xuất và REJECT | Đã thử qua PR #16 với SQLite tạm. REJECT lặp giữ nguyên lịch |
| F06 ACCEPT với thay chặng | PR #16 hiện trả 409. Cần Bảo 06 cập nhật validator |
| Expo S04-S06 kết nối backend thật | Chưa kiểm thử đầu cuối |
| PLAN F02 | Không triển khai trong phần ADAPT này |

Nhánh đích: `5-nhật-logic-ai-cho-plan-f02-và-adapt-f05`. Base đã kiểm tra: `a7a7934`. PR đang mở khi bắt đầu: #16, head `1fc48eb`, phụ trách lưu PLAN/F03/F06.

Hai điểm cập nhật quan trọng từ Leader: `min_rest_minutes` là tổng phút nghỉ tối thiểu mỗi ngày; dữ liệu thật phải là `VERIFIED`. Hai quyết định này thay các diễn giải cũ về một khối nghỉ tối thiểu và nhãn SOURCED.

<!-- pagebreak -->

## 2. Đọc code và hiểu luồng xử lý

Module là nhóm file cùng phụ trách một công việc. Module `backend/adapt_f05` chỉ phụ trách tính phương án; không phụ trách tài khoản, API lưu lịch hoặc giao diện.

| File trong module | Trách nhiệm |
|---|---|
| models.py | Kiểu yêu cầu, lỗi, Candidate và AdaptResult nội bộ |
| catalog.py | Đọc dữ liệu, kiểm tra nhãn/nguồn, giờ mở cửa, chặng có hướng |
| engine.py | Tìm phương án nghỉ/mưa, xếp giờ, tạo diff và kiểm tra lại |
| ranking.py | Baseline dùng luật, MockRanker, GeminiRanker và kiểm tra JSON |
| handoff.py | Xuất bản xem trước và dữ liệu riêng để F06 kiểm tra lại |
| demo.py | Dựng ví dụ MOCK và cho chạy từ Terminal |
| AGENTS.md | Nhắc kiểm tra PR trước code và giữ đúng phạm vi Nhật |

Luồng xử lý:

1. Nhận snapshot CURRENT và yêu cầu có base_version.
2. Kiểm tra loại hoạt động, trạng thái, phiên bản và cấu hình điểm kết thúc.
3. Đọc địa điểm/chặng; thiếu dữ liệu thì ghi đúng mã hoặc cặp điểm thiếu.
4. Python liệt kê số phương án nhỏ, xếp lại phần chưa thực hiện trong cùng ngày.
5. Kiểm tra chặng đến, chặng đi tiếp, giờ mở cửa, thời lượng, nghỉ và hạn giờ.
6. AI hoặc luật xếp thứ tự các phương án hợp lệ; chỉ trả tối đa hai.
7. Tính lại phương án để phát hiện dữ liệu bị sửa; trả preview, chưa lưu lịch.

Snapshot là bản dữ liệu lịch tại một thời điểm. Ví dụ version 1 có A03 còn PENDING; sau khi DONE, backend phải đọc version mới trước khi yêu cầu ADAPT. `deepcopy` tạo bản sao độc lập để việc tính thử không sửa đối tượng lịch đầu vào.

Diff là bảng so sánh trước và sau. `changes` mô tả REST/VISIT. `options[].travel_changes` mô tả chặng đổi giờ, chặng ngừng dùng và chặng mới cho S05. `proposed_days` chứa toàn bộ lịch và lịch sử sau khi áp dụng phương án.

<!-- pagebreak -->

## 3. Nghỉ thêm: tính như thế nào?

Ví dụ MOCK ngày 2 có A01 và A02 DONE; nghỉ 13:00-14:00; A03 và A04 đều tùy chọn, mỗi điểm 45 phút. Các chặng cần dùng trong fixture đều 15 phút; hạn demo là 16:30.

Yêu cầu: chọn REST, nghỉ đến 15:00, ưu tiên giữ A04.

| Phương án | Các mốc sau khoảng nghỉ | Kết quả |
|---|---|---|
| Giữ cả A03/A04 | Đi 15:00-15:15; A03 đến 16:00; đi đến 16:15; A04 đến 17:00; về đến 17:15 | Loại vì vượt 16:30 |
| Bỏ A03, giữ A04 | Đi thẳng REST-A04 15:00-15:15; A04 15:15-16:00; về 16:00-16:15 | Hợp lệ |
| Giữ A03, bỏ A04 | Đi REST-A03 15:00-15:15; A03 15:15-16:00; về thẳng 16:00-16:15 | Hợp lệ |

Baseline xếp phương án giữ A04 lên trước. Ưu tiên là điều mong muốn, không phải quyền bỏ qua hạn giờ: nếu giữ A04 không khả thi nhưng giữ A03 khả thi, chỉ trả phương án còn hợp lệ.

Trình tự thuật toán:

1. Kéo dài đúng REST được chọn. Không đổi giờ bắt đầu hoặc xóa nghỉ khác.
2. Thử giữ toàn bộ VISIT trước. Nếu đủ thời gian, không sinh phương án bỏ thêm.
3. Nếu không đủ, lần lượt thử bỏ một rồi tối đa hai VISIT tùy chọn PENDING phía sau.
4. Tính lại chặng trực tiếp theo cặp điểm thực sự còn lại; không cộng máy móc các chặng cũ.
5. Giữ thời lượng chuẩn của VISIT. REST còn lại giữ nguyên thời lượng và chỉ dịch muộn khi cần.
6. Luôn cộng chặng đến điểm kết thúc ngày trước khi xét hạn giờ.

Bản đầu xét tối đa 8 VISIT tùy chọn và tối đa 2 lần bỏ. Với dữ liệu lớn hơn, báo giới hạn tìm kiếm; không khẳng định mọi phương án trên thực tế đều bất khả thi.

Nếu nghỉ đến 16:30, ngay cả khi bỏ cả hai điểm vẫn cần 15 phút về điểm cuối. Kết quả là không có phương án; lịch nguồn và version vẫn giữ nguyên.

<!-- pagebreak -->

## 4. Đổi điểm vì mưa

Yêu cầu nhận A03 đang PENDING, môi trường OUTDOOR và reason RAIN. Mưa do người dùng báo; module không gọi dự báo thời tiết hoặc suy ra đường đang đóng.

| Bước | Kết quả trong ví dụ MOCK |
|---|---|
| Điểm trước | REST kết thúc lúc 14:00 |
| Điểm thay thế | MOCK-INDOOR, có trải nghiệm trong nhà và thời lượng 45 phút |
| Chặng đến | REST-INDOOR: 14:00-14:15 |
| Tham quan | INDOOR: 14:15-15:00, nằm trọn trong giờ mở cửa |
| Chặng đi tiếp | INDOOR-A04: 15:00-15:15 |
| Phần còn lại | A04 đến 16:00; về điểm cuối lúc 16:15 |

Hoạt động A03 cũ vẫn tồn tại, chuyển REPLACED trong bản xem trước. Hoạt động mới có ID do Python tạo, status PENDING và `replaces_activity_id = A03`. A01/A02 DONE và các ngày khác được giữ nguyên.

Chỉ xét địa điểm INDOOR có nhãn sở thích tham quan. Với dataset hiện tại, điểm nghỉ/đầu-cuối có danh sách sở thích rỗng nên không bị biến thành điểm trải nghiệm. MIXED, OUTDOOR hoặc UNKNOWN không được tự chọn làm phương án mưa. Cần bổ sung vai trò địa điểm rõ hơn trong dữ liệu tương lai nếu quy ước này thay đổi.

Một hoạt động phải nằm trọn trong một khoảng mở cửa. Nếu quán mở 08:00-11:30 và 13:00-17:00 thì không xếp một VISIT chạy xuyên giờ nghỉ trưa. Có thể chờ đến khoảng mở tiếp theo nếu vẫn đủ giờ; khoảng chờ không được tính thành REST. Kết thúc đúng giờ đóng cửa là hợp lệ.

Các trường hợp bị loại: thiếu chặng đến; thiếu chặng đi tiếp; giờ mở cửa null; thời lượng chưa biết; dữ liệu UNVERIFIED; điểm đóng cửa; không còn đủ thời gian về điểm cuối. Bản đầu không tự DROP một điểm khác để ép phương án mưa vừa lịch.

Lựa chọn trong nhà mô tả trải nghiệm tại điểm đến. Nó không bảo đảm chặng đường đến đó tránh được mưa.

<!-- pagebreak -->

## 5. Bộ kiểm tra và dữ liệu

Bất biến là điều luôn phải đúng, kể cả khi AI lỗi. Các bất biến đã có test: DONE không đổi; không đổi ngày khác; DROP chỉ VISIT PENDING tùy chọn; không mất lịch sử DROPPED/REPLACED; không chồng giờ; giữ tổng nghỉ mỗi ngày; không vượt hạn; không tự đoán chặng còn thiếu.

`validate_candidate(itinerary, candidate, catalog)` tính lại phương án từ snapshot, yêu cầu và lựa chọn đã lưu. Nó so sánh lịch, diff, chặng và mốc kết thúc với kết quả tính lại. Khi xuất sang F06, các đối tượng này phải được backend đọc từ kho lưu; tuyệt đối không lấy bản candidate do mobile gửi lên làm nguồn tin cậy.

Fingerprint là mã SHA-256 đại diện nội dung. Thay đổi version, dữ liệu lịch, chặng, giờ mở cửa hoặc cấu hình tuyến làm fingerprint đổi và phương án cũ không qua kiểm tra. Fingerprint không thay thế kiểm tra quyền sở hữu, transaction hoặc version trong database.

| Tình huống | Hành vi |
|---|---|
| A-B có, B-A thiếu | Không suy ngược thời gian |
| Cùng một place_id hợp lệ | Di chuyển 0 phút; không tạo TRAVEL dài 0 |
| Khác điểm nhưng thời lượng 0/âm | Báo dữ liệu không hợp lệ |
| weekly[ngày] là null | Chưa biết giờ mở cửa, không tự xếp tham quan |
| weekly[ngày] là [] | Đã biết đóng cửa trong ngày đó |
| Nhiều REST, tổng đủ 60 phút | Hợp lệ; không bắt mỗi REST dài 60 phút |
| SOURCED trong dataset cũ | Không tự coi là VERIFIED |
| Lịch thay đổi sau tạo phương án | Kiểm tra lại thất bại |

Catalog là lớp đọc dữ liệu, không ghi lại file Bảo 04. Chế độ VERIFIED chỉ nhận bản ghi VERIFIED có nguồn và thời điểm UTC; chế độ MOCK chỉ dùng MOCK. Không tự trộn dữ liệu hai chế độ. Dataset hiện có chưa đủ để chứng minh tính khả thi tuyến thật HCM-Da Lat.

Nếu phần cần xếp lại chứa DONE, thuật toán từ chối phương án và nêu lý do. Ví dụ khi đổi điểm vì mưa, chặng đến điểm cũ đã DONE thì hệ thống cần biết vị trí hiện tại trước khi lập một chặng mới.

<!-- pagebreak -->

## 6. AI hỗ trợ ở đâu?

AI nhận yêu cầu đã chuẩn hóa, sở thích và danh sách phương án đã kiểm tra, mỗi phương án có ID và các sự kiện đúng do Python tính. Không gửi token đăng nhập, mật khẩu hoặc toàn bộ hồ sơ tài khoản.

AI chỉ trả thứ tự candidate_id, reason_codes và tradeoff_code. Ví dụ KEEP nghĩa là đã giữ được hoạt động ưu tiên, END trỏ đến giờ kết thúc do code tính. Python kiểm tra mã có thuộc phương án rồi dựng câu tiếng Việt. AI không được tự tạo URL, địa điểm, giờ, thời lượng hoặc văn bản khẳng định chưa có căn cứ.

| Chế độ | Ý nghĩa |
|---|---|
| RULE_BASELINE | Xếp theo luật, không gọi model |
| MOCK_AI | Bộ giả lập đảo thứ tự để kiểm tra ranh giới; không phải AI thật |
| GEMINI | Gọi Gemini một lần; cần key và model cấu hình rõ |
| RULE_FALLBACK | AI lỗi/JSON sai, dùng lại các phương án Python đã kiểm tra |
| NOT_CALLED | Không có phương án nên không gọi AI |

MockRanker cố ý đảo thứ tự; không sử dụng nó để đánh giá chất lượng gợi ý cho người dùng. Nó chứng minh AI có thể đổi thứ tự nhưng không được sửa nội dung lịch. Baseline mới là mặc định chạy demo bằng luật.

Gemini adapter dùng REST, timeout tối đa 60 giây, không tự retry, không có tool gọi dịch vụ ngoài. Đầu ra JSON sai ID, trùng ID hoặc mã lý do bịa đều bị từ chối. Có thể bật chế độ không fallback để nhận AI_INVALID_OUTPUT, AI_TIMEOUT hoặc AI_UNAVAILABLE.

Nhóm chưa có key nên chưa có bằng chứng gọi Gemini thật. Những test HTTP đã chạy dùng transport giả lập. Khi có key: cấu hình GEMINI_API_KEY và GEMINI_MODEL tại backend, chọn provider gemini rõ ràng, ghi model/prompt_version/latency/token từ lần chạy thật. Không đưa key vào git hoặc chat.

Tài liệu REST/structured output tham khảo: https://ai.google.dev/api/generate-content và https://ai.google.dev/gemini-api/docs/structured-output . Adapter chưa phải xác nhận một model cụ thể khả dụng hoặc miễn phí.

<!-- pagebreak -->

## 7. Chạy trên VS Code và đọc kết quả

Mở Terminal PowerShell tại repo đang checkout nhánh Nhật. Kiểm tra `git status --short --branch` trước. Giữ nguyên thay đổi cá nhân ở mobile/.env.example; commit ADAPT không đưa file đó vào.

Tại thư mục gốc repo:

```powershell
.\backend\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\backend\.venv\Scripts\python.exe -X utf8 -m unittest discover -s backend/tests -v
```

Nếu chưa có môi trường Python, cài Python 3.12 rồi tạo một lần bằng `py -3.12 -m venv backend/.venv`. Trong VS Code chọn Python: Select Interpreter và trỏ đến môi trường đó. Không tạo lại môi trường sẵn có của nhóm nếu đang dùng được. Module dùng stdlib và Pydantic đã đi cùng FastAPI; không thêm SDK hoặc đổi lockfile của nhóm.

Chạy demo:

```powershell
cd backend
.\.venv\Scripts\python.exe -X utf8 -m adapt_f05.demo --case rest --ranker rules
.\.venv\Scripts\python.exe -X utf8 -m adapt_f05.demo --case rain --ranker rules
.\.venv\Scripts\python.exe -X utf8 -m adapt_f05.demo --case no-option
.\.venv\Scripts\python.exe -X utf8 -m adapt_f05.demo --case rest --ranker mock
```

Kết quả demo là JSON nội bộ. `data_mode` là MOCK. `ranking.mode` cho biết cách xếp thứ tự. Mỗi candidate có lịch xem trước, thay đổi REST/VISIT và thay đổi chặng. Khi danh sách rỗng, đọc `no_option_reason` và `diagnostics` để biết vì sao.

Demo mượn fixture ngày 2 của Bảo 04 và thêm hai ngày đệm MOCK để kiểm tra bảo toàn cấu trúc lịch 3 ngày. Hai ngày đệm không mô phỏng tuyến HCM-Da Lat. Test riêng cũng kiểm tra snapshot 4 ngày; không có nghĩa PLAN F02 đã được viết.

Lỗi thường gặp: chạy sai thư mục làm không import được adapt_f05; terminal mã hóa lỗi tiếng Việt thì dùng -X utf8; chưa cài httpx/Pydantic thì cài requirements-dev; mode VERIFIED với dữ liệu MOCK sẽ bị từ chối có chủ đích.

<!-- pagebreak -->

## 8. Điểm ghép với Bảo 06 và Linh

Ví dụ bỏ A04 làm hai chặng A03 → A04 và A04 → END chuyển sang `REPLACED`. Chặng A03 → END có ID mới và trạng thái `PENDING`. A04 là `VISIT` nên chuyển sang `DROPPED`. Chặng `DONE` và mọi ngày khác được bảo toàn.

| `travel_changes[].operation` | Dữ liệu trước và sau |
|---|---|
| `RESCHEDULE` | Cùng ID và cặp điểm đầu/cuối. `before` và `after` cho biết giờ cũ, mới |
| `REPLACE` | Cùng ID và giờ cũ. `before.status=PENDING`, `after.status=REPLACED`. Cặp điểm cũ nằm trong `before_edge`, `after_edge=null` |
| `ADD` | ID mới, `after.status=PENDING`, `before=null`. `after_edge=[from_place_id,to_place_id]` |

`REPLACE` và `ADD` có thể xảy ra theo nhóm, ví dụ hai chặng cũ thành một chặng mới. Chặng mới để `replaces_activity_id=null`. Liên kết một-một qua trường này dành cho VISIT thay thế.

1. F05 đọc CURRENT theo tài khoản rồi đóng giao dịch đọc trước khi gọi engine. Dùng `public, stored = prepare_proposal(result, itinerary, catalog)`, gọi `save_proposal(stored, user_id)` rồi trả `public`. Hai bản dùng cùng ID. Chỉ bản lưu chứa `_validation`.
2. F06 tải option từ SQLite và gọi `validate_stored_option(itinerary, option, catalog)` với CURRENT và catalog mới. Hàm kiểm tra fingerprint và dựng lại lịch cùng diff bằng Python. Mobile gửi `proposal_id`, `decision` và `option_id` theo API quyết định.
3. Bảo 06 cập nhật `validate_preservation` để chấp nhận TRAVEL PENDING → REPLACED khi dòng cũ chỉ đổi trạng thái. Giữ ràng buộc một VISIT thay thế cho VISIT cũ. `apply_days` có thể lưu các dòng giữ lịch sử và thêm chặng mới với schema hiện tại. Khi ghép, giữ quyết định, lịch và bước tăng version trong một giao dịch.
4. Linh dùng `travel_changes` để dựng so sánh S05 theo các cặp điểm trước và sau. Khi tải lại CURRENT ở S06/S03, hiển thị `PENDING`/`DONE` trong tuyến hiện hành và để `REPLACED`/`DROPPED` trong lịch sử. S05/S06 hiện dùng cấu trúc mock riêng, cần nối adapter API có xác thực.

PR #16 tại `1fc48eb` lưu được đề xuất và REJECT giữ nguyên lịch. ACCEPT của T06/T13 trả `409 PROPOSAL_NO_LONGER_VALID` vì validator chỉ chấp nhận VISIT chuyển sang REPLACED. PR #18 tại `516d315` tập trung auth và S01–S03. Kiểm tra merge thử giữa #16 và #18 thấy xung đột `backend/main.py`, `backend/requirements.txt` và `mobile/src/app/index.tsx`. Các chủ PR cần thống nhất trước khi chạy toàn luồng.

PR #19 tại `0682f3a` cung cấp snapshot 3/4 ngày và `handoff/routes_mock.json`. Dùng `target_ids` của từng tuyến để ánh xạ REST, điểm ngoài trời và điểm ưu tiên. Tạo `RouteDay` từ `day_id`, `start_place_id`, `end_place_id`, `start_time` và `end_deadline`. T15 dùng catalog `fixtures/mock-no-replacement`. Phiên bản manifest phục vụ báo cáo. `Catalog.version` là fingerprint kiểm tra dữ liệu lúc áp dụng.

<!-- pagebreak -->

## 9. Kiểm thử, tiêu chí đạt và nguồn

Đã chạy 72 test backend, gồm 49 test ADAPT và 23 test auth/F01. T06/T08/T13/T15 qua cả snapshot 3 và 4 ngày của PR #19. Chi tiết kết quả ghép thử F06 nằm trong `docs/testing/adapt-f05-results.md`.

| Yêu cầu từ tài liệu Leader | Bằng chứng trong phần Nhật |
|---|---|
| T06: nghỉ thêm, đưa phương án bỏ hoạt động | Hai phương án kết thúc 16:15. Mỗi phương án giữ hai chặng cũ REPLACED, thêm một chặng PENDING |
| T08: không còn phương án | Nghỉ 16:30 vẫn cần về; trả lý do, không đổi nguồn |
| T13: thay điểm mưa | VISIT mới liên kết VISIT cũ. Hai chặng cũ REPLACED, hai chặng mới PENDING, về 16:15 |
| T15: điểm trong nhà đóng cửa | Không bịa phương án thay thế |
| Chuẩn dữ liệu mục 5-8 | Giờ mở cửa, thời lượng, hai hướng riêng, tổng REST và điểm cuối |
| Chuẩn dữ liệu mục 9-11 | Tách MOCK/VERIFIED, không đổi DONE, bảo toàn ngày khác |
| AI chỉ xếp ưu tiên | ID/mã lý do sai bị chặn; timeout/quota chuyển fallback hoặc lỗi rõ |
| Kiểm tra lại trước lưu | Thay snapshot/dataset hoặc sửa lịch xem trước làm validator từ chối |

Còn chờ kiểm thử ACCEPT và ACCEPT lặp cho T06/T13 sau khi PR #16 cập nhật validator, cùng việc tải lại lịch trên Expo. Luồng thử dùng SQLite tạm, catalog MOCK và xếp hạng bằng luật. Gemini thật và tuyến nguồn cần kiểm chứng riêng.

Trước lượt code tiếp theo: đọc PR đang mở trên GitHub, kiểm tra head/changed files của PR liên quan, git status và nhánh. Commit nhỏ, chỉ stage file ADAPT; không dùng git add . khi có thay đổi của người khác.

Nguồn chính:

- Chuẩn dữ liệu dùng chung V1, Leader chốt 09/11/2026: https://docs.google.com/document/d/1aPJjNORsFIYY0XOlLE6LmhI6lv7sKjg6Up0Gcb-wvSY/edit
- Hợp đồng PLAN/ADAPT: https://docs.google.com/document/d/1EOlYlre0OumuGy7WDF5lTNluTd0qOx5vPkiEpwp1Ys8/edit
- Hợp đồng dữ liệu/F01/F03: https://docs.google.com/document/d/1iRtt03N4jdBgnBuNHrsQkMCoc_8LmmQpyfauP8qcs1Y/edit
- Issue #5: https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/issues/5
- PR #16 đã đối chiếu, head 1fc48eb: https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/pull/16
- PR #18, auth và S01–S03: https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/pull/18
- PR #19, dữ liệu bàn giao 3/4 ngày: https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/pull/19

Không đọc thư mục BAI_NOP_MIDTERM trong công việc này. Tài liệu này giải thích một phần triển khai ADAPT, không thay báo cáo thiết kế toàn hệ thống hoặc yêu cầu chính thức của môn học.
