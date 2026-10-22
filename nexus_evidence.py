"""On-demand evidence rows; no LLM calls, decryption or shared data cache."""
import pandas as pd
import streamlit as st
import nexus_reports as readable


def value_text(value):
    if value is None or (isinstance(value, str) and not value.strip()):
        return 'Thiếu dữ liệu (ô trống)'
    return readable.plain(value)


def toggle_evidence(key):
    st.session_state[key] = not st.session_state.get(key, False)


def show_evidence_view(item, fetch):
    run_id, result_id = item.get('run_id'), item.get('result_id')
    if not run_id or not result_id:
        return
    key = f'evidence_open:{run_id}:{result_id}'
    opened = st.session_state.get(key, False)
    st.button('Ẩn dòng bằng chứng' if opened else 'Xem dòng bằng chứng',
              key=key + ':button', on_click=toggle_evidence, args=(key,))
    if not opened:
        return
    try:
        data = fetch(f'/audit-runs/{run_id}/results/{result_id}/evidence')
    except Exception:
        st.error('Chưa mở được dòng bằng chứng. Hãy kiểm tra cuộc kiểm toán và thử lại; không xác nhận khi chưa đối chiếu được nguồn.')
        return
    st.info('Đang xem dữ liệu đúng phiên bản đã dùng để chạy kiểm tra. Nếu đã thay mã hoặc che thông tin, màn hình giữ nguyên bản đó; không tự giải mã dữ liệu.')
    rows = data.get('rows', [])
    if not rows:
        st.warning('Kết quả này chưa có dòng bằng chứng được liên kết.')
        return
    for row in rows:
        st.markdown('**' + readable.SOURCES.get(row['source'], row['source']) + '**')
        st.caption(f"File: {row['filename']} · Phiên bản {row['version']} · Dòng {row['source_line']}")
        st.caption('Mã bằng chứng: ' + str(row.get('evidence_id') or 'Chưa ghi nhận'))
        values = row['values']
        st.dataframe(pd.DataFrame([
            {'Chỉ tiêu cần đối chiếu': readable.field(field), 'Giá trị trong file': value_text(values.get(field))}
            for field in row['fields']
        ]), hide_index=True, width='stretch')
        with st.expander('Xem toàn bộ dòng · ' + row['filename'] + ' · ' + str(row['source_line'])):
            st.dataframe(pd.DataFrame([{readable.field(k): value_text(v) for k, v in values.items()}]),
                         hide_index=True, width='stretch')
            st.caption('Mã phiên bản dữ liệu: ' + row['snapshot_id'])
            st.caption('SHA256 của file: ' + row['sha256'])
    if item.get('test_id') == 'T02' and not any(r['source'] == 'authority' for r in rows):
        st.warning('Kết quả này chưa gắn dòng phân quyền. Kiểm tra dữ liệu còn thiếu và bảng phân quyền của cuộc kiểm toán; chưa thể kết luận vượt hạn mức chỉ từ tình trạng thiếu thông tin.')
    st.caption('Số dòng tính cả dòng tiêu đề. Các giá trị hiển thị là dữ liệu đã nhập, không phải bằng chứng mới do AI tạo ra. Mở bằng chứng không thay đổi kết quả hoặc tự xác nhận review.')
