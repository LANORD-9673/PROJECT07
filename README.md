# NEXUS 2.2 dành cho Streamlit

Chạy ứng dụng bằng **streamlit_app.py** ở gốc repo. Gói này không cần React, Node.js hoặc dịch vụ FastAPI riêng.

Đọc [HUONG_DAN_CAP_NHAT_STREAMLIT.md](HUONG_DAN_CAP_NHAT_STREAMLIT.md) trước khi thay mã.

Bản mới gồm bộ 10 khách hàng, policy Word/TXT, authorities Excel/CSV, xóa nguồn chưa dùng, logo alpha và loading riêng, chế độ sáng/tối, menu đầy đủ và dropdown reviewer.

Windows: nhấp START_NEXUS.bat sau khi giải nén và cài Python 3.12.
Streamlit Community Cloud: Repository LANORD-9673/PROJECT07_AI-Internal-Audit-Platform, nhánh đang triển khai, main file streamlit_app.py.

Dữ liệu cũ có thể vẫn còn trong cơ sở dữ liệu đang chạy sau reboot; cập nhật mã không tự xóa lịch sử. Vào Dữ liệu & Audit Run để quản lý snapshot. File đã gắn Run được giữ để truy vết. Bộ demo cũ trong thư mục demo phục vụ regression; nút import trên web chỉ dùng bộ 10 khách hàng.
