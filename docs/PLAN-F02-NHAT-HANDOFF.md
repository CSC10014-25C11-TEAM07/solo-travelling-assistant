# Bàn giao F02 và F05 - Nhật

Mốc code dựa trên main `759f840`, PR #25 head `797c138`. Các hàm trong tài liệu này chưa được gắn vào ứng dụng chạy mặc định. Phần gắn router, catalog và SQLite do Bảo 06 phụ trách.

## F02

`PlanProvider(catalog, templates)` trả một callable nhận `DraftInput` và trả `list[day]`. Mỗi ngày có `date`, `end_deadline`, `activities`. Mỗi activity có `type`, `name`, `place_id`, `start_time`, `end_time`, `is_optional`. Hàm lưu hiện tại cấp ID và trạng thái.

```python
provider = PlanProvider(catalog, templates)  # GeminiRanker, 60 s, lỗi trả APIError
app = create_app(plan_provider=provider)
```

`templates` là dictionary theo số ngày. Mỗi tuyến có `route_id`, `data_status`, `days`. Mỗi ngày cần `start_place_id`, `end_place_id`, `start_time`, `end_deadline`, `stops`. Một stop VISIT có `type`, `place_id`, `is_optional`. Một stop REST có `type`, `place_id`, `duration_minutes`. Các REST giữ vị trí trong tuyến. Một nhóm VISIT liên tiếp được đổi thứ tự tối đa bốn điểm; tối đa 24 cách mỗi ngày và tám lịch hoàn chỉnh được đưa cho model. Giới hạn này nghĩa là không tìm hết mọi lịch có thể có.

Code chỉ lấy địa điểm và chặng trong catalog cùng chế độ MOCK hoặc VERIFIED. Python tính đường đi, giờ mở cửa, tổng nghỉ và hạn ngày, rồi Gemini chỉ xếp hạng ID các lịch hợp lệ. Khi không có tuyến, chặng hoặc dữ liệu đã xác minh, provider trả lỗi thay vì tự tạo số liệu. Khi model timeout hoặc trả cấu trúc sai, provider trả APIError; không tự dùng MOCK. Tuyến nguồn của PR #24 hiện UNVERIFIED, không đủ để chạy lịch thật.

Để kiểm tra với dữ liệu MOCK của Bảo 04, đọc `backend/data/handoff/routes_mock.json`, đọc từng `snapshot` tương ứng, gọi `mock_templates(routes, snapshots)`, trong đó snapshots ánh xạ `route_id` sang JSON của snapshot. Tạo `Catalog` từ `data/fixtures/mock`, mode MOCK và RouteDay tương ứng. Test `backend/tests/test_plan_f02_provider.py` là ví dụ chạy đầy đủ cả API tạo nháp, xác nhận và đọc lại SQLite tạm. Fixture là mô phỏng.

Trước khi dùng VERIFIED, Bảo 04 cần cung cấp tuyến đủ trường trên, địa điểm và chặng có cùng nhãn VERIFIED. `Catalog.version` và mode phụ thuộc nội dung cấu hình; không trộn chặng MOCK vào tuyến thật.

## F05

```python
public, stored = create_proposal(itinerary, payload.model_dump(), catalog_provider)
save_proposal(stored, user_id)  # Bảo 06 gọi trước khi trả public
validator = make_option_validator(catalog_provider)
```

`catalog_provider = make_catalog_provider(data_directory, routes_by_days, mode="MOCK")` tạo catalog mới mỗi lần từ JSON, ánh xạ theo thứ tự ngày sang `day_id` thực và từ chối hạn giờ khác cấu hình. `routes_by_days` ánh xạ số ngày sang cấu hình tuyến đã chọn. Với VERIFIED dùng `mode="VERIFIED"` và chỉ cấu hình tuyến đã xác minh. Mỗi số ngày cần được nhóm chốt một cấu hình, nếu có nhiều tuyến thì cần chọn tuyến lưu cùng lịch thay vì đoán theo số ngày.

`validator(itinerary, option)` khớp chữ ký của PR #25 và kiểm tra bản option do server lưu. PR #25 hiện gọi `AdaptEngine(catalog)` theo mặc định dùng luật. Để nghiệm thu AI thật cần Bảo 06 gọi `create_proposal` ở trên, giữ nguyên bước xác thực và lưu đề xuất. Không truyền nội dung option do mobile gửi vào validator.

`create_proposal` chỉ gọi Gemini khi có phương án hợp lệ và không chuyển sang RuleRanker khi AI lỗi. Nếu không có phương án thì trả options rỗng cùng lý do, không gọi AI.

## Cấu hình và kiểm thử

Đặt `GEMINI_API_KEY` và `GEMINI_MODEL` trong môi trường backend. Không lưu key vào Git hoặc chia sẻ key trong PR. Chưa có key để thực hiện kiểm tra Gemini thật. Model đã thử thành công: chưa có.

```powershell
$env:PYTHONUTF8='1'
python -m unittest discover -s backend/tests -p 'test_plan_f02_provider.py' -v
```

Test sử dụng FakeModel và dữ liệu MOCK, không gọi Gemini và không thể thay thế nghiệm thu AI thật. Cần chạy lại F02 3/4 ngày và F05 nghỉ/mưa với key, ghi model, thời gian, token, dataset_version, commit và kết quả. Sau khi ghép PR #25, chạy lại API F05/F06 có xác thực, ACCEPT/REJECT và gửi lặp. Kiểm thử Expo Go do Đăng xác nhận.

Kết quả trên Windows ngày 16/11: 9 test provider đạt; 16 test API/SQLite F03/F06 gốc đạt. Toàn suite chạy 112 test, một test nguồn tạo symbolic link gặp WinError 1314 do thiếu quyền Windows; 111 test còn lại đạt. Có đặt PYTHONUTF8=1 cho tiến trình con.
