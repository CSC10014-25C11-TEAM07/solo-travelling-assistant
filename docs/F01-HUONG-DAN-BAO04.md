# Hướng dẫn phần việc Bảo 04

Cập nhật 07/11/2026, cho issue #8. Bạn là **Bảo 04**, phụ trách dữ liệu địa điểm,
chặng di chuyển và API gợi ý F01. Bảo 06 phụ trách SQLite/lưu lịch.

Đã fetch và đối chiếu `origin/main` ở `e841624`; chưa có commit mới hơn lúc đồng bộ.
PR #11 SQLite đã ghép; PR #12 tài khoản và PR #10 ADAPT UI còn mở lúc kiểm tra.
Các lệnh dưới đây chạy từ thư mục gốc repo trên Mac, trừ đoạn ghi rõ `cd mobile`.

## Phần đã làm

- F01 đúng đường dẫn và cấu trúc nhóm chốt ngày 06/11/2026: query interests lặp,
  4 mã sở thích, khớp ít nhất một nhãn, ưu tiên khớp nhiều hơn, tối đa 3 kết quả.
- Phản hồi 0–3 điểm; ảnh null; lỗi mã sở thích đúng `VALIDATION_ERROR`/`interests`.
- Điểm nối với session thật của Đăng. Không có module auth thì báo 503;
  không nhận token bất kỳ. Đã thử code thật ở PR #12 trên cơ sở dữ liệu tạm.
- 14 ứng viên có nguồn, 14 chặng xe máy có hướng từ nguồn định tuyến công khai,
  file ghi nguồn/chỗ thiếu và script kiểm cấu trúc/thu lại chặng.
- Bộ MOCK riêng: 8 địa điểm, 10 chặng, trạng thái ngày 2 và T06/T08/T13/T15.
- Harness chạy đăng ký/đăng nhập thật + F01 ngay khi PR #12 còn mở; không cần chép
  auth.py hay tự merge nhánh tài khoản để thử.
- Hàm gọi API TypeScript cho Hân, có xử lý lỗi và hủy request; 9 test transport.
- 22 test backend; kiểm tra HTTP thật và gọi client TypeScript qua HTTP đã qua.
- Bổ sung cấu hình ESLint phù hợp SDK 58 và sửa lỗi kiểu/hydration trong bộ khung;
  lint/typecheck mobile đã qua. Những kiểm tra này chưa thay cho thử trên thiết bị.

14 ứng viên hiện đều là **UNVERIFIED**, vì một số trường cần lập lịch còn chưa rõ.
14 chặng SOURCED là ước tính thuật toán, không phải đo thực địa hoặc thời gian thực.
Bộ dữ liệu này giúp bắt đầu F01 và kiểm logic bằng MOCK; chưa đủ để khẳng định toàn bộ
chuyến xe máy HCM ⇄ Đà Lạt 3–4 ngày đã khả thi.

## Bạn còn phải làm gì, có phải đợi không?

| Việc | Trạng thái và người phối hợp | Bạn làm tiếp thế nào |
|---|---|---|
| API F01, phân loại sở thích, dữ liệu MOCK | Có code và kiểm thử trên nhánh F01 | Chạy thử mục 1/5, nhờ Nhật review PR |
| Tên trường, đường dẫn, mã sở thích | Đã chốt theo tài liệu 06/11 | Giữ hợp đồng hiện có |
| Enum/shape giờ tuần, giá trị null | Còn là đề xuất; Đăng/Leader và Bảo 06 cần chốt | Dùng bảng trong docs/api/f01.md để lấy quyết định; có quyết định mới sửa model/JSON đồng bộ |
| Dữ liệu đủ cho lịch thật | Chưa đủ | Với Nhật chọn điểm/chặng dùng demo, xác minh theo mục 4; không cần xác minh toàn bộ 14 ứng viên trước |
| Đăng nhập + F01 trên main | Auth PR #12 còn mở | Thử ngay bằng harness mục 5; bản tích hợp chung cần Đăng ghép router/lifespan |
| SQLite | Bảo 06 nhập dữ liệu sau chốt enum/shape | Bàn giao places.json, travel_times.json, nguồn và quy tắc thiếu chặng |
| S01 và bằng chứng Android | Cần Hân ghép màn hình, Tân kiểm | Đưa Hân hàm gọi sẵn có ở mục 3; cùng chạy mục 6 trên thiết bị |

