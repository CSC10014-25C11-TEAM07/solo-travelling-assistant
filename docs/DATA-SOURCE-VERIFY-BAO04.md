# Xác minh nguồn — Bảo 04, cập nhật 16/11/2026

Trợ lý đã tra cứu, đối chiếu và cập nhật dữ liệu ở PR #24. Bảo 04 không phải tự
thu thập lại từ đầu. Các mục dưới đây là phần còn cần phản hồi thực tế hoặc quyết
định của nhóm; mẫu hỏi đã soạn sẵn. Chưa gọi điện hoặc gửi tin nhắn cho đơn vị/nhóm.

Dataset: **bao04-mvp-2026-11-16-v1**. Bằng chứng theo từng điểm nằm trong
`backend/data/handoff/source_checks.json`; trạng thái/trường thiếu ở
`backend/data/data_review.json`. Thời điểm đọc nguồn không phải ngày nguồn xuất bản.

## Đã đối chiếu được qua web

| Điểm | Kết quả ngày 16/11 | Cách đưa vào dữ liệu |
|---|---|---|
| P009 Crazy House | [Đơn vị](https://crazyhouse.vn/tham-quan) công bố 08:30–18:00 tất cả các ngày; mô tả có vườn/lối ngoài trời và không gian bên trong. [Cổng tỉnh](https://visitlamdong.vn/vi/bietthuhangnga) nêu 60 phút, đúng địa chỉ 03 Huỳnh Thúc Kháng | Điền lịch tuần; giữ MIXED, 60 phút. Hồ sơ VISIT được đối chiếu đủ trường nên chuyển VERIFIED. 60 phút là ước tính của cổng tỉnh, không phải thời lượng tối thiểu cam kết. Không dùng làm điểm INDOOR cho mưa |
| R003 Tâm Châu | [Trang liên hệ đơn vị](https://www.tamchaucenter.com/lien-he) xác nhận 294A Trần Phú; phần liên hệ ghi thứ 2–CN 07:00–22:00, footer lại 06:30–22:00 | Ghi nhận cả hai; giữ weekly null/UNVERIFIED và bốn chặng liên quan UNVERIFIED. Tọa độ tâm khung nhìn bản đồ nhúng không phải pin cổng |
| P005 Bảo tàng | [Liên hệ](https://baotanglamdong.com.vn/contact) và header ghi 07:30–17:30; mục thông tin trên [trang vé](https://baotanglamdong.com.vn/tickets) ghi hằng ngày 08:00–17:00 | Bổ sung xung đột ngay trong website đơn vị; không tự chọn một khung hoặc lấy giao hai khung làm giờ được xác nhận. Giữ weekly null/UNVERIFIED |
| P001 Ga Đà Lạt | [Cổng tỉnh](https://visitlamdong.vn/vi/nhagadalat): 01 Quang Trung, 07:00–17:30, 90 phút | Đọc lại và giữ 90 phút; giờ chung chưa xác nhận lịch từng thứ/tiếp cận 06:00. Ga là mốc tập kết, không phải nơi ngủ |
| P010 Still Cafe | [Cổng tỉnh](https://visitlamdong.vn/vi/stillcafe): 59 Nguyễn Trãi, 07:00–22:00; không có thời lượng trải nghiệm | Giữ lịch OSM đã lưu và nguồn đối chiếu; không tự điền 45/60 phút hoặc gắn INDOOR |
| P011 An CaFe | [Website đơn vị](https://www.ancafeglobal.com/) xác nhận 63Bis Ba Tháng Hai; nội dung chữ không nêu lịch tuần/thời lượng | Cập nhật nguồn định danh; giữ nhãn UNVERIFIED và ngày đọc cũ của riêng tag giờ OSM. Không nhầm với An Coffee ở 30 Hoàng Diệu |

Giờ P009 khác portal (07:30–19:00) và OSM cũ (08:30–19:00). Quyết định có căn cứ:
dùng lịch dịch vụ tham quan do chính cơ sở công bố rõ cho tất cả ngày trong tuần;
giữ nguyên các giá trị khác và lý do chọn nguồn trong `source_checks.json`. Không
khẳng định website đơn vị có ngày xuất bản mới hơn hoặc giờ tương lai được bảo đảm.
VERIFIED của một hồ sơ VISIT không làm cả tuyến đủ điều kiện; hai tuyến vẫn BLOCKED.

## Phần cần xác nhận với đơn vị

Các số dưới đây là số liên hệ công khai của cơ sở tại URL đi kèm. Có thể hỏi qua
điện thoại hoặc kênh chính thức; không cần đi khảo sát nếu đơn vị cung cấp đủ thông
tin. Không biến một cuộc gọi chưa thực hiện thành bằng chứng đã xác minh.

**1. Tâm Châu — 0263 3866 904**, [nguồn liên hệ](https://www.tamchaucenter.com/lien-he).

> Em đang làm đồ án lập lịch xe máy, cần đối chiếu Nhà hàng Tâm Châu 294A Trần Phú,
> Bảo Lộc. Website có giờ 07:00–22:00 và 06:30–22:00; lịch đón khách từng ngày hiện
> tại là khung nào, có nghỉ trưa/ngày nghỉ không? Anh/chị cho em xin pin đúng cổng
> xe máy, chỗ gửi xe và cách tiếp cận từ cả hai chiều tuyến TP.HCM–Đà Lạt. Khách đi
> lẻ có thể dừng ăn/nghỉ khoảng 60 phút ở đó không?

**2. Bảo tàng — 02633 812 624**, [nguồn liên hệ](https://baotanglamdong.com.vn/contact).

> Em cần đối chiếu cơ sở 04 Hùng Vương, Đà Lạt. Lịch thứ 2 đến chủ nhật hiện là
> khung nào, có nghỉ trưa/ngày nghỉ không? Trang liên hệ ghi 07:30–17:30 nhưng trang
> đặt vé ghi 08:00–17:00. Khi mưa, khu trưng bày nào hoàn toàn có mái và được phép
> tham quan? Thời lượng 120 phút trên cổng du lịch là toàn điểm hay riêng khu này?

**3. Still — 0368 151 215**, [nguồn liên hệ](https://visitlamdong.vn/vi/stillcafe).

> Em đang đối chiếu Still Cafe 59 Nguyễn Trãi. Giờ từng ngày có phải 07:00–22:00
> và có ngoại lệ/nghỉ trưa không? Có khu ngồi trong nhà được dùng khi mưa không?
> Quán có hoạt động/thời lượng trải nghiệm cố định hay khách tự chọn thời gian ngồi?

**4. An CaFe**: dùng kênh liên hệ trên [website đơn vị](https://www.ancafeglobal.com/),
nêu đúng **63Bis Ba Tháng Hai**. Hỏi cùng các mục giờ tuần, thời lượng và phạm vi có
mái như Still. Không chép một số điện thoại có định dạng bất thường từ website thành
liên hệ đã xác nhận. Dinh III cần xác nhận lịch nghỉ trưa qua kênh chính thức; chưa
chọn giờ portal thay cho lịch OSM đang khác nhau.

Nếu quán không có thời lượng cố định, nhóm có thể chốt thời gian dự kiến cho lịch.
Ghi đó là **tham số lập lịch do nhóm chọn**, không ghi “quán xác nhận thời lượng”.
Hiện tại chưa có quyết định này, nên `visit_duration_minutes` của P010/P011 vẫn null.

Ghi kết quả theo mẫu dưới, chỉ điền sau khi nhận phản hồi:

```text
place_id / đúng tên và địa chỉ:
URL/kênh đơn vị, ngày giờ kiểm tra (ghi rõ múi giờ):
Thứ 2 / 3 / 4 / 5 / 6 / 7 / CN: từng khoảng mở cửa, kể cả nghỉ trưa:
Ngoại lệ/ngày lễ hoặc chưa được xác nhận:
Khu vực áp dụng / môi trường / thời lượng (nguồn hay tham số đề xuất):
Pin cổng / chỗ dừng xe / điều kiện tiếp cận nếu có:
Tóm tắt phản hồi và bằng chứng công khai:
Mục vẫn chưa rõ:
```

Trợ lý có thể chuyển kết quả này vào JSON, kiểm nhãn, thu đúng chặng và chạy lại
validator/audit. Chỉ giữ thông tin nghiệp vụ cần thiết; không lưu số riêng hoặc
thông tin cá nhân của người trả lời.

## Hai quyết định cần nhóm chốt

**Nơi ngủ và điểm đầu/cuối.** Đã tìm được một ứng viên có nguồn ngay trong khu vực
dữ liệu hiện có: [Crazy House có lưu trú](https://crazyhouse.vn/), 03 Huỳnh Thúc
Kháng. [Chính sách](https://crazyhouse.vn/chinh-sach) nêu nhận phòng từ 14:00, trả
phòng không muộn hơn 12:00. Đây chỉ là **ứng viên**, chưa chọn/đặt phòng, chưa xác
nhận còn phòng hoặc cổng vào sớm/muộn. Nhóm có thể chọn nơi khác.

Sau khi chọn, cần xác nhận địa chỉ/cổng, giờ ra/vào, đỗ xe, tọa độ và chặng tới/từ
điểm đầu/cuối mỗi ngày. Không lấy giờ tham quan P009 làm giờ khách lưu trú; không
đổi ga thành homestay hoặc tự dùng chung ID khi hai loại quyền tiếp cận khác nhau.
H001 cũng cần chốt vị trí tập kết/đỗ xe và quyền tiếp cận lúc 06:00.

**Ngân sách thời gian tuyến.** Cấu hình hiện tại có cận dưới ngày đi:

```text
06:00 + H001→R003 380 phút + REST 60 phút + R003→P001 237 phút = 17:17
```

Đã vượt hạn đề xuất 17:00 ít nhất 17 phút, chưa tính chặng tới chỗ ngủ/buffer. Đây
là phép tính có điều kiện vì tọa độ cổng R003 còn thiếu; không phải giờ đến được
bảo đảm. Ngày về tương ứng cận dưới 17:19 so với hạn 18:00. Cần chốt lại tuyến/điểm
nghỉ và ngân sách giờ có buffer; không rút ngắn chặng hoặc nới hạn trong dữ liệu để
báo PASS. Giữ cấu hình đang có cho tới khi nhóm quyết định.

Tin nhắn đề xuất để Bảo 04 chuyển cho nhóm (chưa gửi):

> Mình đã cập nhật nguồn ngày 16/11 ở PR #24. Crazy House đã đối chiếu đủ hồ sơ VISIT;
> các điểm còn thiếu/xung đột đều có nguồn và câu hỏi sẵn. Nhờ nhóm chốt nơi lưu trú,
> vị trí tập kết H001 và cách xử lý ngày đi có cận dưới 17:17 vượt hạn đề xuất 17:00
> trước buffer/chặng tới nơi ngủ. Xin chốt thêm ngân sách thời gian trải nghiệm
> Still/An nếu quán không quy định. Khi có quyết định, mình bổ sung dữ liệu/chặng và
> chạy lại audit; hiện hai tuyến nguồn vẫn BLOCKED.

Điểm nghỉ/mốc đầu-cuối không có VISIT không được điền giả thời lượng 1 phút để qua
schema. `Place` hiện yêu cầu thời lượng tham quan khi gắn VERIFIED
(`backend/place_models.py`); nếu cần biểu diễn một anchor chỉ dùng để REST/tập kết,
ghi rõ vấn đề để nhóm thống nhất với chủ schema, không tự đổi hợp đồng.
