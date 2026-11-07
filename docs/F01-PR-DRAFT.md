Refs #8

S01 cần gợi ý địa điểm đúng sở thích theo hợp đồng 06/11. Bản này thêm
`GET /api/v1/places/recommendations` dùng query interests lặp, xác thực session,
ưu tiên số nhãn khớp, trả tối đa 3 điểm và lỗi validation đúng field interests.

Đã chuẩn bị 12 địa điểm ứng viên có nguồn, 6 chặng xe máy có hướng lấy từ
Valhalla/OSM và bộ MOCK riêng cho nghỉ thêm/đổi điểm vì mưa.
12 địa điểm vẫn giữ UNVERIFIED vì lịch tuần/thời lượng/tiếp cận còn thiếu hoặc mâu thuẫn;
6 chặng là ước tính, chưa phủ đầy đủ HCM ⇄ Đà Lạt.

## Cách thử và kết quả

```bash
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
backend/.venv/bin/python -m unittest discover -s backend/tests -v
backend/.venv/bin/python backend/scripts/preview_f01.py coffee
```

Validator qua cho hai bộ; 22 tests qua. Đã kiểm tra register/login/F01/logout/token hết hạn
với code auth thật của PR #12 trên SQLite tạm; xem docs/testing/f01-results.md.

## Cần review và ghép

- Nhật review nguồn/chặng, logic xếp hạng và bộ MOCK; Hân kiểm S01 trên thiết bị.
- Đăng/Bảo 06 chốt enum area/environment/data_status và opening_hours theo phần đề xuất
  trong docs/api/f01.md, rồi nhập SQLite. Chưa tự coi các chi tiết này đã được nhóm duyệt.
- PR #12 chưa merged ở thời điểm kiểm. F01 gọi `auth.session_response`; khi chưa có auth,
  có Bearer vẫn trả AUTH_NOT_READY 503. Giữ cả hai router khi ghép main.py.
- Chưa có bằng chứng ghép S01/Android hoặc hoàn tất toàn bộ T01–T15; không đóng #8 từ bản nháp này.