**Không phải ngồi đợi file của người khác mới bắt đầu.** Bạn có thể chạy API, kiểm nguồn,
bổ sung dữ liệu và thử auth ngay. Chỉ các bước chốt hợp đồng/nhập SQLite/ghép màn hình
và nghiệm thu chung cần người phụ trách tương ứng. Chưa đủ điều kiện đóng issue #8.

## 1. Chạy thử ngay trên Mac của bạn

Mở Terminal trong thư mục gốc `solo-travelling-assistant`.
Môi trường backend/.venv đã được tạo trên máy trong lần làm này. Sau khi clone trên máy khác,
hoặc nếu chưa có môi trường, chạy:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
```

Kiểm tra hai bộ dữ liệu và chạy kiểm thử:

```bash
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/validate_places.py --data-dir backend/data/fixtures/mock
backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

Lần lượt mong đợi:

- `VALID: 14 places; 14 directed legs`, với 14 địa điểm UNVERIFIED và 14 chặng SOURCED.
- `VALID: 8 places; 10 directed legs`, toàn bộ MOCK.
- `Ran 22 tests` và `OK`.

Xem gợi ý ngay, chưa cần ghép tài khoản hay mở app:

```bash
backend/.venv/bin/python backend/scripts/preview_f01.py coffee
backend/.venv/bin/python backend/scripts/preview_f01.py nature culture
```

Lệnh đầu trả Là Việt Nguyễn Công Trứ, Still Cafe và An Cafe. Lệnh sau đưa Thiền viện Trúc Lâm lên trước
vì khớp cả nature/culture, rồi các điểm khớp một sở thích. Đây là **preview offline**,
không chứng minh đăng nhập hoặc giao diện Android đã ghép.

## 2. Hiểu các file bạn bàn giao

| File | Bạn dùng để làm gì |
|---|---|
| `backend/data/places.json` | Bàn giao địa điểm cho F01 và Bảo 06 |
| `backend/data/data_review.json` | Xem từng điểm còn thiếu gì; giữ giờ nguồn báo và ghi chú |
| `backend/data/sources.json` | Giải thích dữ liệu lấy từ đâu và trường nào do nhóm phân loại |
| `backend/data/travel_times.json` | Bàn giao chặng có hướng cho Nhật/Bảo 06 |
| `backend/data/travel_time_evidence.json` | Đối chiếu thời gian nguồn trả và cách làm tròn |
| `backend/data/fixtures/` | Dữ liệu giả lập để Nhật/Linh/Tân ghép kiểm thử độc lập |
| `docs/api/f01.md` | Gửi Hân/Đăng/Bảo 06; phân biệt đã chốt với đề xuất |
| `docs/testing/f01-results.md` | Kết quả thực tế đã chạy và phần còn chờ kiểm trên app |
| `backend/scripts/run_f01_demo.py` | Chạy auth thật + F01 cục bộ từ snapshot PR #12 |
| `mobile/src/services/places.ts` | Hàm Hân có thể import để gọi F01 |

Không đổi P001…P011/R001…R003 sau khi đã giao. `A01`…`A04` là mã hoạt động
trong lịch; một hoạt động VISIT trỏ tới một `place_id`. Hai loại mã có vai trò khác nhau.

## 3. Việc bạn cần chốt với nhóm

### Đăng và Bảo 06

Gửi `docs/api/f01.md` và hai JSON mẫu. Đề nghị Leader chốt:

1. Các mã `area`, `environment`, `data_status` trong bảng đề xuất.
2. `opening_hours.timezone` và `opening_hours.weekly` gồm 7 thứ; null là chưa biết,
   [] là đã biết đóng cửa, mỗi ngày có thể có nhiều khoảng và nghỉ trưa.
3. Cho phép trường thiếu ở bản ghi UNVERIFIED, chẳng hạn thời lượng null.

Tên trường đã theo bản chốt. Các enum/shape trên chưa được nhóm xác nhận chỉ vì
đã có code trên nhánh này. Bảo 06 sở hữu việc nhập SQLite; không cần bạn tự sửa
schema lịch trong `itinerary_schema.sql` để làm F01.

### Nhật

Nhờ Nhật chọn các điểm thật dự định dùng và liệt kê chặng cần cho lịch demo.
Mỗi cặp phải nêu rõ chiều, ví dụ P001→P005 và P005→P001.
14 chặng hiện có chỉ nối sáu điểm trong Đà Lạt; chưa phủ tuyến đi/về HCM hoặc mọi cặp.

