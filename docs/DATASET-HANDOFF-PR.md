Refs #8. Tiếp tục phần chưa nghiệm thu sau PR #24 đã merge.

Bổ sung kiểm chứng S01 trên Android Emulator/Expo Go58 với main `dbb46af` và dataset `bao04-mvp-2026-11-16-v1`. S01 gọi API/session SQLite thật, hiển thị đúng khi đổi coffee→nature và chọn nhiều sở thích. Ca bỏ hết sở thích lúc request đang tải bị kẹt loading; có ảnh/XML, query/status/ID không chứa token, và regression thất bại trước sửa.

Bản vá thêm `L(false)` trong nhánh sở thích rỗng đã có regression PASS cục bộ, được bàn giao dưới dạng patch trong `docs/testing/s01-android/`. Việc đưa thay đổi vào file S01 của Hân đang chờ Bảo 04 quyết định; PR #26 của Hân đang mở ở cùng file. Manifest/checklist ghi **PARTIAL_EMULATOR_FAIL** cho main và **NOT_RUN** cho điện thoại thật.

Cập nhật người chốt tuyến là Bảo 04 theo xác nhận của người dùng. Có phương án cụ thể chờ chọn: Crazy House, ngân sách VISIT Still/An60phút, hạn ngày đi/về18:00 và buffer30phút. Bổ sung evidence riêng cho chặng P001→P009 (452.109giây→8phút,3.055km, vẫn UNVERIFIED). Đề xuất chưa áp dụng vào catalog/tuyến; cổng/giờ lưu trú và các venue còn thiếu nguồn. Hai tuyến hiện hành vẫn ready=false với34/44gaps.

Kiểm tra đã chạy:

- Backend: **123 tests PASS**; mobile F01 transport: **9 PASS**; typecheck: **PASS**.
- Native main: **7 ca PASS,1 FAIL**; native regression của patch cục bộ: **PASS**. Chỉ regression đó được chạy lại trên patch.
- Lint: **FAIL**, cùng4errors/31warnings trước và sau patch; vị trí/rule được ghi trong `checks.json`.
- Review độc lập không có phát hiện critical/important; cập nhật trạng thái S01 cũ theo góp ý nhỏ.

Tài liệu/bằng chứng:

- [Checklist và kết quả S01](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/testing/s01-f01-handoff.md)
- [Kết quả máy đọc được và lint](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/testing/s01-android/checks.json)
- [Nguồn còn thiếu và lựa chọn Bảo04 cần chốt](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/DATA-SOURCE-VERIFY-BAO04.md)
- [Đầu vào/bằng chứng phương án tuyến](https://github.com/CSC10014-25C11-TEAM07/solo-travelling-assistant/blob/feat/8-s01-source-followup/docs/testing/source-route-proposal.json)

Chưa nghiệm thu điện thoại thật, tuyến thật, AI hoặc toàn luồng PLAN/ADAPT bằng những kiểm tra này. Issue #8 còn phần dữ liệu/kiểm tích hợp cần hoàn thiện; không đóng issue từ bằng chứng MOCK hoặc API riêng lẻ.
