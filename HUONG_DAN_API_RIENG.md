# API Gemini riêng và tên reviewer tùy chọn — NEXUS 2.4

## API key riêng

1. Mở mục **API Gemini của bạn** ở thanh bên.
2. Nhập Gemini API key của bạn vào ô mật khẩu rồi bấm **Dùng key này cho phiên hiện tại**.
3. Vào **Vai trò & cấu hình** và bấm **Kiểm tra key và danh sách model**. Đọc được danh sách model chưa chứng minh generateContent còn quota.
4. Quay lại **đúng Audit Run** đang làm và thử lại **Tạo findings bằng LLM**. Không cần tạo lại RCM/Test Plan hoặc chạy lại Python khi các kết quả đó đã được lưu.

Key riêng được ưu tiên cho mọi bước LLM và kiểm tra model trong phiên đó. Key chỉ lưu tạm trong RAM của phiên; không ghi vào database, audit trail, file xuất hoặc biến môi trường dùng chung. Ô nhập che ký tự và được làm trống sau khi gửi. Key vẫn được gửi qua máy chủ app tới Google để thực hiện yêu cầu. Kết thúc phiên có thể cần nhập lại; bấm nút xóa key để bỏ key khỏi phiên ngay.

Nếu key riêng lỗi, app hiển thị lỗi, không tự chuyển sang key chủ ứng dụng. Bấm **Xóa key riêng và dùng cấu hình ứng dụng** để quay về key trong Streamlit Secrets (nếu có). Khóa vault và cấu hình phê duyệt baseline vẫn do chủ app quản lý.

Hạn mức Gemini tính theo Google project. Key mới trong cùng project không tăng quota. Project của key riêng cũng có thể gặp 429 nếu hết hạn mức hoặc giới hạn model. Model riêng có thể chọn hoặc nhập ở thanh bên; nếu không chọn thì dùng PROJECT07_GEMINI_MODEL của ứng dụng.

## Tên reviewer

Ở các form duyệt RCM, Test Plan, kết quả kiểm tra, Finding, Report và bảo vệ dữ liệu: chọn tên trong danh sách hoặc gõ tên mới rồi nhấn **Enter**. Hoàn thành ghi chú và xác nhận trước khi bấm lưu review. Tên mới được lưu với lần review; đây vẫn là tên tự khai, chưa phải cơ chế đăng nhập hay xác thực người duyệt.

## Cập nhật GitHub

Giải nén gói v2.4, upload toàn bộ nội dung thư mục bên trong lên gốc repo, ghi đè các file cùng tên và commit. Entry point vẫn là streamlit_app.py. Giữ Secrets đang dùng và reboot app. Kiểm tra dòng NEXUS 2.4 · STREAMLIT trên giao diện.

## Chọn hoặc tự nhập model AI

1. Trong **AI của bạn · Gemini**, nhập key riêng nếu muốn. Có thể dùng key đã cấu hình của app mà không nhập lại.
2. Bấm **Lấy danh sách model khả dụng** để lấy tên model hỗ trợ generateContent cho key đang dùng.
3. Ở **Mô hình AI · chọn hoặc nhập tên**, chọn model trong danh sách hoặc gõ tên model Google cung cấp rồi nhấn **Enter**.
4. Bấm **Dùng model này**. Kiểm tra dòng **Model đang dùng**.
5. Giữ Audit Run hiện tại và thử lại bước Findings. Model riêng chỉ áp dụng các lần gọi tiếp theo; kết quả cũ vẫn ghi model đã tạo ra chúng.
6. Bấm **Dùng model mặc định của ứng dụng** để bỏ lựa chọn model riêng; API key riêng được giữ lại.

Đây là lựa chọn model của người dùng; không tự đổi model khi gặp lỗi. Danh sách metadata không xác nhận model còn quota hay hỗ trợ đầy đủ cấu trúc JSON app yêu cầu. Model không được phép, hết quota hoặc đầu ra không hợp lệ vẫn hiển thị lỗi để người dùng xử lý. Key và model được tách riêng theo phiên; lịch sử LLM ghi model thực sự được chọn cho từng lần gọi.
