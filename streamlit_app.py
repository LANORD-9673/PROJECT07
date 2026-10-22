import hashlib
import json
import os
import re
from datetime import date, time, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title='NEXUS | Project 07', page_icon=str(ROOT / 'assets/nexus-logo.png'), layout='wide', initial_sidebar_state='expanded')

# Deployment settings are controlled by the app owner, never by visitors.
KEYS = ('GEMINI_API_KEY', 'PROJECT07_GEMINI_MODEL', 'PROJECT07_GEMINI_TIMEOUT',
        'PROJECT07_APPROVED_BASELINE_SHA256', 'PROJECT07_APPROVED_AUTHORITY_SHA256',
        'PROJECT07_AUTHORITY_APPROVAL_REFERENCE', 'PROJECT07_DB_PATH',
        'PROJECT07_VAULT_MASTER_KEY', 'PROJECT07_VAULT_DIR', 'PROJECT07_GEMINI_MAX_RETRIES')
try:
    for key in KEYS:
        if key in st.secrets:
            os.environ[key] = str(st.secrets[key])
except FileNotFoundError:
    pass
os.environ['PROJECT07_REQUIRE_GATES'] = '1'

from streamlit_runtime import initialize, request as backend_request, ApiError
from nexus_ui import shell, home, loading
import nexus_reports as readable
from nexus_review import render_review_queue
from nexus_exports import table_xlsx, mapping_xlsx, XLSX_MIME
REVIEWERS = ['Hoàng Minh Khuê', 'Đinh Nghiêm Khánh Lam', 'Phan Ngô Ngọc Lan', 'Bùi Lê Hồng Ngọc', 'Trương Thị Thanh Thảo', 'Trương Mỹ Uyên']


@st.cache_resource(show_spinner=False)
def setup_backend():
    initialize()
    return True


setup_backend()


def request(method, path, **kwargs):
    return backend_request(method, path, gemini_api_key=st.session_state.get('gemini_session_key'), gemini_model=st.session_state.get('gemini_session_model'), **kwargs)


def api(path):
    return request('GET', path)


def mutate(path, payload=None, **kwargs):
    with loading():
        return request('POST', path, json=payload, **kwargs) if payload is not None else request('POST', path, **kwargs)


def action(label, path, payload=None, disabled=False, key=None):
    if st.button(label, disabled=disabled, key=key or path, type='primary'):
        try:
            mutate(path, payload)
            st.session_state['notice'] = 'Thao tác hoàn tất. Kết quả đã được lưu vào audit trail.'
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))


def download(data, name, key):
    if isinstance(data, list):
        report = {'title': 'Kết quả kiểm tra dữ liệu', 'sections': [readable.table_section('Chi tiết kết quả', readable.result_rows(data))]}
    else:
        report = {'title': readable.KINDS.get(data.get('kind'), 'Tài liệu kiểm toán'),
                  'metadata': [('Trạng thái', readable.label(data.get('state'))), ('Model đã dùng', data.get('model'))],
                  'sections': readable.document_sections(data)}
    st.download_button('Tải tài liệu Word dễ đọc', readable.word_bytes(report),
                       file_name=str(Path(name).with_suffix('.docx')),
                       mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document', key=key)


def show_table(rows):
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')


def show_evidence(item):
    st.write(readable.reason(item.get('reason_code')))
    show_table(readable.evidence_rows(item))
    observed = item.get('observed_values', {})
    if observed:
        show_table([{'Trường được đối chiếu': readable.field(k), 'Giá trị quan sát': readable.plain(v)} for k, v in observed.items()])
    if item.get('result_id'):
        st.caption('Mã kết quả để truy vết: ' + item['result_id'])


def show_sections(report):
    for section in report['sections']:
        if section['title'].startswith('Phụ lục'):
            with st.expander(section['title']):
                if section['text']: st.write(section['text'])
                show_table(section['rows'])
        else:
            st.markdown('### ' + section['title'])
            if section['text']: st.write(section['text'])
            show_table(section['rows'])


def review_form(title, path, key, extra=None, decision_key=None, disabled=False):
    with st.form(key):
        st.markdown(f'**{title}**')
        reviewer = st.selectbox('Người review · chọn hoặc nhập tên', REVIEWERS, index=None, placeholder='Chọn hoặc gõ tên rồi nhấn Enter', key=key + '_reviewer', accept_new_options=True)
        reason = st.text_area('Căn cứ / ghi chú review', key=key + '_reason')
        payload = dict(extra or {})
        if decision_key:
            payload[decision_key] = st.selectbox('Kết luận', ['CONFIRMED', 'NEEDS_FOLLOWUP', 'REJECTED'], format_func=readable.label)
        checked = st.checkbox('Tôi đã đối chiếu nguồn và bằng chứng liên quan')
        submitted = st.form_submit_button('Lưu review', disabled=disabled)
    if submitted:
        if not checked or not (reviewer or '').strip() or not reason.strip():
            st.error('Cần đối chiếu bằng chứng, chọn hoặc nhập tên người review và ghi căn cứ trước khi lưu.')
        else:
            try:
                mutate(path, dict(payload, reviewer=reviewer, reason=reason))
                st.session_state['notice'] = 'Đã lưu review của con người.'
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))


