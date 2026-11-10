# ADAPT F05 - kết quả kiểm tra 10/11/2026

Đối chiếu PR #17 `311e94b`, F06 của PR #16 `1fc48eb`, S01–S03 của PR #18 `516d315` và dataset PR #19 `0682f3a`. Yêu cầu bổ sung trong `New requirements.txt` quy định giữ TRAVEL cũ dưới trạng thái REPLACED.

Từ repo root, chạy `python -X utf8 -m unittest discover -s backend/tests -v`. Kết quả 72 test đạt trong môi trường Python 3.12, gồm 49 test ADAPT và 23 test auth/F01. Đã kiểm tra xuất/đọc lại JSON, đổi giờ giữ ID kể cả khi lặp cặp điểm, bảo toàn DONE, từ chối diff bị sửa và từ chối dữ liệu cũ.

Đã chạy tám lượt với manifest `bao04-handoff-2026-11-10-v1` của PR #19. Mỗi lượt dùng snapshot CURRENT và target IDs theo `routes_mock.json`. Bảng dưới áp dụng cho cả 3D và 4D.

| Ca | Kết quả F05 |
|---|---|
| T06 nghỉ đến 15:00 | 2 option, đều về 16:15. Mỗi option có 2 TRAVEL REPLACED và 1 TRAVEL PENDING mới |
| T08 nghỉ đến 16:30 | 0 option, có lý do vượt hạn |
| T13 đổi điểm vì mưa | 1 option, về 16:15. Giữ 2 TRAVEL REPLACED và thêm 2 TRAVEL PENDING |
| T15 catalog không có điểm thay phù hợp | 0 option, có lý do |

Ghép thử **nguyên head PR #16** bằng tài khoản test và SQLite tạm. Với T06/T13 trên cả 3D và 4D:

- Đọc CURRENT từ API, xuất F05, gọi `save_proposal`, đọc lại JSON từ SQLite và xác minh option. CURRENT vẫn ở version 1.
- Gọi ACCEPT và nhận HTTP 409 `PROPOSAL_NO_LONGER_VALID`. Validator hiện chỉ cho VISIT chuyển sang REPLACED. Đọc lại thấy lịch và quyết định chưa đổi.
- Gọi REJECT hai lần. Cả hai trả cùng kết quả và CURRENT giữ nguyên.
- Gọi riêng `apply_days` trong giao dịch thử. Writer lưu đầy đủ các dòng lịch sử/chặng mới và tăng version một lần. Giao dịch thử được rollback. Đây là kiểm tra writer riêng.
- Chạy 9 test gốc của PR #16 từ snapshot PR. Cả 9 đạt trên các ca F06 có sẵn.

Sau khi Bảo 06 ghép validator, lặp lại hai ca T06/T13 qua F05/F06. Mỗi ACCEPT cần trả version 2, đọc lại có đầy đủ lịch sử, chặng mới xuất hiện một lần. Gửi cùng ACCEPT lần nữa và so sánh ID, số chặng và version. Chạy REJECT trên proposal mới của lịch seed để đối chiếu version 1. Linh kiểm tra S05 hiển thị tuyến trước/sau và S06 đọc lại đúng tuyến. Gemini và Expo chưa được chạy ở lượt này.
