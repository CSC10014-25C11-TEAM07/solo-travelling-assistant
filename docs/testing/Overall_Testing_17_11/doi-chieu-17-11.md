
## Đối chiếu code và nhiệm vụ còn lại

| Phát hiện | Căn cứ trong repo nguồn | Người phụ trách theo TASK 17/11 | Kiểm tra lại sau sửa |
|---|---|---|---|
| S03 duyệt toàn bộ hoạt động rồi sắp xếp và hiển thị, chưa lọc PENDING/DONE | mobile/src/app/current.tsx, đoạn activities khoảng dòng 148 | Hân | Sau ACCEPT, hoạt động DROPPED/REPLACED được giữ trong dữ liệu lịch sử và loại khỏi danh sách đang thực hiện |
| Tạo đề xuất chưa truyền timeout riêng, dùng mặc định 15000 ms | mobile/src/features/adapt/api.ts, hàm propose và features/plan/api.ts | Linh | Tạo F05 có timeout 90000 ms, đọc và quyết định vẫn 15000 ms |
| Ứng dụng mặc định tạo bằng mock_plan | backend/main.py, create_app/configured_app | Bảo 06 phối hợp Nhật | Chạy lệnh backend chung và chứng minh F02 gọi Gemini thật cho 3D/4D |
| Endpoint đề xuất dùng AdaptEngine(catalog), chưa gọi f05_provider.create_proposal | backend/adapt_api.py, khoảng dòng 114 | Bảo 06 phối hợp Nhật | Có bằng chứng Gemini xếp ưu tiên/giải thích phương án khả thi, bảo toàn xác thực và lưu đề xuất |
| Bộ bàn giao nguồn còn thiếu điều kiện chạy tuyến | docs/testing/dataset-handoff-results.md và docs/PLAN-F02-NHAT-HANDOFF.md | Bảo 04, Đăng chốt lựa chọn tuyến | Chạy validator/audit sau khi cập nhật, ghi dataset_version và phần thiếu |

Các phát hiện trên trùng những việc đang được giao trong TASK 17/11. Cần đối chiếu bản tích hợp mới sau khi người phụ trách bàn giao.

## Bằng chứng hiện có

`docs/testing/demo-reset-results.md` ghi kết quả cục bộ ngày 10/11, gồm reset lặp cho lịch 3D/4D, rollback, cách ly tài khoản, F03/F06, ACCEPT gửi lặp và khởi tạo lại app. Bộ này gọi F05 ở tầng domain bằng RuleRanker.

`docs/testing/dataset-handoff-results.md` ghi kết quả ngày 16/11, gồm F01 qua TestClient, dữ liệu và replay F05. Hai tuyến nguồn còn ready=false. Đây là báo cáo có sẵn và cần phân biệt với lần chạy mới.

TASK 17/11 ghi Đăng đã thử trên iPhone với MOCK các luồng tài khoản, PLAN, DONE và hai ca ADAPT. Các file đã kiểm tra chưa cung cấp đủ ảnh/video và metadata để gắn PASS nghiệm thu cho từng ca T01–T15. Bảng CSV để trống thực tế và bằng chứng nhằm chờ nhập kết quả từng lần chạy.

## Kết quả chạy mới trên bản sao

Python 3.14.3, Node.js v26.13.1. Mã nguồn lấy từ working tree đang có, dataset_version `bao04-mvp-2026-11-16-v1`. Các bài hiện có được chạy với database tạm do test tạo. Sau khi cấp quyền mạng nội bộ, TestClient chạy được.

| Bộ kiểm thử | Kết quả |
|---|---|
| `python -X utf8 -m unittest discover -s backend/tests -v` | 123 bài, 121 đạt và 2 lỗi môi trường |
| `python -X utf8 -m unittest discover -s backend -p test_plan_f03.py -v` | 16/16 đạt |
| `node --test tests/places.test.mjs` từ mobile | 9/9 đạt |
| `node --test tests/adapt.contract.test.mjs` từ mobile | 4/4 đạt |

Tổng 150 bài đạt và 2 lỗi môi trường trong bốn bộ trên. Không cộng lại lượt kiểm riêng 49 bài ADAPT vì đã thuộc suite backend chính. Hai bài lỗi là test từ chối symlink/hardlink của demo_reset và test dangling symlink của source_bundle. Windows trả WinError 1314 ngay ở bước chuẩn bị symbolic link. Cần chạy lại hai bài trên môi trường có quyền tạo symlink để xác minh đầy đủ.

Log mới nằm cùng báo cáo tại `Tan-backend-tests.log` và `Tan-plan-f03-tests.log`. Kiểm thử JavaScript F01 có cảnh báo MODULE_TYPELESS_PACKAGE_JSON và vẫn đạt 9 bài.

Các bài tự động dùng MOCK/FakeModel và kiểm giao tiếp cục bộ. Chưa có lần gọi Gemini thật hoặc thao tác Expo Go trong đợt này. Các kết quả này chưa đủ để xác nhận từng ca nghiệm thu đầu cuối trong bảng T01–T15.

## Danh sách bàn giao tiếp theo

1. Điền T01–T15 từ lần chạy thực tế, gắn commit, dataset_version, thiết bị, chế độ AI và nhãn dữ liệu.
2. Thu thập bằng chứng iPhone đã được Đăng ghi nhận trong TASK 17/11, xác định đúng ca và bản chạy.
3. Chạy lại S03, timeout F05 và hai luồng ADAPT sau khi nhận bản tích hợp.
4. Bổ sung ca gửi lặp xác nhận/ACCEPT/REJECT/DONE, quyết định khác sau xử lý, phiên bản cũ, quyền sở hữu, phiên hết hạn/thu hồi, lỗi AI/API/lưu và khởi động lại backend.
5. Kiểm T07 khi hai phương án cùng khả thi bằng hai ưu tiên giữ khác nhau, có bằng chứng AI thật. Kiểm riêng T08/T15 options rỗng và lý do phù hợp.
6. Ghi các lệnh chạy/reset đã thực hiện thành công và đường dẫn database kiểm thử. Công cụ reset có sẵn tại backend/scripts/reset_demo.py và hướng dẫn tại docs/testing/demo-reset-guide.md.