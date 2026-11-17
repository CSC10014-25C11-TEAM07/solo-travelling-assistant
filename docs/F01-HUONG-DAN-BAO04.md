# Hướng dẫn phần việc Bảo 04

Cập nhật 16/11/2026. Bạn phụ trách dữ liệu địa điểm, chặng và F01 ở issue #8.
PR #13 đã vào main. Việc mới là bộ **bao04-mvp-2026-11-17-v2** theo yêu cầu Leader,
trên nhánh feat/8-data-readiness-15nov, theo phân công MVP 14/11. PR #19 đã merge.

Đọc [bàn giao dữ liệu](DATASET-HANDOFF-BAO04.md) trước: có tuyến nguồn 3/4 ngày,
snapshot MOCK đầy đủ, mapping T06/T08/T13/T15, nguồn và thông tin thiếu.
Chuẩn Leader 09/11 thay các enum đề xuất trong hướng dẫn cũ.
Trợ lý đã bổ sung nguồn ngày 16/11; [hướng dẫn xác minh](DATA-SOURCE-VERIFY-BAO04.md)
có kết quả tra cứu, câu hỏi cho đơn vị và hai quyết định nhóm còn thiếu.

## Phần đã có

- F01 đúng hợp đồng: interests lặp, nature/coffee/culture/food, khớp ít nhất một nhãn,
  ưu tiên số nhãn khớp, tối đa 3 kết quả, ảnh null và lỗi interests đúng cấu trúc.
- Auth thật + F01 cùng main.app; token sau logout bị 401.
- Catalog nguồn: 15 hồ sơ (P009 VERIFIED, 14 UNVERIFIED), 20 ước tính chặng VERIFIED, 4 chặng còn UNVERIFIED.
  Có file ghi rõ thiếu gì; chưa tuyên bố tuyến thật đã khả thi.
- Snapshot CURRENT MOCK 3/4 ngày, đủ đầu/cuối/hạn giờ/nghỉ/chặng. Ca không có phương
  án mưa dùng catalog riêng, không lẫn quán hợp lệ.
- Client `mobile/src/services/places.ts` cho Hân ghép S01. Ca đổi sở thích trên thiết bị
  chưa nghiệm thu; checklist ở `docs/testing/s01-f01-handoff.md`.

## Chạy trên Mac

Mở Terminal ở gốc repo. backend/.venv hiện đã có trên máy; chỉ tạo khi chưa tồn tại,
không tạo đè môi trường nhóm đang dùng.

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
```

Kiểm dữ liệu và test backend:

```bash
backend/.venv/bin/python backend/scripts/validate_places.py
backend/.venv/bin/python backend/scripts/audit_data_handoff.py
backend/.venv/bin/python backend/scripts/replay_handoff_f05.py
backend/.venv/bin/python backend/scripts/prepare_source_bundle.py --output-dir /tmp/sta-source-review-new
backend/.venv/bin/python -m unittest discover -s backend/tests -v
```

Đọc cả checks_passed và source_routes[*].ready_for_real_plan trong audit.
MOCK đạt kiểm dữ liệu không biến tuyến nguồn còn thiếu thành VERIFIED.

Xem gợi ý offline:

```bash
backend/.venv/bin/python backend/scripts/preview_f01.py coffee
backend/.venv/bin/python backend/scripts/preview_f01.py nature culture
```

Coffee trả P006/P010/P011; nature+culture ưu tiên P002. Preview không phải bằng chứng S01.

Chạy backend bình thường:

```bash
cd backend
.venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Mở http://127.0.0.1:8000/docs: register tài khoản thử, login, lấy access_token,
bấm Authorize rồi gọi recommendations. Username a–z/số/gạch dưới, 3–30 ký tự;
backend hiện yêu cầu password 15–128 ký tự. Không dùng mật khẩu cá nhân để demo.
Logout rồi gọi F01 bằng token cũ phải trả 401.

Muốn SQLite tạm tự xóa sau demo, chạy từ gốc repo:

```bash
backend/.venv/bin/python -m pip install -r backend/requirements-integration.txt
backend/.venv/bin/python backend/scripts/run_f01_demo.py --port 8001
```

Harness lấy auth từ Git ref tin cậy trong repo nhóm, in SHA đã ghim và tạo SQLite tạm.
Ctrl+C dừng server/xóa tài khoản tạm. Nó tái hiện auth, không thay main.app.

## Việc làm tiếp cùng nhóm

1. Đưa Nhật/Bảo 06/Tân cùng dataset_version và manifest; không trộn catalog T13/T15.
   Nhật kiểm RouteDay/thời gian; Bảo 06 nhập/reset SQLite, ánh xạ tài khoản;
   Tân ghi thực tế và bằng chứng từng ca.
2. Ưu tiên xác minh đúng chi nhánh R003, giờ tuần/nghỉ trưa và thời lượng các điểm đã
   chọn. Gaps có mã trong report. Chưa đủ thì giữ UNVERIFIED.
3. Bảo04 đã chốt L001 Crazy House, VISIT Still/An60 phút, hạn đi/về18:00 và buffer30.
   V2 dùng chặng trực tiếp giữa các stop; cận dưới có điều kiện gồm nơi ngủ/REST/buffer là17:42/17:45; còn thiếu
   giờ/quyền tiếp cận nên chưa được dùng làm lịch khả thi. Nhật nhận cấu hình rồi kiểm ràng buộc.
4. PR #18 đã merge; khi có build ghép hiện tại, chạy checklist S01 và giữ bằng chứng đổi sở thích.
   EXPO_PUBLIC_API_URL dùng IP LAN; restart Expo sau đổi .env.
5. Đăng/trợ lý review bản ghép theo phân công mới; Đăng quyết định merge. Issue #8 chỉ kết thúc khi nhóm dùng được
   cùng bộ dữ liệu và các phần tích hợp/kiểm thử cần thiết hoàn tất.

Cách thêm chặng, nguồn, quy tắc missing != 0 và phần cần xác minh nằm trong
`backend/data/README.md` và `docs/DATASET-HANDOFF-BAO04.md`.
