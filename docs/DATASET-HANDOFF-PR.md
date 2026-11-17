Refs #8. Tiếp tục phần kiểm chứng còn thiếu sau PR #24 đã merge.

Khi bỏ hết sở thích trong lúc F01 còn tải, S01 xóa thẻ nhưng giữ “Đang tải gợi ý…” vì effect cũ đã bị vô hiệu và nhánh rỗng không reset loading. Thêm `L(false)` vào nhánh đó; request cũ vẫn không được ghi đè lựa chọn mới. Bảo 04 đã chốt nhận sửa S01 trong PR này; Đã ghép main `ac35605` gồm PR #25/#26, giữ phần tích hợp PLAN và xử lý xung đột S01.

Có bằng chứng native Expo Go 58/Android Emulator trên main `dbb46af`, API/session SQLite thật: 7 ca PASS,1 ca FAIL; cùng regression clear-inflight thất bại trước sửa (exit 1) và đạt sau sửa (exit 0). Ca đó cũng được chạy lại và PASS sau khi ghép ac35605; có ảnh/XML/hash riêng cho bản ghép. Ảnh/XML, query/status/ID và hash file S01 có trong `docs/testing/s01-android/`; không lưu token. Điện thoại thật vẫn NOT_RUN.

Kiểm tra: **123 backend tests PASS**, **9 mobile F01 transport tests PASS**, **typecheck PASS**. Đã kiểm lại sau ghép ac35605: backend 123 tests, mobile 9 tests, typecheck và regression native đều PASS. Lint mới vẫn FAIL với 3 errors/28 warnings sẵn từ main; bảng 4 errors/31 warnings trước ghép được giữ riêng. Rule/vị trí/hash nằm trong checks.json.post_merge. Review độc lập không có phát hiện critical/important. Không coi toàn bộ bản ghép đã qua quality checks hoặc nghiệm thu app.

Phần dữ liệu: cập nhật Bảo 04 là người chốt tuyến, có đề xuất riêng đang PENDING_USER_DECISION: Crazy House, VISIT Still/An 60 phút, hạn ngày đi/về 18:00 và buffer 30 phút. Có evidence mới P001→P009: 452.109 giây→8 phút, 3.055 km, vẫn UNVERIFIED. Đề xuất chưa áp dụng vào catalog/tuyến; còn venue/cổng/giờ lưu trú cần xác nhận. Hai tuyến thật hiện hành vẫn ready=false, 34/44 gaps; không đóng #8 từ các kết quả MOCK/API riêng lẻ.

- [Kết quả và cách tái hiện S01](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/testing/s01-f01-handoff.md)
- [Checks, lint và hash](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/testing/s01-android/checks.json)
- [Nguồn còn thiếu/lựa chọn Bảo 04 chốt](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/DATA-SOURCE-VERIFY-BAO04.md)
- [Đầu vào/evidence phương án tuyến](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/testing/source-route-proposal.json)
