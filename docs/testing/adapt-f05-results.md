# ADAPT F05 - kết quả kiểm tra 09/11/2026

Base: a7a79347199ac6982d4499ea568d28b1e8b0d84d. PR liên quan: #16 tại 1fc48eb70ba0381a552cb7f5a4c12c85e998e9ad. Không sửa file của PR #16.

Lệnh từ repo root: `python -X utf8 -m unittest discover -s backend/tests -v`.

- 69 test đạt: 46 test mới trong test_adapt_f05.py, 23 test auth/F01 hiện có.
- T06: nghỉ đến 15:00; DROP A03 hoặc A04; cả hai phương án kết thúc 16:15.
- T08: nghỉ đến 16:30; không có phương án, kể cả khi bỏ cả hai VISIT vẫn cần chặng về 15 phút.
- T13: thay A03 bằng MOCK-INDOOR 14:15-15:00; về 16:15; giữ dòng cũ REPLACED.
- T15: các INDOOR phù hợp đóng cửa; không có phương án.
- Kiểm tra đủ chặng vào/ra/cuối, giờ đóng cửa, nghỉ trưa, duration, version, fingerprint, lịch sử và DONE.
- AI giả lập sai ID/mã lý do, timeout, HTTP 429 và phản hồi hỏng: được kiểm tra; không có lời gọi Gemini thật.
- Adapter Gemini được test qua opener giả lập, không có API key thật và không phát sinh phí.
- Chạy candidate T06 qua validate_preservation của PR #16: hai phương án đều bị `ValueError: Activity history was removed` vì thay các TRAVEL PENDING. Đây là điểm ghép đã xác nhận, không sửa code bạn khác để ép qua.

Đã chạy trên môi trường Python 3.12 riêng, FastAPI 0.162.2, Pydantic 2.14.3, httpx 0.28.1, argon2-cffi 25.1.0. Không tuyên bố đạt trên mọi phiên bản chưa chạy.

Các test không đại diện cho nghiệm thu F06/Expo/AI thật. Xem docs/ADAPT_F05_HANDOFF.md để biết cách chạy và phần còn chờ thống nhất.
