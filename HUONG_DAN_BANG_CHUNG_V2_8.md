# NEXUS 2.8 — Xem dòng bằng chứng trong phần review

## Cập nhật trên GitHub và Streamlit

1. Giải nén Project07_NEXUS_Streamlit_v2.8_FULL.zip.
2. Upload toàn bộ nội dung BÊN TRONG thư mục Project07_NEXUS_Streamlit_v2.8 vào gốc repo hiện tại, thay các file trùng tên. Không upload nguyên ZIP hoặc tạo thêm một tầng thư mục ngoài.
3. Commit, giữ nguyên Secrets hiện có và reboot ứng dụng Streamlit. Entry point vẫn là streamlit_app.py (hoặc main.py alias ở gốc). Kiểm tra dưới logo có NEXUS 2.8 · STREAMLIT.
4. Bản này không đổi policy, dữ liệu mẫu, hash phê duyệt hoặc khóa vault. Không tạo lại khóa chỉ để cập nhật tính năng xem bằng chứng. Không đưa khóa thật lên GitHub.

Nếu chỉ thay các file liên quan, cần đủ: streamlit_app.py, nexus_evidence.py (mới), nexus_ui.py, backend/services/rule_engine/api.py và backend/main.py. Khuyến nghị dùng gói đầy đủ để tránh thiếu module.

## Cách sử dụng

1. Vào Kiểm tra và ngoại lệ; chạy T01–T03 nếu chưa có kết quả.
2. Lọc Ngoại lệ hoặc Chưa đủ thông tin và Chờ review, rồi chọn hồ sơ cần xem.
3. Ngay dưới bảng tham chiếu/mã kết quả, bấm **Xem dòng bằng chứng**.
4. Đọc tên file, phiên bản, vị trí dòng và mã bằng chứng. Bảng Chỉ tiêu cần đối chiếu / Giá trị trong file hiển thị các giá trị thực tế cần cho thủ tục.
5. Mở **Xem toàn bộ dòng** để xem mọi cột của bản ghi, mã snapshot và SHA256 của file.
6. Với T02, đọc cả dòng bảng phân quyền được liên kết, gồm nhân sự, chi nhánh, chức danh, hạn mức và thời gian hiệu lực. Nếu chưa có dòng phân quyền được liên kết, màn hình cảnh báo, không tự chọn một bản phân quyền khác để kết luận.
7. Sau khi đối chiếu nguồn và quy định, chọn người review, ghi căn cứ và lưu kết luận. Xem bằng chứng hoặc Chọn tất cả không tự xác nhận hay thay đổi kết quả.
8. Bấm **Ẩn dòng bằng chứng** để thu gọn. Mỗi kết quả có trạng thái mở riêng; đổi lựa chọn không hiển thị nhầm dòng của kết quả trước.

## Dữ liệu hiển thị có ý nghĩa gì?

- Đây là bản ghi đã lưu khi nhập file, thuộc phiên bản được cuộc kiểm toán sử dụng. Nhập file mới sau đó không thay thế bằng chứng của cuộc kiểm toán cũ.
- Mã bằng chứng là mã tham chiếu liên kết kết quả với nguồn, không phải mật khẩu hay nội dung hồ sơ được mã hóa trong mã đó.
- Dòng hiển thị là vị trí bản ghi được hệ thống đánh số khi nhập, tính cả dòng tiêu đề. Nếu file gốc có dòng trống, nhiều dòng trong một ô hoặc đã sắp xếp lại, đối chiếu thêm mã hồ sơ; không chỉ dựa vào số dòng vật lý trong trình soạn thảo.
- Ô trống được ghi **Thiếu dữ liệu (ô trống)**; giá trị 0 vẫn hiển thị 0. Không tự điền dữ liệu còn thiếu hoặc suy đoán vi phạm.
- Giữ nguyên chuỗi mã, số 0 ở đầu và dữ liệu thay mã/che thông tin. Chức năng không giải mã vault hoặc sử dụng bảng đối chiếu riêng để phục hồi danh tính khách hàng.
- Dữ liệu hiển thị không được gửi thêm cho Gemini. Chức năng này đọc nội bộ, không dùng hạn ngạch LLM.
- Mở dòng dữ liệu giúp kiểm tra đầu vào; kiểm toán viên vẫn phải đối chiếu chính sách và chứng từ nghiệp vụ cần thiết. Một dòng CSV không tự chứng minh chứng từ gốc là xác thực.
- Tính năng này không bổ sung xác thực người dùng hoặc phân quyền production. Tiếp tục chỉ sử dụng dữ liệu giả lập trên bản demo công khai.

## Kỹ thuật và kiểm thử

API đọc: GET /api/audit-runs/{run_id}/results/{result_id}/evidence.
Truy vấn kiểm tra đúng run, kết quả, snapshot và vị trí dòng được liên kết; không chuyển sang file mới nhất. Không sửa dữ liệu, review hoặc bản nháp phía sau. Dùng được với kết quả đã lưu trước bản 2.8 nếu snapshot liên quan còn tồn tại; không cần chạy lại LLM chỉ để xem bằng chứng.
