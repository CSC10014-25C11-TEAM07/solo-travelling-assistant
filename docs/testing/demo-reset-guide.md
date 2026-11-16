# Công cụ nạp lại CURRENT v1

Công cụ khôi phục snapshot MOCK 3 hoặc 4 ngày của Bảo 04 vào SQLite kiểm thử,
để mỗi lượt demo bắt đầu từ cùng một lịch. Công cụ dùng cấu trúc thật của
`auth`, `itinerary_store` và `adapt_store`, không thay đổi API hoặc dữ liệu nguồn.

## Chuẩn bị một lần

Chạy tại thư mục gốc repo, dùng Python trong môi trường backend đã cài
`backend/requirements-dev.txt`. Nếu máy dùng môi trường ảo, kích hoạt môi trường
đó trước khi dùng lệnh `python` bên dưới. Không cần Gemini, điện thoại hoặc mạng
để reset và chạy bộ kiểm thử này.

## Một lệnh nạp lịch demo bốn ngày

```bash
python -X utf8 backend/scripts/reset_demo.py
```

Mặc định:

- Database: `backend/.test-data/tan-demo.test.sqlite3`, được Git bỏ qua.
- Dataset: phiên bản đọc từ `backend/data/handoff/manifest.json`.
- Snapshot: `fixtures/current_v1_4day.json`, trạng thái CURRENT, version 1.
- Catalog: `fixtures/mock`, chuẩn bị cho T06.
- Tài khoản thử: `mock_tan_demo`, user_id `MOCK-TAN-USER`.
- Mật khẩu MOCK công khai: `MOCK-only-test-password-2026`.

Đây là tài khoản được tạo thật trong SQLite thử bằng bộ băm mật khẩu của dự án.
Thông tin trên hoàn toàn giả lập, không sử dụng làm tài khoản thật. Những lần reset
sau giữ nguyên tài khoản, mật khẩu và phiên đăng nhập hiện có; chỉ nạp lại dữ liệu
lịch của tài khoản được chọn. Công cụ không in mật khẩu hay token.

Chạy lại cùng lệnh để reset. Exit code 0 và `reset: "PASS"` chỉ xuất hiện sau khi
lịch được lưu, đóng kết nối rồi đọc lại khớp toàn bộ snapshot.

## Chọn số ngày và ca thử

```bash
python -X utf8 backend/scripts/reset_demo.py --days 3 --scenario T06
python -X utf8 backend/scripts/reset_demo.py --days 4 --scenario T13
python -X utf8 backend/scripts/reset_demo.py --days 4 --scenario T15
```

| Ca | Catalog được ghi nhận | Kết quả nghiệp vụ mong đợi khi ghép F05/F06 |
|---|---|---|
| T06 | `fixtures/mock` | Nghỉ tới 15:00; bỏ một điểm để kết thúc 16:15 |
| T08 | `fixtures/mock` | Nghỉ tới 16:30; không có phương án vì còn chặng về |
| T13 | `fixtures/mock` | Thay A03 bằng điểm trong nhà; kết thúc 16:15 |
| T15 | `fixtures/mock-no-replacement` | Không có điểm thay thế hợp lệ |

`--scenario` chọn metadata/catalog cần dùng khi kiểm, không tự gọi F05 hoặc áp dụng
một phương án. T06/T13/T15 vẫn reset cùng snapshot gốc cho độ dài đã chọn.
T15 giữ đủ địa điểm và ID, chỉ dùng catalog âm tính riêng; không xóa quán còn được
ngày 3 tham chiếu. Catalog phải được F05/test harness đọc theo đúng metadata này.

Hai snapshot dùng mã ngày/hoạt động riêng. Đầu ra có `target_ids` lấy từ
`handoff/routes_mock.json`: dùng mã như `MOCK4D-A03`, không gửi chuỗi `A03` chung.
Version 1 là trạng thái fixture đã nạp sẵn DONE, không phải kết quả chạy các thao
tác DONE qua API. Khi kiểm F03 thật, lấy version backend mới trả về.

## Chọn file hoặc tài khoản thử khác

```bash
python -X utf8 backend/scripts/reset_demo.py --database backend/.test-data/another.test.sqlite3 --days 4 --scenario T06
```

File mới được khởi tạo bằng schema hiện có của dự án và gắn dấu nhận diện nội bộ.
File đã tồn tại nhưng chưa có dấu nhận diện bị từ chối, kể cả tên có đuôi test.
Không có cờ bỏ qua bảo vệ. Không dùng `backend/app.sqlite3`.

Nếu Bảo 06 đã tạo tài khoản khác qua API trên **chính database thử đã được công cụ
khởi tạo**, truyền `--user-id` thực tế của tài khoản đó:

```text
python -X utf8 backend/scripts/reset_demo.py --database <file.test.sqlite3> --days 3 --user-id <user_id_thử>
```

Không tự tạo tài khoản khi `--user-id` không tồn tại. Nếu ID của snapshot đang thuộc
lịch của tài khoản khác, thao tác bị từ chối và rollback; không lấy ID của người
khác. Khuyến nghị một tài khoản demo chính trên mỗi database thử riêng.

