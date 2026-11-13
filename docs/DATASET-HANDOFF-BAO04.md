# Bàn giao dữ liệu tuyến mẫu và ba ca ADAPT

Phiên bản: **bao04-handoff-2026-11-10-v1**. Phụ trách dữ liệu: Bảo 04.
Nhật kiểm logic, Bảo 06 nhập SQLite, Tân chạy và ghi bằng chứng; Hân ghép F01 trên S01.

**Bộ MOCK 3/4 ngày dùng được để kiểm logic. Hai tuyến có nguồn đã chọn điểm và chặng,
nhưng chưa đủ dữ liệu để chạy như lịch thực tế đã xác minh.** Không dùng số MOCK bù
vào tuyến có nguồn. File `backend/data/handoff/manifest.json` xác định phiên bản và các bộ đi kèm.

Chuẩn áp dụng: [Chuẩn dữ liệu dùng chung V1, chốt 09/11](https://docs.google.com/document/d/1aPJjNORsFIYY0XOlLE6LmhI6lv7sKjg6Up0Gcb-wvSY/edit)
và [API PLAN/ADAPT V1](https://docs.google.com/document/d/1EOlYlre0OumuGy7WDF5lTNluTd0qOx5vPkiEpwp1Ys8/edit).

## Bộ nào dùng cho việc nào

Các đường dẫn dưới đây tính từ `backend/data/`.

| Bộ/file | Người nhận và mục đích | Trạng thái |
|---|---|---|
| `places.json`, `travel_times.json` | Nhật/Bảo 06: thông tin có nguồn, F01 và hồ sơ bổ sung dữ liệu | 15 địa điểm UNVERIFIED; 16 ước tính chặng VERIFIED và 4 chặng UNVERIFIED |
| `handoff/routes_source.json` | Cấu hình hai tuyến nguồn 3/4 ngày, điểm đầu/cuối, hạn giờ, thứ tự điểm và nghỉ/ngày | SOURCE-3D/SOURCE-4D chưa sẵn sàng lập lịch thực |
| `handoff/source_checks.json`, `data_review.json` | Tân/Nhật: nguồn đã đọc, trường thiếu, xung đột, việc cần bổ sung từng điểm | Không coi URL có sẵn là xác minh đầy đủ |
| `fixtures/mock/` | T06 nghỉ thêm phải bỏ điểm; T08 nghỉ quá muộn; T13 đổi điểm vì mưa thành công | 11 điểm/20 chặng, toàn bộ MOCK |
| `fixtures/mock-no-replacement/` | T15 không có điểm thay thế hợp lệ | 11 điểm/20 chặng MOCK; catalog riêng |
| `fixtures/current_v1_3day.json`, `current_v1_4day.json` | Snapshot CURRENT có đủ ngày/hoạt động cho Nhật/Bảo 06/Tân | MOCK, version 1, chưa phải tài khoản/ID do API thật cấp |
| `handoff/routes_mock.json` | Điểm đầu/cuối, giờ bắt đầu/hạn giờ của từng ngày và mapping activity_id cho hai snapshot | MOCK-3D/MOCK-4D |
| `fixtures/scenarios.json` | Đầu vào API, catalog phải dùng và các đường đi/kết quả mong đợi | T06/T08/T13/T15; `checked_paths` là dữ liệu kiểm thử, không phải trường gửi API |

`current_v1_day2.json` cũ vẫn giữ để tương thích bản demo của Nhật; đó chỉ là ngày 2.
Hai snapshot mới có đầy đủ ngày đi/về bằng dữ liệu giả lập, không dùng ngày đệm rỗng.
ID hoạt động/ngày của snapshot 3D và 4D khác nhau để không đụng nhau khi nhập.

## Hai tuyến có nguồn đã chọn

H001: mốc tập kết đề xuất tại Bưu điện Trung tâm Sài Gòn; R003: ứng viên điểm nghỉ
Tâm Châu 294A Trần Phú, Bảo Lộc; P001: Ga Đà Lạt. H001/R003 có `interests: []`,
không trở thành thẻ gợi ý tham quan. P001 chỉ làm mốc Đà Lạt trong cấu hình này,
không phải khách sạn; còn thiếu chặng kết nối tới chỗ lưu trú thực tế.

| Ngày | SOURCE-3D | SOURCE-4D |
|---|---|---|
| 1 | H001 → R003 (nghỉ 60 phút) → P001 | Giống tuyến 3D |
| 2 | P001 → Still Cafe P010 (nghỉ 60 phút) → Bảo tàng P005 → P001 | Giống tuyến 3D |
| 3 | P001 → R003 (nghỉ 60 phút) → H001 | P001 → P005 (nghỉ 30 phút) → Dinh III P008 → Crazy House P009 → An Cafe P011 (nghỉ 30 phút) → P001 |
| 4 | — | P001 → R003 (nghỉ 60 phút) → H001 |

Ngày mẫu là 14–16/12/2026 hoặc 14–17/12/2026. Tổng nghỉ yêu cầu 60 phút/ngày
là dữ liệu chọn cho hai tuyến mẫu, không phải quy tắc sức khỏe cho mọi người.
Giờ đi 06:00, ngày nội vùng bắt đầu 08:00. Hạn 17:00 cho ngày đi/nội vùng và 18:00
cho ngày về là **đề xuất cấu hình tuyến cần Nhật kiểm khả thi**, không phải giờ đóng cửa
địa điểm và không được coi đã xác minh. Không áp dụng mốc MOCK 16:30 cho tuyến thật.

Đã thu đủ 20 ước tính chặng có hướng cho các cặp được chọn và các chặng nội vùng
có từ bản trước. Các cặp khác ngoài danh sách vẫn có thể thiếu; không suy chiều ngược.

**Vấn đề thời gian đã phát hiện:** ước tính H001→R003 là 380 phút và R003→P001 là
237 phút. Nếu các tọa độ/ước tính này được chấp nhận, chỉ lái xe và nghỉ 60 phút từ
06:00 đã tới **17:17**, vượt hạn đề xuất 17:00, chưa cộng tham quan hoặc buffer.
Lượt về tương ứng 236 + 383 + 60 phút, cận dưới là 17:19. Đây không phải giờ đến
cam kết; cả bốn chặng qua R003 vẫn UNVERIFIED vì chưa xác nhận tọa độ đúng số nhà.
Nhật cần kiểm lại tuyến/điểm nghỉ/ngân sách giờ, không dùng các con số này để tuyên bố
chuyến 3/4 ngày đã khả thi hoặc tự đổi hạn giờ trong AI.

## Đã kiểm được gì và còn thiếu gì

Nguồn đọc lại ngày 10/11 được ghi theo từng dòng trong `handoff/source_checks.json`.
Các điểm chưa đọc lại được giữ ngày kiểm cũ; không đổi tất cả checked_at thành ngày mới.

| Điểm | Dữ kiện đã đọc được | Cần bổ sung trước khi dùng tự động |
|---|---|---|
| P001 Ga Đà Lạt | Cổng Lâm Đồng nêu 07:00–17:30, tham quan 90 phút | Lịch từng thứ/ngày lễ, tiếp cận điểm tập kết, nối chỗ lưu trú |
| P005 Bảo tàng | Website chính thức nêu 07:30–17:30 | Khác giờ OSM/nghỉ trưa; thời lượng khu trưng bày |
| P008 Dinh III | Cổng Lâm Đồng nêu 07:00–17:30, 60 phút | OSM ghi nghỉ trưa và đóng 17:00; chưa giải quyết xung đột |
| P009 Crazy House | Cổng Lâm Đồng nêu 07:30–19:00, 60 phút | OSM mở 08:30; chưa chốt lịch tuần |
| P010 Still Cafe | Đúng 59 Nguyễn Trãi, giờ chung 07:00–22:00; tag tuần OSM đã lưu | Thời lượng chuẩn, môi trường, ngoại lệ/ngày lễ |
| P011 An Cafe | Có tag OSM 07:00–22:00, nguồn đọc 07/11 | Chưa đọc lại được OSM lượt này; thời lượng và môi trường |
| R003 Tâm Châu | Website đơn vị có chi nhánh 294A Trần Phú | Tọa độ Photon/OSM mới chỉ khớp tên/đường, thiếu số nhà; giờ và tiếp cận xe máy |
| H001 | Photon/OSM trả tên và số 2 Công trường Công xã Paris | Chỗ tập kết/đỗ xe và giờ tiếp cận điểm đầu/cuối |

Overpass bị timeout, OSM API kết nối bị reset; trang Tâm Châu trực tiếp trả 403.
Thông tin chi nhánh Tâm Châu còn được nhìn thấy trong chỉ mục nguồn chính thức;
giới hạn truy cập được ghi lại, không thay bằng dữ kiện tự tạo.

16 chặng VERIFIED có nghĩa đã đối chiếu **ước tính mô hình**: đúng query motorcycle,
cặp tọa độ và `ceil(summary.time/60)`. Không có giao thông trực tiếp, nghỉ, buffer hoặc
xác minh quyền đi xe máy trên từng đoạn. Giữ raw summary và query tái tạo trong
`travel_time_evidence.json`/`travel_times.json`. Bốn chặng qua R003 vẫn UNVERIFIED.
Không đổi nhãn SOURCED cũ thành VERIFIED hàng loạt: đã thực sự thu lại cả đợt và rà số liệu.

## Ba ca MOCK cần dùng chung

Ngày 2: A01/A02 DONE; nghỉ 13:00–14:00; A03/A04 PENDING tùy chọn, mỗi điểm 45 phút;
chặng nội vùng 15 phút; hạn demo 16:30. ID thật trong hai snapshot có tiền tố
MOCK3D-/MOCK4D-; lấy mapping từ `routes_mock.json`, không tự lấy chuỗi A03 làm API ID.

| Ca | Catalog | Kết quả đã đối chiếu |
|---|---|---|
| T06 nghỉ đến 15:00 | `fixtures/mock` | Giữ cả hai đến 17:15, vượt hạn; bỏ A03 hoặc A04 đều về 16:15 |
| T13 đổi A03 vì mưa | `fixtures/mock` | REST→INDOOR 14:00–14:15; VISIT 14:15–15:00; INDOOR→A04 15:00–15:15; về cuối ngày 16:15 |
| T15 không có điểm hợp lệ | `fixtures/mock-no-replacement` | MOCK-CLOSED là INDOOR nhưng đóng cửa; MOCK-INDOOR là MIXED trong riêng catalog này nên không được tự chọn |

T15 vẫn giữ tất cả ID/chặng, vì snapshot 4 ngày còn có một VISIT bình thường tại
quán MIXED ở ngày 3. Không xóa địa điểm đang được ngày khác tham chiếu. T08 là ca
biên bổ sung: nghỉ đến 16:30 thì bỏ hết điểm vẫn phải đi 15 phút, đến 16:45.

T13 cần đủ **REST→MOCK-INDOOR và MOCK-INDOOR→MOCK-A04**, cộng A04→END.
Xóa thử bất kỳ một trong hai chặng đổi điểm phải làm kiểm tra thất bại, không trả 0.
T15 phải dùng catalog riêng; chỉ gửi danh sách MOCK-CLOSED trong metadata mà vẫn
đọc catalog có quán INDOOR mở cửa sẽ không chứng minh được “không có phương án”.

Xem/từ chối không đổi CURRENT. Khi ACCEPT, giữ DONE; VISIT cũ REPLACED và VISIT mới
PENDING, liên kết replaces_activity_id. Theo mục 11.1 chuẩn chung đã chốt, chặng PENDING
thừa được giữ lịch sử ở REPLACED, chặng mới PENDING; không DROP TRAVEL. Bảo 06/Nhật
phải ghép phần lưu này đúng giao dịch/version; kiểm dữ liệu không thay thế kiểm F06.

## Chạy kiểm tra và nạp lại dữ liệu

Từ gốc repo trên Mac:

```bash
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock-no-replacement
backend/.venv/bin/python backend/scripts/audit_data_handoff.py --output /tmp/sta-handoff-report.json
backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

Audit exit 0 nghĩa cấu trúc, lịch MOCK và kỳ vọng kiểm thử khớp; phải đọc riêng
`source_routes[*].ready_for_real_plan`, hiện đều **false** và có danh sách `gaps`.
Thiếu chặng/thiếu ca/REST không đủ hoặc T15 bị lẫn quán hợp lệ làm audit exit 1.
Audit không gọi mạng, AI hoặc ghi SQLite. Báo cáo lưu trong `docs/testing/` có phiên bản rõ.

Nhật chọn snapshot và RouteDay tương ứng, lấy request theo `target_ids`. Trong mode
MOCK dùng catalog của từng ca. Trong mode VERIFIED không dùng hồ sơ UNVERIFIED/null.
Bảo 06 nhập `places`/`travel_times` theo JSON, giữ mã địa điểm, sinh travel_time_id khi lưu.
Để seed CURRENT, Bảo 06/Tân ánh xạ MOCK-USER sang tài khoản thử có thật và liên kết ID
trong cùng fixture. Không POST nguyên snapshot vào API tạo nháp; API đó chỉ nhận input
PLAN theo hợp đồng. Nạp lại fixture đã chọn trước mỗi ca, version ban đầu 1; thao tác
DONE thật sẽ tăng version, vì vậy lấy version mới từ backend khi chạy F03/ADAPT.

Đã replay T06/T08/T13/T15 cho cả 3D và 4D bằng code domain của Nhật PR #17, commit
`311e94b639f47daecc39867ea561e4604238c1d0`, RULE_BASELINE: 8 lượt đạt, giữ nguồn,
DONE và các ngày khác. Đây là preview domain, không phải bằng chứng Gemini/F06/Android.
Xem `docs/testing/dataset-handoff-f05-replay.json` và `dataset-handoff-results.md`.

## Việc còn lại của từng người

- Nhật: kiểm tuyến nguồn, giải quyết các gaps trước khi đưa vào mode VERIFIED;
  ánh xạ RouteDay và ghép bridge F05 theo quy tắc chặng đã chốt.
- Bảo 06: nhập dữ liệu; seed/reset đúng tài khoản; kiểm lưu lịch và lịch sử chặng trong
  F06 cùng transaction/version. Dữ liệu thiếu vẫn giữ UNVERIFIED.
- Tân: ghi commit, dataset_version, snapshot/catalog, request, version, thực tế và bằng
  chứng từng ca. Chạy lại sau ACCEPT/REJECT và mở lịch từ backend mới.
- Bảo 04: bổ sung thông tin R003/giờ/thời lượng theo danh sách gaps khi có nguồn xác nhận.
- Hân và Bảo 04: khi PR #18 có bản ghép phù hợp, chạy ca đổi sở thích S01 theo
  `docs/testing/s01-f01-handoff.md`. Hiện ca trên thiết bị vẫn **NOT_RUN**.
