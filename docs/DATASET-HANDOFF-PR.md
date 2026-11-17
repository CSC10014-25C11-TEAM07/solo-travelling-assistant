Refs #8. Khi bỏ hết sở thích trong lúc F01 đang tải, S01 xóa thẻ nhưng giữ spinner vì nhánh rỗng chưa reset loading. Thêm `L(false)`; phản hồi cũ vẫn không ghi đè lựa chọn mới. Giữ nguyên phần tích hợp PLAN từ main `ac35605` (PR #25/#26).

Tuyến nguồn 3/4 ngày trước đây thiếu nơi ngủ/chặng nối và còn chờ chốt ngân sách giờ. Dataset **bao04-mvp-2026-11-17-v1** áp dụng cấu hình Bảo 04 đã duyệt:

- Tách **L001 Crazy House** làm mốc lưu trú mẫu, không dùng lịch VISIT của P009 cho khách lưu trú. Thêm P001↔L001, truy vấn độc lập từng chiều, mỗi chiều 8 phút/UNVERIFIED; mọi đêm và nhánh mưa nối đủ về L001.
- VISIT Still/An **60 phút** mỗi điểm là ngân sách do Bảo 04 chọn, REST tính riêng. Hạn ngày đi/về **18:00**, nội vùng **17:00**, buffer **30 phút** ngoài REST tối thiểu **60 phút/ngày**. Audit tính buffer trước deadline, kể cả sau WAIT, và từ chối buffer sai kiểu/âm.
- Catalog 16 điểm/26 chặng; tập nguồn nhỏ 9 điểm/26 chặng, REVIEW_ONLY. Giữ nguyên MOCK, schema/API, engine và SQLite. Không nâng nhãn VERIFIED từ quyết định cấu hình.

Cả hai tuyến và nhánh mưa không còn MISSING_LEG. Cận dưới có chặng nơi ngủ/REST/buffer là **17:55/17:57**; đây chưa phải lịch khả thi. Hai tuyến vẫn **ready=false**, 42/55 gaps lặp theo ngày: còn pin/giờ/tiếp cận R003/L001/H001/P001, còn phòng và giờ/môi trường venue. L001 chỉ dùng tọa độ khu P009 làm tham chiếu, không phải cổng khách lưu trú đã xác minh. Không đóng #8 từ kết quả offline.

Kiểm mới trên dataset này: **127 backend tests PASS**, ba validators PASS, audit cấu trúc/MOCK PASS, **8 lượt F05 replay PASS**, export 9 điểm/26 chặng PASS. Test buffer có RED trước implementation và GREEN sau sửa. Hash đầu vào và lệnh ở báo cáo bên dưới.

Bằng chứng S01 giữ nguyên: Expo Go 58/Android Emulator với API/session SQLite thật, baseline 7 PASS/1 FAIL; ca clear-inflight FAIL trước sửa và PASS sau sửa, rồi PASS lại sau khi ghép ac35605. Lần kiểm S01 đó có 9 transport tests và typecheck PASS; lint còn 3 errors/28 warnings sẵn từ main. Đợt dữ liệu này không chạy lại native; điện thoại thật vẫn NOT_RUN, chưa xác nhận toàn bộ AI/API/lưu thật.

- [Checks/hash cấu hình và dữ liệu](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/testing/source-route-configuration-checks.json)
- [Kết quả bàn giao mới và giới hạn](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/testing/dataset-handoff-results.md)
- [Quyết định đã áp dụng và evidence chặng](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/testing/source-route-proposal.json)
- [Dữ kiện nguồn còn cần xác minh](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/DATA-SOURCE-VERIFY-BAO04.md)
- [Kết quả/cách tái hiện S01](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/testing/s01-f01-handoff.md)
