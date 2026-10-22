# Review nhanh — NEXUS 2.6

## Cập nhật lên GitHub

1. Giải nén `Project07_NEXUS_Streamlit_v2.6_FULL.zip` trên máy.
2. Mở thư mục `Project07_NEXUS_Streamlit_v2.6`, upload **nội dung bên trong** vào gốc repo và nhánh mà ứng dụng Streamlit đang theo dõi. Không upload nguyên ZIP hoặc thêm một tầng thư mục ngoài.
3. Upload đủ tệp và thư mục trong gói. Đặc biệt cần thay `streamlit_app.py`, `nexus_ui.py`, và thêm **`nexus_review.py`** ở cùng cấp với `requirements.txt`.
4. Commit rồi kiểm tra ứng dụng đã cập nhật. Nếu cần, reboot trong trang quản lý Streamlit. Dòng dưới logo sẽ là **NEXUS 2.6 · STREAMLIT**.
5. Giữ Secrets, khóa vault và dữ liệu hiện tại. Bản cập nhật này không thay quy tắc Python, hash tài liệu demo hoặc cấu hình API; không cần tạo khóa mới.

## Dùng bộ lọc và danh sách đã chọn

Vào **Kiểm tra và ngoại lệ**, chọn đúng cuộc kiểm toán đã có kết quả:

- Mặc định chỉ hiển thị **Ngoại lệ** và **Chưa đủ thông tin**, trạng thái **Chờ review**.
- Có thể lọc thêm T01, T02, T03, hoặc thay loại kết quả/trạng thái. Muốn xem toàn bộ, chọn tất cả giá trị trong ba bộ lọc. Bỏ hết lựa chọn trong một bộ lọc sẽ không hiển thị kết quả nào.
- Bấm **Chọn tất cả kết quả đã lọc**, hoặc chọn từng mục trong danh sách. **Bỏ chọn tất cả** chỉ bỏ danh sách xem xét.
- Dùng **Kết quả tiếp theo / Kết quả trước**, hoặc chọn trực tiếp một mục để đọc bằng chứng.
- Với từng kết quả, chọn người review, ghi căn cứ, kết luận phù hợp, xác nhận đã đối chiếu bằng chứng rồi bấm **Lưu review**.
- Nếu đang lọc Chờ review, mục vừa lưu sẽ rời danh sách; các mục đã chọn còn phù hợp bộ lọc được giữ lại. Nếu không còn mục nào, đổi bộ lọc để tiếp tục xem.

**Chọn tất cả không tự xác nhận, không lưu review hàng loạt và không tạo phát hiện kiểm toán.** Các chốt rà soát, ghi nhận người review và bảo vệ báo cáo hiện có vẫn được áp dụng qua cùng API review từng kết quả.

## Hiểu hai bộ đếm

- **Ngoại lệ còn chờ xử lý**: kết quả Ngoại lệ chưa Đã xác nhận hoặc Không chấp nhận.
- **Chưa đủ thông tin còn chờ xử lý**: đếm riêng kết quả thiếu thông tin chưa kết thúc review.
- Cả hai bộ đếm gồm Chờ review và Cần làm rõ thêm, tính trên toàn cuộc kiểm toán, không chỉ các dòng đang lọc.
- Chọn Cần làm rõ thêm chưa kết thúc xử lý, nên số chờ xử lý không giảm. Để xem các mục đó, chọn thêm trạng thái này trong bộ lọc.
- Xác nhận kết quả Đạt yêu cầu không làm giảm số ngoại lệ. Duyệt một phát hiện kiểm toán cũng không xóa phát hiện khỏi tổng số.

## Những điểm giữ nguyên

Thiếu thông tin không tự trở thành vi phạm. Cần kiểm tra dữ liệu và căn cứ trước khi kết luận. Xác nhận một kết quả thiếu thông tin chỉ ghi nhận đánh giá đó, không tự bổ sung dữ liệu hoặc biến nó thành ngoại lệ để sinh finding. Tệp Word tải từ trang kết quả vẫn chứa toàn bộ kết quả của cuộc kiểm toán, không chỉ danh sách đã lọc.

Giao diện dùng tên reviewer tự khai, chưa thay thế đăng nhập hoặc chữ ký số. Dữ liệu và quyết định review lưu theo cơ chế hiện có; danh sách chọn/bộ lọc là trạng thái phiên, không phải cơ chế sao lưu bền vững.
