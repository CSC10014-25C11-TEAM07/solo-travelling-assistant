# Kết quả kiểm tra F01

Ngày kiểm tra: 07/11/2026. Nhánh: feat/8-places-f01. Phạm vi: backend F01,
chất lượng cấu trúc dữ liệu và fixtures, không phải nghiệm thu toàn bộ T01–T15.

Môi trường đã chạy: Python 3.14.2, FastAPI 0.162.0, Pydantic 2.14.3 trên macOS.

## Kiểm tra đã chạy

| Kiểm tra | Kết quả quan sát |
|---|---|
| Validator dữ liệu thật | PASS: 12 địa điểm UNVERIFIED, 6 chặng SOURCED; không có ID/chặng trùng hoặc chặng mồ côi |
| Validator MOCK | PASS: 8 địa điểm/10 chặng MOCK trong thư mục riêng |
| 22 tests trong backend/tests/test_places.py | PASS: xếp hạng, cap 3, kết quả 0/1, đổi sở thích, lỗi interests, auth, giờ và hướng chặng |
| Preview coffee | PASS: trả P006, ảnh null, lý do theo coffee |
| Preview nature/culture | PASS: P002 khớp hai nhãn đứng trước điểm khớp một nhãn |
| OpenAPI | PASS: có /api/v1/places/recommendations và HTTPBearer |
| Auth code thật PR #12 | PASS: đăng ký → đăng nhập → F01; token sai/đã logout/hết hạn bị 401; interests sai bị 422 |
| Bằng chứng chặng | PASS: 6 truy vấn motorcycle, thời gian làm tròn lên theo giây nguồn trả |
| Script collect_travel_times.py | PASS: chạy thật một chặng P001→P005 ra thư mục tạm; JSON qua model validator, không sửa bộ đã bàn giao |

Lệnh kiểm thử:

```bash
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

Auth được kiểm với snapshot commit `2bd6854aea1addb9cad4c4a57a3fbcc37913aae7`,
file `backend/auth.py` từ `origin/feat/2-auth-api`, bằng
`backend/scripts/check_f01_auth.py --auth-file <snapshot.py>`.
Module auth được nạp tạm, dùng SQLite riêng và xóa sau kiểm. Không chép auth.py vào
nhánh F01, không ghi vào app.sqlite3, không tự merge PR #12. Kết quả này xác nhận giao diện
ghép giữa hai router, chưa xác nhận bản ghép cuối trên main.

## Kỳ vọng của dữ liệu MOCK đã đối chiếu

- T06: nghỉ đến 15:00 + 3 chặng × 15 phút + 2 hoạt động × 45 phút = 17:15.
  Giữ một hoạt động và hai chặng kết thúc 16:15, đáp ứng mốc MOCK 16:30.
- T08: nghỉ đến 16:30, vẫn còn chặng đến cuối ngày nên không thể đạt mốc.
- T13: có quán trong nhà MOCK mở cửa và chặng tương ứng; thời lượng 45 phút.
- T15: chỉ có điểm trong nhà MOCK đóng cả ngày; không có lựa chọn hợp lệ.

Đây là kiểm tra dữ liệu/kết quả kỳ vọng, không phải bằng chứng module F05/F06
đã tạo hoặc áp dụng phương án. Nhật/Linh/Bảo 06/Tân còn cần ghép và kiểm riêng.

## Còn phải xác minh

- Leader chốt enum/shape còn là đề xuất trong docs/api/f01.md.
- Giờ tuần, thời lượng, điều kiện tiếp cận và chặng còn thiếu của điểm thật;
  xem backend/data/data_review.json. Không có địa điểm nào đang được đánh dấu đã xác minh đầy đủ.
- Đăng ghép auth trên main; Bảo 06 nhập dữ liệu SQLite.
- Hân nối S01 với tài khoản thật trên thiết bị và cùng Tân lưu bằng chứng.
- Không đánh dấu Android hoặc toàn bộ T01–T15 PASS trước khi quan sát thực thi.
