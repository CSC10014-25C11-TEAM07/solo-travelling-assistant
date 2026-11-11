Refs #8

Nhật/Bảo 06/Tân cần cùng bộ dữ liệu cho tuyến 3/4 ngày và ba ca ADAPT trong lúc chờ
ghép UI. Bản này bàn giao **bao04-handoff-2026-11-10-v1**, có manifest, RouteDay,
snapshot CURRENT đầy đủ và checklist S01, thay các enum đề xuất cũ bằng chuẩn Leader 09/11.

## Bộ dữ liệu và mục đích

- `handoff/routes_source.json`: chọn hai tuyến TP.HCM–Bảo Lộc–Đà Lạt–TP.HCM 3/4 ngày,
  điểm đầu/cuối/hạn từng ngày và tổng nghỉ. **Cả hai chưa đủ để lập lịch thật**.
- Catalog nguồn: 15 điểm UNVERIFIED; thu/rà lại 20 chặng motorcycle, 16 ước tính VERIFIED
  và 4 qua R003 giữ UNVERIFIED vì tọa độ chưa khớp số nhà 294A.
- `fixtures/mock/` + CURRENT 3D/4D: T06 nghỉ thêm phải bỏ A03 hoặc A04; T13 đổi mưa có
  đủ REST→INDOOR, INDOOR→A04 và chặng về. T08 là ca nghỉ quá muộn bổ sung.
- `fixtures/mock-no-replacement/`: T15, không bị lẫn quán INDOOR mở từ T13; vẫn giữ
  đủ ID/chặng cho snapshot 4 ngày.

`source_checks.json`, `data_review.json` và audit report nêu nguồn, trường thiếu và
xung đột từng điểm. Hạn 17:00/18:00 của tuyến nguồn là đề xuất cần Nhật kiểm; ngày đi
có cận dưới điều kiện 17:17, đã vượt 17:00 trước VISIT/buffer. P001 chỉ là mốc tập kết,
không phải chỗ lưu trú. Không dùng MOCK bù vào source hay gắn VERIFIED vì có URL.

## Kiểm tra

```bash
backend/.venv/bin/python -m unittest discover -s backend/tests -v
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock-no-replacement
backend/.venv/bin/python backend/scripts/audit_data_handoff.py
```

37 backend tests PASS. Replay code domain của Nhật PR #17 commit `311e94b` cho T06/T08/T13/T15
trên cả hai snapshot: 8 lượt PASS, 2/0/1/0 candidate, giữ DONE/ngày khác, mốc khả thi 16:15.
Đã kiểm độc lập các snapshot đề xuất. Test chống thiếu chặng tới/đi tiếp, catalog bị lẫn,
thiếu ca/nhánh, thiếu nghỉ và collector tự nâng nhãn cũng qua.

Chi tiết: `docs/DATASET-HANDOFF-BAO04.md`, `docs/testing/dataset-handoff-results.md`.

## Ghép và giới hạn

Nhật dùng RouteDay/target_ids và catalog đúng ca; Bảo 06 ánh xạ tài khoản/ID, nhập/reset
SQLite; Tân ghi commit + dataset_version + thực tế/bằng chứng. Các hồ sơ còn thiếu giữ
UNVERIFIED. Collector thu mới cũng luôn xuất UNVERIFIED chờ review.

Chưa xác nhận F06 persistence/Gemini/tuyến thật hoặc app. Khi Hân có bản ghép PR #18,
chạy `docs/testing/s01-f01-handoff.md` để chốt đổi sở thích trên S01; hiện **NOT_RUN**.
Không đóng #8 từ PR này.
