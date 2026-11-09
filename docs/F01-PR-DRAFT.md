Refs #8

S01 cần gợi ý địa điểm đúng sở thích theo hợp đồng 06/11. Bản này thêm
`GET /api/v1/places/recommendations` dùng query interests lặp, xác thực session,
ưu tiên số nhãn khớp, trả tối đa 3 điểm và lỗi validation đúng field interests.

Đã chuẩn bị 14 địa điểm ứng viên có nguồn, 14 chặng xe máy có hướng lấy từ
Valhalla/OSM và bộ MOCK riêng cho nghỉ thêm/đổi điểm vì mưa.
14 địa điểm vẫn giữ UNVERIFIED vì lịch tuần/thời lượng/tiếp cận còn thiếu hoặc mâu thuẫn;
14 chặng là ước tính, chưa phủ đầy đủ HCM ⇄ Đà Lạt.

Thêm client TypeScript để Hân gọi F01 từ S01, cùng harness đăng ký/login thật + F01
từ snapshot Git trên SQLite tạm. Đã ghép main `e2ce034` sau khi auth PR #12 merged,
lấy main.py của main làm nền và thêm places_router ngay sau auth_router theo review
của Đăng. Giữ lifespan khởi tạo tài khoản, handler validation và /health.
S01–S03 ở PR #14 đã bị revert bởi PR #15; chưa có bằng chứng ghép F01 trên UI/Android.
Để chạy lint/typecheck mobile, bổ sung cấu hình lint SDK 58 và sửa kiểu CSS/ref,
hook hydration trong bộ khung; lockfile không đổi phiên bản dependency cũ.

## Cách thử và kết quả

```bash
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
backend/.venv/bin/python -m unittest discover -s backend/tests -v
backend/.venv/bin/python backend/scripts/preview_f01.py coffee
backend/.venv/bin/python backend/scripts/check_f01_auth.py
```

Kiểm tra lại ngày 09/11/2026:

- Validator qua cho hai bộ; **23 tests backend và 9 tests transport PASS**.
- Thêm regression test trên chính main.app/lifespan, không override xác thực.
- Uvicorn main:app + SQLite tạm: **login 200 → F01 200 → logout 200 → dùng token cũ gọi F01 401 / INVALID_SESSION**.
- Client TypeScript gọi HTTP thật qua bản ghép thành công. Script session kiểm thêm token sai/hết hạn.
- Mobile typecheck PASS; lint exit 0 với 0 lỗi, 9 cảnh báo unused ở phần ADAPT nhận từ main.

Chi tiết và phạm vi kiểm tra trong `docs/testing/f01-results.md`. Không ghi token hoặc
tài khoản test vào app.sqlite3; các server/DB tạm đã dọn sau kiểm.

Chạy `backend/scripts/run_f01_demo.py --port 8001` bằng Python trong backend/.venv;
tại `mobile/` chạy `npm run test:f01:integration`. Xem hướng dẫn đầy đủ trong
`docs/F01-HUONG-DAN-BAO04.md`.

## Cần review và ghép

- Nhật review nguồn/chặng, logic xếp hạng và bộ MOCK; Hân kiểm S01 trên thiết bị.
- Đăng/Bảo 06 chốt enum area/environment/data_status và opening_hours theo phần đề xuất
  trong docs/api/f01.md, rồi nhập SQLite. Chưa tự coi các chi tiết này đã được nhóm duyệt.
- PR #12 đã merged, nhánh F01 đã ghép main và giữ cả hai router/lifespan. Nhật review
  tiếp phần F01/dataset sau khi conflict đã được xử lý.
- Chưa có bằng chứng ghép S01/Android hoặc hoàn tất toàn bộ T01–T15; không đóng #8 từ bản nháp này.
