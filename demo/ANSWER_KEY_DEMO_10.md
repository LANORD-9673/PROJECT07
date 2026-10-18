# Đáp án tình huống mô phỏng — không nhập vào workflow

Nhãn dự kiến do người xây dựng bộ demo quy định theo policy, chưa được auditor chứng nhận độc lập. Dùng để kiểm tra phần mềm, không dùng làm ground truth chứng minh độ chính xác của Gemini.

| Dòng | T01 | T02 | T03 | Căn cứ tình huống |
|---|---|---|---|---|
| R001 | PASS | PASS | PASS | 320 triệu, đúng quyền AP101 |
| R002 | PASS | PASS | PASS | Đúng ranh giới 500 triệu, AP101 đủ hạn mức |
| R003 | PASS | PASS | PASS | 1,25 tỷ, AP102 đủ hạn mức |
| R004 | PASS | PASS | PASS | Đúng ranh giới 2 tỷ, AP102 đủ hạn mức |
| R005 | PASS | PASS | PASS | AP201 tại CN02, 780 triệu |
| R006 | EXCEPTION | PASS | PASS | Người lập = người duyệt AP101; Điều 2.1 |
| R007 | PASS | EXCEPTION | PASS | 720 triệu vượt hạn mức AP101 500 triệu; Điều 2.2 |
| R008 | PASS | PASS | EXCEPTION | Giải ngân 09:00, phê duyệt 10:00 cùng ngày; Điều 2.3 |
| R009 | PASS | PASS | NOT_APPLICABLE | Chưa giải ngân |
| R010 | PASS | INSUFFICIENT_INFORMATION | INSUFFICIENT_INFORMATION | Thiếu thời điểm phê duyệt, không được kết luận PASS |

Kỳ vọng 30 kết quả: 24 PASS, 3 EXCEPTION, 2 INSUFFICIENT_INFORMATION, 1 NOT_APPLICABLE. Ba ngoại lệ có thể dùng để demo ba finding theo từng kiểm soát, sau khi auditor review. Dòng R010 cần bổ sung bằng chứng riêng.
