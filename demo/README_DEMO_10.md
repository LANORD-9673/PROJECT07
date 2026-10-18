# Bộ hồ sơ tín dụng 10 khách hàng

Dữ liệu hoàn toàn giả lập, theo cấu trúc sổ khoản vay phục vụ kiểm toán. Một khách hàng có một khoản vay. Kỳ giao dịch 09–16/10/2026, CN01 và CN02. Tên người và số tiền được tạo để thử app; ID-SIM là số giấy tờ giả, không phải CCCD thật.

## Các file dùng trong app

- `loans_10.xlsx` hoặc `loans_10.csv`: 10 khoản vay, 19 cột, một bảng.
- `authorities_10.xlsx` hoặc `authorities_10.csv`: 3 người có phân quyền, 8 cột.
- `POL-LOAN-01_compact.txt`: policy rút gọn, UTF-8, import trực tiếp.
- `AUTHORITIES_README.md`: phụ lục phân quyền để đối chiếu.
- `ANSWER_KEY_DEMO_10.md`: đáp án viết theo tình huống, dành cho người kiểm chứng; KHÔNG upload làm nguồn kiểm toán.

Nút Import bộ demo dùng đúng ba file CSV/TXT. Excel là lựa chọn nhập riêng, có hash khác CSV. CSV có UTF-8 BOM để Excel đọc tiếng Việt. Không thêm dòng tiêu đề phía trên tên cột, không gộp ô, không thêm sheet vào file nhập. Thời điểm giữ chuỗi ISO 8601 kèm +07:00 vì đây là định dạng nguồn mà app yêu cầu; các cột số lưu dạng số trong Excel. `interest_rate_pct=8.5` nghĩa là lãi suất 8,5%/năm mô phỏng, chưa tính tiền lãi.

## Từ điển trường

| Trường | Ý nghĩa |
|---|---|
| row_id / loan_id / customer_id | Mã dòng / hợp đồng / khách hàng, duy nhất trong file |
| full_name / id_document | Họ tên và số giấy tờ mô phỏng, nên thay mã khi bảo vệ |
| loan_product / loan_purpose | Nhóm sản phẩm và mục đích vay |
| amount_vnd / currency | Số tiền vay và đồng tiền VND |
| term_months / interest_rate_pct | Kỳ hạn tháng và lãi suất %/năm |
| collateral_value_vnd | Giá trị tài sản bảo đảm giả lập, chưa dùng trong T01–T03 |
| branch_id | Chi nhánh của khoản vay |
| maker_id / approver_id | Mã người lập và phê duyệt; phải giữ quan hệ đối chiếu với employee_id |
| approval_status / approval_time | Trạng thái và thời điểm phê duyệt |
| disbursement_status / disbursement_time | Trạng thái và thời điểm giải ngân |
| employee_id / employee_name / role | Người được cấp quyền và chức danh |
| authority_limit_vnd | Hạn mức cá nhân mỗi khoản VND |
| valid_from / valid_to | Hiệu lực phân quyền, tính cả hai đầu mút |
| decision_reference | Mã quyết định mô phỏng |

Khi thay mã cả loans và authorities, dùng cùng mã phạm vi; không MASK các mã liên kết nếu cần chạy T02. Auditor cần đối chiếu lại authority đã thay mã và dùng hash của snapshot mới.