page = shell()
with st.sidebar.container(border=True):
    st.markdown('**AI của bạn · Gemini**')
    st.caption('Key riêng được ưu tiên trong phiên này. Nếu không nhập, app dùng key của chủ ứng dụng khi có.')
    with st.form('session_gemini_key', clear_on_submit=True):
        entered_key = st.text_input('API key Gemini riêng', type='password', max_chars=512, autocomplete='off')
        save_key = st.form_submit_button('Dùng key này cho phiên hiện tại')
    if save_key:
        value = entered_key.strip()
        if not value or any(char.isspace() for char in value):
            st.error('Nhập API key không có khoảng trắng. Key hiện tại chưa thay đổi.')
        else:
            st.session_state['gemini_session_key'] = value
            st.session_state.pop('gemini_model_options', None)
            st.success('Đã nhận key riêng; chưa kiểm chứng quyền gọi model hoặc quota.')
    if st.session_state.get('gemini_session_key'):
        st.caption('Đang dùng: API key riêng của phiên này.')
        if st.button('Xóa key riêng và dùng cấu hình ứng dụng', key='clear_session_gemini_key'):
            st.session_state.pop('gemini_session_key', None)
            st.session_state.pop('gemini_model_options', None)
            st.rerun()
    else:
        st.caption('Đang dùng: cấu hình API của ứng dụng.' if os.environ.get('GEMINI_API_KEY', '').strip() else 'Chưa có API key đang dùng.')
    if st.button('Lấy danh sách model khả dụng', key='session_list_models'):
        try:
            checked = mutate('/llm/check')
            st.session_state['gemini_model_options'] = checked['generate_content_models']
            st.success('Đã lấy danh sách model cho key đang dùng. Chưa kiểm chứng quota tạo nội dung.')
        except ApiError as exc:
            st.error(str(exc))
    active_model = st.session_state.get('gemini_session_model') or os.environ.get('PROJECT07_GEMINI_MODEL', 'gemini-3.8-flash').strip().removeprefix('models/')
    model_options = list(dict.fromkeys([active_model] + st.session_state.get('gemini_model_options', [])))
    with st.form('session_model_form'):
        chosen_model = st.selectbox('Mô hình AI · chọn hoặc nhập tên', model_options, key='session_model_choice', accept_new_options=True,
                                    placeholder='Chọn model hoặc gõ tên rồi Enter')
        save_model = st.form_submit_button('Dùng model này')
    if save_model:
        value = str(chosen_model or '').strip().removeprefix('models/')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', value):
            st.error('Tên model không hợp lệ. Nhập mã model do Google cung cấp.')
        else:
            st.session_state['gemini_session_model'] = value
            st.success('Đã áp dụng model cho các lần gọi AI tiếp theo trong phiên.')
    st.caption('Model đang dùng: ' + (st.session_state.get('gemini_session_model') or active_model))
    if st.session_state.get('gemini_session_model') and st.button('Dùng model mặc định của ứng dụng', key='clear_session_model'):
        st.session_state.pop('gemini_session_model', None)
        st.session_state.pop('session_model_choice', None)
        st.rerun()
    st.caption('Key lưu tạm trong RAM của phiên, không ghi vào hồ sơ kiểm toán. Quota theo Google project và model; key khác cùng project vẫn chung hạn mức. Model đã chọn phải được key cho phép sử dụng.')
if 'notice' in st.session_state:
    st.success(st.session_state.pop('notice'))

run_list = api('/audit-runs')
run_ids = [x['run_id'] for x in run_list]
labels = {x['run_id']: x['audit_name'] + ' · ' + x['run_id'][:8] for x in run_list}
selected = st.session_state.get('active_run')
rid = st.sidebar.selectbox('Cuộc kiểm toán đang mở', run_ids, index=run_ids.index(selected) if selected in run_ids else 0,
                           format_func=lambda x: labels[x]) if run_ids else None
if rid:
    st.session_state['active_run'] = rid
st.sidebar.caption('Demo dùng chung dữ liệu, chưa xác thực người duyệt. Chỉ dùng dữ liệu giả lập.')
st.sidebar.button('Làm mới dữ liệu', on_click=lambda: None)

if page == 'Trang chủ':
    home(len(run_list))

