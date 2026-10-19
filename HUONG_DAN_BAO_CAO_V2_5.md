# NEXUS 2.5 — nội dung dễ đọc và báo cáo đánh giá

## Bảo vệ dữ liệu

Chọn file, mã hóa, sau đó review cách bảo vệ từng cột bằng các lựa chọn: Thay bằng mã giả, Che giá trị, Giữ nguyên. Các lựa chọn tiếng Việt được chuyển về đúng phương pháp xử lý của backend. Dữ liệu tải xuống vẫn giữ định dạng nguồn; auditor tải riêng bảng đối chiếu có tiêu đề tiếng Việt và biên bản bảo vệ Word. Biên bản không chứa giá trị gốc từng ô; bảng đối chiếu chứa giá trị gốc và cần lưu riêng. Không gửi bảng đối chiếu vào AI.

## Cuộc kiểm toán

Chọn tài liệu bằng tên, loại và phiên bản. Ngày/giờ hiệu lực nhập bằng bộ chọn ngày giờ theo giờ Việt Nam. Danh sách file, ma trận rủi ro, kế hoạch kiểm tra, kết quả, căn cứ và bằng chứng hiện thành bảng/đoạn văn tiếng Việt. Trạng thái và nguyên nhân kiểm tra được diễn giải; mã hồ sơ và mã bằng chứng vẫn được giữ để tra cứu. Tài liệu từng bước có thể tải Word.

## Đánh giá và hồ sơ

Chọn đúng cuộc kiểm toán, mở Đánh giá và hồ sơ rồi bấm Tải báo cáo đánh giá Word. Báo cáo lấy dữ liệu đã lưu của cuộc kiểm toán và không gọi thêm Gemini. Bao gồm:
- Thông tin nhận dạng báo cáo và thời điểm lập theo giờ Việt Nam.
- Kết luận về các bước còn thiếu và tổng số lượt kiểm tra, hồ sơ, ngoại lệ.
- Trạng thái review, người review và thời điểm được ghi nhận.
- Số liệu kiểm tra theo từng nhóm kết quả.
- Chỉ tiêu trích dẫn, độ phủ thủ tục, liên kết bằng chứng, kèm giải thích giới hạn.
- Công việc còn cần xử lý và vai trò đề xuất xử lý, không tự gán danh tính hay cam kết hạn hoàn thành.
- Đối chứng 18 tình huống quy tắc Python, tách khỏi đánh giá chất lượng AI thực tế.
- Giới hạn và phụ lục nguồn tài liệu, lịch sử AI, nhật ký kiểm toán.

Tỷ lệ chưa đủ dữ liệu sẽ ghi Chưa có dữ liệu, không tự coi là 0% hoặc 100%. Độ chính xác nghiệp vụ và mức bám sát nguồn của AI chưa được đo bằng đáp án độc lập. File Word là mẫu báo cáo nghiệp vụ của NEXUS, chưa được chứng nhận theo một chuẩn kiểm toán cụ thể. Auditor cần review trước khi sử dụng; app vẫn chặn phát hành chính thức vì demo chưa có xác thực/phân quyền.

## Cập nhật ứng dụng

Giải nén gói 2.5, upload toàn bộ nội dung bên trong thư mục lên gốc GitHub, ghi đè các file trùng tên, commit và reboot Streamlit. Giữ Secrets đang dùng. Kiểm tra dòng NEXUS 2.5 · STREAMLIT. Entry point vẫn là streamlit_app.py. File nexus_reports.py mới nằm ở gốc và phải được upload cùng gói.