Nhật rà thời lượng, giờ từng ngày và các điểm thay thế hợp lệ. Có thể dùng bộ MOCK
để ghép logic ngay trong lúc bổ sung dữ liệu thật. Các JSON trong `fixtures/`
là đầu vào kiểm thử đề xuất; JSON PLAN/ADAPT chính thức còn thuộc bản tổng hợp của nhóm.

### Hân

Hân có thể dùng ngay mẫu phản hồi và bốn mã sở thích để dựng thẻ:

```http
GET /api/v1/places/recommendations?interests=nature&interests=coffee
Authorization: Bearer <access_token>
```

Khi đổi sở thích, gọi lại API; hiện đúng 0–3 kết quả; ảnh null thì dùng ảnh mặc định.
Nếu gọi mạng, cần tài khoản của Đăng và đăng nhập trước.

Hàm gọi đã có trong `mobile/src/services/places.ts`. Ví dụ trong luồng của Hân,
sau khi đã có `accessToken` từ login và `selectedInterests` kiểu `Interest[]`:

```ts
import { fetchRecommendations } from '@/services/places';

const controller = new AbortController();
const result = await fetchRecommendations({
  apiUrl: process.env.EXPO_PUBLIC_API_URL ?? '',
  accessToken,
  interests: selectedInterests,
  signal: controller.signal,
});
// result.places: render đúng số lượng 0–3 thẻ.
// Khi bỏ màn hình/đổi sở thích: controller.abort(); bỏ qua AbortError.
```

Hân cần tự gắn loading/error/empty, ảnh mặc định và bảo đảm kết quả request cũ không
ghi đè lựa chọn mới. Hiện màn hình trong main vẫn là bộ khung kiểm tra backend,
chưa có S01 để ghép trực tiếp. Không ghi access token vào log hoặc mã nguồn.

Kiểm tra phần mobile (Node >=22.18 để chạy test TypeScript; máy này dùng Node 26):

```bash
cd mobile
npm ci
npm run test:f01
npm run lint
npx tsc --noEmit
cd ..
```

Nội dung ngắn bạn có thể tự gửi nhóm:

> Mình đã có bản F01 theo chốt 06/11, kèm dataset và dữ liệu MOCK kiểm thử.
> Hân xem docs/api/f01.md để nối S01. Nhật rà dữ liệu/chặng cần dùng và review logic.
> Nhờ Đăng/Bảo 06 chốt enum và cấu trúc giờ tuần trong phần đề xuất trước khi nhập SQLite.
> Những dòng chưa đủ thông tin vẫn mang UNVERIFIED; chưa dùng như lịch thực tế đã kiểm chứng.

## 4. Xác minh dataset thật theo cách cụ thể

Mở `backend/data/data_review.json`. Với mỗi điểm dùng trong demo, thực hiện:

1. Mở URL nguồn; kiểm tra đúng cơ sở, không nhầm chi nhánh.
2. Xác nhận giờ từng ngày, ngày nghỉ, nghỉ trưa; nếu nguồn mâu thuẫn, hỏi đơn vị
   hoặc giữ null/chọn điểm khác. Không tự chọn một khoảng giờ cho tiện demo.
3. Xác nhận khu trong nhà phù hợp nếu dùng đổi điểm vì mưa. MIXED không tự được
   xem như INDOOR; việc đi đến đó còn phụ thuộc chặng và ràng buộc.
4. Nhờ Nhật chốt thời lượng trải nghiệm. Giả định để thử phải ghi MOCK hoặc ghi rõ
   ở file review; không chuyển thành dữ kiện đã được địa điểm xác nhận.
5. Sửa các trường liên quan, ghi nguồn/ngày/cách kiểm tra trong review. Khi đủ thông tin
   mới đổi SOURCED; chạy validator, rồi khởi động lại backend.

Các việc ưu tiên:

| Điểm | Cần xác nhận |
|---|---|
| Bảo tàng Lâm Đồng | Giờ giữa các nguồn khác nhau; chọn khu trưng bày và thời lượng |
| Là Việt Nguyễn Công Trứ | Giờ theo từng thứ và thời lượng trải nghiệm; nguồn đơn vị đã có tên/giờ chung |
| Dinh III | Nghỉ trưa và giờ đóng cửa khác nhau giữa OSM/cổng du lịch |
| Crazy House | Giờ mở cửa 07:30 hay 08:30; phân biệt không gian trong/ngoài nhà |
| Still Cafe / An Cafe | Đã có giờ tuần từ OSM; cần xác nhận ngoại lệ, phần có mái và thời lượng |
| Các điểm còn lại | Xác nhận lịch theo từng thứ trước khi dùng kiểm ràng buộc |
| Tâm Châu Lộc An/Di Linh/Bảo Lộc | Giờ, điểm dừng xe máy, tiện ích và tiếp cận theo từng chiều |

