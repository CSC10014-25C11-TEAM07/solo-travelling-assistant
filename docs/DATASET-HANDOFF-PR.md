Refs #8

Bàn giao dữ liệu/F01 của Bảo 04 theo phân công MVP 14/11. Phiên bản hiện tại:
`bao04-mvp-2026-11-16-v1`, tiếp tục mốc 15/11 và bộ đã merge ở PR #19.

- Giữ bốn ca MOCK T06/T08/T13/T15; CLI replay tám lượt trên snapshot 3/4 ngày qua F05 đã merge, kiểm DONE/ngày khác, bản lưu JSON và snapshot đề xuất độc lập.
- Audit nguồn tính VISIT, REST, chờ mở cửa, ngày/điểm nghỉ, chặng đúng hướng/điểm cuối và giờ tiếp cận mốc. Thiếu dữ liệu hoặc trễ không báo ready.
- Nguồn ngày 16/11: P009 Crazy House đối chiếu đủ trường hồ sơ VISIT, dùng lịch đơn vị 08:30–18:00 hằng ngày, MIXED và thời lượng ước tính 60 phút của cổng tỉnh. Giữ đối chiếu với giờ portal/OSM và lý do chọn nguồn; không lấy VERIFIED của một điểm làm nghiệm thu tuyến.
- Catalog: 15 điểm (1 VERIFIED, 14 UNVERIFIED), 24 chặng (20 ước tính VERIFIED, 4 qua R003 UNVERIFIED). Đọc được Tâm Châu Center và An CaFe; giữ xung đột hai giờ mở Tâm Châu và lịch khác nhau trên trang vé/header bảo tàng. Không đoán cổng, thời lượng café hoặc phạm vi INDOOR.
- Xuất tập nguồn nhỏ 8 điểm/24 chặng + cấu hình/provenance/readiness sang thư mục mới. Không ghi SQLite/đổi hợp đồng hoặc sửa phần tích hợp, AI, mobile của các bạn khác.
- Có `docs/DATA-SOURCE-VERIFY-BAO04.md`: phần trợ lý đã tra cứu, mẫu hỏi có nguồn liên hệ, mẫu ghi kết quả và ứng viên nơi ngủ để nhóm chốt. Chưa gửi tin, gọi điện, đặt phòng hoặc thay cấu hình tuyến.

Kiểm tra lại ngày 16/11:

- `python -m unittest discover -s backend/tests -q`: **103 tests PASS**.
- Ba catalog validators, `audit_data_handoff.py`, `replay_handoff_f05.py` (**8 lượt PASS**, counts 2/0/1/0) và `prepare_source_bundle.py --output-dir <new-dir>`: exit0.
- F01 qua main.app TestClient + SQLite auth tạm: **7 ca PASS**, gồm đổi sở thích, input thiếu/sai và token đã logout. JSON report có hash catalog/chặng, không có token.
- Chi tiết/tái hiện ở `docs/testing/dataset-handoff-results.md`; hai tuyến nguồn vẫn ready=false, với 34/44 gaps (gồm mục lặp theo ngày).

Tuyến thật 3/4 ngày vẫn BLOCKED: giờ/thời lượng/tiếp cận venue, pin cổng R003, nơi ngủ/chặng nối và ngày đi có cận dưới 17:17 vượt hạn đề xuất 17:00 trước buffer. Hai nhánh mưa đủ chặng nhưng venue còn thiếu dữ liệu. Chưa xác nhận S01/Expo Go, F02/F05 AI thật hoặc F06/SQLite qua app. Không đóng #8 và không tự merge.

Nhật nhận fixture/RouteDay và dữ liệu có nhãn; Bảo 06 nhận source pack để rà/import; Tân dùng đúng catalog và ghi mode/version; Hân/Bảo 04 chạy S01 trên bản ghép. Hướng dẫn ở `docs/DATASET-HANDOFF-BAO04.md` và `docs/DATA-SOURCE-VERIFY-BAO04.md`.
