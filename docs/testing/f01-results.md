# Kết quả kiểm tra F01

Ngày kiểm tra lại: 09/11/2026. Nhánh: feat/8-places-f01. Phạm vi: backend F01,
chất lượng cấu trúc dữ liệu, fixtures và client transport; chưa nghiệm thu S01/Android
hoặc toàn bộ T01–T15.

Môi trường đã chạy: Python 3.14.2, FastAPI 0.162.0, Pydantic 2.14.3 trên macOS.
Mobile: Node 26.7.0, npm 11.19.0, Expo SDK 58, TypeScript 6.0.3.
Đã ghép main `e2ce034` theo [review của Đăng](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/pull/13#issuecomment-6735931799).
Giải quyết conflict `backend/main.py` bằng bản main làm nền, giữ lifespan khởi tạo
auth, handler validation, auth_router và /health; thêm places_router ngay sau auth_router.

## Kiểm tra đã chạy

| Kiểm tra | Kết quả quan sát |
|---|---|
| Validator dữ liệu thật | PASS: 14 địa điểm UNVERIFIED, 14 chặng SOURCED; không có ID/chặng trùng hoặc chặng mồ côi |
| Validator MOCK | PASS: 8 địa điểm/10 chặng MOCK trong thư mục riêng |
| 22 tests trong backend/tests/test_places.py | PASS: xếp hạng, cap 3, kết quả 0/1, đổi sở thích, lỗi interests, auth, giờ và hướng chặng |
| Regression test test_auth_f01_integration.py | PASS: app và lifespan thật trong main.py khởi tạo SQLite tạm, đăng ký/login/F01, validation interests, logout và từ chối token cũ |
| Preview coffee | PASS: trả P006/P010/P011, ảnh null, lý do theo coffee |
| Preview nature/culture | PASS: P002 khớp hai nhãn đứng trước điểm khớp một nhãn |
| OpenAPI | PASS: có /api/v1/places/recommendations và HTTPBearer |
| Auth code thật PR #12 | PASS: đăng ký → đăng nhập → F01; token sai/đã logout/hết hạn bị 401; interests sai bị 422 |
| Bằng chứng chặng | PASS: 14 truy vấn motorcycle, thời gian làm tròn lên theo giây nguồn trả |
| Script collect_travel_times.py | PASS: thu thêm 8 chặng giữa 6 điểm, kiểm JSON/evidence rồi mới bổ sung; quan sát P011→P008 = 7 phút, P008→P011 = 8 phút |
| run_f01_demo.py qua HTTP | PASS: server chạy với auth thật và SQLite tạm; đăng ký/login/F01/logout; token đã logout bị 401 |
| main:app đã ghép qua HTTP thật | PASS: login 200 → F01 200 → logout 200 → F01 với token cũ 401 / INVALID_SESSION; /health 200 |
| 9 test mobile transport | PASS: query/Bearer, ảnh null, rỗng, lỗi 401/422/503, URL/input sai, response sai, mạng, hủy fetch và hủy khi đọc body |
| Client TypeScript → server HTTP thật | PASS: đăng ký/login, coffee và nature+culture, lỗi validation, token sai/đã logout; script places.integration.mjs |
| Mobile lint/typecheck | PASS: npx tsc --noEmit; npm run lint exit 0, 0 lỗi và 9 cảnh báo unused trong màn ADAPT nhận từ main |

Lệnh kiểm thử:

```bash
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
backend/.venv/bin/python -m unittest discover -s backend/tests -v
backend/.venv/bin/python backend/scripts/check_f01_auth.py
```

Tổng backend: **23 tests PASS**. Auth hiện có được nhận từ main sau khi PR #12 merged;
commit gốc `2bd6854aea1addb9cad4c4a57a3fbcc37913aae7`. Script check_f01_auth.py vẫn
kiểm riêng module trên SQLite tạm. Regression test mới dùng chính `main.app`, không
dùng app tạo bởi harness và không override dependency xác thực.

Kiểm HTTP bổ sung khởi động Uvicorn `main:app` trên 127.0.0.1:8018 với duy nhất
`auth.DB_PATH` trỏ SQLite tạm; giữ nguyên router/lifespan/handler thật. Client TypeScript
chạy `F01_TEST_PORT=8018 npm run test:f01:integration` qua server này thành công.
Sau đó quan sát riêng các HTTP status 200 → 200 → 200 → 401 như bảng trên.
Server đã dừng, DB tạm đã xóa; không ghi tài khoản hoặc token vào app.sqlite3.

Để chạy lại client qua HTTP, giữ `backend/scripts/run_f01_demo.py --port 8001`
đang chạy, rồi mở Terminal khác:

```bash
cd mobile
npm run test:f01
npm run test:f01:integration
npm run lint
npx tsc --noEmit
```

Integration script dùng tài khoản mới ngẫu nhiên trong DB demo tạm, không in token;
server dừng thì DB bị xóa. Có thể dùng `F01_TEST_PORT=8018` nếu demo chạy cổng khác.
Test client dùng Node fetch; chưa xác minh fetch/URL trên thiết bị Expo thật.

Mobile trước thay đổi có lỗi thiếu khai báo CSS và kiểu ref của TabTrigger/Pressable;
đã dùng khai báo SDK `expo/types` và kiểu ref của Pressable để sửa. Expo lint tự cài
ESLint 9 + eslint-config-expo 58; sửa hook hydration web theo useSyncExternalStore.
Lockfile thêm dependency lint, không đổi phiên bản package cũ.

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
- Nhật review lại PR #13 sau khi ghép main; Bảo 06 nhập dữ liệu địa điểm/chặng vào SQLite.
- Hân nối S01 với tài khoản thật trên thiết bị và cùng Tân lưu bằng chứng.
- Không đánh dấu Android hoặc toàn bộ T01–T15 PASS trước khi quan sát thực thi.