elif page == 'Vai trò & cấu hình':
    st.subheader('AI hỗ trợ ở đâu, con người cần làm gì?')
    st.dataframe(pd.DataFrame([
        ['Viết code', 'Hỗ trợ thiết kế, tạo code và gợi ý sửa lỗi', 'Đọc diff, kiểm chứng nghiệp vụ, test và duyệt PR'],
        ['Policy → RCM', 'LLM1 trích xuất risk/control và quote', 'Đối chiếu policy gốc, duyệt RCM'],
        ['RCM → Test Plan', 'LLM2 soạn thủ tục và evidence', 'Duyệt kế hoạch và phạm vi'],
        ['Data → Exceptions', 'Python chạy T01, T02, T03', 'Xác minh từng exception'],
        ['Exceptions → Findings', 'LLM3 viết finding gắn bằng chứng', 'Review từng finding'],
        ['Findings → Report', 'LLM4 tổng hợp báo cáo DRAFT', 'Review báo cáo; không tự coi là phát hành FINAL'],
    ], columns=['Bước', 'LLM / Python', 'Con người']), hide_index=True, width='stretch')
    st.info('Streamlit chạy giao diện Python và backend trong cùng ứng dụng. Không cần deploy FastAPI riêng hoặc build React.')
    st.markdown('**Trạng thái cấu hình**')
    st.write('Provider: **Gemini API — Google AI Studio**')
    st.write('API key: ' + ('key riêng của phiên hiện tại' if st.session_state.get('gemini_session_key') else 'key của chủ ứng dụng' if os.environ.get('GEMINI_API_KEY', '').strip() else 'chưa cấu hình — nhập key ở thanh bên'))
    st.write('Model: ' + (st.session_state.get('gemini_session_model') or os.environ.get('PROJECT07_GEMINI_MODEL', 'gemini-3.8-flash')))
    from services.privacy import master_key_status
    vault_ready, vault_message = master_key_status()
    st.write('Khóa mã hóa vault: ' + ('đã sẵn sàng' if vault_ready else 'chưa sẵn sàng'))
    if not vault_ready:
        st.caption(vault_message)
    st.caption('Chỉ kiểm tra cấu hình; chưa chứng minh kết nối hoặc chất lượng model. API key không hiển thị trên giao diện.')
    if st.button('Kiểm tra key và danh sách model', key='gemini_check'):
        try:
            checked = mutate('/llm/check')
            st.session_state['gemini_model_options'] = checked['generate_content_models']
            st.success('Google chấp nhận truy cập danh sách model. Chưa kiểm chứng việc tạo nội dung.')
            if not checked['configured_model_listed']:
                st.warning('Model đang dùng chưa có trong danh sách trả về. Bấm Lấy danh sách model khả dụng ở thanh bên rồi chọn model khác, hoặc tự nhập tên model Google cung cấp.')
            show_table([{'Model tạo nội dung được phép truy cập': name} for name in checked['generate_content_models']])
            st.caption(checked['note'])
        except ApiError as exc:
            st.error(str(exc))
    pins = all(os.environ.get(x, '').strip() for x in ('PROJECT07_APPROVED_BASELINE_SHA256', 'PROJECT07_APPROVED_AUTHORITY_SHA256', 'PROJECT07_AUTHORITY_APPROVAL_REFERENCE'))
    st.write('Hồ sơ phê duyệt baseline: ' + ('đã cấu hình — backend vẫn đối chiếu hash khi chạy' if pins else 'chưa đủ; Tests sẽ bị chặn'))
    with st.expander('SHA256 của bộ demo để chủ ứng dụng đối chiếu'):
        for name in ('POL-LOAN-01_compact.txt', 'authorities_10.csv'):
            st.text(name)
            st.code(hashlib.sha256((ROOT / 'demo' / name).read_bytes()).hexdigest())
        st.caption('Hash không thay cho phê duyệt. Chỉ cấu hình Secrets sau khi con người đã rà soát đúng bộ tài liệu.')
    st.info('Nhập API key riêng ở thanh bên, hoặc dùng GEMINI_API_KEY của chủ app trong Streamlit Secrets. Nếu key riêng lỗi, app dừng bước đó để bạn xử lý; không tự dùng quota của chủ app thay thế.')

