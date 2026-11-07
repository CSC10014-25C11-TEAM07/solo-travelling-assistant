# Dữ liệu địa điểm và chặng di chuyển F01

Bộ đầu tiên cho issue #8, bám tên trường trong quyết định nhóm ngày 06/11/2026.
Enum và cấu trúc giờ tuần là **đề xuất v0.1**, xem `docs/api/f01.md` trước khi nhập SQLite.

## Nội dung hiện có

| File | Nội dung |
|---|---|
| `places.json` | 12 ứng viên có nguồn: 9 điểm Đà Lạt và 3 chi nhánh Tâm Châu để khảo sát điểm nghỉ |
| `travel_times.json` | 6 chặng có hướng giữa P001/P005/P008/P009; ước tính xe máy từ Valhalla |
| `data_review.json` | Những trường đã đọc được, giờ nguồn báo và việc còn cần xác nhận cho từng điểm |
| `sources.json` | Nguồn và cách gán thông tin cho từng nhóm trường |
| `place_coordinates.json` | 4 tọa độ từ OSM để tái tạo các truy vấn chặng |
| `travel_time_evidence.json` | Số giây/khoảng cách nguồn trả, phương thức lấy và cách làm tròn |
| `fixtures/mock/` | 8 địa điểm và 10 chặng giả lập, ID có tiền tố MOCK |
| `fixtures/current_v1_day2.json` | Trạng thái ngày 2 làm đầu vào kiểm thử, không phải JSON PLAN chính thức |
| `fixtures/scenarios.json` | Đầu vào/kết quả mong đợi T06, T08, T13, T15 |

## Trạng thái và giới hạn dữ liệu thật

12 địa điểm đều giữ **UNVERIFIED**: tên và một phần thông tin đã có nguồn,
nhưng lịch từng thứ, thời lượng hoặc điều kiện tiếp cận còn thiếu/mâu thuẫn.
Không chuyển sang SOURCED chỉ vì có một URL. `checked_at` là lúc đọc nguồn online,
không phải ngày khảo sát tại chỗ. Không dùng 12 dòng này như một lịch thực tế đã xác minh.

- F01 có thể gợi ý tên/nhãn đã tổng hợp từ nguồn. Phần tạo lịch thật phải xử lý dữ liệu thiếu.
- Giờ nguồn báo được giữ ở `data_review.json`. Không tự sao chép một khoảng giờ sang 7 ngày.
- Bảo tàng Lâm Đồng: trang liên hệ, trang trưng bày số và OSM có giờ khác nhau.
  Trang trưng bày số còn có địa chỉ Hà Nội trong nội dung nên không dùng để chốt giờ.
- Dinh III: cổng du lịch và OSM khác nhau về giờ nghỉ trưa/giờ đóng cửa.
- Crazy House: cổng du lịch ghi mở 07:30; OSM ghi 08:30.
- Điểm nghỉ Tâm Châu: là ứng viên từ website đơn vị, chưa xác nhận giờ, tiện ích,
  khả năng dừng xe máy hoặc chiều tiếp cận. `interests: []` để không trộn vào thẻ gợi ý trải nghiệm.
- `environment` và nhãn sở thích là phân loại đề xuất từ mô tả nguồn; cần rà phần thực sự có mái.
- Tất cả ảnh là null; frontend dùng ảnh mặc định theo hợp đồng.
- Chưa có đủ chặng HCM ⇄ Đà Lạt hoặc ma trận đủ cho mọi kết hợp địa điểm. Nhật cần chỉ rõ
  các cặp còn thiếu từ lịch demo, rồi bổ sung có nguồn hoặc dùng bộ MOCK độc lập.

## Quy tắc chặng

- A→B và B→A là hai dòng độc lập. Không nhân đôi hoặc suy chiều ngược.
- Cùng một ID đã tồn tại: 0 phút. Thiếu chặng: báo thiếu dữ liệu, không dùng 0.
- `get_travel_time` chặn chặng UNVERIFIED và mặc định chặn MOCK; test phải chỉ rõ `allow_mock=True`.
- Sáu chặng SOURCED lấy từ Valhalla/FOSSGIS public demo, profile **motorcycle**.
  Thời gian là `ceil(summary.time / 60)`. Giữ số liệu thô trong evidence.
- Đây là ước tính từ bản đồ/thuật toán, không bao gồm bảo đảm điều kiện đường,
  giao thông thời gian thực, nghỉ hoặc khoảng đệm. Profile motorcycle của Valhalla được ghi beta.
- Các tham số ưu tiên tránh đường lớn/thu phí không có nghĩa đã xác minh mọi đoạn đường.
- App F01 không gọi máy chủ demo này. Script chỉ thu một số chặng để làm dữ liệu ngoại tuyến.

## Kiểm tra và bổ sung

Từ thư mục gốc repo:

```bash
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
```

Khi bổ sung một điểm:

1. Giữ ID đã bàn giao; tạo ID mới cho điểm mới. A01–A04 là ID hoạt động, không phải place_id.
2. Ghi nguồn và thời điểm đọc; đối chiếu lịch theo từng ngày và giờ nghỉ trưa.
3. Cập nhật `data_review.json`, nêu rõ thông tin nào là ước tính hoặc chưa xác minh.
4. Chỉ đổi SOURCED khi các trường cần thiết đã được đối chiếu; kiểm tra lại validator.
5. Khởi động lại backend để bỏ cache catalog.

Thu lại 6 chặng hiện có vào thư mục mới để review:

```bash
backend/.venv/bin/python backend/scripts/collect_travel_times.py --output-dir /tmp/sta-routes-review
```

Script cần httpx trong `requirements-dev.txt`, không cần API key. Giới hạn một đợt nhỏ
1–20 chặng, cách nhau ít nhất 1,2 giây, không tự retry. Lỗi nguồn thì dừng, không tạo
thời gian giả. Dùng thư mục output mới; đối chiếu rồi mới thay dữ liệu bàn giao.

## Nguồn và ghi công

- [Cổng du lịch Lâm Đồng](https://visitlamdong.vn/): dữ kiện cơ bản và thời lượng tham khảo;
  giữ URL từng địa điểm trong dataset, không sao chép bài mô tả hoặc ảnh.
- [Là Việt](https://laviet.coffee/tu-chung-toi/),
  [Bảo tàng Lâm Đồng](https://baotanglamdong.com.vn/contact),
  [Tâm Châu](https://tamchau.com/showroom/): thông tin do đơn vị công bố.
- © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), ODbL 1.0:
  tọa độ, tag opening_hours trong evidence và mạng đường nền.
  Giữ ghi công/điều kiện ODbL khi sử dụng hoặc phân phối phần dữ liệu bắt nguồn từ OSM.
- [Valhalla](https://valhalla.github.io/valhalla/api/route/api-reference/) và
  [FOSSGIS public demo](https://valhalla.github.io/valhalla/start/introduction/):
  ước tính chặng. Bản này chỉ thực hiện lấy mẫu nhỏ, không cấu hình làm backend định tuyến cho người dùng.

SOURCED không đồng nghĩa “cập nhật thời gian thực” hoặc “đã xác minh tuyến an toàn”.
