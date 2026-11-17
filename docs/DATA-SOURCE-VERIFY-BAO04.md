# Xác minh nguồn — Bảo 04, cập nhật 17/11/2026

Trợ lý đã tra cứu, đối chiếu và cập nhật dữ liệu ở PR #24. Bảo 04 không phải tự
thu thập lại từ đầu. Bảo 04 đã chốt toàn bộ lựa chọn cấu hình ngày17/11. Các mục còn thiếu
là dữ kiện thực tế của đơn vị; mẫu hỏi đã soạn sẵn. Chưa gọi điện hoặc gửi tin nhắn cho đơn vị/nhóm.

Dataset: **bao04-mvp-2026-11-17-v1**. Bằng chứng theo từng điểm nằm trong
`backend/data/handoff/source_checks.json`; trạng thái/trường thiếu ở
`backend/data/data_review.json`. Thời điểm đọc nguồn không phải ngày nguồn xuất bản.

## Đã đối chiếu được qua web

| Điểm | Kết quả ngày 16/11 | Cách đưa vào dữ liệu |
|---|---|---|
| P009 Crazy House | [Đơn vị](https://crazyhouse.vn/tham-quan) công bố 08:30–18:00 tất cả các ngày; mô tả có vườn/lối ngoài trời và không gian bên trong. [Cổng tỉnh](https://visitlamdong.vn/vi/bietthuhangnga) nêu 60 phút, đúng địa chỉ 03 Huỳnh Thúc Kháng | Điền lịch tuần; giữ MIXED, 60 phút. Hồ sơ VISIT được đối chiếu đủ trường nên chuyển VERIFIED. 60 phút là ước tính của cổng tỉnh, không phải thời lượng tối thiểu cam kết. Không dùng làm điểm INDOOR cho mưa |
| R003 Tâm Châu | [Trang liên hệ đơn vị](https://www.tamchaucenter.com/lien-he) xác nhận 294A Trần Phú; phần liên hệ ghi thứ 2–CN 07:00–22:00, footer lại 06:30–22:00 | Ghi nhận cả hai; giữ weekly null/UNVERIFIED và bốn chặng liên quan UNVERIFIED. Tọa độ tâm khung nhìn bản đồ nhúng không phải pin cổng |
| P005 Bảo tàng | [Liên hệ](https://baotanglamdong.com.vn/contact) và header ghi 07:30–17:30; mục thông tin trên [trang vé](https://baotanglamdong.com.vn/tickets) ghi hằng ngày 08:00–17:00 | Bổ sung xung đột ngay trong website đơn vị; không tự chọn một khung hoặc lấy giao hai khung làm giờ được xác nhận. Giữ weekly null/UNVERIFIED |
| P001 Ga Đà Lạt | [Cổng tỉnh](https://visitlamdong.vn/vi/nhagadalat): 01 Quang Trung, 07:00–17:30, 90 phút | Đọc lại và giữ 90 phút; giờ chung chưa xác nhận lịch từng thứ/tiếp cận 06:00. Ga là mốc tập kết, không phải nơi ngủ |
| P010 Still Cafe | [Cổng tỉnh](https://visitlamdong.vn/vi/stillcafe): 59 Nguyễn Trãi, 07:00–22:00; không có thời lượng trải nghiệm | Giữ lịch OSM và nguồn đối chiếu; ngày17/11 Bảo04 chọn VISIT60 phút làm ngân sách, không phải quán xác nhận. Môi trường vẫn null/UNVERIFIED |
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

Nếu quán không có thời lượng cố định, Bảo 04 có thể chốt thời gian dự kiến cho lịch.
Ghi đó là **tham số lập lịch do Bảo 04 chọn**, không ghi “quán xác nhận thời lượng”.
Ngày17/11 Bảo04 đã chốt60 phút cho P010/P011; catalog đã điền, provenance
ở `planning_decision` trong source_checks/data_review. Hai điểm vẫn UNVERIFIED
vì thiếu môi trường/xác nhận giờ; REST tính thêm riêng.

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

## Cấu hình Bảo 04 đã chốt và áp dụng 17/11

[Quyết định và evidence](testing/source-route-proposal.json) có trạng thái **APPLIED**,
`applied_to_catalog_or_routes:true`. Không còn chờ nhóm hoặc Bảo04 chốt các tham số này.

| Mục | Giá trị đã áp dụng |
|---|---|
| Nơi ngủ mẫu | L001 Crazy House, 03 Huỳnh Thúc Kháng; tách P009 VISIT, không lập VISIT tại L001 |
| Thời lượng Still/An | VISIT 60 phút mỗi điểm do Bảo04 chọn; REST cộng riêng, không phải quán xác nhận |
| Hạn ngày đi/về | 18:00; ngày nội vùng 17:00 |
| Dự phòng | 30 phút/ngày ngoài REST tối thiểu 60 phút/ngày; audit dành khoản này trước deadline |
| Chặng lưu trú | P001→L001:452.109 giây→8 phút,3.055 km; L001→P001:433.679 giây→8 phút,3.054 km. Thu17/11 độc lập từng chiều, đều UNVERIFIED |
| Tuyến3/4ngày và nhánh mưa | Đủ chặng có hướng đến/về L001 qua P001; không còn MISSING_LEG |

[Địa chỉ](https://crazyhouse.vn/contact) và [chính sách](https://crazyhouse.vn/chinh-sach)
đã đọc lại17/11: nhận phòng từ14:00, trả phòng không muộn hơn12:00. Các thông tin này
**không xác nhận** pin cổng khách lưu trú, ra/vào06:00, đỗ xe hoặc còn phòng ngày mẫu.
Không đặt phòng/gửi liên hệ. Cổng/weekly của L001 giữ null, nguồn tọa độ chỉ là tham
chiếu khu tham quan P009 từ OSM. Không lấy giờ VISIT08:30–18:00 làm giờ khách lưu trú.
Chặng đề xuất P001→P009 thu16/11 được giữ riêng làm lịch sử, không nhập thành chặng L001.
Hai chặng L001 dùng query/evidence17/11 đúng ID, không suy chiều ngược hoặc tạo travel0.

Các đêm đều kết thúc/bắt đầu tại L001. Ngày nội vùng bắt đầu08:00, ngày đi/về06:00;
H001 vẫn là mốc tập kết/điểm cuối TP.HCM của cấu hình, chưa xác nhận chỗ dừng/tiếp cận.
P001 là mốc đi qua/tham quan, không phải nơi ngủ; cần quyền tiếp cận sớm/cận cuối ngày.

Ngân sách cận dưới đã tính chặng nơi ngủ và dự phòng:

```text
Ngày đi: 06:00 + 380 + REST60 + 237 + 8 + buffer30 = 17:55 (hạn18:00)
Ngày về: 06:00 + 8 + 236 + REST60 + 383 + buffer30 = 17:57 (hạn18:00)
```

Còn5/3 phút ngoài khoản dự phòng30 phút. Phép tính này phụ thuộc tọa độ tham chiếu
R003/L001 và chưa tính WAIT khi giờ/quyền tiếp cận còn thiếu. Buffer không bảo đảm
traffic/an toàn hoặc giờ đến. Không rút ngắn chặng hoặc REST để báo PASS.

Audit vẫn báo **ready=false**,42/55 gaps của tuyến3/4ngày (có lặp theo ngày).
`conditional_lower_bound_finish_including_buffer` là cận dưới, không phải lịch đầy đủ;
`conditional_finish_including_buffer` vẫn null do giờ nghỉ/tham quan chưa rõ.
Audit tính buffer cho deadline nhưng không tạo loại activity mới trong F02/F05;
không sửa engine, HTTP hoặc SQLite của các bạn khác.

Việc còn cần phản hồi thực tế: pin/giờ/tiếp cận R003; cổng/ra vào/đỗ xe/còn phòng L001;
H001/P001 ngoài giờ; lịch mâu thuẫn P005/P008 và môi trường/giờ Still/An. Thời lượng
Still/An và lựa chọn nơi ngủ/hạn/buffer đã xong, không yêu cầu chốt lại.

Điểm nghỉ/mốc không có VISIT giữ duration null, không điền giả1 phút để gắn VERIFIED.
`Place` hiện đòi duration/weekly đủ cho VERIFIED (`backend/place_models.py`); L001
hợp lệ dưới nhãn UNVERIFIED với interests rỗng nên không lọt vào gợi ý F01.
