# Dữ liệu địa điểm và tuyến mẫu

Phiên bản **bao04-mvp-2026-11-16-v1**, áp dụng chuẩn dữ liệu Leader chốt 09/11.
Đọc [hướng dẫn bàn giao](../../docs/DATASET-HANDOFF-BAO04.md) để biết bộ dùng cho từng ca,
nguồn, cách reset và phần cần bổ sung. Hợp đồng HTTP F01 không đổi.
[Xác minh nguồn 16/11](../../docs/DATA-SOURCE-VERIFY-BAO04.md) có kết quả mới, mẫu hỏi
đơn vị và cấu hình còn cần Bảo 04 chốt. Trợ lý đã thực hiện phần tra cứu có thể làm qua web.

| File/thư mục | Nội dung |
|---|---|
| `places.json` | 15 hồ sơ có nguồn: P009 VERIFIED, 14 UNVERIFIED; 11 trải nghiệm, 3 điểm nghỉ và mốc H001 |
| `travel_times.json` | 24 chặng có hướng: 20 ước tính VERIFIED, 4 qua R003 còn UNVERIFIED |
| `place_coordinates.json` | 8 tọa độ/ứng viên; R003 chưa khớp số nhà |
| `travel_time_evidence.json` | Summary, checked_at UTC, query, phương thức/làm tròn và nhận xét rà soát |
| `data_review.json`, `handoff/source_checks.json` | Trường thiếu, xung đột, ngày đọc thực tế và việc cần bổ sung |
| `handoff/routes_source.json` | Tuyến nguồn 3/4 ngày; cả hai chưa đủ điều kiện lập lịch thật |
| `handoff/source_adapt_checks.json` | Hai nhánh P010→P005→P008→P001 và P011→P005→P001; đủ chặng, venue vẫn thiếu thông tin |
| `handoff/routes_mock.json` | RouteDay và mapping ID cho snapshot MOCK 3/4 ngày |
| `fixtures/current_v1_3day.json`, `current_v1_4day.json` | CURRENT MOCK đủ ngày đi/về, nghỉ và chặng, version 1 |
| `fixtures/mock/` | 11 điểm/20 chặng MOCK cho nghỉ thêm và đổi mưa thành công |
| `fixtures/mock-no-replacement/` | 11 điểm/20 chặng MOCK riêng cho ca không có điểm thay thế |
| `fixtures/scenarios.json` | T06/T08/T13/T15, request, catalog và đường đi/kết quả mong đợi |
| `fixtures/current_v1_day2.json` | Fixture ngày 2 cũ, giữ cho tương thích demo |

## Quy tắc dữ liệu

- Area chỉ có HCMC/DALAT/EN_ROUTE. Môi trường có INDOOR/OUTDOOR/MIXED.
  Hồ sơ UNVERIFIED chưa rõ môi trường giữ null, không đoán là trong nhà.
- VERIFIED/MOCK/UNVERIFIED thay nhãn SOURCED cũ. Có URL chưa đủ gắn VERIFIED.
  20 ước tính đã được rà query motorcycle, đầu/cuối, số giây/cách làm tròn; 4 chặng bổ sung ngày 15/11.
  Nhãn VERIFIED của chặng chỉ áp dụng ước tính, không xác minh venue hay quyền đi từng đoạn.
- P009 đã đối chiếu đủ hồ sơ VISIT: lịch đơn vị 08:30–18:00 hằng ngày, MIXED và
  thời lượng ước tính 60 phút từ cổng tỉnh. Giữ nguồn/khác biệt cũ và lý do chọn giờ
  trong source_checks.json. VERIFIED ở cấp điểm không xác nhận cả tuyến. 14 điểm
  còn lại UNVERIFIED vì thiếu/xung đột giờ, thời lượng, chi nhánh hoặc tiếp cận.
- A→B và B→A độc lập; cùng ID hợp lệ là 0. Thiếu chặng không phải 0.
- MOCK tách riêng; không dùng bù dữ liệu thực. `get_travel_time` cần opt-in cho MOCK.
- T15 dùng catalog riêng: điểm INDOOR đóng cửa, quán còn lại MIXED. Không xóa điểm
  đang được ngày khác tham chiếu hoặc dùng catalog T13 có quán INDOOR mở cửa.
