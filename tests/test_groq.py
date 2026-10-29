import hashlib
import json

import httpx
import pytest

from backend.agent import Gateway
from backend.privacy import Detector, PrivacyError


async def test_groq_exact_bytes_key_isolation_and_text_contract(monkeypatch):
    captured = {}

    async def post(self, url, **kwargs):
        captured.update(url=url, **kwargs)
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"action": {"type": "done", "snapshot_id": "s_test"}})}}]})

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    gateway = Gateway(Detector())
    gateway.api_key = "gemini-key-canary"
    gateway.groq_api_key = "groq-key-canary"
    action, _ = await gateway.plan({"snapshot_id": "s_test", "regions": [{"id": "region_1"}]}, "Read", [], [], "groq")
    assert action.type == "done"
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer groq-key-canary"
    assert "x-goog-api-key" not in captured["headers"]
    assert b"key-canary" not in captured["content"]
    body = json.loads(captured["content"])
    assert body["response_format"]["json_schema"]["strict"] is True
    assert "request_context" not in json.dumps(body["response_format"])
    assert "anyOf" not in json.dumps(body["response_format"])
    assert "maxLength" not in json.dumps(body["response_format"])
    assert gateway.last_receipt["digest"] == hashlib.sha256(captured["content"]).hexdigest()
    assert gateway.last_receipt["destination"] == "Groq"
    assert gateway.last_receipt["image_disclosed"] is False


@pytest.mark.parametrize("key,image", [("", None), ("test-key", b"pixels")])
async def test_groq_rejects_missing_key_or_pixels_before_network(monkeypatch, key, image):
    async def post(*args, **kwargs):
        pytest.fail("Unsupported request must not leave the device")

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    gateway = Gateway(Detector())
    gateway.groq_api_key = key
    with pytest.raises(PrivacyError):
        await gateway.plan({}, "Read", [], [], "groq", image=image)
    assert gateway.last_receipt is None


async def test_groq_cannot_override_text_only_policy(monkeypatch):
    async def post(*args, **kwargs):
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"action": {"type": "request_context", "snapshot_id": "s_test", "region_id": "region_1"}})}}]})

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    gateway = Gateway(Detector())
    gateway.groq_api_key = "test-key"
    with pytest.raises(PrivacyError, match="action contract"):
        await gateway.plan({"snapshot_id": "s_test"}, "Read", [], [], "groq")


async def test_groq_bad_request_diagnostic_never_echoes_response(monkeypatch):
    async def post(*args, **kwargs):
        return httpx.Response(400, json={"error": "schema PRIVATE_CANARY"})

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    gateway = Gateway(Detector())
    gateway.groq_api_key = "test-key"
    with pytest.raises(PrivacyError, match="structured action schema") as exc:
        await gateway.plan({}, "Read", [], [], "groq")
    assert "PRIVATE_CANARY" not in str(exc.value)


@pytest.mark.parametrize("proposal", [
    {"type": "done", "snapshot_id": "stale"},
    {"type": "click", "snapshot_id": "s_test", "target_id": "invented"},
    {"type": "fill_public", "snapshot_id": "s_test", "target_id": "private_field", "text": "public"},
    {"type": "done", "snapshot_id": "s_test", "text": "unrelated"},
    {"type": "fill_public", "snapshot_id": "s_test", "target_id": "public_field", "text": "x" * 501},
])
async def test_fixed_schema_keeps_local_action_restrictions(monkeypatch, proposal):
    async def post(*args, **kwargs):
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"action": proposal})}}]})
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    gateway = Gateway(Detector())
    gateway.groq_api_key = "test-key"
    observation = {"snapshot_id": "s_test", "controls": [
        {"id": "private_field", "role": "input", "purpose": "password"},
        {"id": "public_field", "role": "input", "purpose": None},
    ]}
    with pytest.raises(PrivacyError, match="action contract"):
        await gateway.plan(observation, "Read", ["password"], [], "groq")


async def test_fixed_schema_accepts_unused_nulls(monkeypatch):
    async def post(*args, **kwargs):
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"action": {
            "type": "done", "snapshot_id": "s_test", "target_id": None,
            "text": None, "secret_ref": None, "direction": None,
        }})}}]})
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    gateway = Gateway(Detector())
    gateway.groq_api_key = "test-key"
    action, _ = await gateway.plan({"snapshot_id": "s_test"}, "Read", [], [], "groq")
    assert action.type == "done"


async def test_pacing_waits_for_budget_without_resending(monkeypatch):
    import backend.agent as agent
    clock = [100.0]
    waits = []
    monkeypatch.setattr(agent.time, "monotonic", lambda: clock[0])
    async def sleep(seconds):
        waits.append(seconds)
        clock[0] += seconds
    monkeypatch.setattr(agent.asyncio, "sleep", sleep)
    gateway = Gateway(Detector())
    await gateway.pace_groq(6000)
    await gateway.pace_groq(6000)
    await gateway.pace_groq(6000)
    assert waits == [61.0]
    assert len(gateway.groq_reservations) == 1


async def test_pacing_rejects_oversized_observation():
    gateway = Gateway(Detector())
    with pytest.raises(PrivacyError, match="request budget"):
        await gateway.pace_groq(25000)
    assert gateway.groq_reservations == []
