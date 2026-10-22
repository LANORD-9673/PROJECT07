"""Exercise real Streamlit widgets, including reruns after review/filter changes."""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
from nexus_review import pending_counts


APP = '''
import sys
sys.path.append(ROOT_PATH)
import streamlit as st
from nexus_review import render_review_queue
run = st.selectbox('Cuộc kiểm toán thử', ['A', 'B'])
if 'rows' not in st.session_state:
    st.session_state.rows = [
        dict(result_id='a', row_id='R001', test_id='T01', test_result='PASS', human_review='PENDING'),
        dict(result_id='b', row_id='R002', test_id='T02', test_result='EXCEPTION', human_review='PENDING'),
        dict(result_id='c', row_id='R003', test_id='T02', test_result='INSUFFICIENT_INFORMATION', human_review='PENDING'),
        dict(result_id='d', row_id='R004', test_id='T03', test_result='EXCEPTION', human_review='CONFIRMED'),
        dict(result_id='e', row_id='R005', test_id='T03', test_result='EXCEPTION', human_review='NEEDS_FOLLOWUP')]
rows = st.session_state.rows if run == 'A' else [dict(result_id='other', row_id='OTHER', test_id='T02', test_result='EXCEPTION', human_review='PENDING')]
item = render_review_queue(rows, run)
if item is not None:
    st.text('Bằng chứng: ' + item['result_id'])
    if st.button('Lưu xác nhận thử'):
        item['human_review'] = 'CONFIRMED'
        st.rerun()
'''.replace('ROOT_PATH', repr(str(ROOT)))


def app():
    at = AppTest.from_string(APP).run(timeout=20)
    assert not at.exception
    return at


def button(at, label):
    return next(x for x in at.button if x.label == label)


def test_default_queue_selection_navigation_and_saved_review_refresh():
    at = app()
    assert at.dataframe[0].value['Hồ sơ'].tolist() == ['R002', 'R003']
    assert [x.value for x in at.metric] == ['2', '1']
    button(at, 'Chọn tất cả kết quả đã lọc').click().run()
    assert not at.exception
    assert at.multiselect[3].value == ['b', 'c']
    assert at.text[0].value == 'Bằng chứng: b'
    button(at, 'Kết quả tiếp theo →').click().run()
    assert at.text[0].value == 'Bằng chứng: c'
    button(at, '← Kết quả trước').click().run()
    assert at.text[0].value == 'Bằng chứng: b'
    # Selecting all has not modified the review states or pending counts.
    assert [x.value for x in at.metric] == ['2', '1']
    button(at, 'Lưu xác nhận thử').click().run()
    assert not at.exception
    assert [x.value for x in at.metric] == ['1', '1']
    assert at.multiselect[3].value == ['c']
    assert at.text[0].value == 'Bằng chứng: c'
    button(at, 'Lưu xác nhận thử').click().run()
    assert not at.exception
    assert at.multiselect[3].value == []
    assert len(at.text) == 0


def test_filter_changes_prune_selection_and_empty_means_no_results():
    at = app()
    button(at, 'Chọn tất cả kết quả đã lọc').click().run()
    at.multiselect[0].set_value(['INSUFFICIENT_INFORMATION']).run()
    assert not at.exception
    assert at.multiselect[3].value == ['c']
    at.multiselect[1].set_value(['CONFIRMED']).run()
    assert not at.exception
    assert at.multiselect[3].value == []
    assert len(at.text) == 0
    at.multiselect[1].set_value([]).run()
    assert not at.exception
    assert len(at.dataframe) == 0
    assert button(at, 'Chọn tất cả kết quả đã lọc').disabled


def test_followup_filter_clear_all_and_run_isolation():
    at = app()
    at.multiselect[1].set_value(['NEEDS_FOLLOWUP']).run()
    button(at, 'Chọn tất cả kết quả đã lọc').click().run()
    assert at.multiselect[3].value == ['e']
    button(at, 'Bỏ chọn tất cả').click().run()
    assert at.multiselect[3].value == []
    assert len(at.text) == 0
    at.selectbox[0].set_value('B').run()
    assert not at.exception
    assert at.multiselect[3].value == []
    button(at, 'Chọn tất cả kết quả đã lọc').click().run()
    assert at.text[0].value == 'Bằng chứng: other'


def test_counts_do_not_confuse_pass_with_exception_or_followup_with_resolved():
    rows = [dict(test_result=kind, human_review=state)
            for kind, state in [('PASS', 'PENDING'), ('EXCEPTION', 'CONFIRMED'),
                                ('EXCEPTION', 'REJECTED'), ('EXCEPTION', 'NEEDS_FOLLOWUP'),
                                ('INSUFFICIENT_INFORMATION', 'PENDING')]]
    assert pending_counts(rows) == {'EXCEPTION': 1, 'INSUFFICIENT_INFORMATION': 1}
