# Bảo 04 — bàn giao theo TASK 17/11

Dataset **bao04-mvp-2026-11-17-v2**, tiếp tục PR #30 tại `1404791`. Phần bổ sung
này chỉ sửa dữ liệu, loader/audit và tài liệu của Bảo04. PR #30 còn mở nên PR bổ sung
lấy nhánh của #30 làm base; cần ghép #30 trước. Không đóng issue #8 từ kiểm offline.

## Đã thực hiện

| Yêu cầu TASK17 | Bàn giao |
|---|---|
| Tuyến3/4ngày | `backend/data/handoff/routes_source.json`, đủ điểm đầu/cuối, REST và chặng xe máy có hướng |
| Định dạng cho F02 | Mỗi ngày có `stops` REST/VISIT. Audit kiểm thứ tự/duration trùng cấu hình và không âm thầm bỏ waypoint |
| Điểm trong nhà vì mưa | P006: chỉ khu ghế ngồi có trần ở Là Việt,200 Nguyễn Công Trứ; tọa độ marker/đích dẫn đường của cổng tỉnh, đối chiếu địa chỉ đơn vị |
| Không dùng nhầm bảo tàng toàn khu | P005120 phút sửa INDOOR→MIXED theo phạm vi toàn khu; không lấy cả khu làm điểm INDOOR |
| Chặng đến điểm mới và đi tiếp | Thêm16 truy vấn motorcycle độc lập;8 ước tính đã rà chuyển VERIFIED,8 chạm R003/L001 giữ UNVERIFIED |
| Hai ca ADAPT trên cả hai tuyến | `handoff/source_scenarios.json`: nghỉ thêm30 phút và RAIN ×3D/4D, audit nguyên ngày trước/sau; không tạo CURRENT, activity_id hoặc DONE giả |
| Nguồn/ngày/nhãn/version | `sources.json`, `data_review.json`, `handoff/source_checks.json`, coordinates và raw summaries giữ provenance; manifest có version/previous_version |

Catalog đầy đủ16 điểm (P009 VERIFIED,15 UNVERIFIED),42 chặng (28 ước tính VERIFIED,
14 UNVERIFIED chạm R003/L001). Tập nhỏ REVIEW_ONLY có10 điểm/42 chặng; exporter
mang theo cả input và audit của4ca mới. MOCK, F01 HTTP, mobile, models dùng chung,
router, SQLite và engine F02/F05 không đổi so với base.

