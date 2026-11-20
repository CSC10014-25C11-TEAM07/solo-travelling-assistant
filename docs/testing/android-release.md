# Bàn giao bản Android

Nhánh `feat/android-sourced-demo` bắt đầu từ main `26adf63` và đã ghép commit `8982a54` của PR #37 trên nhánh Android.

## Chạy backend của bản Android

Chọn Python 3.12 trở lên và cài thư viện từ `requirements.txt` ở gốc repo. Trên alwaysdata chọn loại site **User program**, đặt thư mục làm việc ở gốc repo. Đặt `STA_DATABASE_PATH` thành đường dẫn tuyệt đối tới file SQLite trong thư mục dữ liệu riêng của tài khoản hosting, bên ngoài thư mục triển khai. Tạo thư mục cha trước khi chạy và chỉ cấp quyền ghi cho tài khoản chạy backend.

Đặt `ADAPT_MODE=VERIFIED`, `GEMINI_MODEL` và `GEMINI_API_KEY` trong cấu hình riêng của backend. Khởi động bằng Python của môi trường đã cài thư viện.

```sh
python -m uvicorn main:app --app-dir backend --host "$IP" --port "$PORT"
```

Kiểm tra `/health` từ mạng di động. Tạo tài khoản thử và lịch, khởi động lại backend rồi đọc lại đúng lịch trước khi nghiệm thu.

## Tạo bản cài

Đặt `EXPO_PUBLIC_API_URL` trong môi trường EAS **preview** thành URL HTTPS của backend. Biến này chỉ chứa địa chỉ công khai. Từ `mobile/`, chạy `npx eas-cli build --platform android --profile demo`. Cài APK từ kết quả build rồi thử trên Android qua 4G.

Dự án EAS đã được liên kết với tài khoản nhóm `@dori3009s-team/solo-travelling-assistant`. Bản build đầu tiên cần cấu hình chứng chỉ ký Android và địa chỉ backend thật.

Đã cập nhật các gói Expo theo đề xuất SDK 58 và chạy Expo Doctor đạt 20/20. Kiểm tra npm ngày 20/11/2026 còn 8 cảnh báo mức vừa trong cây phụ thuộc, liên quan đến `minimatch` và công cụ Expo/ESLint. Chạy thử `npm audit fix --dry-run` không giảm được số cảnh báo. Cần xem lại khi có bản sửa tương thích SDK.

## Tiến độ kiểm chứng

Chế độ VERIFIED dùng bản dữ liệu đóng cùng backend trong `backend/data/android/`. F01, F02 và F05 dùng cùng bản này. Nguồn từng địa điểm, phạm vi giờ dùng để lập lịch, tọa độ và kết quả tra các chặng bổ sung có trong `source_review.json`. Các chặng có hướng đã xác minh từ bộ bàn giao trước mang theo URL truy vấn và thời điểm kiểm tra. Mỗi giờ đi xe là ước tính Valhalla/OpenStreetMap. Hai chặng nối TP.HCM và La Ngà có cờ hạn chế theo giờ. Dữ liệu không cung cấp điều hướng trực tiếp.

Tuyến bắt đầu và kết thúc trên Công trường Công xã Paris, mỗi chiều có ba điểm nghỉ tại Cảnh Thảo Nguyên ở La Ngà, Tâm Châu tại 294A Trần Phú, Bảo Lộc và Cali Center tại 417 Quốc lộ 20, Đức Trọng. Mốc qua đêm là đường Huỳnh Thúc Kháng gần Crazy House. Việc đặt phòng, chỗ đậu xe và giờ nhận/trả phòng do người đi xác nhận. Lịch chỉ xếp bảo tàng cho hoạt động tham quan. Hồ Xuân Hương là hoạt động ngoài trời cho ca mưa, khu ngồi trong nhà của Là Việt là một phương án thay thế.

