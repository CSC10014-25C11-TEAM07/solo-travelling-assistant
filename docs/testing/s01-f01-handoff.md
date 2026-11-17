# Kiểm chứng đổi sở thích trên S01

**Baseline dbb46af: PARTIAL_FAIL trên Android Emulator/Expo Go. Bản sửa đã kiểm lại sau ghép main ac35605: regression PASS. Điện thoại thật: NOT_RUN.**
Đã kiểm bản ghép `dbb46affa6ad371f98ec133b61f8b2ec3d41528f`, dataset
`bao04-mvp-2026-11-16-v1`, ngày 16/11/2026. PR #24 đã merge; kết quả này tiếp tục
phần kiểm chứng S01 mà nhóm trưởng nhắc. Không suy từ test API thành PASS giao diện.

Môi trường: Medium_Phone_API_37.0, arm64, 1080×2400, Expo Go SDK58; Metro 18082,
main.app/backend 18001, SQLite mới trong thư mục thử. Dữ liệu F01 là catalog nguồn.
Một lớp quan sát chuyển tiếp main.app ghi query/status/ID và việc có Bearer, không
lưu token. Chỉ các ca được ghi rõ độ trễ dùng delay 5 giây có kiểm soát; không thay
phản hồi nghiệp vụ. Timestamp bằng chứng dùng UTC của máy chạy, đồng hồ máy ảo có
thể khác múi giờ.

## Kết quả quan sát trên main

| Ca | Kỳ vọng và kết quả | Bằng chứng |
|---|---|---|
| Chọn coffee | PASS: Bearer, HTTP 200, P006/P010/P011; đúng tên và lý do trong mục “Dành cho bạn” | [Ảnh](s01-android/coffee.png), [XML](s01-android/coffee.xml) |
| Coffee → nature | PASS: danh sách đổi thành P002/P003/P004; không giữ ba thẻ coffee | [XML](s01-android/nature.xml), network-events.json |
| Nature + culture | PASS: query interests lặp; P002/P001/P003, điểm khớp hai nhãn ưu tiên | [Ảnh](s01-android/nature-culture.png), [XML](s01-android/nature-culture.xml) |
| Đổi trong khi phản hồi coffee chậm 5 giây | PASS: phản hồi nature mới về trước coffee cũ; cuối cùng vẫn P002/P003/P004 | [XML](s01-android/latest-selection-wins.xml), [thứ tự phản hồi](s01-android/network-events.json) |
| Bỏ hết sau khi tải xong | PASS: xóa thẻ, hiện “Chưa có gợi ý phù hợp.” | [XML](s01-android/clear-settled.xml) |
| Bỏ hết khi coffee đang tải | **FAIL**: thẻ được xóa nhưng “Đang tải gợi ý…” còn hiển thị sau khi response đã về | [Ảnh trước sửa](s01-android/clear-inflight-before.png), [regression exit 1](s01-android/clear-inflight-before.json) |
| Chọn lại rồi bỏ hết | PASS: một request mới thành công khôi phục được trạng thái; không giải quyết ca đang tải ở trên | [XML](s01-android/clear-after-recovery.xml) |
| Đăng xuất trên S01 | PASS: quay lại màn đăng nhập. Backend auth/F01 test riêng cũng kiểm token đã logout bị 401 | [XML](s01-android/logout.xml), backend test_auth_f01_integration.py |

Chi tiết máy đọc được: [ui-results.json](s01-android/ui-results.json) và
[checks.json](s01-android/checks.json). Mục “Khám phá Đà Lạt” là danh sách tham khảo
local, được tách khỏi mục “Dành cho bạn” khi đánh giá F01; không lấy danh sách local
làm bằng chứng rằng API đã trả đúng.

## Kiểm lại sau khi main cập nhật

Ngày 17/11 đã ghép main `ac35605` gồm PR #25/#26 để giải quyết xung đột ở S01.
Giữ nguyên setDraftId/result.itinerary và các module tích hợp của Hân/Bảo 06; phần
code khác main của PR này chỉ là thêm `L(false)` trong nhánh sở thích rỗng.

- Regression native cùng kịch bản delay 5 giây trên bản ghép: **PASS, exit 0**.
  [Ảnh hiện tại](s01-android/clear-inflight-merged.png), [kết quả/hash](s01-android/clear-inflight-merged.json).
- Backend 123 tests, mobile 9 tests và typecheck: **PASS** sau ghép.
- Lint sau ghép: **FAIL, 3 errors/28 warnings** (S01:17 set-state-in-effect và
  adapt/context:25 refs,:62 set-state-in-effect). Lỗi plan/state cũ đã được main xử
  lý. So sánh Plan với nguyên bản ac35605 cho cùng rule/line/count; các file mobile
  khác khớp main. Không tự sửa lint của phần khác trong đợt này.
- [Patch theo main hiện tại](s01-android/current-main-clear-loading.patch).
  `checks.json.post_merge` tách riêng kết quả/hash mới khỏi bằng chứng dbb46af cũ.

