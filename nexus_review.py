"""Filter and select a review queue without changing audit decisions."""

RESULT_TYPES = ('EXCEPTION', 'INSUFFICIENT_INFORMATION', 'PASS', 'BLOCKED',
                'NOT_APPLICABLE', 'OUT_OF_SCOPE')
REVIEW_STATES = ('PENDING', 'NEEDS_FOLLOWUP', 'CONFIRMED', 'REJECTED')
ATTENTION_TYPES = ('EXCEPTION', 'INSUFFICIENT_INFORMATION')


def filter_results(results, result_types, review_states, test_ids):
    """Empty filters mean no matches, never silently broaden the scope."""
    return [r for r in results
            if r['test_result'] in result_types
            and r.get('human_review', 'PENDING') in review_states
            and r['test_id'] in test_ids]


def pending_counts(results):
    """Needs-followup is unresolved but distinct from never reviewed."""
    return {kind: sum(r['test_result'] == kind
                      and r.get('human_review', 'PENDING') not in ('CONFIRMED', 'REJECTED')
                      for r in results) for kind in ATTENTION_TYPES}


def render_review_queue(results, run_id):
    """Return one selected result for the existing evidence/review form."""
    import pandas as pd
    import streamlit as st
    import nexus_reports as readable

    prefix = 'result_queue_' + run_id + '_'
    counts = pending_counts(results)
    left, right = st.columns(2)
    left.metric('Ngoại lệ còn chờ xử lý', counts['EXCEPTION'])
    right.metric('Chưa đủ thông tin còn chờ xử lý', counts['INSUFFICIENT_INFORMATION'])
    st.caption('Còn chờ xử lý gồm Chờ review và Cần làm rõ thêm. '
               'Xác nhận một kết quả đạt không làm giảm số ngoại lệ.')

    with st.container(border=True):
        st.markdown('**Lọc kết quả cần xem xét**')
        col1, col2, col3 = st.columns(3)
        kinds = col1.multiselect('Loại kết quả', RESULT_TYPES, default=list(ATTENTION_TYPES),
                                format_func=readable.label, key=prefix + 'types')
        states = col2.multiselect('Trạng thái review', REVIEW_STATES, default=['PENDING'],
                                 format_func=readable.label, key=prefix + 'states')
        test_options = sorted({r['test_id'] for r in results})
        tests_key = prefix + 'tests'
        st.session_state[tests_key] = [x for x in st.session_state.get(tests_key, test_options)
                                       if x in test_options]
        tests = col3.multiselect('Thủ tục kiểm tra', test_options, key=tests_key)

    filtered = filter_results(results, kinds, states, tests)
    st.caption(f'Đang hiển thị {len(filtered)} / {len(results)} kết quả theo bộ lọc.')
    if filtered:
        st.dataframe(pd.DataFrame(readable.result_rows(filtered)), hide_index=True, width='stretch')

    by_id = {r['result_id']: r for r in filtered}
    options = list(by_id)
    selection_key = prefix + 'selected'
    # Scope selection to this run and the current filter, including after a saved review.
    st.session_state[selection_key] = [x for x in st.session_state.get(selection_key, []) if x in by_id]
    all_col, clear_col = st.columns(2)
    if all_col.button('Chọn tất cả kết quả đã lọc', key=prefix + 'all', disabled=not options):
        st.session_state[selection_key] = options
    if clear_col.button('Bỏ chọn tất cả', key=prefix + 'clear',
                        disabled=not st.session_state[selection_key]):
        st.session_state[selection_key] = []

    def describe(result_id):
        r = by_id[result_id]
        return (f"{r['row_id']} · {r['test_id']} · {readable.label(r['test_result'])} · "
                f"{readable.label(r.get('human_review', 'PENDING'))}")

    selected = st.multiselect('Danh sách chọn để đọc bằng chứng và review', options,
                             format_func=describe, key=selection_key)
    st.caption(f'Đã chọn {len(selected)} kết quả. Chọn tất cả chỉ tạo danh sách xem xét; '
               'không tự xác nhận hay lưu review hàng loạt.')
    if not filtered:
        st.info('Không có kết quả khớp bộ lọc. Nếu cần xem các mục còn phải bổ sung, '
                'chọn thêm trạng thái Cần làm rõ thêm.')
        return None
    if not selected:
        st.info('Chọn kết quả trong danh sách hoặc bấm Chọn tất cả kết quả đã lọc để bắt đầu.')
        return None

    current_key = prefix + 'current'
    if st.session_state.get(current_key) not in selected:
        st.session_state[current_key] = selected[0]
    position = selected.index(st.session_state[current_key])

    def move(step):
        index = selected.index(st.session_state[current_key])
        st.session_state[current_key] = selected[index + step]

    prev_col, next_col = st.columns(2)
    prev_col.button('← Kết quả trước', key=prefix + 'previous', disabled=position == 0,
                    on_click=move, args=(-1,))
    next_col.button('Kết quả tiếp theo →', key=prefix + 'next', disabled=position == len(selected) - 1,
                    on_click=move, args=(1,))
    current = st.selectbox('Chọn kết quả để đọc bằng chứng và review', selected,
                           format_func=describe, key=current_key)
    st.caption(f'Kết quả {selected.index(current) + 1} / {len(selected)} trong danh sách đã chọn.')
    return by_id[current]
