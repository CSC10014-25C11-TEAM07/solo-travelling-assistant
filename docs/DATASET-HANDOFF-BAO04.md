# Bàn giao Bảo 04 — mốc MVP 15/11/2026

Phiên bản: **bao04-mvp-2026-11-15-v1**, tiếp tục bộ PR #19. Phạm vi theo mục 3.5
bản phân công 14/11: dữ liệu, F01, loader/validator và cấu hình tuyến. Không sửa
router, SQLite, provider AI hoặc giao diện của các bạn khác.

**Đã chốt bốn ca MOCK và tập nguồn nhỏ để rà/nạp. Hai tuyến nguồn chưa đủ điều kiện
lập lịch thật.** Nghiệm thu 18/11 vẫn cần AI thật, API/lưu thật và Expo Go có bằng chứng.

## Chọn bộ đúng ca

Đường dẫn tính từ `backend/data/`; `handoff/manifest.json` là mục lục phiên bản.

| Việc/ca | Catalog và cấu hình | Kết quả kiểm được |
|---|---|---|
| F01 sở thích | `places.json`, `travel_times.json` | 15 địa điểm có nguồn, không dùng MOCK; không có mốc tập kết/nghỉ trong gợi ý |
| T06 nghỉ thêm phải bỏ điểm | `fixtures/mock/` | Nghỉ đến 15:00: giữ hai điểm tới 17:15; bỏ một điểm về 16:15 |
| T08 nghỉ quá muộn | `fixtures/mock/` | Nghỉ tới 16:30, bỏ hết vẫn về 16:45; không có phương án |
| T13 đổi điểm vì mưa | `fixtures/mock/` | REST→INDOOR→A04→END, về 16:15; đủ hai chặng của điểm mới |
| T15 không có điểm thay hợp lệ | `fixtures/mock-no-replacement/` | INDOOR đóng cửa; điểm còn mở là MIXED; không có phương án |
| CURRENT đầy đủ | `fixtures/current_v1_3day.json`, `current_v1_4day.json` | Đủ ngày đi/về HCMC, TRAVEL/REST/VISIT; ID riêng cho từng snapshot |
| Mapping cho Nhật/Tân | `handoff/routes_mock.json`, `fixtures/scenarios.json` | Lấy `target_ids` đúng snapshot, không gửi metadata `checked_paths` lên API |
| Nguồn 3/4 ngày | `handoff/routes_source.json` | Cấu hình còn BLOCKED, xem `gaps` trong audit |
| Nguồn cho nhánh mưa | `handoff/source_adapt_checks.json` | P010→P005→P008→P001 và P011→P005→P001 đủ chặng; chưa đủ venue/giờ để chạy thật |

MOCK giữ nguyên nội dung từ PR #19: hai catalog đều 11 điểm/20 chặng, snapshot3D/4D
version1. Ca T15 không xóa ID vì ngày khác còn tham chiếu. `current_v1_day2.json` là
fixture cũ một ngày, chỉ giữ tương thích demo. Replay hiện tại dùng **F05 đã merge**,
RuleRanker, 8 lượt T06/T08/T13/T15 × 3D/4D. SHA256 của fixture và implementation ở
`docs/testing/dataset-handoff-f05-replay.json` để nhận biết thay đổi sau kiểm.

## Tập nguồn nhỏ đã đối chiếu

Catalog đầy đủ: **15 điểm UNVERIFIED; 24 chặng có hướng, gồm 20 ước tính VERIFIED
và 4 qua R003 UNVERIFIED**. Tập tối thiểu gồm 8 điểm được cả tuyến và nhánh mưa
tham chiếu: H001, R003, P001, P005, P008, P009, P010, P011; kèm 24 chặng, tọa độ,
raw evidence, cấu hình và báo cáo. Đây là **REVIEW_ONLY**, không phải seed tự động
được phép lập lịch thật. Catalog F01 đầy đủ vẫn giữ 15 điểm.

Bổ sung 15/11:

