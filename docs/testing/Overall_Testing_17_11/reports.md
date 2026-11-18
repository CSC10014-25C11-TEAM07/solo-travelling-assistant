# BÁO CÁO CHI TIẾT CÁC TASK ĐÃ THỰC HIỆN

**Dự án** Solo Travelling Assistant  
**Phần việc** Kiểm thử và đối chiếu nhiệm vụ của Tân  
**Ngày lập báo cáo** 17/11/2026  
**Căn cứ phân công mới nhất** TASK 17/11, hạn bàn giao 18/11/2026

## 1. Kết quả thực hiện

Đợt làm việc đã hoàn thành việc đọc và đối chiếu 12 tài liệu dự án, kiểm tra mã nguồn liên quan đến nhiệm vụ kiểm thử của Tân, rà soát bằng chứng có sẵn, chạy các bộ kiểm thử tự động và chuẩn bị bảng theo dõi T01–T15.

Bốn bộ kiểm thử chính có tổng cộng **152 bài**, gồm **150 bài đạt** và **2 bài gặp lỗi môi trường khi tạo symbolic link trên Windows**. Hai bài này cần được chạy lại trên môi trường có quyền phù hợp. Các kết quả đầu cuối trên thiết bị và Gemini thật còn cần bổ sung bằng chứng để nghiệm thu MVP.

Các thao tác với repo nguồn trong đợt này là đọc mã nguồn, đọc tài liệu và đọc thông tin Git. Phân tích và chạy thử được thực hiện trên bản sao trong workspace. Các file báo cáo được tạo riêng, ngoài repo nguồn. PR hiện tại được giữ nguyên theo yêu cầu của Tân.

## 2. Môi trường và bản mã nguồn được kiểm tra

| Nội dung | Giá trị ghi nhận |
|---|---|
| Repo nguồn | `D:/WORKPLACE/Computational Thinking/solo-travelling-assistant` |
| Nhánh đọc được | `17_11_vndt/OvrTest` |
| HEAD đọc được | `ac35605cff7e35d491c2950b89358ce5cf1e92bb` |
| Bản sao chạy thử | `C:/Users/admin/Documents/Codex/2026-11-17/s/work/repo-review` |
| Python | 3.14.3 |
| Node.js | v26.13.1 |
| Phiên bản dữ liệu trong manifest | `bao04-mvp-2026-11-16-v1` |
| Cách chạy backend test | unittest, FastAPI TestClient và database tạm do test tạo |
| Cách chạy frontend test | Node.js test runner |

Git báo lỗi ownership khi đọc lần đầu. Sau khi dùng cấu hình safe.directory riêng cho câu lệnh để đọc thông tin, đã lấy được tên nhánh và HEAD. Lệnh kiểm tra trạng thái working tree tiếp tục gặp lỗi quyền truy cập. Vì vậy, commit trên được dùng làm mốc tham chiếu. Bản sao kiểm thử lấy từ các file đang có trong thư mục nguồn và chưa được xác nhận khớp hoàn toàn với HEAD. Trạng thái PR trên GitHub chưa được truy cập trong đợt này.

## 3. Chi tiết các task đã hoàn thành

### Task 1. Đọc và tổng hợp tài liệu dự án

**Trạng thái hoàn thành việc đọc và tổng hợp.**

Đã đọc 5 tài liệu kỹ thuật gồm hợp đồng tài khoản, chốt dữ liệu/API F01–F03, hợp đồng PLAN/ADAPT V1, chuẩn dữ liệu dùng chung và quy tắc lưu thay đổi chặng khi ADAPT.

Đã đọc thêm 7 tài liệu sản phẩm và tổ chức công việc gồm Kế hoạch triển khai, Nội dung tham chiếu sản phẩm, Phân công Midterm, Phân công hoàn thành app ngày 14/11, Idea Specification V1.0, Scope Brief v01 và TASK 17/11.

Kết quả tổng hợp xác định phạm vi bắt buộc hiện tại gồm tài khoản, F01–F03, F05–F06, chuyến xe máy TP.HCM ⇄ Đà Lạt trong 3 hoặc 4 ngày và hai ca ADAPT nghỉ thêm/đổi điểm vì mưa. Các hướng mở rộng trong tài liệu ý tưởng được đối chiếu với phạm vi triển khai mới nhất khi đánh giá công việc hiện tại.

### Task 2. Đối chiếu phân công dành cho Tân

**Trạng thái hoàn thành việc đối chiếu.**

Đã đối chiếu vai trò của Tân qua các tài liệu Midterm, kế hoạch triển khai, phân công 14/11 và TASK 17/11. Phần việc hiện tại gồm tổng hợp bằng chứng, cập nhật T01–T15, chạy các ca còn thiếu, kiểm tra lại sau sửa lỗi, kiểm thử bản tích hợp Gemini và hoàn thiện hướng dẫn chạy/reset.