Nguồn P006: [đơn vị](https://laviet.coffee/tu-chung-toi/) xác nhận đúng200 Nguyễn
Công Trứ và giờ chung07:00–22:00; [cổng tỉnh](https://visitlamdong.vn/vi/lavietcoffeedl)
mô tả khu ghế ngồi có trần. Nhãn INDOOR chỉ áp dụng khu này, không gồm tour sản xuất.
VISIT60 phút cho P006 là ngân sách mẫu do trợ lý chọn cho TASK17 theo mức café hiện
có, không phải thời lượng quán xác nhận hay một phê duyệt riêng mới của người dùng.
Giờ chung chưa phải bảng giờ tuần; P006 vẫn UNVERIFIED, `weekly` null.

P005: [mô tả đơn vị](https://baotanglamdong.com.vn/about/lam-dong-museum) cho thấy
hồ sơ toàn khu gồm các không gian khác nhau. [Trang vé](https://baotanglamdong.com.vn/tickets)
vẫn có08:00–17:00 hằng ngày khác header07:30–17:30; không chọn tùy tiện một khung.
Chỉ lưu tóm tắt sự kiện, URL/hash/ngày; không chép nguyên bài hoặc ảnh.

## Cấu hình đã chốt và thay đổi đường nối

Các lựa chọn người dùng đã duyệt giữ nguyên, không chờ Đăng/nhóm chốt lại:

| Tham số | Giá trị/trạng thái |
|---|---|
| Nơi ngủ mẫu | L001 Crazy House,03 Huỳnh Thúc Kháng — đã áp dụng, tách P009 VISIT |
| Still/An | VISIT60 phút mỗi điểm do Bảo04 chọn; REST riêng |
| Hạn cuối ngày | Ngày đi/về18:00, nội vùng17:00 |
| Nghỉ và dự phòng | REST tối thiểu60 phút/ngày, buffer30 phút riêng trước deadline |
| Giờ bắt đầu | Đi/về06:00, nội vùng08:00 |

V1 có P001 làm waypoint không có hoạt động trên ngày đi/về và một số chặng về nơi
ngủ. F02 chỉ nhận REST/VISIT nên không thể chuyển các waypoint đó thành hoạt động
1 phút. V2 dùng chặng trực tiếp giữa các stop thực: H001→R003→L001 và chiều về;
ngày nội vùng đi thẳng từ/đến L001 khi không còn hoạt động ở ga. P001 vẫn là VISIT90
phút của ngày2. R003↔L001 được lấy riêng hai chiều, đều232 phút, giữ UNVERIFIED.

```text
Ngày đi: 06:00 + 380 + REST60 + 232 + buffer30 = 17:42, hạn18:00
Ngày về: 06:00 + 232 + REST60 + 383 + buffer30 = 17:45, hạn18:00
```

Đây là cận dưới theo tọa độ tham chiếu, chưa tính WAIT khi giờ/tiếp cận chưa rõ;
không phải lịch hợp lệ hay bảo đảm giờ đến. Cả hai tuyến vẫn ready=false,38/50 gaps
lặp theo ngày. Tất cả chặng của tuyến/nhánh mưa có dữ liệu ước tính; không thiếu chặng.

## Hai ca ADAPT nguồn

| Case | Thay đổi | Chặng thay vì mưa |
|---|---|---|
| SOURCE3D-REST-30 | REST P01060→90 phút; giữ các VISIT và nơi ngủ | Không đổi geometry |
| SOURCE3D-RAIN-P006 | VISIT P001→P006; giữ VISIT/REST P010 và VISIT P005 | L001→P006→P010→P005→L001 |
| SOURCE4D-REST-30 | REST P00530→60 phút; REST P01130 phút giữ nguyên | Không đổi geometry |
| SOURCE4D-RAIN-P006 | VISIT P008→P006; giữ các VISIT/REST còn lại | L001→P005→P006→P009→P011→L001 |

`audit_data_handoff.py` kiểm ngày trước/sau thay đổi, thời lượng, cửa sổ giờ, cả chặng
cuối và buffer. Thiếu giờ/chặng thì lịch đầy đủ là null, không dùng cận dưới để báo
source_data_complete. Bốn ca đều còn thiếu dữ kiện nguồn; ready_for_real_adapt luôn
false vì đây chưa phải CURRENT/trigger thật và chưa chạy engine F05 trên nguồn.

Đã rà cả30 đường của các ngày/biến thể F02 và212 đường khi bỏ các VISIT tùy chọn
(có đường trùng giữa các probe): không thiếu cặp có hướng. Kiểm này chỉ chứng minh
độ phủ chặng, không chứng minh nhãn VERIFIED, cửa mở hoặc tính khả thi.

## Dữ kiện thực tế còn thiếu

| Điểm/phần | Cần bổ sung trước khi dùng nguồn thật |
|---|---|
| R003 | Pin đúng cổng/số294A, giờ tuần/nghỉ trưa, chỗ dừng xe và tiếp cận hai chiều; website có hai giờ khác nhau |
| L001 | Cổng khách lưu trú, ra/vào06:00/cuối ngày, đỗ xe và khả năng lưu trú ngày mẫu; giờ tham quan P009 không thay giờ khách lưu trú |
| H001 | Vị trí tập kết/đỗ xe và quyền tiếp cận06:00/chiều về |
| P001/P005/P008 | Lịch tuần/ngày lễ, các xung đột giờ; điều kiện REST tại P005 |
| P006 | Giờ từng thứ/nghỉ trưa/ngày lễ; đã có phạm vi trong nhà/tọa độ/chặng/ngân sách mẫu |
| P010/P011 | Môi trường và xác nhận giờ tuần/ngoại lệ; thời lượng lập lịch60 phút đã chốt |

Không có lựa chọn nơi ngủ/hạn/buffer cũ đang chờ duyệt. Đây là các dữ kiện cần bằng
chứng của đơn vị, không thể tự chốt thành sự thật. Câu hỏi/kênh công khai ở
[guide nguồn](DATA-SOURCE-VERIFY-BAO04.md); chưa gọi điện/gửi liên hệ/đặt phòng.

## Yêu cầu phần dùng chung — chưa sửa trong PR dữ liệu

| Chủ phần / file | Bằng chứng và việc cần xử lý |
|---|---|
| Nhật — `backend/plan_f02.py`, `_schedule` | Probe kiểm soát: kết thúc10:30, hạn10:45 vẫn nhận dù buffer30; hiện chỉ audit Bảo04 cộng buffer. Cần kiểm ngân sách dự phòng trong engine khi nhận cấu hình nguồn |
| Nhật — cùng hàm | Probe với REST tại A có cửa sổ thứ3 rỗng vẫn tạo lịch đến10:30; nhánh REST chưa kiểm cửa sổ, điểm đầu/cuối cũng chưa kiểm access. Cần bổ sung validator và regression thuộc F02 |
| Chủ chuẩn/Bảo04 + Nhật/Bảo06 — `backend/place_models.py`, `adapt_f05/catalog.py` | Place VERIFIED hiện đòi duration VISIT/weekly đủ, trong khi H001/R003/L001 là anchor không VISIT. Cần phân biệt vai trò/trường áp dụng trước khi nạp VERIFIED; không điền giả1 phút hoặc nâng toàn bộ nhãn |
| Bảo06 — wiring F02/F05/catalog | Dùng cùng dataset/routes/options-validator; `templates={len(r['days']):r ...}` từ routes_source có stops. Giữ source bị chặn cho tới khi nguồn đủ và các ràng buộc trên được engine xử lý. Không trộn MOCK hoặc override nhãn |

[Provider observations](testing/task17-provider-observations.json) ghi probe dữ liệu
kiểm soát trong bộ nhớ, RuleRanker, không Gemini/HTTP/SQLite. JSON nguồn thật vẫn bị
PlanProvider mode VERIFIED từ chối đúng với DATA_INCOMPLETE ở cả3D/4D. Không sửa code
của các chủ phần để làm dữ liệu chạy qua; các phát hiện được ghi để review/tích hợp.

## Kiểm tra và tái hiện

```bash
python -m unittest discover -s backend/tests
python backend/scripts/validate_places.py
python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock-no-replacement
python backend/scripts/audit_data_handoff.py --output /tmp/sta-task17-audit.json
python backend/scripts/replay_handoff_f05.py --output /tmp/sta-task17-replay.json
python backend/scripts/prepare_source_bundle.py --output-dir /tmp/sta-task17-source-new
```

Mac dùng interpreter đã cài requirements, ví dụ backend/.venv/bin/python. Export
phải trỏ thư mục mới, giữ nhãn và không ghi SQLite. Audit exit0 nghĩa cấu trúc/kỳ vọng
MOCK đúng; phải đọc riêng source_routes/source_scenarios và mọi gap.

TASK17 ghi nhận Đăng đã thử luồng MOCK trên iPhone. Đợt này chỉ kiểm phần dữ liệu;
không nhận là đã tự chạy lại điện thoại, Gemini, ACCEPT/REJECT hoặc nghiệm thuT01–T15.
Bằng chứng S01 trước đó và báo cáo của các chủ phần được giữ nguyên phạm vi.
