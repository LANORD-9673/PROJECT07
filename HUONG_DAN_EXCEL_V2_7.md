# NEXUS 2.7 — tải dữ liệu thành từng cột trong Excel

## Vì sao CSV bị dồn vào cột A?

CSV là văn bản có dấu phân cách. Khi mở trực tiếp, Excel có thể dùng dấu phân cách theo cài đặt máy, khác dấu phẩy của tệp. Khi đó cả dòng hiện trong một ô. Dữ liệu vẫn có thể đọc đúng trên web, nhưng Excel chưa tách các trường.

## Sau khi cập nhật bản 2.7

Trong **Bảo vệ dữ liệu**, sau khi duyệt phương án bảo vệ:

1. Chọn **Tải dữ liệu đã bảo vệ — Excel, mỗi chỉ tiêu một cột**. Mỗi chỉ tiêu là một cột, mỗi hồ sơ là một dòng, mỗi giá trị là một ô.
2. Chọn **Tải bảng đối chiếu chi tiết cho auditor — Excel** để nhận bảng đối chiếu với các cột riêng: Dòng dữ liệu, Tên cột, Cách bảo vệ, Mã hồ sơ gốc, Mã hồ sơ đã bảo vệ, Phương pháp, Giá trị gốc, Giá trị đã bảo vệ.
3. Tệp gốc đã mã hóa vẫn là tệp mã hóa nhị phân. Muốn đọc dữ liệu dạng bảng, dùng bản Excel đã bảo vệ hoặc bảng đối chiếu riêng theo đúng mục đích.

Bản Excel chuyển từ CSV giữ thứ tự cột, số dòng và giá trị. Mã và dữ liệu dạng chuỗi được lưu dưới dạng văn bản để giữ số 0 đầu và mã dài. Tên chỉ tiêu của dữ liệu phân tích được giữ nguyên để có thể nhập lại vào web. Với đầu vào XLSX, nút Excel tiếp tục sử dụng bản đã bảo vệ giữ định dạng nguồn theo các điều kiện hỗ trợ hiện có.

Nút tải CSV đúng định dạng nguồn và bảng đối chiếu CSV vẫn có để tương thích các công cụ khác. Tệp CSV không được đổi đuôi thành XLSX; nút Excel tạo workbook XLSX thực sự.

Bản Excel tạo thêm được giữ tạm trong bộ nhớ phiên để tải, không ghi một bản bảng đối chiếu mới xuống máy chủ. Auditor cần tải và lưu bảng đối chiếu riêng trước khi đóng phiên hoặc reboot ứng dụng.

## Cập nhật mã

Giải nén `Project07_NEXUS_Streamlit_v2.7_FULL.zip`, upload nội dung trong thư mục `Project07_NEXUS_Streamlit_v2.7` lên gốc repo và nhánh Streamlit đang theo dõi. Cần có tệp mới `nexus_exports.py` cùng cấp `streamlit_app.py`, `nexus_review.py`, `nexus_reports.py` và `requirements.txt`. Commit; kiểm tra dưới logo có dòng **NEXUS 2.7 · STREAMLIT**. Giữ Secrets và khóa vault đang dùng.

## Tệp CSV đã tải trước đây

Không cần tải lên web lại chỉ để tách cột. Trong Excel, dùng **Data → From Text/CSV**, chọn tệp và dấu phân cách **Comma (,)** nếu giống ảnh. Với tệp dùng dấu chấm phẩy, chọn **Semicolon (;)**. Chọn UTF-8 nếu tiếng Việt hiển thị sai. Trong bước biến đổi dữ liệu, đặt các cột mã, số điện thoại, giấy tờ và định danh dài thành **Text** trước khi nạp. Kiểm tra kết quả rồi lưu bản mới dạng **Excel Workbook (.xlsx)**; giữ bản CSV ban đầu để đối chiếu.

Không lưu đè sau khi Excel đã tự làm mất số 0 đầu hoặc làm tròn mã dài; hãy nhập lại từ bản CSV gốc với kiểu Text.
