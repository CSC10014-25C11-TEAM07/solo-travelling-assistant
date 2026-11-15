# Kết quả bàn giao dữ liệu — 15/11/2026

Dataset **bao04-mvp-2026-11-15-v1**, base main `0b446b1` (gồm F05 #20, SQLite/API
#16, dataset #19 và giao diện #18). Các báo cáo JSON cùng thư mục là bằng chứng offline
và TestClient; không xác nhận đã nghiệm thu app.

| Kiểm tra | Kết quả và giới hạn |
|---|---|
| Backend `python -m unittest discover -s backend/tests` | **103 tests PASS**; baseline trước thay đổi 86 tests |
| Catalog nguồn | 15 venue UNVERIFIED; 24 chặng: 20 ước tính VERIFIED, 4 UNVERIFIED qua R003 |
| Hai catalog MOCK | Mỗi bộ 11 điểm/20 chặng; nội dung fixture giữ nguyên so với main/PR19 |
| Offline audit | Hai full snapshots + bốn ca PASS; SOURCE-3D/4D vẫn ready=false với 34/46 gaps, gồm các gap lặp theo ngày |
| F05 domain đã merge | **8 lượt PASS**, T06/T08/T13/T15 ×3D/4D, số phương án 2/0/1/0; ca có phương án kết thúc16:15 |
| Bản lưu F05 | JSON round trip + validate_stored_option PASS; snapshot đề xuất kiểm độc lập chặng/giờ/REST; giữ DONE/ngày khác |
| Source bundle CLI | Xuất 8 điểm/24 chặng, cấu hình, tọa độ/evidence và blockers; giữ nguyên nhãn, không ghi DB |
| F01 public routes trên main.app | TestClient + đăng ký/login/session SQLite thật: coffee/nature/multi/food đúng; anchors bị loại; input thiếu/sai422; token sau logout401 |
| S01/Expo Go | **NOT_RUN** trên thiết bị; PR18 đã merge, dùng checklist s01-f01-handoff.md |
| AI thật, API F05/F06, SQLite ACCEPT/REJECT/restart | **Chưa xác nhận bởi đợt kiểm này** |

## Những lỗi audit được bảo vệ

Test mới chứng minh audit không báo ready khi VISIT làm trễ, chờ qua nghỉ trưa làm
trễ, REST không có cửa sổ, VISIT/REST ngoài route, sai ngày, thiếu chặng đúng hướng,
giới hạn tuyến chưa giải quyết hoặc mốc xuất phát đóng cửa. Unknown vẫn là unknown;
WAIT không tính vào REST. Export từ chối thư mục đã có, output trong catalog và cả
symlink treo. Replay xóa chặng INDOOR→A04 phải FAIL cho T13, không lặng lẽ PASS.

Các kiểm tra mới đã chạy RED trước implementation, GREEN sau sửa. API F01 có thêm
coverage trên catalog thực, không thay HTTP contract hoặc logic xếp hạng vốn đã đúng.

## Tái hiện

Từ gốc repo, dùng Python có requirements backend; Mac có thể thay `python` bằng
`backend/.venv/bin/python`:

```bash
python -m unittest discover -s backend/tests -v
python backend/scripts/validate_places.py
python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock-no-replacement
python backend/scripts/audit_data_handoff.py --output /tmp/sta-handoff-report.json
python backend/scripts/replay_handoff_f05.py --output /tmp/sta-f05-replay.json
python backend/scripts/prepare_source_bundle.py --output-dir /tmp/sta-source-review-new
```

Để tái hiện kiểm F01 bốn nhóm sở thích/clear/logout, chạy test
`backend/tests/test_auth_f01_integration.py` bằng unittest discover; test khởi tạo
main.app và SQLite tạm, không ghi account/token vào app.sqlite3. Kết quả quan sát thêm
được lưu trong `f01-mvp-http-results.json` (không chứa token).

Replay ghi hash của implementation F05 và tám file fixture/catalog/config đã dùng.
Nó gọi module hiện có trên branch checkout, không tải code PR cũ từ mạng, không gọi
Gemini và không ghi proposal vào SQLite. Rules/MOCK chỉ chứng minh domain, không thay
thế các test tích hợp API của Tân/Bảo06 hay nghiệm thu AI thật.

## Blockers còn thật

Hai nhánh mưa nguồn đủ chặng nhưng P005 còn xung đột giờ và phạm vi khu có mái; các
venue khác cũng còn thiếu. R003 chưa khớp số nhà/cổng; chưa có nơi ngủ và chặng nối.
Ngày đi có cận dưới17:17 so với hạn17:00. Không tăng deadline hoặc gắn VERIFIED để
làm demo chạy qua. Chi tiết từng điểm và cách bổ sung: ../DATASET-HANDOFF-BAO04.md.

Đã code, đã test riêng, đã merge và đã kiểm trên app là bốn trạng thái khác nhau.
PR này chưa đóng #8; Đăng quyết định merge/nghiệm thu, Tân tổng hợp T01–T15.
