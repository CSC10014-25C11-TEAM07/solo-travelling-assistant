Refs #8. Bàn giao phần dữ liệu/loader/validator của Bảo04 theo TASK17, tiếp tục PR #30 (`1404791`). PR này lấy nhánh #30 làm base vì #30 chưa merge; cần ghép #30 trước.

Tuyến nguồn trước đây chưa có stops đúng định dạng F02, bộ nguồn chỉ rà nhánh mưa và P005 toàn khu bị coi là INDOOR. Dataset **bao04-mvp-2026-11-17-v2** bổ sung:

- Stops REST/VISIT khớp audit; chặng trực tiếp giữa các stop, không biến waypoint ga thành VISIT1 phút. Giữ nơi ngủ/giờ/REST/buffer Bảo04 đã chốt.
- Sửa P005 toàn khu thành MIXED. Dùng P006 khu ghế ngồi có trần ở Là Việt200 Nguyễn Công Trứ làm ứng viên mưa; có tọa độ/nguồn/phạm vi và ngân sách mẫu60 phút (không phải thời lượng quán xác nhận; weekly vẫn null/UNVERIFIED).
- Thêm16 chặng motorcycle độc lập, đủ đường đến điểm mới/đi tiếp, các hoán vị F02 và đường bỏ VISIT tùy chọn:42 chặng,28 ước tính VERIFIED/14 UNVERIFIED chạm R003/L001. Các26 chặng cũ giữ nguyên.
- Bốn input nguồn EXTEND_REST/RAIN×3D/4D và audit ngày trước/sau; exporter mang theo đầy đủ case/replacement/audit. Không tạo CURRENT, DONE hay đề xuất F05 giả.

Kiểm tra: **136 backend tests PASS**, ba validator PASS, audit cấu trúc/MOCK PASS, **8 F05 MOCK replay PASS**, source export **10 điểm/42 chặng** PASS. Các test scenario/stops/export có RED trước implementation và GREEN sau sửa. Graph probe30 biến thể ngày/212 đường có bỏ VISIT không thiếu cặp có hướng; chỉ kiểm coverage.

Hai tuyến vẫn **ready=false38/50 gaps**. Cận dưới gồm nơi ngủ/REST/buffer mới17:42/17:45 chưa phải lịch khả thi. Chưa xác minh cổng/giờ/đỗ xe/còn phòng và một số giờ tuần/môi trường venue; không nâng nhãn từ quyết định cấu hình. P00660 phút là lựa chọn ngân sách mẫu của đợt TASK17, không ghi thành phê duyệt riêng mới của người dùng.

Đã tái hiện và bàn giao hai điểm phần dùng chung: F02 chưa áp dụng buffer và chưa kiểm cửa sổ REST/access. Có file/hàm, expected/actual trong tài liệu; không sửa engine/router/SQLite/models/mobile hoặc MOCK của các chủ phần. Nguồn UNVERIFIED vẫn bị PlanProvider VERIFIED từ chối DATA_INCOMPLETE. Không xác nhận Gemini, điện thoại hoặc ACCEPT/REJECT/restart bằng đợt này, không đóng #8.

- Bàn giao, quyết định đã chốt, dữ kiện thiếu và yêu cầu chủ phần: `docs/TASK17-BAO04-HANDOFF.md`
- Kết quả/hash/lệnh: `docs/testing/task17-bao04-checks.json`
- Provider/graph observations: `docs/testing/task17-provider-observations.json`
- Audit/replay mới: `docs/testing/dataset-handoff-report.json`, `dataset-handoff-f05-replay.json`
