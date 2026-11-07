Refs #8

S01 cần gợi ý địa điểm đúng sở thích theo hợp đồng 06/11. Bản này thêm
`GET /api/v1/places/recommendations` dùng query interests lặp, xác thực session,
ưu tiên số nhãn khớp, trả tối đa 3 điểm và lỗi validation đúng field interests.

Đã chuẩn bị 14 địa điểm ứng viên có nguồn, 14 chặng xe máy có hướng lấy từ
Valhalla/OSM và bộ MOCK riêng cho nghỉ thêm/đổi điểm vì mưa.
14 địa điểm vẫn giữ UNVERIFIED vì lịch tuần/thời lượng/tiếp cận còn thiếu hoặc mâu thuẫn;
14 chặng là ước tính, chưa phủ đầy đủ HCM ⇄ Đà Lạt.

Thêm client TypeScript để Hân gọi F01 từ S01, cùng harness đăng ký/login thật + F01
từ snapshot PR #12 trên SQLite tạm. Main chưa có màn S01 nên chưa ghép UI/Android.
Để chạy lint/typecheck mobile, bổ sung cấu hình lint SDK 58 và sửa kiểu CSS/ref,
hook hydration trong bộ khung; lockfile không đổi phiên bản dependency cũ.

## Cách thử và kết quả

```bash
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
backend/.venv/bin/python -m unittest discover -s backend/tests -v
backend/.venv/bin/python backend/scripts/preview_f01.py coffee
backend/.venv/bin/python backend/scripts/check_f01_auth.py --auth-ref origin/feat/2-auth-api
```

Validator qua cho hai bộ; 22 tests backend và 9 tests transport qua. Mobile lint và
typecheck qua. Đã kiểm tra register/login/F01/logout/token hết hạn với code auth thật
của PR #12 trên SQLite tạm; client TypeScript gọi HTTP thật cũng qua. Auth snapshot:
`2bd6854aea1addb9cad4c4a57a3fbcc37913aae7`. Xem `docs/testing/f01-results.md`.

Chạy `backend/scripts/run_f01_demo.py --port 8001` bằng Python trong backend/.venv;
tại `mobile/` chạy `npm run test:f01:integration`. Xem hướng dẫn đầy đủ trong
`docs/F01-HUONG-DAN-BAO04.md`.

## Cần review và ghép

- Nhật review nguồn/chặng, logic xếp hạng và bộ MOCK; Hân kiểm S01 trên thiết bị.
- Đăng/Bảo 06 chốt enum area/environment/data_status và opening_hours theo phần đề xuất
  trong docs/api/f01.md, rồi nhập SQLite. Chưa tự coi các chi tiết này đã được nhóm duyệt.
- PR #12 chưa merged ở thời điểm kiểm. F01 gọi `auth.session_response`; khi chưa có auth,
  có Bearer vẫn trả AUTH_NOT_READY 503. Giữ cả hai router khi ghép main.py.
- Chưa có bằng chứng ghép S01/Android hoặc hoàn tất toàn bộ T01–T15; không đóng #8 từ bản nháp này.