elif page == 'Bảo vệ dữ liệu':
    from services.privacy import protect_file, read_table, suggest_columns, pseudonymize, PrivacyError, master_key_status
    st.subheader('Bảo vệ dữ liệu trước khi phân tích')
    st.info('Bước 1: mã hóa file gốc để bảo vệ toàn bộ nội dung. Bước 2: chọn cách bảo vệ từng cột để tạo bản dữ liệu dùng cho kiểm toán. Bước 3: auditor review rồi tải file hoặc đưa vào cuộc kiểm toán.')
    st.caption('Thay bằng mã giả: thay tên hoặc thông tin nhận dạng bằng mã. Che giá trị: ẩn nội dung nhưng giữ cột. Giữ nguyên: giữ dữ liệu cần tính toán. Auditor cần kiểm tra lại mọi cột trước khi sử dụng.')
    sample_path = ROOT / 'demo' / 'loans_10.xlsx'
    if sample_path.is_file():
        st.download_button('Tải Excel giả lập 10 khách hàng — từng chỉ tiêu một cột', sample_path.read_bytes(),
                           'Nexus_Simulated_Loans_10.xlsx', XLSX_MIME, key='privacy_sample_download')
        st.caption('10 khách hàng hư cấu; mã giấy tờ ID-SIM, không phải CCCD thật.')
    if st.button('Xóa lựa chọn và kết quả trên màn hình', key='clear_private'):
        for item in ('private_job','private_reviewed'):
            st.session_state.pop(item,None)
        st.session_state['upload_generation']=st.session_state.get('upload_generation',0)+1
        st.rerun()
    file = st.file_uploader('Chọn file bất kỳ để mã hóa — tối đa 10 MB', key='private_upload_'+str(st.session_state.get('upload_generation',0)))
    vault_ready, vault_message = master_key_status()
    if not vault_ready:
        st.error('Chưa thể mã hóa vì khóa vault chưa được cấu hình đúng.')
        st.info('Liên hệ chủ ứng dụng để thiết lập khóa bảo vệ file trong phần quản trị Streamlit. Sau khi thiết lập, mở lại trang này và chọn file để tiếp tục.')
        with st.expander('Hướng dẫn dành cho chủ ứng dụng'):
            st.write('Xem file HUONG_DAN_BAO_VE_DU_LIEU.md trong gói mã nguồn. Khóa bảo vệ file được đặt trong Streamlit Secrets và cần giữ nguyên khi cập nhật ứng dụng.')
    elif file:
        raw = file.getvalue()
        fingerprint = hashlib.sha256(raw).hexdigest() + file.name
        job = st.session_state.get('private_job')
        if not job or job['fingerprint'] != fingerprint:
            st.caption('File đã tải lên nhưng chưa mã hóa. Bấm nút bên dưới để bắt đầu.')
            if st.button('Mã hóa file đã chọn', key='encrypt_'+hashlib.sha256(fingerprint.encode()).hexdigest()[:16], type='primary'):
                try:
                    with loading('Đang mã hóa file…'):
                        protected = protect_file(raw, file.name)
                    job = {'fingerprint': fingerprint, 'protected': protected}
                    st.session_state['private_job'] = job
                    st.session_state.pop('private_reviewed', None)
                except PrivacyError as exc:
                    st.error(str(exc))
                except OSError:
                    st.error('Không tạo được vault riêng tư; kiểm tra quyền ghi và cấu hình lưu trữ.')
        job = st.session_state.get('private_job')
        if job and job['fingerprint'] == fingerprint:
            protected = job['protected']
            st.success('Đã mã hóa toàn bộ file và lưu khóa từng file dưới dạng đã được mã hóa trong vault máy chủ.')
            st.caption('Mã lưu trữ file đã bảo vệ: ' + protected['file_id'])
            st.download_button('Tải file gốc đã mã hóa', protected['encrypted_bytes'], protected['download_name'], 'application/octet-stream', key='encrypted_download')
            if Path(file.name).suffix.lower() in ('.csv', '.xlsx'):
                try:
                    frame = read_table(raw, file.name)
                except PrivacyError as exc:
                    st.warning(str(exc)); st.stop()
                st.write(f'Bảng đọc được: {len(frame)} dòng, {len(frame.columns)} cột. Xuất giữ đủ cột và thứ tự. XLSX chỉ hỗ trợ một sheet dữ liệu không có công thức/ảnh/chart.')
                with st.form('privacy_review_' + protected['file_id']):
                    default_scope = st.session_state.setdefault('privacy_default_scope', 'AUDIT-' + os.urandom(8).hex())
                    scope = st.text_input('Mã phạm vi kiểm toán — dùng giống nhau cho hồ sơ vay và bảng phân quyền', default_scope)
                    suggestion = pd.DataFrame(suggest_columns(frame))
                    suggestion['action'] = suggestion['action'].map(readable.ACTIONS)
                    suggestion['meaning'] = suggestion['column'].map(readable.field)
                    plan = st.data_editor(suggestion, hide_index=True, width='stretch',
                        disabled=['column', 'meaning', 'reason'], num_rows='fixed',
                        column_config={'column': 'Tên cột trong file', 'meaning': 'Nội dung dữ liệu', 'reason': 'Vì sao được đề xuất', 'action': st.column_config.SelectboxColumn('Cách bảo vệ', options=list(readable.ACTIONS.values()), required=True)}, column_order=['column', 'meaning', 'action', 'reason'])
                    reviewer = st.selectbox('Người review phương án bảo vệ · chọn hoặc nhập tên', REVIEWERS, index=None, placeholder='Chọn hoặc gõ tên rồi nhấn Enter', accept_new_options=True)
                    checked = st.checkbox('Tôi đã đối chiếu file gốc; xác nhận các cột giữ nguyên được phép sử dụng cho kiểm toán')
                    submitted = st.form_submit_button('Duyệt và xuất bản mã giả')
                if submitted:
                    if not checked or not reviewer:
                        st.error('Chọn người review và xác nhận phương án xử lý cột.')
                    else:
                        try:
                            codes = {value: key for key, value in readable.ACTIONS.items()}
                            edited = [{'column': row['column'], 'action': codes[row['action']], 'reason': row['reason']} for row in plan.to_dict('records')]
                            with loading('Đang bảo vệ dữ liệu và tạo bảng đối chiếu…'):
                                reviewed = pseudonymize(frame, edited, scope, reviewer, protected['file_id'], source_bytes=raw, source_name=file.name)
                            reviewed['source_fingerprint'] = fingerprint
                            st.session_state['privacy_default_scope'] = scope.strip()
                            st.session_state['private_reviewed'] = reviewed
                            st.success('Đã tạo file đúng định dạng nguồn và bảng đối chiếu riêng để auditor tải xuống. Bảng đối chiếu chỉ dành cho auditor tải và lưu riêng.')
                        except PrivacyError as exc:
                            st.error(str(exc))
                        except OSError:
                            st.error('Không xử lý được file; chưa xuất bản mã giả.')
                reviewed = st.session_state.get('private_reviewed')
                if reviewed and reviewed['source_fingerprint'] == fingerprint:
                    st.caption('Nếu đổi phương án hoặc phạm vi, bấm Duyệt và xuất lại. Bản bên dưới là kết quả của lần duyệt đã lưu.')
                    st.dataframe(reviewed['frame'].head(20).rename(columns=readable.FIELDS), hide_index=True, width='stretch')
                    # The original XLSX has already passed the existing source-layout checks.
                    # CSV gets a separate workbook so Excel does not need to guess its delimiter.
                    if reviewed['export_filename'].lower().endswith('.xlsx'):
                        excel_bytes = reviewed['export_bytes']
                    else:
                        if 'download_xlsx_bytes' not in reviewed:
                            reviewed['download_xlsx_bytes'] = table_xlsx(reviewed['frame'])
                        excel_bytes = reviewed['download_xlsx_bytes']
                    st.download_button('1. Tải dữ liệu đã bảo vệ — Excel, mỗi chỉ tiêu một cột', excel_bytes,
                                       str(Path(reviewed['export_filename']).with_suffix('.xlsx')), XLSX_MIME, key='protected_xlsx_download')
                    if not reviewed['export_filename'].lower().endswith('.xlsx'):
                        st.download_button('Tải thêm bản đúng định dạng nguồn (CSV)', reviewed['export_bytes'],
                                           reviewed['export_filename'], reviewed['export_mime'], key='protected_csv_download')
                    st.caption('Nên chọn Excel (.xlsx) để mở trực tiếp với từng cột riêng. Bản CSV giữ dấu phân cách của nguồn; khi mở CSV trong Excel, cần chọn đúng dấu phân cách.')
                    st.warning('Bảng đối chiếu chứa giá trị gốc và mã tương ứng. Auditor cần lưu riêng ở nơi có quyền truy cập phù hợp; không đưa bảng này vào cuộc kiểm toán hoặc gửi cho AI. Biên bản Word bên dưới ghi nhận phương án và người review, không chứa giá trị gốc từng ô.')
                    if 'download_mapping_xlsx_bytes' not in reviewed:
                        reviewed['download_mapping_xlsx_bytes'] = mapping_xlsx(reviewed['audit_mapping_csv_bytes'])
                    st.download_button('2. Tải bảng đối chiếu chi tiết cho auditor — Excel', reviewed['download_mapping_xlsx_bytes'],
                                       'AUDITOR_ONLY_mapping_' + protected['file_id'] + '.xlsx', XLSX_MIME, key='auditor_mapping_download')
                    st.download_button('Tải thêm bảng đối chiếu CSV', readable.readable_mapping(reviewed['audit_mapping_csv_bytes']),
                                       'AUDITOR_ONLY_mapping_' + protected['file_id'] + '.csv', 'text/csv', key='auditor_mapping_csv_download')
                    st.download_button('3. Tải biên bản bảo vệ dữ liệu Word', readable.word_bytes(readable.privacy_report(reviewed)),
                                       'NEXUS_Bien_ban_bao_ve_' + protected['file_id'] + '.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', key='auditor_review_download')
                    st.caption('Bảng đối chiếu chỉ được giữ tạm trong RAM của phiên để phục vụ tải; tải và lưu riêng trước khi đóng/reboot app.')
                    st.caption('Mã tham chiếu bảng đối chiếu để auditor lưu trữ: ' + reviewed['mapping_reference'])
                    with st.form('import_private_' + protected['file_id']):
                        source = st.selectbox('Đưa bản đã review vào cuộc kiểm toán', ['loans', 'authorities'], format_func=lambda x: readable.SOURCES[x])
                        logical_id = st.text_input('Mã bộ dữ liệu để lưu và tra cứu', 'PROTECTED-DEMO')
                        imported = st.form_submit_button('Lưu dữ liệu đã bảo vệ vào cuộc kiểm toán')
                    if imported:
                        fields = {('dataset_id' if source == 'loans' else 'authority_id'): logical_id}
                        try:
                            result = mutate('/import/' + source, files={'file': ('protected.csv', reviewed['csv_bytes'])}, data=fields)
                            st.success('Đã lưu phiên bản dữ liệu đã bảo vệ để sử dụng trong cuộc kiểm toán.')
                            st.caption('Các thủ tục tự động hiện hỗ trợ cấu trúc hồ sơ Project 07. Bảng phân quyền sau khi thay mã là một bản mới; người quản trị cần đối chiếu và duyệt lại trước khi kiểm tra hạn mức.')
                        except ApiError as exc:
                            st.error(str(exc))
            else:
                st.caption('File này đã được mã hóa nguyên vẹn. Tự chọn phương án xử lý cột chỉ áp dụng với CSV/XLSX có cấu trúc.')
    st.warning('Vault local trên Streamlit Community Cloud không được xem là lưu trữ bền vững. Mất khóa chủ hoặc mất file khóa trong vault thì không thể giải mã; cần sao lưu có kiểm soát. Demo chưa có phân quyền tài khoản để dùng dữ liệu khách hàng thật.')