## Những dữ liệu được reset

Trong một giao dịch, công cụ dọn toàn bộ lịch nháp/lịch đã xác nhận của **tài khoản
được chọn**, các ngày/hoạt động liên quan và các đề xuất ADAPT của tài khoản đó,
bao gồm payload, quyết định và kết quả gửi lặp. Sau đó nạp lại đúng một lịch CURRENT
v1 theo snapshot đã chọn. Vì vậy, một lịch mới được xác nhận ở lượt thử trước không
che khuất lịch demo theo `confirmed_at`.

Các liên kết `replaces_activity_id` trong lịch sử thay mưa được xử lý trước khi xóa.
Nếu lỗi lưu hoặc ID xung đột, giao dịch bị hủy: lịch và đề xuất trước đó được giữ.
Tài khoản, session và lịch/đề xuất của tài khoản khác không bị reset.

Không tạo bảng `places`/`travel_times` riêng để thay schema của Bảo 06. Hiện catalog
được kiểm tra từ JSON bàn giao; metadata ghi rõ catalog nào cần dùng. Khi Bảo 06
ghép catalog vào SQLite hoặc thêm bảng phụ thuộc mới, cần review lại thứ tự cleanup
và kiểm thử khóa ngoại. Không âm thầm tắt khóa ngoại hoặc tự xóa bảng chưa biết.

## Kết nối với backend thử

CLI chỉ nạp file SQLite và kết thúc. Nó **không đổi** đường dẫn database của backend
đang chạy. Backend mặc định vẫn dùng `backend/app.sqlite3`.

Bảo 06/Đăng cần cấu hình tiến trình backend kiểm thử dùng đúng file đã chọn trước
khi khởi tạo app; các store hiện dùng kết nối từ `auth.DB_PATH`. Không sửa đường
dẫn database thật để chạy demo. Bộ integration test đi kèm đã trỏ `auth.DB_PATH`
vào database tạm và dùng các router/xác thực thật để kiểm thao tác này.

Sau khi ghép server test, đọc `GET /api/v1/itineraries/current` bằng tài khoản thử
và kiểm tra itinerary_id, user_id, version cùng toàn bộ ngày/hoạt động trước demo.
Không POST nguyên snapshot vào API tạo nháp; API đó chỉ nhận năm trường PLAN.

## Xác nhận chạy hai lần liên tiếp

Chạy cùng lệnh hai lần. So sánh các trường:

- `dataset_version`, `dataset_fingerprint`, `snapshot`, `catalog`.
- `state_fingerprint`, `itinerary_id`, `status`, `version`.
- `day_count`, `activity_count`, `target_ids`.

Mỗi lần phải CURRENT/version 1; ngày 2 giữ DONE, nghỉ 13:00–14:00 và A03/A04
PENDING như mẫu. Kết quả thực tế lần này ở `demo-reset-evidence.json`.

Chạy các kiểm thử của công cụ:

```bash
python -X utf8 -m unittest discover -s backend/tests -p test_demo_reset.py -v
```

Các bài kiểm chứng minh: CLI chạy hai lần cho 3D/4D; reset sau DONE và sau một chuyến
mới; F05 RuleRanker → lưu đề xuất → ACCEPT/REJECT bằng router F06 thật; gửi lặp;
reset sau ACCEPT xóa chặng mới/lịch sử và quyết định cũ; session và dữ liệu người
khác được giữ; đọc lại sau khi app khởi tạo lại; lỗi ghi giữa chừng rollback.

Các ca chấp nhận dùng `validate_stored_option` của Nhật, không dùng validator luôn
trả true. T08/T15 cũng được kiểm không có option và từ chối giữ nguyên lịch.

## Mốc công việc và phạm vi kết quả

| Mốc tương đối | Việc của Tân |
|---|---|
| Ngày 4 | Kiểm PLAN khi có bản ghép; ghi dữ liệu và kết quả thật |
| Ngày 6 | Kiểm ADAPT; reset cùng snapshot trước mỗi lượt nghỉ thêm/đổi mưa |
| Ngày 10 | Chạy đủ T01–T15 trên bản nộp; lưu kết quả và bằng chứng |

Ghi commit bản chạy, dataset_version, snapshot/catalog, tài khoản thử, request,
version, mong đợi, thực tế và bằng chứng. Không đưa token/mật khẩu thật vào log.

Kết quả công cụ không thay thế nghiệm thu toàn bộ T01–T15, Gemini, Expo hoặc Android.
Integration test gọi F05 ở tầng domain, rồi dùng HTTP TestClient cho F03/F06; không
chứng minh endpoint tạo đề xuất F05 hoặc giao diện đã tích hợp.

Điều chỉnh review đã nhận: Đăng review chính PR S04–S06 của Linh; Nhật hỗ trợ dữ
liệu phương án F05. Không tự suy ra reviewer cho PR công cụ của Tân. Hiện chỉ viết
file và kiểm thử cục bộ, chưa tạo nhánh/commit hoặc mở PR.