## Lỗi và bản sửa đi cùng PR tiếp nối

Tại `mobile/src/app/plan.tsx:17`, khi interests rỗng, effect gọi `SP([])` rồi return
trước khi reset loading. Effect cũ đã cleanup `active=false`, nên `.finally()` của
request cũ cũng không tắt được loading. Bản sửa thêm `L(false)` trong nhánh
rỗng, giữ nguyên cơ chế bỏ qua response cũ và hợp đồng HTTP.

- Chạy regression trên main: **FAIL, exit 1**, có request coffee delay 5 giây và ảnh/XML.
- Cùng regression trên bản sửa cục bộ: **PASS, exit 0**, hiện trạng thái rỗng và hết loading.
- [Patch đã kiểm](s01-android/proposed-clear-loading.patch), [ảnh sau sửa](s01-android/clear-inflight-after.png), [kết quả](s01-android/clear-inflight-after.json).
- Hai JSON regression ghi SHA256 file S01 tương ứng. Bản sửa được đưa vào file S01 trong PR tiếp nối theo phê duyệt của Bảo 04 ngày 17/11;
  kết quả main ở trên gắn với commit dbb46af trước sửa. Chưa xác nhận merge/nghiệm thu.
  PR #26 của Hân đã merge qua main ac35605; đã giữ phần tích hợp đó và kiểm lại
  regression ở bản ghép. Không kết luận về toàn bộ luồng PLAN từ ca F01 này.

Chỉ ca regression đã được chạy lại trên patch; các ca trong bảng là kết quả của main
trước patch. Đợt này không ghi toàn bộ giao diện là PASS sau sửa.

## Kiểm tra mã nguồn trước khi ghép ac35605

- Backend: `python -m unittest discover -s backend/tests -q`: **123 PASS**.
- Mobile transport: `npm run test:f01`: **9 PASS**; có cảnh báo Node
  MODULE_TYPELESS_PACKAGE_JSON sẵn có.
- `tsc --noEmit`: **PASS**.
- Lint: **FAIL cả trước/sau patch**, cùng 4 errors/31 warnings. Các lỗi:
  plan.tsx:17 và plan/state.tsx:8 (`react-hooks/set-state-in-effect`);
  adapt/context.tsx:25 (`react-hooks/refs`) và:62 (`react-hooks/set-state-in-effect`).
  Không coi bản ghép đã qua đầy đủ quality checks.

## Tái hiện ca mạng chậm

1. Dùng đúng commit/dataset trên, cài thư viện theo lockfile trong checkout thử;
   chạy backend với SQLite thử riêng. Không reset database đang sử dụng.
2. Chạy Expo Go Android, đăng ký/đăng nhập tài khoản thử với mật khẩu 15–128 ký tự.
   Ghi OS/thiết bị, commit frontend/backend và dataset_version.
3. Với một middleware **chỉ trong server test**, làm chậm request
   `/api/v1/places/recommendations` có đúng interests=coffee trong 5 giây rồi chuyển
   tiếp nguyên request tới main.app. Ví dụ tệp chạy tạm từ thư mục backend:

```python
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
import uvicorn
import auth
from main import app

@app.middleware("http")
async def test_latency(request, call_next):
    if (request.url.path == "/api/v1/places/recommendations"
            and request.query_params.getlist("interests") == ["coffee"]):
        await asyncio.sleep(5)
    return await call_next(request)

if __name__ == "__main__":
    with TemporaryDirectory(prefix="s01-check-") as directory:
        auth.DB_PATH = Path(directory) / "s01.test.sqlite3"
        uvicorn.run(app, host="0.0.0.0", port=8001)
```

4. Đặt `EXPO_PUBLIC_API_URL` tới server test, restart Expo. Với máy ảo và API
   localhost, có thể dùng `adb reverse tcp:8001 tcp:8001`; điện thoại dùng IP LAN
   cùng Wi-Fi và kiểm `/health` trước.
5. Bỏ hết sở thích, chọn coffee rồi bỏ coffee trước khi 5 giây kết thúc. Cuộn xuống
   “Dành cho bạn”, đợi response hoàn tất. Main còn loading; patch phải hiện trạng
   thái rỗng, không có thẻ hoặc loading cũ. Lưu ảnh và HTTP status/query đã che token.
6. Chọn coffee rồi nhanh chóng chuyển sang nature; cho coffee cũ về sau. Kỳ vọng
   danh sách cuối cùng theo nature. Trở về mạng thường, chạy lại coffee/multi/logout.

## Chưa được xác nhận bởi đợt này

Điện thoại Android thật và nghiệm thu Expo Go của Đăng; empty response bằng catalog
riêng; các lỗi mạng khác/timeout/AI/lưu; F02/F05/F06; tính khả thi tuyến thật. Các
mục chưa chạy giữ NOT_RUN. Lint còn lỗi; ca clear-inflight đã được sửa và kiểm trên nhánh PR, cần nghiệm thu bản ghép/điện thoại thật.
