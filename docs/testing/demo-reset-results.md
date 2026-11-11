# Kết quả kiểm tra công cụ reset

Ngày kiểm tra 10/11/2026. Dataset `bao04-handoff-2026-11-10-v1`.
Các file công cụ đang ở working tree, chưa commit và chưa mở PR.

## Hai lần chạy liên tiếp

Đã chạy CLI thật và đọc lại bằng kết nối SQLite mới sau mỗi lần lưu.
Chi tiết đầu ra từng lượt nằm trong `demo-reset-evidence.json`.

| Snapshot | Lần 1 | Lần 2 | Ngày / hoạt động | Trạng thái / phiên bản |
|---|---|---|---|---|
| CURRENT 3 ngày | PASS | PASS | 3 / 17 | CURRENT / 1 |
| CURRENT 4 ngày | PASS | PASS | 4 / 24 | CURRENT / 1 |

Trong mỗi cặp, toàn bộ JSON đầu ra giống nhau, bao gồm state_fingerprint,
dataset_fingerprint, ID, số ngày và số hoạt động. Lịch đã lưu khớp toàn bộ snapshot
sau khi ánh xạ user_id sang tài khoản thử. Không phát sinh bản ghi trùng.

Fingerprint lịch ba ngày:
`785926b66083a25eebb7eef0b71555544aeaffc344bd285b2fe0824d28e29592`.

Fingerprint lịch bốn ngày:
`92f3b53a588d54129ecb2b046d2eea7f951d6dbb192d19f2a8a35330a357ce81`.

## Các bài kiểm thử đã chạy

| Lệnh từ gốc repo | Kết quả |
|---|---|
| `python -X utf8 -m unittest discover -s backend/tests -p test_demo_reset.py -v` | 11/11 PASS |
| `python -X utf8 -m unittest discover -s backend/tests -v` | 97/97 PASS, đã bao gồm 11 bài mới |
| `python -X utf8 -m unittest discover -s backend -p test_plan_f03.py -v` | 16/16 PASS |

Tổng hai suite không trùng: **113 bài đạt**. Không cộng lại 11 bài chạy riêng.
Python và phiên bản thư viện của lần chạy được ghi trong JSON bằng chứng.

Các kiểm tra mới đã xác nhận:

- CLI chạy được từ ngoài thư mục repo, khôi phục chính xác cả snapshot 3D/4D.
- T15 chọn catalog `mock-no-replacement`, giữ địa điểm ngày khác còn tham chiếu.
- File app, file SQLite chưa có dấu nhận diện, symlink và hard link bị từ chối.
- Fixture lỗi hoặc user_id không tồn tại không làm mất lịch đang lưu.
- Mô phỏng lỗi INSERT sau bước xóa dữ liệu: lịch, đề xuất cũ và version được rollback.
- Reset sau thao tác DONE và sau khi tạo/xác nhận chuyến mới khôi phục đúng v1.
- Lịch, đề xuất và phiên của tài khoản khác không bị thay đổi.
- Ánh xạ được vào tài khoản thử thật khi không xung đột ID; từ chối lấy ID của
  snapshot đang thuộc tài khoản khác.

## Kiểm thử tích hợp F05 và F06

Với T06/T13 trên cả 3D và 4D, bài kiểm dùng catalog/RouteDay thật từ bộ bàn giao,
F05 `RuleRanker`, `prepare_proposal`, `save_proposal` và validator
`validate_stored_option`. Xác thực và các router F03/F06 chạy qua HTTP TestClient,
không thay bằng tài khoản hoặc validator luôn trả thành công.

Đã quan sát:

1. Đọc lịch v1, tạo và lưu đề xuất; lịch hiện hành chưa đổi.
2. ACCEPT trả 200/version 2, có lịch sử TRAVEL REPLACED và các hoạt động mới;
   hoạt động DONE được giữ nguyên.
3. Gửi lại cùng ACCEPT trả đúng kết quả đã ghi.
4. Reset đưa lịch về toàn bộ snapshot v1, dọn hoạt động/lịch sử phát sinh và đề xuất.
5. Dùng lại session cũ vẫn đọc được v1; quyết định dựa trên proposal đã dọn trả 404.
6. Khởi tạo lại app và đọc bằng session đã lưu vẫn thấy đúng lịch v1.

Trên snapshot 4D, đã kiểm REJECT hai lần cho T06/T08/T13/T15. T08/T15 trả không có
option ở tầng F05; REJECT giữ nguyên lịch. Reset cũng dọn được kết quả REJECT đã lưu.

## Giới hạn và bàn giao

Đây là kết quả reset SQLite và kiểm tích hợp cục bộ, không phải nghiệm thu T01–T15
đầu cuối. Chưa gọi Gemini, chưa chạy Expo/Android, chưa kiểm đường mạng từ điện thoại.
F05 được gọi ở tầng domain, chưa kiểm endpoint HTTP tạo đề xuất từ giao diện.

CLI không chuyển database của backend đang chạy. Bảo 06/Đăng cần trỏ tiến trình
backend thử vào đúng file đã nạp, đối chiếu schema và catalog metadata trước khi
Tân chạy trên app. Công cụ dùng schema hiện có; chưa tạo thêm bảng places/travel_times.

Khi có thay đổi schema hoặc thêm bảng phụ thuộc lịch/đề xuất, chạy lại kiểm thử và
review cleanup cùng Bảo 06. Không dùng dữ liệu MOCK bù vào lịch nguồn còn thiếu.
Các mốc ngày 4, 6, 10 được giữ trong hướng dẫn; không đánh dấu trước các mốc là đã đạt.