elif page == 'Dữ liệu & Audit Run':
    st.subheader('Tiếp nhận hồ sơ và tạo cuộc kiểm toán')
    st.caption('Chọn bộ dữ liệu, chính sách và bảng phân quyền sử dụng. Mỗi file được giữ theo phiên bản để có thể đối chiếu lại bằng chứng.')
    if st.button('Tiếp nhận bộ hồ sơ mẫu 10 khách hàng', type='primary'):
        try:
            definitions = [
                ('policies', 'POL-LOAN-01_compact.txt', {'policy_id': 'POL-LOAN-01', 'policy_set_id': 'BASELINE', 'effective_from': '2026-10-08T00:00:00+07:00'}),
                ('loans', 'loans_10.csv', {'dataset_id': 'DEMO-10'}),
                ('authorities', 'authorities_10.csv', {'authority_id': 'DEMO-AUTH-10'}),
            ]
            for endpoint, name, fields in definitions:
                mutate('/import/' + endpoint, files={'file': (name, (ROOT / 'demo' / name).read_bytes())}, data=fields)
            st.session_state['notice'] = 'Đã tiếp nhận bộ hồ sơ mẫu. Chọn phiên bản tài liệu bên dưới để tạo cuộc kiểm toán.'
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))
    with st.expander('Tải bộ hồ sơ mẫu 10 khách hàng'):
        for sample in ('loans_10.xlsx','loans_10.csv','POL-LOAN-01_compact.docx','POL-LOAN-01_compact.txt','authorities_10.xlsx','authorities_10.csv'):
            st.download_button(sample,(ROOT/'demo'/sample).read_bytes(),sample,key='sample_'+sample)
    with st.expander('Tiếp nhận tài liệu khác'):

        with st.form('upload'):
            kind = st.selectbox('Loại tài liệu', ['policies', 'loans', 'authorities'], format_func=lambda x: readable.SOURCES[x])
            file = st.file_uploader('TXT / DOCX / PDF / CSV / XLSX', type=['txt', 'docx', 'pdf', 'csv', 'xlsx'])
            logical = st.text_input('Mã nguồn', 'POL-LOAN-01')
            policy_set = st.text_input('Bộ quy định áp dụng', 'BASELINE')
            effective_date = st.date_input('Ngày hiệu lực của chính sách', value=date(2026, 10, 8), format='DD/MM/YYYY')
            effective_time = st.time_input('Giờ bắt đầu hiệu lực theo giờ Việt Nam', value=time(0, 0))
            effective = datetime.combine(effective_date, effective_time, tzinfo=ZoneInfo('Asia/Ho_Chi_Minh')).isoformat()
            submit = st.form_submit_button('Tiếp nhận file')
        if submit and file and kind in ('loans', 'authorities'):
            st.error('Dữ liệu bảng tùy chỉnh phải qua màn hình Bảo vệ dữ liệu; import bản mã giả sau khi review.')
        if submit and file and kind == 'policies':
            fields = {'policy_id': logical, 'policy_set_id': policy_set, 'effective_from': effective} if kind == 'policies' else {('dataset_id' if kind == 'loans' else 'authority_id'): logical}
            try:
                mutate('/import/' + kind, files={'file': (file.name, file.getvalue())}, data=fields)
                st.session_state['notice'] = 'Đã tiếp nhận phiên bản tài liệu mới.'
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))
    snaps = api('/snapshots')
    groups = {kind: [x for x in snaps if x['source_type'] == kind] for kind in ('policy', 'loans', 'authority')}
    if all(groups.values()):
        with st.form('create_run'):
            name = st.text_input('Tên cuộc kiểm toán', 'Project 07 — Demo tín dụng')
            chosen = {}
            for kind, field in [('policy', 'policy_snapshot_id'), ('loans', 'dataset_snapshot_id'), ('authority', 'authority_snapshot_id')]:
                options = groups[kind]
                item = st.selectbox(readable.SOURCES[kind] + ' sử dụng', range(len(options)), format_func=lambda i, options=options: f"{options[i]['filename']} · Phiên bản {options[i]['version']} · {readable.when(options[i].get('imported_at'))}")
                chosen[field] = options[item]['snapshot_id']
            submitted = st.form_submit_button('Tạo cuộc kiểm toán')
        if submitted:
            try:
                result = mutate('/audit-runs', dict(chosen, audit_name=name))
                st.session_state['active_run'] = result['run_id']
                st.session_state['notice'] = 'Đã tạo cuộc kiểm toán. Mở Ma trận rủi ro và kiểm soát để bắt đầu.'
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))
    else:
        st.info('Cần đủ chính sách, hồ sơ khoản vay và bảng phân quyền trước khi tạo cuộc kiểm toán.')
    st.markdown('### Quản lý file đã import')
    st.caption('Xóa được file chưa gắn vào cuộc kiểm toán. File đang sử dụng được giữ để bảo toàn bằng chứng. Xóa phiên bản dữ liệu không xóa file gốc đã mã hóa trong kho bảo vệ.')
    show_table(readable.snapshot_rows(snaps))
    unused=[item for item in snaps if not item.get('used_by_runs')]
    if unused:
        target=st.selectbox('File cần xóa',unused,format_func=lambda x:f"{x['filename']} · Phiên bản {x['version']}")
        confirm=st.checkbox('Tôi xác nhận xóa phiên bản file này và các dòng dữ liệu đã tiếp nhận',key='confirm_delete_'+target['snapshot_id'])
        if st.button('Xóa file đã import',disabled=not confirm,type='primary'):
            try:
                with loading('Đang xóa file đã import…'):
                    request('DELETE','/snapshots/'+target['snapshot_id'])
                st.session_state['notice']='Đã xóa file: '+target['filename']
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))
    elif snaps:
        st.info('Các file hiện có đều đang được sử dụng trong cuộc kiểm toán.')