- min_rest_minutes là tổng REST mỗi ngày. 16:30 chỉ là hạn của ca demo ngày 2.
- Restart backend sau khi đổi JSON để bỏ cache. F01 không gọi dịch vụ định tuyến.

## Kiểm tra offline

```bash
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock-no-replacement
backend/.venv/bin/python backend/scripts/audit_data_handoff.py
backend/.venv/bin/python backend/scripts/replay_handoff_f05.py
backend/.venv/bin/python backend/scripts/prepare_source_bundle.py --output-dir /tmp/sta-source-review-new
```

Audit exit 0 xác nhận cấu trúc/kỳ vọng của bộ kiểm khớp. Tuyến thật báo riêng
`ready_for_real_plan: false` và từng gap. Không sửa số liệu để ép tuyến thành khả thi.

Exporter tạo tập nhỏ 8 điểm/24 chặng + cấu hình + provenance + readiness trong thư mục **mới**.
Giữ nguyên nhãn, không ghi SQLite, không dùng thay catalog F01 đầy đủ. Hai tuyến vẫn BLOCKED.
Audit tính VISIT, REST, chờ cửa mở, cả chặng cuối và quyền tiếp cận theo giờ của mốc; chưa biết
đầu vào thì dừng lịch có điều kiện và báo gap. Replay F05 kiểm 8 lượt domain, không chứng minh
API F05/F06, AI thật hoặc thiết bị.

## Thu thêm chặng

```bash
backend/.venv/bin/python backend/scripts/collect_travel_times.py --pairs /tmp/f01-pairs.json --output-dir /tmp/sta-routes-review
```

Pairs chứa from_place_id/to_place_id; các ID cần tọa độ có nguồn. Chọn thư mục output
mới. Script giới hạn đợt nhỏ 1–20 chặng, cách nhau 1,2 giây, không tự retry; lỗi nguồn
thì dừng. Kết quả mới luôn UNVERIFIED để chờ rà đúng điểm, query và evidence rồi mới
quyết định nhãn. Không chép đè bộ cũ bằng output chỉ chứa một chặng.

## Nguồn và ghi công

- [Cổng du lịch Lâm Đồng](https://visitlamdong.vn/), [Là Việt](https://laviet.coffee/tu-chung-toi/),
  [Bảo tàng Lâm Đồng](https://baotanglamdong.com.vn/contact), [Tâm Châu](https://tamchau.com/gioi-thieu/):
  giữ URL từng điểm, không sao chép bài mô tả/ảnh. Ảnh trong catalog nguồn đều null.
- Bổ sung 16/11: [Crazy House](https://crazyhouse.vn/tham-quan),
  [Tâm Châu Center](https://www.tamchaucenter.com/lien-he),
  [An CaFe](https://www.ancafeglobal.com/) và [trang vé bảo tàng](https://baotanglamdong.com.vn/tickets).
  Giữ nguồn từng trường và quyết định xử lý xung đột trong `handoff/source_checks.json`.
- © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL 1.0:
  tọa độ, tag giờ và mạng đường; giữ ghi công/điều kiện ODbL khi dùng hoặc phân phối.
  [Photon](https://photon.komoot.io/) cung cấp geocoding OSM cho H001/R003.
- [Valhalla route API](https://valhalla.github.io/valhalla/api/route/api-reference/):
  motorcycle; ceil(summary.time/60). Public demo chỉ dùng lấy mẫu nhỏ, không làm
  backend định tuyến cho người dùng.

VERIFIED của ước tính không bảo đảm traffic, giờ đến thực tế hay quyền/độ an toàn đi
xe máy từng đoạn. Bốn chặng qua tọa độ ứng viên R003 vẫn UNVERIFIED.

S01 đã kiểm trên Android Emulator/Expo Go ở main dbb46af; main dbb46af có lỗi clear-inflight; PR tiếp nối có bản sửa đã kiểm regression.
Điện thoại thật vẫn NOT_RUN. Xem `s01_device_test` trong manifest và
[checklist/kết quả S01](../../docs/testing/s01-f01-handoff.md). Chỉ metadata kiểm
chứng được cập nhật; catalog, chặng và cấu hình tuyến bao04-mvp-2026-11-16-v1 giữ nguyên.