Từ **Xem lịch đã lưu**, chọn **Mở lịch mẫu riêng**. Ngày 2 có các hoạt động buổi sáng đã hoàn thành. Chọn nghỉ đến 15:00 để so sánh việc giữ hồ hoặc An Cafe, hoặc chọn đổi Hồ Xuân Hương vì mưa. Có thể nạp lại từ đầu, đóng mẫu để trở về lịch cá nhân hoặc thử trên hai tài khoản riêng. Mỗi mẫu được cấp bộ ID mới. Thao tác nạp mẫu chọn một lịch cố định từ dữ liệu thật. Nút tạo lịch cá nhân và chức năng tạo đề xuất dùng Gemini.

Chạy `python -m unittest discover -s backend/tests -p test_android_release.py` để thử qua API với SQLite riêng. Bài này thử ngày xuất phát ở cả bảy thứ, lịch 3/4 ngày, đọc lại sau khi tạo lại ứng dụng, hai ca ADAPT, ACCEPT gửi lặp, REJECT, cách ly tài khoản và khôi phục lịch cá nhân. Bộ xếp hạng thay thế trong bài kiểm thử giúp chạy khi chưa có khóa Gemini.

Đã chạy giao diện web trong trình duyệt ở kích thước điện thoại, kết nối backend cục bộ với bộ xếp hạng thay thế. Lượt này đi qua đăng ký, đăng nhập, tạo và xác nhận lịch 4 ngày, áp dụng đổi điểm vì mưa, tải lại phiên bản 2, nạp lại lịch mẫu, từ chối nghỉ thêm và trở về lịch cá nhân. Đã bổ sung kiểm thử cho cả hai lựa chọn giữ hoạt động trong ca nghỉ thêm khi bộ xếp hạng trả thứ tự ngược. Khi có phương án hợp lệ giữ điểm ưu tiên, phương án đó được xếp trước.

Màn hình so sánh đã hiển thị các chặng bị thay và chặng mới từ dữ liệu phương án, đồng thời bỏ phần mô tả thay đổi bị lặp. Bài kiểm thử có ca điểm thay trong nhà đóng cửa, cần trả về không có phương án và giữ nguyên lịch.

Theo lựa chọn của lãnh đạo ngày 20/11/2026, hai ngày đường dài được bổ sung điểm nghỉ và mốc kết thúc được mở rộng đến 20:00, giữ 30 phút dự phòng. Hai điểm mới dùng 15 phút nghỉ mỗi điểm, Tâm Châu 60 phút. Nếu người dùng chọn tổng nghỉ lớn hơn 90 phút, phần tăng được cộng vào Tâm Châu. Từ 06:00, tổng thời gian tính toán là 12 giờ 38 phút chiều đi và 12 giờ 42 phút chiều về trước thời gian dự phòng. Nếu yêu cầu giờ xuất phát hoặc nghỉ khiến lịch vượt giới hạn, backend báo không có lịch khả thi.

Cảnh Thảo Nguyên công bố mở cửa hằng ngày tại https://tramdungchancanhthaonguyen.com/. Cali Center có hai bảng giờ theo tuần tại https://wanderlog.com/place/details/3410879/cali-center và https://cafecalicenter.restaurants-info.com/. Dùng giao của hai bảng cho khung 06:30–22:00. Giờ và thời gian đi lại có thể thay đổi, cần kiểm tra trước chuyến đi. Trong màn hình nghỉ thêm, người dùng có thể chọn một trong các khoảng nghỉ còn chờ của ngày đó. Những lịch đã lưu theo hạn 18:00 tiếp tục dùng hạn cũ khi điều chỉnh.

Trước khi bàn giao cần thử Gemini qua backend công khai, cài APK rồi mở lại qua 4G và ghi kết quả nghiệm thu T01–T15. Tân giữ bảng kịch bản giờ cố định riêng trong `docs/testing/Overall_Testing_17_11/`.
