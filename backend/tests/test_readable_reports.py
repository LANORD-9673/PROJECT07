import io
import json
import sys
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree
sys.path.append(str(Path(__file__).resolve().parents[2]))
import nexus_reports as reports
from services.evaluation import benchmark


def fixture():
    evaluation = {'total': 2, 'counts': {'PASS': 1, 'EXCEPTION': 1}, 'structural_metrics': {
        'quote_match_rate': None, 'test_coverage': 1, 'evidence_link_integrity': None},
        'regression_benchmark': benchmark(), 'llm_calls': [], 'accuracy': None}
    wf = {'run': {'audit_name': 'Kiểm toán hồ sơ tín dụng', 'run_id': 'test-run'},
          'documents': [], 'result_reviews': [], 'finding_reviews': []}
    results = [{'row_id': 'R001', 'result_id': 'r1', 'test_result': 'PASS'},
               {'row_id': 'R002', 'result_id': 'r2', 'test_result': 'EXCEPTION'}]
    return evaluation, wf, results


def test_missing_metrics_never_presented_as_zero_or_full_accuracy():
    e, wf, results = fixture()
    report = reports.evaluation_report(e, wf, [], results)
    section = next(x for x in report['sections'] if x['title'] == 'Chỉ tiêu cấu trúc và khả năng truy vết')
    assert section['rows'][0]['Kết quả'] == 'Chưa có dữ liệu'
    assert section['rows'][1]['Kết quả'] == '100.0%'
    assert section['rows'][2]['Kết quả'] == 'Chưa có dữ liệu'
    limits = next(x['text'] for x in report['sections'] if x['title'] == 'Giới hạn và lưu ý sử dụng')
    assert 'AI trên hồ sơ cuộc kiểm toán chưa được đo' in limits


def test_counts_and_human_review_use_actual_exceptions():
    e, wf, results = fixture()
    wf['result_reviews'] = [{'result_id': 'r2', 'review_state': 'CONFIRMED'}]
    report = reports.evaluation_report(e, wf, [], results)
    summary = report['sections'][0]['text']
    assert '2 lượt kiểm tra trên 2 hồ sơ' in summary
    assert '1 đã được auditor xác nhận và 0 còn chờ xử lý' in summary
    assert '0 còn chờ xử lý' in summary
    assert 'chưa được phát hành' not in report['sections'][0]['text'] or report['metadata'][-1][1] == 'Bản nháp cần auditor review'


def test_fixed_benchmark_is_explicitly_separate_from_ai_accuracy():
    e, wf, results = fixture()
    report = reports.evaluation_report(e, wf, [], results)
    section = next(x for x in report['sections'] if x['title'] == 'Đối chứng bộ quy tắc phần mềm')
    assert 'tách biệt với độ chính xác của AI' in section['text']
    assert all(x['Phạm vi'] == '18 tình huống quy tắc cố định' for x in section['rows'])


def test_word_contains_readable_tables_and_original_observations():
    doc = {'kind': 'FINDINGS', 'payload': {'findings': [{'finding_key': 'F01', 'title': 'Vượt hạn mức',
        'criteria': 'Căn cứ hạn mức', 'condition': 'Số tiền vượt hạn mức', 'risk': 'Rủi ro tín dụng',
        'recommendation': 'Review lại phân quyền', 'source_quote': 'Giữ nguyên câu trích dẫn.',
        'evidence_details': [{'row_id': 'R002', 'reason_code': 'APPROVAL_LIMIT_EXCEEDED_TIER_1',
                             'observed_values': {'amount_vnd': '900000000'}}]}]}}
    raw = reports.word_bytes({'title': 'Phát hiện kiểm toán', 'sections': reports.document_sections(doc)})
    with ZipFile(io.BytesIO(raw)) as z:
        xml = ElementTree.fromstring(z.read('word/document.xml'))
        text = ''.join(xml.itertext())
        assert 'Giữ nguyên câu trích dẫn.' in text and '900000000' in text
        assert 'Số tiền vay (VND)' in text
        assert '{"' not in text and 'observed_values' not in text


def test_privacy_word_excludes_cell_originals_and_mapping_preserves_values():
    data = {'source_filename': 'test.csv', 'reviewer': 'Auditor', 'reviewed_at': '2026-10-19T10:00:00+07:00',
            'scope': 'SCOPE', 'row_count': 1, 'column_count': 1, 'file_id': 'file-id', 'review_id': 'review-id',
            'plan': [{'column': 'full_name', 'action': 'TOKENIZE'}],
            'cell_details': [{'original_value': 'Sensitive Person'}]}
    report = reports.privacy_report({'audit_report_json_bytes': json.dumps(data).encode()})
    assert 'Sensitive Person' not in json.dumps(report)
    mapping = b'data_row,column,action,original_row_id,protected_row_id,method,original_value,protected_value\r\n1,full_name,TOKENIZE,R1,NX1,HMAC-SHA256 scope token,Sensitive Person,NX_person\r\n'
    output = reports.readable_mapping(mapping).decode('utf-8-sig')
    assert 'Giá trị gốc' in output and 'Thay bằng mã giả' in output
    assert 'Sensitive Person,NX_person' in output