- P005: [cổng du lịch tỉnh](https://visitlamdong.vn/vi/baotangld) nêu thời lượng
  120 phút cho toàn điểm. Đã điền có nguồn; chưa coi đó là thời lượng riêng khu có mái.
- [Website bảo tàng](https://baotanglamdong.com.vn/contact) nêu 07:30–17:30, cổng tỉnh
  nêu 07:30–16:30; lịch nghỉ trưa OSM cũ còn khác. `opening_hours.weekly` giữ null.
- Đọc lại [Ga Đà Lạt](https://visitlamdong.vn/vi/nhagadalat),
  [Still Cafe](https://visitlamdong.vn/vi/stillcafe) và
  [Là Việt](https://laviet.coffee/tu-chung-toi/); chỉ cập nhật ngày đọc của đúng mục.
- Thu và rà thêm P008→P001 **12 phút**, P011→P005 **7 phút**, P005→P009 **8 phút**,
  P009→P001 **8 phút**. Hai cặp sau phục vụ đường nối khi bỏ điểm. Có raw summary,
  query và ngày thu 15/11, tọa độ OSM giữ ngày đọc gốc 07/11.

VERIFIED của chặng là **ước tính mô hình** đã rà cặp tọa độ/query motorcycle và
`ceil(summary.time/60)`, không phải đo thực tế, traffic hoặc xác nhận quyền đi xe máy
từng đoạn. Collector luôn xuất UNVERIFIED; chỉ bốn chặng mới đã rà thủ công mới được
nâng nhãn. Tất cả venue vẫn UNVERIFIED. Không dùng dữ liệu MOCK bù vào bộ nguồn.

## Những chỗ Bảo 04 cần xác minh tiếp

Ưu tiên phần nhỏ bên dưới; chưa cần thu thêm hàng chục địa điểm.

| Ưu tiên | Điểm/việc | Đã có | Cần hỏi/ghi bằng chứng |
|---|---|---|---|
| 1 | R003 Tâm Châu 294A Trần Phú, Bảo Lộc | Ứng viên tọa độ theo tên/đường, bốn chặng ước tính | Đúng số nhà/tọa độ cổng, giờ tuần, chỗ dừng xe máy và tiếp cận hai chiều; website vẫn 403 ngày 15/11 |
| 1 | Điểm ngủ Đà Lạt + H001 | Ga P001 và bưu điện H001 mới là mốc đề xuất | Chọn địa chỉ lưu trú thực; giờ/chỗ tiếp cận điểm đầu-cuối; tọa độ và chặng nối nơi ngủ. Không gọi ga là homestay |
| 1 | P005 Bảo tàng, 02633 812 624 | 120 phút toàn điểm, 04 Hùng Vương | Lịch từng thứ/ngày lễ, nghỉ trưa, thời lượng/phạm vi khu có mái cho RAIN; giải quyết ba lịch khác nhau |
| 2 | P010 Still Cafe, 0368 151 215 | 59 Nguyễn Trãi, giờ chung 07:00–22:00 | Thời lượng tham quan dự kiến được nhóm chốt, khu có mái và ngoại lệ giờ |
| 2 | P011 An Cafe | Tag giờ OSM cũ 07:00–22:00 | Thời lượng, môi trường, lịch tuần/ngày lễ; chưa có lần đọc nguồn mới |
| 2 | P001/P008/P009 | Thời lượng lần lượt 90/60/60 phút | Lịch tuần; P008 có xung đột nghỉ trưa, P009 có xung đột giờ mở; không tự chọn một nguồn để gắn VERIFIED |

Cách ghi: URL/ảnh thông tin đơn vị hoặc nội dung trả lời có ngày, địa chỉ đúng chi nhánh,
7 ngày mở cửa (kể cả nghỉ trưa), thời lượng và phạm vi có mái. Điền vào
`data_review.json`/`source_checks.json` rồi mới cập nhật trường catalog. Không lưu số cá
nhân hoặc thông tin không cần thiết; các số ở bảng là số liên hệ công khai của venue.
Thời lượng tự chọn để lập lịch phải ghi là tham số đề xuất và được nhóm chốt; không
biến thành thời lượng “đơn vị xác nhận”.

**Vướng thời gian cần Nhật/Đăng xử lý:** ngày đi 06:00 + 380 + 60 nghỉ + 237 phút =
**17:17**, đã vượt hạn dự kiến 17:00 trước VISIT/buffer. Ngày về tương ứng 17:19 so với
hạn18:00. Bốn chặng qua R003 chưa xác nhận tọa độ; đây là cận dưới có điều kiện. Không
âm thầm nới hạn hoặc rút ngắn chặng. Khi có tuyến/điểm nghỉ đúng, thu lại các cặp liên
quan rồi chạy audit. Hạn17:00/18:00 là cấu hình đề xuất, 16:30 chỉ dùng ở MOCK ngày2.

## Chạy lại và bàn giao cho nhóm

Dùng Python đã cài requirements backend (Mac có thể dùng `backend/.venv/bin/python`
thay `python`; Windows dùng interpreter trong `backend/.venv/Scripts/`). Từ gốc repo:

```bash
python -m unittest discover -s backend/tests -v
python backend/scripts/validate_places.py
python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock-no-replacement
python backend/scripts/audit_data_handoff.py --output /tmp/sta-handoff-report.json
python backend/scripts/replay_handoff_f05.py --output /tmp/sta-f05-replay.json
python backend/scripts/prepare_source_bundle.py --output-dir /tmp/sta-source-review-new
```

Exporter yêu cầu thư mục mới, từ chối ghi trong/đè lên catalog, không theo symlink
output và không ghi SQLite. Mở `readiness.json` trong output trước khi nạp. Tên file
export ngắn và phẳng: `places.json`, `travel_times.json`, `routes_source.json`,
`source_adapt_checks.json`, evidence, manifest và review; không chứa catalog MOCK.
Audit exit0 chỉ nghĩa cấu trúc/kỳ vọng MOCK khớp. Tuyến nguồn báo riêng false; lịch có
điều kiện tính VISIT/REST/chờ mở cửa và điểm đầu/cuối, không tính WAIT là REST.

- **Nhật:** dùng fixtures/catalog đúng ca; map RouteDay và target_ids. Bộ nguồn chưa
  được dùng mode VERIFIED; giải quyết gaps rồi kiểm ràng buộc F02/F05.
- **Bảo 06:** nhận JSON export, giữ place_id và nhãn, cấp ID SQLite. Việc import/seed
  SQLite thuộc Bảo 06; không có database bị xóa/reset bởi các công cụ của PR này.
- **Tân:** PR #22 phụ trách reset/test; dùng database riêng và ánh xạ MOCK-USER/ID
  theo fixture. Ghi version backend trả về; DONE thật làm tăng version. Không POST
  nguyên snapshot vào API tạo nháp vì API chỉ nhận input PLAN.
- **Hân/Bảo 04/Đăng:** PR #18 đã merge; chạy checklist
  `docs/testing/s01-f01-handoff.md` trên bản ghép/Expo Go. API đã kiểm bốn nhóm sở
  thích qua phiên SQLite thật, nhưng S01/thiết bị vẫn **NOT_RUN**.

Xem kết quả và giới hạn trong `docs/testing/dataset-handoff-results.md`. Chưa đóng
issue #8: nguồn thực và kiểm tích hợp/thiết bị còn thiếu. Theo mốc mới: 16/11 bổ sung
nguồn tối thiểu, 17/11 kiểm bản ghép, 18/11 cố định phiên bản cuối sau nghiệm thu.
