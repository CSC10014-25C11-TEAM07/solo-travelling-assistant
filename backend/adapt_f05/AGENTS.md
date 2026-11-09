# Nhật - phạm vi ADAPT F05

Trước mọi lượt code, đọc danh sách PR đang mở trên GitHub và file thay đổi của PR liên quan. Đọc issue #5, git status và nhánh hiện tại trước khi sửa. Không giả định kết quả kiểm tra PR từ phiên trước còn mới.

Chỉ sửa module này, test ADAPT và tài liệu ADAPT trong công việc F05. Các file main.py, adapt_api.py, adapt_store.py, itinerary_api.py và itinerary_store.py thuộc phần tích hợp/lưu trữ của Đăng/Bảo 06; không sửa nếu chưa có yêu cầu mới cho phép. Giữ thay đổi chưa commit của người dùng.

Áp dụng Chuẩn dữ liệu dùng chung V1 ngày 09/11/2026: tổng REST tối thiểu mỗi ngày; dữ liệu VERIFIED/UNVERIFIED/MOCK. SOURCED không tự đổi thành VERIFIED. Không sửa dataset nguồn của Bảo 04 để làm test xanh.

Mặc định chạy rules hoặc mock; không gọi Gemini thật khi chưa được yêu cầu. Không ghi key, token hoặc dữ liệu tài khoản vào log/test fixture. Không coi adapter HTTP được mock là bằng chứng AI thật.

Đầu ra hiện là F05_DOMAIN_PREVIEW_V1 nội bộ. Chưa có thống nhất về thay/xóa TRAVEL trong hợp đồng F05/F06. Không bỏ qua handoff.to_api_v1 hoặc tự đăng ký endpoint nhận ACCEPT. Cần Bảo 06/Leader chốt trước.

Từ repo root chạy: `python -m unittest discover -s backend/tests -v`. Từ backend chạy: `python -m adapt_f05.demo --case rest --ranker mock`. Test mới phải bảo vệ bất biến nghiệp vụ, không chỉ so output với chính hàm đang kiểm thử.
