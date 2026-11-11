# Kết quả kiểm tra bộ bàn giao dữ liệu

Ngày 10/11/2026. Dataset **bao04-handoff-2026-11-10-v1**; base main `a7a7934`.
Phạm vi: cấu trúc/nguồn/giới hạn dữ liệu, tuyến MOCK 3/4 ngày và preview domain ADAPT.
Chưa nghiệm thu tuyến thật, SQLite/F06, Gemini hoặc S01/Android.

| Kiểm tra | Kết quả |
|---|---|
| Catalog nguồn | 15 địa điểm UNVERIFIED; 20 chặng có hướng: 16 ước tính VERIFIED, 4 UNVERIFIED qua R003 |
| Hai catalog MOCK | Mỗi bộ 11 điểm/20 chặng; không trộn source/MOCK |
| Snapshot MOCK 3/4 ngày | Đủ ngày, điểm đầu/cuối, chặng, giờ, tổng REST/ngày và về mốc HCMC |
| T06 | Giữ cả hai điểm tới 17:15; bỏ A03 hoặc A04 tới 16:15 |
| T08 | Nghỉ tới 16:30 vẫn cần chặng cuối, đến 16:45; không hợp lệ |
| T13 | Đủ chặng REST→INDOOR và INDOOR→A04, cộng chặng về; kết thúc 16:15 |
| T15 | Catalog riêng không có INDOOR đang mở/phù hợp; không có phương án |
| Toàn bộ backend unittest | **37 tests PASS**, gồm auth/F01 và 14 kiểm tra mới về chuẩn/bàn giao/collector |
| Chạy code Nhật PR #17 | **8 lượt PASS**: 4 ca × 2 độ dài, số phương án 2/0/1/0 |
| Candidate từ PR #17 | Audit độc lập từng snapshot đề xuất: đúng chặng/giờ/REST; giữ DONE/ngày khác; đổi mưa old REPLACED/new PENDING |

Lệnh kiểm tra chính:

```bash
backend/.venv/bin/python -m unittest discover -s backend/tests -v
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock-no-replacement
backend/.venv/bin/python backend/scripts/audit_data_handoff.py --output /tmp/sta-handoff-report.json
```

`dataset-handoff-report.json` là đầu ra audit đi kèm. `checks_passed: true` không
đồng nghĩa các tuyến nguồn sẵn sàng: cả SOURCE-3D/SOURCE-4D có ready_for_real_plan false.
Day 1 có cận dưới có điều kiện 17:17, vượt hạn đề xuất 17:00, chưa tính VISIT/buffer.

## Kiểm tra chống báo đạt sai

Các test sửa bản sao tạm, không thay dữ liệu bàn giao:

- Xóa lần lượt chặng tới hoặc đi tiếp của điểm thay mưa: T13/audit phải thất bại,
  báo đúng from_place_id/to_place_id, không dùng 0 phút.
- Đổi T15 sang catalog T13 có quán INDOOR mở: audit phải thất bại.
- Bỏ một ca bắt buộc hoặc để T06 không còn checked_paths: audit phải thất bại.
- Rút REST xuống 30 phút khi yêu cầu 60/ngày: snapshot phải báo REST_SHORTFALL.
- Trả routing HTTP 200 với tọa độ ứng viên: collector vẫn xuất UNVERIFIED chờ rà.
- Chuẩn mới chấp nhận VERIFIED, từ chối SOURCED, area cũ và checked_at không phải UTC;
  hồ sơ thiếu môi trường không được gắn VERIFIED.

Hai lỗi collector tự gắn VERIFIED và audit bỏ sót checked_paths rỗng được tái hiện
bằng test trước sửa; sau sửa cả test và bộ đầy đủ đều qua. Review độc lập đã kiểm
code/dữ liệu và nêu hai lỗi này trước khi hoàn thiện.

## Cách đã replay với code Nhật

Module `backend/adapt_f05` được đọc từ Git commit
`311e94b639f47daecc39867ea561e4604238c1d0` của PR #17 vào thư mục tạm; không chép module
vào nhánh dữ liệu và không gọi Gemini. Mỗi route đọc snapshot/target_ids/RouteDay từ
handoff/routes_mock.json, rồi tạo EXTEND_REST hoặc REPLACE_LOCATION theo scenarios.json.
Catalog được chọn theo từng ca, mode MOCK. AdaptEngine dùng RuleRanker.

Đã kiểm số candidate, mốc 16:15, hai ID DROP riêng, nguồn không bị sửa, DONE/ngày khác,
trạng thái VISIT thay thế và audit độc lập proposed_days. Ghi kết quả trong
`dataset-handoff-f05-replay.json`. Các module/DB tạm đã dọn sau chạy.

PR #17 là code domain chưa vào main ở thời điểm này. Kết quả này không xác nhận
bridge API/F06, transaction/idempotency, lưu lịch sử TRAVEL hoặc app đã tích hợp.
Nhóm áp dụng mục 11.1 chuẩn dữ liệu 09/11 khi ghép, không gọi preview là quyết định đã lưu.

## Phần chưa chạy hoặc chưa đủ dữ liệu

- Toàn bộ 15 hồ sơ thật chưa đủ thông tin để tự động lập lịch. Thiếu cụ thể ở source_checks,
  data_review và gaps của audit; R003 chưa khớp đúng số nhà, còn chặng nối chỗ lưu trú.
- Thời gian routing là mô hình motorcycle; chưa có traffic, buffer hoặc xác minh đường thực tế.
- S01 đổi sở thích trên build Hân, Android/iOS và bằng chứng T01–T15 đầu cuối: **NOT_RUN**.
- Nhập SQLite, ACCEPT/REJECT, gửi lặp và mở lại sau khởi động: Bảo 06/Nhật/Tân cần ghép và kiểm.