Bạn không bắt buộc gọi tất cả địa điểm ngay. Ưu tiên điểm thật được chọn cho demo;
điểm chưa xác nhận tiếp tục mang UNVERIFIED. Không cần mua API để chạy bộ hiện có.

### Nguồn và công cụ: dùng thế nào cho đúng?

- **Địa điểm:** mở URL trong `data_review.json` bằng trình duyệt. Ưu tiên website
  của đơn vị và cổng visitlamdong.vn; đối chiếu đúng địa chỉ/chi nhánh. Không cần
  tải một dataset Kaggle chung vì thường thiếu giờ, khu có mái và nguồn từng điểm.
- **Giờ:** ghi chính xác thứ/ngày nghỉ/nghỉ trưa. P010/P011 có tag tuần OSM nên đã
  điền được lịch thường; chưa có xác nhận ngày lễ. Khi nguồn mâu thuẫn, bạn gọi/hỏi
  đơn vị hoặc nhờ người trong nhóm xác minh. Giữ ghi chú nguồn và ngày kiểm.
- **Thời lượng:** con số từ cổng du lịch là thời lượng tham khảo, không bảo đảm
  cho mọi người. Điểm null cần Nhật chốt giả định lập lịch; ghi rõ đó là giả định.
- **Chặng xe máy:** dùng script thu Valhalla có sẵn, không lấy thời gian ô tô để
  gắn nhãn xe máy. Không có dữ liệu thì báo thiếu, không dùng 0 hoặc khoảng cách
  đường chim bay thay cho thời gian thực tế.
- **Kiểm cấu trúc/API:** Terminal + validator/test; Swagger ở `/docs` là đủ để
  thử thủ công. Không cần mua Postman hay công cụ AI để chạy F01.

Ví dụ khi Nhật yêu cầu thêm P001→P011: cả hai ID đã có tọa độ. Tạo một file ngoài
dataset, chẳng hạn `/tmp/f01-pairs.json`, nội dung:

```json
[{"from_place_id":"P001","to_place_id":"P011"}]
```

Sau đó chạy (thư mục output phải mới/chưa có file kết quả):

```bash
backend/.venv/bin/python backend/scripts/collect_travel_times.py --pairs /tmp/f01-pairs.json --output-dir /tmp/f01-new-routes
```

Đối chiếu `travel_times.json` và `travel_time_evidence.json` trong output; thêm đúng
cặp mới vào hai file bàn giao, không ghi đè toàn bộ bộ cũ bằng một chặng. Nếu thu
chiều ngược thì yêu cầu riêng. Với điểm chưa có tọa độ, xác minh và thêm tọa độ có
nguồn vào `place_coordinates.json` trước. Chạy lại validator và restart backend.

Public demo chỉ phù hợp đợt nhỏ 1–20 chặng. Nếu nhóm cần thu nhiều/gọi định tuyến
cho người dùng liên tục, đó là lúc chọn dịch vụ trả phí hoặc tự host; bản này chưa
cần mua key và chưa gắn tài khoản thanh toán nào.

## 5. Thử HTTP ngay, rồi kiểm lại khi ghép main

