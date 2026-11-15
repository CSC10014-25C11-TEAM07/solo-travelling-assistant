Refs #8

Bàn giao mốc 15/11 của Bảo 04 theo phân công MVP 14/11: `bao04-mvp-2026-11-15-v1`.

- Giữ bốn ca MOCK T06/T08/T13/T15, thêm CLI replay 8 lượt trên snapshot3D/4D qua F05 đã merge; kiểm DONE/ngày khác, bản lưu JSON và snapshot đề xuất độc lập.
- Audit nguồn cộng VISIT, REST và chờ mở cửa; kiểm ngày, điểm nghỉ, chặng đúng hướng/điểm cuối và giờ tiếp cận mốc. Thiếu dữ liệu hoặc vượt giờ không báo ready.
- Điền 120 phút P005 từ cổng du lịch tỉnh; giữ UNVERIFIED vì giờ/phạm vi khu có mái chưa thống nhất. Rà thêm 4 chặng có hướng: catalog hiện 15 venue UNVERIFIED, 20 ước tính VERIFIED +4 UNVERIFIED.
- Xuất tập nguồn nhỏ 8 điểm/24 chặng + cấu hình/provenance/readiness sang thư mục mới. Không ghi SQLite hoặc đổi nhãn; không sửa backend tích hợp/AI/mobile.

Kiểm tra: `python -m unittest discover -s backend/tests -v`; ba catalog validators; `audit_data_handoff.py`; `replay_handoff_f05.py`; `prepare_source_bundle.py --output-dir <new-dir>`. Kết quả trong `docs/testing/dataset-handoff-results.md`.

Tuyến thật 3/4 ngày vẫn BLOCKED: giờ/thời lượng/tiếp cận venue, đúng tọa độ R003, chỗ ngủ/chặng nối và ngày đi có cận dưới17:17 vượt hạn17:00. Hai nhánh mưa có đủ chặng nhưng venue chưa đủ dữ liệu. Đã kiểm API F01 qua phiên SQLite thật bằng TestClient; chưa xác nhận S01/Expo Go, F02/F05 AI thật hoặc F06/SQLite qua app. Không đóng #8.

Nhật dùng fixture/RouteDay; Bảo06 nhận source pack để rà/import; Tân dùng đúng catalog và ghi mode/version; Hân/Bảo04 chạy S01 khi có bản ghép. Hướng dẫn và việc cần xác minh tiếp ở `docs/DATASET-HANDOFF-BAO04.md`.
