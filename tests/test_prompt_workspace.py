import importlib
import pytest
from fastapi.testclient import TestClient
from backend.contracts import groq_schema

module = importlib.import_module('backend.app')


@pytest.mark.parametrize('url', ['https://attacker.invalid/', 'http://127.0.0.1:8765/api/status', 'file:///C:/secret', 'https://www.saucedemo.com/?redirect=https://attacker.invalid', 'https://www.saucedemo.com@attacker.invalid/'])
def test_prompt_entry_rejects_unlisted_navigation(url):
    response = TestClient(module.app).post('/api/agent/runs', headers={'x-privacy-session':module.token}, json={'url':url,'task':'Read the page','provider':'groq'})
    assert response.status_code == 400


def test_prompt_entry_preserves_instructions_and_local_policy(monkeypatch):
    seen = []
    async def start(payload):
        seen.append(payload)
        return {'id':'test-run'}
    monkeypatch.setattr(module, 'start', start)
    response = TestClient(module.app).post('/api/agent/runs', headers={'x-privacy-session':module.token}, json={'url':'http://127.0.0.1:8766/scenario/support','task':'Choose Billing, write the reply and ask me before sending.','provider':'groq'})
    assert response.status_code == 200
    assert seen[0].scenario == 'support'
    assert seen[0].task.startswith('Choose Billing')
    assert seen[0].mode == 'contract'


def test_prompt_entry_requires_session():
    assert TestClient(module.app).post('/api/agent/runs', json={'url':'https://www.saucedemo.com/','task':'Read page'}).status_code == 401


def test_groq_wire_schema_stays_identical_across_observations():
    first = {'snapshot_id':'first','controls':[{'id':'one','role':'input','purpose':'password'}]}
    second = {'snapshot_id':'second','controls':[]}
    assert groq_schema(first, ['password']) == groq_schema(second, [])
    schema = str(groq_schema(second, []))
    assert 'anyOf' not in schema and "'enum': [None]" not in schema


def test_support_example_keeps_category_instruction_with_real_detector():
    from backend.privacy import Detector
    from backend.contracts import DEFAULT_TASKS
    detector = Detector()
    detector.initialize()
    assert detector.status['presidio']
    safe, _ = detector.sanitize(DEFAULT_TASKS['support'])
    assert '"Billing"' in safe
    assert 'Set the issue category' in safe
