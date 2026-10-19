# Cập nhật ứng dụng Streamlit hiện tại

## 1. Sao lưu và thay mã trên GitHub

Tải một bản sao repo trước khi thay. Giữ riêng Secrets đang dùng, khóa vault và dữ liệu cần lưu; không đưa các giá trị này lên GitHub.

Giải nén Project07_NEXUS_Streamlit_v2.4_FULL.zip. Upload nội dung bên trong thư mục Project07_NEXUS_Streamlit_v2.4 vào gốc repo LANORD-9673/PROJECT07_AI-Internal-Audit-Platform. Không upload nguyên ZIP và không thêm tầng thư mục ngoài.

Gốc repo cần có:

```text
streamlit_app.py
streamlit_runtime.py
nexus_ui.py
main.py
requirements.txt
.streamlit/config.toml
assets/
backend/
demo/
data/
contracts/
scripts/
```

Có thể bỏ các file giao diện React cũ như frontend/, Dockerfile và hướng dẫn React nếu bạn chỉ dùng Streamlit. Những file trùng tên phải được thay bằng bản mới trong gói này. Đừng xóa backend/, demo/, data/ hoặc contracts/: ứng dụng cần chúng. Không chọn backend/main.py làm file khởi chạy Streamlit.

Trên GitHub: Add file → Upload files → kéo nội dung gói → Commit changes. Đảm bảo requirements.txt nằm ở gốc. Nếu trong repo cũ vẫn có requirements.txt khác cạnh entrypoint đang dùng, Streamlit có thể chọn nhầm bộ phụ thuộc; dùng đúng entrypoint ở gốc như bước 2.

## 2. Kiểm tra đúng ứng dụng triển khai

Trong Streamlit Community Cloud, kiểm tra ứng dụng đang theo dõi đúng repo và nhánh vừa commit. File khởi chạy cần là **streamlit_app.py** ở gốc repo. Gói cũng có main.py ở gốc làm alias tương thích nếu ứng dụng trước đây chọn main.py. Không cần tạo link React hoặc Render.

Giữ Secrets cũ trong phần quản lý app. Reboot sau khi commit và cập nhật cấu hình. Nếu bản cũ vẫn hiện, kiểm tra log: đúng repo, branch, entrypoint và commit mới chưa. Trang mới hiện dòng **NEXUS 2.4 · STREAMLIT** phía dưới logo. Không chỉ dựa vào việc reboot để biết đã chạy bản mới.

## 3. Cấu hình bộ demo mới

Nút Import bộ demo 10 khách hàng dùng:
- POL-LOAN-01_compact.txt
- loans_10.csv
- authorities_10.csv

Policy rút gọn và authority có hash khác bộ cũ. Nhóm phải đọc và đối chiếu hai tài liệu, sau đó mới cập nhật PROJECT07_APPROVED_BASELINE_SHA256, PROJECT07_APPROVED_AUTHORITY_SHA256 và PROJECT07_AUTHORITY_APPROVAL_REFERENCE trong Secrets. Xem SECRETS_MAU.toml. Giữ nguyên GEMINI_API_KEY, model đang dùng được và PROJECT07_VAULT_MASTER_KEY nếu dùng kho cũ.

Mã biên bản phải là xác nhận thực tế của nhóm; không coi mẫu cấu hình là phê duyệt. Khi dùng Word hoặc Excel thay TXT/CSV, lấy hash đúng định dạng trong demo/SHA256_DEMO_10.json. File thay mã có hash mới, cần đối chiếu lại. Upload không tự phê duyệt baseline.

Luồng: Import demo → Tạo Audit Run → RCM và review → Test Plan và review → Tests & Exceptions → review ngoại lệ → Findings → Report. Có 3 ngoại lệ cài sẵn, 2 kết quả thiếu thông tin; đáp án nằm riêng trong demo/ANSWER_KEY_DEMO_10.md.

## 4. Xóa dữ liệu đã nhập

Dữ liệu & Audit Run → Quản lý file đã import → chọn File cần xóa → xác nhận → Xóa file đã import. Nguồn đang gắn vào một cuộc kiểm toán không cho xóa. Nút xóa lựa chọn ở trang Bảo vệ chỉ dọn dữ liệu tạm của phiên, không xóa archive trong vault. Reboot cũng không được xem là thao tác xóa toàn bộ lịch sử hoặc sao lưu.

## 5. Chạy tại máy nếu cần

Cài Python 3.12, giải nén và chạy START_NEXUS.bat. Hoặc mở terminal tại thư mục có streamlit_app.py:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Cấu hình bí mật cục bộ trong .streamlit/secrets.toml; không upload file này lên GitHub. Nếu tạo vault demo mới, dùng scripts/generate_vault_key.py. Không thay khóa cho vault cũ.

## Giới hạn

Chưa có đăng nhập/phân quyền; tên reviewer là lựa chọn tự khai, FINAL vẫn bị chặn. Vault local của Community Cloud không được xem là lưu trữ bền vững. Gemini còn phụ thuộc key, project, model và tải phía Google; không có kết quả AI giả để thay khi API lỗi.
