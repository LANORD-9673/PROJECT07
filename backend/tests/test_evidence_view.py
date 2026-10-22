import hashlib
import json
import sys
from pathlib import Path

from test_imports import AUTH, LOANS, upload
from test_rule_api import prepare


def executed(client, monkeypatch, loans=LOANS):
    raw = b'SYNTHETIC POLICY FOR EVIDENCE TEST'
    rid = prepare(client, 'BASELINE', raw)
    if loans != LOANS:
        # Create a new run pinned to the alternative dataset; the first run remains unchanged.
        custom = upload(client, '/api/import/loans', 'dataset_id', 'custom', 'blank.csv', loans).json()['data']
        from models.db import connect
        with connect() as con:
            run = dict(con.execute('SELECT * FROM audit_runs WHERE run_id=?', (rid,)).fetchone())
        rid = client.post('/api/audit-runs', json=dict(
            policy_snapshot_id=run['policy_snapshot_id'], dataset_snapshot_id=custom['snapshot_id'],
            authority_snapshot_id=run['authority_snapshot_id'], audit_name='Alternative')).json()['data']['run_id']
    monkeypatch.setenv('PROJECT07_REQUIRE_GATES', '0')
    monkeypatch.setenv('PROJECT07_APPROVED_BASELINE_SHA256', hashlib.sha256(raw).hexdigest())
    monkeypatch.setenv('PROJECT07_AUTHORITY_APPROVAL_REFERENCE', 'SYNTHETIC_TEST_ONLY')
    monkeypatch.setenv('PROJECT07_APPROVED_AUTHORITY_SHA256', hashlib.sha256(AUTH.encode()).hexdigest())
    response = client.post(f'/api/audit-runs/{rid}/tests/execute')
    assert response.status_code == 200
    return rid, {row['test_id']: row for row in response.json()['data']['results']}


def evidence(client, rid, result):
    return client.get(f"/api/audit-runs/{rid}/results/{result['result_id']}/evidence")


def test_row_values_authority_and_no_review_mutation(client, monkeypatch):
    rid, results = executed(client, monkeypatch)
    before = client.get(f'/api/audit-runs/{rid}/results').json()['data']
    for test_id in ('T01', 'T02', 'T03'):
        response = evidence(client, rid, results[test_id])
        assert response.status_code == 200
        data = response.json()['data']
        assert data['test_id'] == test_id
        loan = data['rows'][0]
        assert loan['values']['amount_vnd'] == '500000000'
        assert loan['filename'] == 'loans.csv' and loan['version'] == 1
        assert loan['source_line'] == 2
        assert loan['evidence_id'] == results[test_id]['evidence_refs'][0]['evidence_id']
    t02 = evidence(client, rid, results['T02']).json()['data']['rows']
    assert len(t02) == 2 and t02[1]['source'] == 'authority'
    assert t02[1]['values']['authority_limit_vnd'] == '2000000000'
    assert t02[1]['filename'] == 'auth.csv'
    assert client.get(f'/api/audit-runs/{rid}/results').json()['data'] == before


def test_later_imports_do_not_replace_pinned_evidence(client, monkeypatch):
    rid, results = executed(client, monkeypatch)
    upload(client, '/api/import/loans', 'dataset_id', 'demo', 'new.csv', LOANS.replace('500000000', '700000000'))
    upload(client, '/api/import/authorities', 'authority_id', 'demoauth', 'newauth.csv', AUTH.replace('2000000000', '800000000'))
    rows = evidence(client, rid, results['T02']).json()['data']['rows']
    assert rows[0]['values']['amount_vnd'] == '500000000'
    assert rows[1]['values']['authority_limit_vnd'] == '2000000000'
    assert all(row['version'] == 1 for row in rows)


def test_wrong_run_or_unknown_result_is_not_returned(client, monkeypatch):
    rid, results = executed(client, monkeypatch)
    other = prepare(client, 'BASELINE', b'OTHER SYNTHETIC POLICY')
    assert evidence(client, other, results['T02']).status_code == 404
    assert evidence(client, 'unknown-run', results['T02']).status_code == 404
    assert evidence(client, rid, {'result_id': 'unknown-result'}).status_code == 404


def test_blank_data_stays_blank_without_invented_authority(client, monkeypatch):
    rid, results = executed(client, monkeypatch, LOANS.replace('2026-10-01T08:00:00+07:00', ''))
    rows = evidence(client, rid, results['T02']).json()['data']['rows']
    assert len(rows) == 1
    assert rows[0]['values']['approval_time'] == ''
    assert 'approval_time' in rows[0]['fields']


def test_corrupt_reference_cannot_read_another_snapshot(client, monkeypatch):
    rid, results = executed(client, monkeypatch)
    item = results['T02']
    item['evidence_refs'][0]['snapshot_id'] = 'unrelated-snapshot'
    from models.db import connect
    with connect() as con:
        con.execute('UPDATE rule_results SET result_json=? WHERE result_id=?', (json.dumps(item), item['result_id']))
    response = evidence(client, rid, item)
    assert response.status_code == 409
    assert response.json()['errors'][0]['code'] == 'EVIDENCE_MISMATCH'


ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
UI_APP = '''
import streamlit as st
from nexus_evidence import show_evidence_view
which = st.selectbox('Kết quả', ['A', 'B'])
def fetch(path):
    st.session_state['calls'] = st.session_state.get('calls', 0) + 1
    return {'rows': [dict(source='loans', source_line=11, filename='protected.csv', version=1,
        evidence_id='ev-' + which, snapshot_id='snapshot-a', sha256='file-sha',
        fields=['row_id', 'amount_vnd', 'approval_time'],
        values={'row_id': 'NX_001', 'amount_vnd': '0', 'approval_time': '', 'loan_id': '0001'})]}
show_evidence_view(dict(run_id='run-a', result_id=which, test_id='T02'), fetch)
st.text('Calls: ' + str(st.session_state.get('calls', 0)))
'''


def test_streamlit_open_hide_missing_values_and_result_isolation():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_string(UI_APP).run(timeout=20)
    assert not at.exception
    assert at.text[0].value == 'Calls: 0' and not at.dataframe
    at.button[0].click().run()
    assert not at.exception and at.button[0].label == 'Ẩn dòng bằng chứng'
    values = at.dataframe[0].value['Giá trị trong file'].tolist()
    assert values == ['NX_001', '0', 'Thiếu dữ liệu (ô trống)']
    assert at.dataframe[1].value['Mã khoản vay'].tolist() == ['0001']
    assert at.warning and 'chưa gắn dòng phân quyền' in at.warning[0].value
    at.selectbox[0].set_value('B').run()
    assert not at.exception and not at.dataframe
    assert at.button[0].label == 'Xem dòng bằng chứng'
    at.selectbox[0].set_value('A').run()
    at.button[0].click().run()
    assert not at.dataframe and at.button[0].label == 'Xem dòng bằng chứng'