Đã ghi nhận các yêu cầu bổ sung về gửi lặp, phiên bản cũ, phiên đăng nhập, quyền sở hữu, lỗi API/AI và dữ liệu sau khởi động lại. Theo kế hoạch review cố định, Tân review phần của Linh và Bảo 04 review phần bàn giao của Tân.

### Task 3. Chuẩn bị bản sao phục vụ kiểm tra

**Trạng thái hoàn thành.**

Đã sao chép các thư mục `backend/`, `mobile/`, `docs/` và file `requirements.txt` vào workspace riêng để đọc, phân tích và chạy thử. Đã tìm được Python thực tế cài trên máy sau khi các lệnh Python qua WindowsApps gặp lỗi truy cập.

Đã đọc hướng dẫn có trong repo cho phần liên quan, gồm hướng dẫn mobile. Đợt kiểm tra sử dụng các bài test hiện có. Các sửa đổi mã nguồn ứng dụng và PR chưa được thực hiện trong đợt báo cáo này.

### Task 4. Rà soát code theo các lỗi đã được giao

**Trạng thái hoàn thành rà soát, đã ghi nhận các điểm cần người phụ trách xử lý.**

| Phát hiện từ mã nguồn | File và vị trí liên quan | Đối chiếu phân công | Kết quả cần kiểm lại |
|---|---|---|---|
| S03 lấy danh sách activities rồi sắp xếp và render, chưa lọc trạng thái đang có hiệu lực | `mobile/src/app/current.tsx`, khoảng dòng 148 | Hân sửa S03 | Sau ADAPT, danh sách đang thực hiện hiển thị PENDING/DONE |
| Hàm tạo đề xuất chưa truyền timeout riêng vào HTTP client | `mobile/src/features/adapt/api.ts`, hàm `propose`; mặc định tại `features/plan/api.ts` | Linh sửa timeout F05 | Tạo đề xuất dùng 90 giây, đọc và quyết định dùng 15 giây |
| Factory ứng dụng mặc định nhận `mock_plan` | `backend/main.py`, `create_app` và `configured_app` | Bảo 06 tích hợp F02 của Nhật | Lệnh backend chung chạy được F02 với Gemini thật |
| Endpoint tạo đề xuất gọi `AdaptEngine(catalog).generate(...)` | `backend/adapt_api.py`, khoảng dòng 114 | Bảo 06 tích hợp giao tiếp F05 của Nhật | Luồng mặc định gọi provider dùng Gemini theo bàn giao |
| Báo cáo dữ liệu và bàn giao provider còn ghi thiếu điều kiện chạy tuyến nguồn | `docs/testing/dataset-handoff-results.md`, `docs/PLAN-F02-NHAT-HANDOFF.md` | Bảo 04 hoàn thiện dữ liệu, Đăng chốt lựa chọn còn thiếu | Chạy lại validator/audit trên dữ liệu cập nhật |

Các phát hiện phù hợp với TASK 17/11. Kết luận về S03 và timeout được rút ra từ việc đọc code. Chưa có video tái hiện hai điểm này trên điện thoại trong đợt kiểm tra.

### Task 5. Rà soát báo cáo và bằng chứng đã có

**Trạng thái hoàn thành rà soát các file liên quan tìm thấy trong repo.**

Đã đọc `docs/testing/demo-reset-results.md`. Báo cáo ngày 10/11 ghi nhận reset lặp cho snapshot 3D/4D, rollback, cách ly tài khoản, lưu quyết định, gửi lại ACCEPT và đọc dữ liệu sau khởi tạo lại ứng dụng. Bài kiểm trong báo cáo dùng F05 ở tầng domain với RuleRanker.

Đã đọc `docs/testing/adapt-f05-results.md`. Báo cáo ghi các lượt T06/T08/T13/T15 và lịch sử vướng validator khi ghép với bản F06 trước đó. Nội dung này được dùng để hiểu quá trình tích hợp, còn kết quả hiện tại được đối chiếu bằng lượt chạy mới.

Đã đọc `docs/testing/dataset-handoff-results.md` ngày 16/11 và bàn giao `docs/PLAN-F02-NHAT-HANDOFF.md`. Các tài liệu ghi rõ phạm vi kiểm tra cục bộ, trạng thái tuyến nguồn và nhu cầu tích hợp provider.

TASK 17/11 ghi nhận Đăng đã thử các luồng chính trên iPhone qua Expo Go với MOCK. Các file đã kiểm tra chưa cung cấp đủ bằng chứng và metadata để điền kết quả nghiệm thu từng ca T01–T15. Nội dung Đăng đã thử được giữ dưới dạng kết quả do tài liệu ghi nhận.