else:
    if not rid:
        st.info('Tiếp nhận hồ sơ và tạo cuộc kiểm toán trước khi tiếp tục.')
        st.stop()
    base = '/audit-runs/' + rid
    wf = api(base + '/workflow')
    docs = {d['kind']: d for d in wf['documents']}
    if page in ('RCM', 'Test Plan'):
        kind, route, rows = ('RCM', 'rcm', 'controls') if page == 'RCM' else ('PLAN', 'test-plan', 'tests')
        document = docs.get(kind)
        approved = bool(document and document['state'] == 'APPROVED')
        st.subheader('Ma trận rủi ro và kiểm soát' if kind == 'RCM' else 'Kế hoạch kiểm tra kiểm toán')
        action('Tạo bản nháp bằng LLM', base + '/' + route + '/generate', disabled=approved)
        if kind == 'RCM':
            with st.expander('Chính sách nguồn để đối chiếu'):
                st.text(api('/policies/' + wf['run']['policy_snapshot_id'] + '/text')['extracted_text'])
        if document:
            st.write('Trạng thái: **' + readable.label(document['state']) + '** · Model đã dùng: ' + document['model'])
            show_sections({'sections': readable.document_sections(document)})
            download(document, kind + '_' + rid + '.json', kind + '_download')
            review_form('Auditor review ' + readable.KINDS[kind].lower(), base + '/' + route + '/approve', kind + '_approve', disabled=approved)

    elif page == 'Tests & Exceptions':
        st.subheader('Kết quả kiểm tra và ngoại lệ cần review')
        st.caption('Các thủ tục chạy sau khi ma trận rủi ro, kế hoạch kiểm tra, chính sách và bảng phân quyền đã được duyệt đúng phiên bản.')
        action('Chạy T01–T03 bằng Python', base + '/tests/execute')
        results = api(base + '/results')['results']
        reviews = {x['result_id']: x['review_state'] for x in wf['result_reviews']}
        for result in results:
            result['human_review'] = reviews.get(result['result_id'], 'PENDING')
        if results:
            download(results, 'results_' + rid + '.json', 'results_download')
            st.caption('Tệp tải xuống chứa toàn bộ kết quả. Bảng bên dưới thay đổi theo bộ lọc.')
            item = render_review_queue(results, rid)
            if item is not None:
                show_evidence(item)
                review_form('Review kết quả đang chọn', base + '/results/' + item['result_id'] + '/review',
                            'result_' + item['result_id'], decision_key='review_state')
        else:
            st.info('Chưa có kết quả. Hãy chạy T01–T03 sau khi hoàn tất các bước duyệt căn cứ và kế hoạch.')

    elif page == 'Findings':
        st.subheader('Phát hiện kiểm toán và bằng chứng')
        st.caption('Auditor cần kết luận từng ngoại lệ trước khi soạn phát hiện. Mỗi phát hiện phải nêu căn cứ chính sách và liên kết tới bằng chứng đã kiểm tra.')
        action('Soạn phát hiện kiểm toán bằng AI', base + '/findings/generate')
        document = docs.get('FINDINGS')
        if document:
            download(document, 'findings_' + rid + '.json', 'findings_download')
            states = {x['finding_key']: x['state'] for x in wf['finding_reviews']}
            for item in document['payload']['findings']:
                with st.expander(item['finding_key'] + ' — ' + item['title'] + ' · ' + readable.label(states.get(item['finding_key'], 'PENDING')), expanded=True):
                    for key in ('criteria', 'condition', 'risk', 'recommendation'):
                        st.markdown('**' + {'criteria': 'Tiêu chí và căn cứ', 'condition': 'Thực trạng quan sát', 'risk': 'Rủi ro có thể phát sinh', 'recommendation': 'Kiến nghị'}[key] + '**')
                        st.write(item[key])
                    criteria = item['criteria_evidence']
                    st.markdown('**Điều khoản chính sách làm căn cứ**')
                    st.write('Điều khoản: ' + str(criteria.get('clause', 'Chưa ghi nhận')))
                    st.write(criteria.get('source_quote', ''))
                    for evidence in item['evidence_details']:
                        st.markdown('**Bằng chứng hồ sơ ' + str(evidence.get('row_id', '')) + '**')
                        show_evidence(evidence)
                    review_form('Auditor review phát hiện này', '/findings/' + item['finding_key'] + '/review', 'finding_' + rid + '_' + item['finding_key'], extra={'run_id': rid}, decision_key='state')

    elif page == 'Report':
        st.subheader('Báo cáo kiểm toán chờ review')
        action('Soạn báo cáo từ các phát hiện đã xác nhận', base + '/report/generate', disabled=docs.get('REPORT', {}).get('state') == 'APPROVED')
        document = docs.get('REPORT')
        if document:
            st.write('Trạng thái review: **' + readable.label(document['state']) + '** · Phát hành: **Bản nháp**')
            for key in ('executive_summary', 'scope', 'methods', 'findings_summary', 'limitations', 'recommendations'):
                st.markdown('### ' + {'executive_summary': 'Tóm tắt điều hành', 'scope': 'Phạm vi kiểm toán', 'methods': 'Phương pháp thực hiện', 'findings_summary': 'Tổng hợp phát hiện', 'limitations': 'Giới hạn của cuộc kiểm toán', 'recommendations': 'Kiến nghị'}[key])
                st.write(document['payload'][key])
            with st.expander('Số liệu tổng hợp và danh mục bằng chứng'):
                show_table([{'Kết quả': readable.label(k), 'Số lượt kiểm tra': v} for k, v in document['payload'].get('deterministic_counts', {}).items()])
                for finding in document['payload'].get('evidence_appendix', []):
                    st.write(str(finding.get('finding_key', '')) + ' · ' + str(finding.get('title', '')))
                    for evidence in finding.get('evidence_details', []): show_evidence(evidence)
            download(document, 'report_DRAFT_' + rid + '.json', 'report_download')
            review_form('Con người review báo cáo', base + '/report/approve', 'report_approve', disabled=document['state'] == 'APPROVED')
            st.caption('Demo chưa có xác thực/phân quyền người duyệt, nên báo cáo vẫn DRAFT và backend chặn phát hành FINAL.')

    elif page == 'Evaluation':
        st.subheader('Báo cáo đánh giá cuộc kiểm toán')
        evaluation = api(base + '/evaluation')
        events = api(base + '/events')
        results = api(base + '/results')['results']
        all_sources = api('/snapshots')
        source_ids = {wf['run'][k] for k in ('policy_snapshot_id', 'dataset_snapshot_id', 'authority_snapshot_id')}
        sources = [x for x in all_sources if x['snapshot_id'] in source_ids]
        report = readable.evaluation_report(evaluation, wf, events, results, sources)
        st.caption('NEXUS · Hồ sơ đánh giá · Bản nháp cần auditor review')
        show_table([{'Thông tin báo cáo': k, 'Nội dung': v} for k, v in report['metadata']])
        st.download_button('Tải báo cáo đánh giá Word', readable.word_bytes(report),
                           'NEXUS_Bao_cao_danh_gia_' + rid[:8] + '.docx',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document', key='eval_word_download')
        show_sections(report)
