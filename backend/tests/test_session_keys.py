"""Session credential routing: no network or live API keys."""
import asyncio
import json
import sys
import threading
from pathlib import Path

from services import gemini


def test_scoped_key_resets_on_error_and_redacts_both_keys(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'host-secret-test')
    try:
        with gemini.api_key_scope('visitor-secret-test'):
            assert gemini.effective_api_key() == 'visitor-secret-test'
            message = gemini.sanitized_message('host-secret-test visitor-secret-test')
            assert 'secret-test' not in message
            raise RuntimeError('test cleanup')
    except RuntimeError:
        pass
    assert gemini.effective_api_key() == 'host-secret-test'
    assert gemini.os.environ['GEMINI_API_KEY'] == 'host-secret-test'


def test_generation_uses_scoped_key_without_changing_environment(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'host-test')
    monkeypatch.setenv('PROJECT07_GEMINI_MODEL', 'model-host')
    headers = []
    def fake(req, timeout):
        headers.append((req.get_header('X-goog-api-key'), req.full_url))
        return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '{"controls": []}'}]}}]}
    monkeypatch.setattr(gemini, 'read_generation_response', fake)
    with gemini.api_key_scope('visitor-test', 'models/model-visitor'):
        assert gemini.generate('LLM1_RCM', '', {})[1] == 'model-visitor'
    gemini.generate('LLM1_RCM', '', {})
    assert headers[0][0] == 'visitor-test' and '/model-visitor:generateContent' in headers[0][1]
    assert headers[1][0] == 'host-test' and '/model-host:generateContent' in headers[1][1]
    assert gemini.os.environ['PROJECT07_GEMINI_MODEL'] == 'model-host'


def test_parallel_streamlit_requests_keep_separate_credentials(monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    import streamlit_runtime
    monkeypatch.setenv('GEMINI_API_KEY', 'host-test')
    barrier = threading.Barrier(2, timeout=10)
    models = {'visitor-a': 'model-a', 'visitor-b': 'model-b', 'host-test': 'model-host'}
    class Response:
        def __init__(self, model): self.model = model
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self):
            return json.dumps({'models': [{'name': 'models/' + self.model, 'supportedGenerationMethods': ['generateContent']}]}).encode()
    def fake(req, timeout):
        key = req.get_header('X-goog-api-key')
        if key != 'host-test': barrier.wait()
        return Response(models[key])
    monkeypatch.setattr(gemini.urllib.request, 'urlopen', fake)
    async def parallel():
        return await asyncio.gather(*[
            streamlit_runtime._request('POST', '/llm/check', gemini_api_key=key, gemini_model='selected-' + key)
            for key in ('visitor-a', 'visitor-b')])
    a, b = asyncio.run(parallel())
    assert a['generate_content_models'] == ['model-a']
    assert b['generate_content_models'] == ['model-b']
    assert a['configured_model'] == 'selected-visitor-a'
    assert b['configured_model'] == 'selected-visitor-b'
    assert streamlit_runtime.request('POST', '/llm/check')['generate_content_models'] == ['model-host']
    assert gemini.effective_api_key() == 'host-test'


def test_invalid_session_model_stops_before_network(monkeypatch):
    import pytest
    monkeypatch.setattr(gemini, 'read_generation_response', lambda *args: pytest.fail('invalid model reached network'))
    with gemini.api_key_scope('visitor-test', '../invalid-model'):
        with pytest.raises(gemini.GeminiError, match='Invalid PROJECT07_GEMINI_MODEL'):
            gemini.generate('LLM1_RCM', '', {})


def test_failed_call_logs_selected_session_model(client, monkeypatch):
    import pytest
    from fastapi import HTTPException
    from services import workflow
    from models.db import connect
    def fail(*args): raise gemini.GeminiError('MODEL_RATE_LIMIT', 'test quota exceeded')
    monkeypatch.setattr(gemini, 'generate', fail)
    with gemini.api_key_scope('visitor-test', 'model-session-quota'):
        with pytest.raises(HTTPException):
            workflow.llm_generate('run-test', 'LLM3_FINDINGS', '', {})
    with connect() as c:
        row = c.execute('SELECT model,status FROM llm_calls ORDER BY created_at DESC LIMIT 1').fetchone()
    assert row['model'] == 'model-session-quota' and row['status'] == 'ERROR'