### Task 6. Chạy suite backend chính

**Trạng thái đã chạy đủ suite, còn 2 bài cần xác minh lại do quyền Windows.**

Lệnh chạy từ thư mục gốc bản sao

```powershell
python -X utf8 -m unittest discover -s backend/tests -v
```

Kết quả có **123 bài**, **121 bài đạt**, **2 bài lỗi**, thời gian runner ghi nhận **14,012 giây**. Tiến trình kết thúc với mã 1 do hai lỗi.

Phạm vi các bài hiện có bao gồm logic ADAPT, đầu ra/ranking AI giả lập, auth/F01 tích hợp, dữ liệu và ràng buộc, reset database kiểm thử, replay bộ bàn giao, provider F02/F05, xuất bộ nguồn và kiểm tra mức sẵn sàng của tuyến.

Hai bài gặp lỗi

| Bài kiểm | Hiện tượng | Phạm vi chưa xác minh |
|---|---|---|
| `test_app_name_symlink_and_hardlink_are_refused` trong `test_demo_reset` | WinError 1314 khi tạo symbolic link phục vụ chuẩn bị test | Cần chạy lại đầy đủ bài bảo vệ đường dẫn liên kết |
| `test_dangling_symlink_output_is_not_followed` trong `test_source_bundle` | WinError 1314 khi tạo dangling symbolic link | Cần chạy lại bài bảo vệ đầu ra qua liên kết |

Lỗi xảy ra ở bước tạo liên kết trong môi trường Windows. Hai bài này giữ trạng thái lỗi môi trường và cần được chạy lại trên máy có quyền tạo symlink.

Bằng chứng chi tiết nằm trong `Tan-backend-tests.log`.

### Task 7. Chạy suite API/SQLite PLAN, F03 và quyết định ADAPT

**Trạng thái hoàn thành, 16/16 bài đạt.**

Lệnh chạy từ thư mục gốc bản sao

```powershell
python -X utf8 -m unittest discover -s backend -p test_plan_f03.py -v
```

Runner ghi nhận **3,526 giây**, mã thoát 0. Các bài kiểm đã xác nhận trong phạm vi fixture của suite gồm

- Kiểm tra đầu vào PLAN, xác thực, xác nhận lịch, lưu/đọc dữ liệu và quyền sở hữu.
- Đánh dấu DONE, gửi lại, cập nhật đồng thời và rollback.
- ACCEPT đồng thời chỉ áp dụng một lần, gửi lại quyết định và xử lý quyết định xung đột.
- Giữ hoạt động DONE, chặn phương án sai và đề xuất cũ.
- REJECT giữ nguyên tuyến cho cả nghỉ thêm và đổi điểm vì mưa.
- Bảo toàn lịch sử chặng, giữ ID khi chỉ đổi giờ và xử lý số lượng chặng thay thế khác nhau.
- Rollback lịch, chặng và quyết định khi thao tác lưu thất bại.

Suite này có các cấu hình kiểm thử riêng, trong đó một số bài dùng validator MOCK để kiểm hành vi lưu. Phạm vi đạt của suite cần được đọc cùng bộ kiểm ràng buộc và lượt nghiệm thu tích hợp.

Bằng chứng chi tiết nằm trong `Tan-plan-f03-tests.log`.

### Task 8. Chạy kiểm thử JavaScript F01

**Trạng thái hoàn thành, 9/9 bài đạt.**

Lệnh chạy từ `mobile/`

```powershell
node --test tests/places.test.mjs
```

Đã kiểm query sở thích lặp, Bearer token, ảnh null, danh sách rỗng, lỗi phiên, lỗi validation, đầu vào thiếu/sai, phản hồi sai cấu trúc hoặc quá ba điểm, URL backend không hợp lệ, lỗi mạng và hủy yêu cầu bằng AbortSignal.

Node có cảnh báo `MODULE_TYPELESS_PACKAGE_JSON`. Runner vẫn hoàn thành với 9 bài đạt, mã thoát 0. Bằng chứng lượt chạy nằm trong đầu ra công cụ của cuộc trò chuyện, chưa được lưu thành log JavaScript riêng.

### Task 9. Chạy kiểm thử chuyển đổi dữ liệu ADAPT phía mobile

**Trạng thái hoàn thành, 4/4 bài đạt.**

Lệnh chạy từ `mobile/`

```powershell
node --test tests/adapt.contract.test.mjs
```

Đã kiểm ánh xạ ID lịch, version, ngày và REST; phản hồi không có phương án cùng lý do; giữ đúng option_id và dữ liệu trước/sau; từ chối payload F05 không nhất quán. Runner kết thúc với mã thoát 0. Bằng chứng lượt chạy nằm trong đầu ra công cụ của cuộc trò chuyện.