Tài khoản đang ở [PR #12](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/pull/12)
ở thời điểm kiểm tra 07/11/2026. Khi Đăng ghép, giữ cả router/lifespan tài khoản
và router F01 như hướng dẫn trong `docs/api/f01.md`.

### Chạy ngay khi PR #12 còn mở

```bash
git fetch origin
backend/.venv/bin/python -m pip install -r backend/requirements-integration.txt
backend/.venv/bin/python backend/scripts/check_f01_auth.py --auth-ref origin/feat/2-auth-api
backend/.venv/bin/python backend/scripts/run_f01_demo.py --port 8001
```

Lệnh cuối giữ Terminal chạy. Harness đọc **code thật từ repo nhóm**, in commit SHA,
khởi tạo SQLite tạm và chạy auth + F01 cùng tiến trình. SHA đã kiểm lần này là
`2bd6854aea1addb9cad4c4a57a3fbcc37913aae7`; muốn tái hiện đúng bản đó, thêm
`--auth-ref 2bd6854aea1addb9cad4c4a57a3fbcc37913aae7`.
Không dùng ref từ repo lạ. Ctrl+C dừng server và xóa tài khoản demo tạm.

Mở **http://127.0.0.1:8001/docs** rồi thao tác theo danh sách bên dưới.
Hoặc giữ server demo đang chạy, mở Terminal khác ở gốc repo và kiểm tra luôn
hàm TypeScript với HTTP thật:

```bash
cd mobile
npm run test:f01:integration
cd ..
```

Script tự tạo tài khoản test, login, gọi F01 và logout; không in mật khẩu/token.
Chỉ chạy với server demo dùng SQLite tạm ở trên. Đổi port thì đặt `F01_TEST_PORT`.
Muốn điện thoại gọi: thêm `--host 0.0.0.0`, đặt `EXPO_PUBLIC_API_URL` trong
`mobile/.env` thành `http://IP_LAN_CUA_MAC:8001`; điện thoại cùng Wi-Fi, restart Expo.
Đây là server phát triển cục bộ; chưa phải bản deploy của nhóm.

### Sau khi Đăng ghép tài khoản vào nhánh chung

Chạy backend bình thường:

```bash
cd backend
.venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Mở `http://127.0.0.1:8000/docs`:

1. Dùng `/api/v1/auth/register` để tạo **tài khoản demo**.
   Theo bản auth đang kiểm, username 3–30 ký tự gồm a–z/số/gạch dưới;
   password 15–128 ký tự. Không dùng mật khẩu cá nhân để demo.
2. `/api/v1/auth/login` bằng tài khoản vừa tạo; lấy `access_token`.
3. Bấm Authorize; nhập token cho HTTPBearer.
4. Mở GET recommendations; thử riêng coffee, nature, rồi nhiều interests.
5. Thử sở thích sai: HTTP 422 có field interests. Thử bỏ token: HTTP 401.
6. Đăng xuất rồi dùng lại token cũ phải bị từ chối.

Nếu hiện AUTH_NOT_READY hoặc chưa có /auth/register trên /docs: auth chưa ghép,
chuyển sang harness ở trên hoặc preview offline. Không tắt kiểm tra token.

Sau khi `backend/auth.py` có trên nhánh chung, kiểm tra riêng việc ghép:

```bash
backend/.venv/bin/python backend/scripts/check_f01_auth.py
```

Lệnh này chạy từ **gốc repo**, dùng SQLite tạm và không ghi vào app.sqlite3.
Cần các thư viện tài khoản theo requirements của Đăng, gồm argon2-cffi.

## 6. Cùng Tân và Hân ghi bằng chứng

- Đổi coffee/nature/culture/food và ghi gợi ý thực tế; không yêu cầu lúc nào cũng đủ 3 điểm.
- Kiểm tra kết quả rỗng bằng catalog test; không sửa dữ liệu thật thành giả để ép ca này.
- Nhờ Hân gọi đúng Bearer và query lặp từ S01 trên thiết bị demo; chụp ảnh kết quả.
- Với ADAPT, reset `current_v1_day2.json` trước mỗi ca; dùng `scenarios.json` làm kỳ vọng.
- T06: nghỉ đến 15:00, giữ cả hai sẽ đến 17:15; bỏ A03 hoặc A04 thì đến 16:15.
- T08: nghỉ đến 16:30 mà còn 15 phút di chuyển → không có phương án hợp lệ.
- T13: thay A03 bằng MOCK-INDOOR trong cùng ngày; T15 chỉ có MOCK-CLOSED → không có phương án.
- Chưa đánh dấu T01–T15 hay Android PASS chỉ từ các test backend của nhánh này.

## 7. Bàn giao PR

Nhánh công việc: `feat/8-places-f01`. Reviewer theo issue là Nhật.
Mẫu mô tả ở `docs/F01-PR-DRAFT.md`; nêu rõ dữ liệu còn UNVERIFIED và auth đang ghép.
Giữ PR ở trạng thái nháp trong lúc còn chốt dữ liệu/tích hợp. Sau mỗi lần sửa,
commit trên nhánh này rồi đẩy tiếp; xem PR bằng:

```bash
git push -u origin feat/8-places-f01
gh pr view feat/8-places-f01 --web
```

Chỉ xem issue #8 hoàn tất khi Hân/Nhật dùng cùng bộ dữ liệu để chạy và kiểm thử,
các phần dữ liệu cần cho bản demo đã được xử lý và thay đổi đã được review/ghép.
Mình không tự gửi tin cho các thành viên trong lần làm này.