### Task 10. Chẩn đoán và xử lý trở ngại khi chạy kiểm thử

**Trạng thái hoàn thành chẩn đoán và chạy lại các suite sau khi khắc phục.**

Lượt chạy backend đầu tiên bị kẹt khi TestClient khởi tạo socket nội bộ. Đã dùng traceback có giới hạn thời gian để xác định vị trí chờ tại `socket.accept` trong quá trình tạo event loop. Đã dừng hai lượt bị kẹt.

Sau khi được cấp quyền mạng cục bộ cho lượt làm việc, TestClient chạy được và đã chạy lại suite backend chính cùng suite API/SQLite. Hai lỗi symbolic link còn lại được ghi nhận theo kết quả chạy mới.

Đã chạy riêng 49 bài `test_adapt_f05.py`, tất cả đạt. Các bài này đã nằm trong suite 123 bài, nên tổng số cuối cùng chỉ tính một lần.

### Task 11. Chuẩn bị bảng nghiệm thu và báo cáo bàn giao

**Trạng thái hoàn thành chuẩn bị biểu mẫu và tổng hợp kết quả.**

Đã tạo bảng `Tan-T01-T15.csv` gồm đủ 15 ca theo tài liệu Nội dung tham chiếu sản phẩm, có thao tác, kết quả mong đợi và các cột để ghi thực tế, trạng thái, commit, dataset_version, chế độ AI, nhãn dữ liệu, thiết bị và bằng chứng.

Các ca được để trạng thái chưa chạy nghiệm thu đầu cuối trong đợt này. Kết quả unit/integration test được ghi trong báo cáo, còn trạng thái từng ca nghiệm thu cần điền từ lần chạy đúng kịch bản trên bản tích hợp.

Đã tạo báo cáo đối chiếu `Tan-doi-chieu-17-11.md` và lưu hai log backend. Báo cáo chi tiết hiện tại tổng hợp toàn bộ các task đã thực hiện và giới hạn của từng kết quả.

## 4. Bảng tổng hợp kiểm thử

| Bộ kiểm thử | Tổng số | Đạt | Lỗi môi trường |
|---|---|---|---|
| Backend chính | 123 | 121 | 2 |
| PLAN/F03/F06 API và SQLite | 16 | 16 | 0 |
| Mobile F01 | 9 | 9 | 0 |
| Mobile ADAPT contract | 4 | 4 | 0 |
| **Tổng** | **152** | **150** | **2** |

Tổng trên tính bốn bộ kiểm thử chính và loại lượt chạy riêng 49 bài ADAPT đã có trong backend chính.

## 5. Phần còn cần thực hiện để nghiệm thu

| Công việc | Điều kiện hoặc bằng chứng cần bổ sung |
|---|---|
| Kiểm tra lại hai bài symbolic link | Môi trường cho phép tạo symlink |
| Kiểm Gemini thật F02/F05 | Bản tích hợp, model đã dùng, cấu hình backend, kết quả 3D/4D và hai ca ADAPT |
| Kiểm S03 và timeout F05 sau sửa | Bản bàn giao của Hân/Linh và bằng chứng thao tác |
| Chạy T01–T15 trên bản tích hợp | Commit, dataset_version, kết quả thực tế và ảnh/video hoặc log từng ca |
| Đối chiếu bằng chứng iPhone của Đăng | File bằng chứng, bản chạy và dữ liệu tương ứng |
| Đánh giá tuyến nguồn cập nhật | Dữ liệu đủ điều kiện, các quyết định tuyến và kết quả validator/audit mới |
| Bàn giao hướng dẫn reset đã kiểm trên môi trường chung | Lệnh, database kiểm thử và xác nhận backend đọc đúng file |

Các lỗi chức năng được phát hiện trong code đã được mô tả để đối chiếu với người phụ trách. Đợt này chưa sửa các file ứng dụng, chưa tạo PR mới và chưa thay đổi PR hiện tại.

## 6. Các file bàn giao

| File | Nội dung |
|---|---|
| `Tan-bao-cao-chi-tiet-task-da-thuc-hien.md` | Báo cáo chi tiết các task đã thực hiện |
| `Tan-doi-chieu-17-11.md` | Đối chiếu nhiệm vụ, code và phần còn thiếu |
| `Tan-T01-T15.csv` | Bảng theo dõi 15 ca nghiệm thu |
| `Tan-backend-tests.log` | Log suite backend chính, 123 bài |
| `Tan-plan-f03-tests.log` | Log suite API/SQLite, 16 bài |

Nguồn đối chiếu gồm 12 tài liệu người dùng cung cấp, mã nguồn trong repo và kết quả chạy mới của các bộ kiểm thử hiện có. Báo cáo phản ánh đợt kiểm tra trong cuộc trò chuyện này.
