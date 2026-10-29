import json
import pytest
import httpx
from backend.agent import Gateway, PermitVault
from backend.privacy import Detector, PrivacyError


@pytest.mark.parametrize("status", [401, 402, 403, 404, 429, 500, 503])
async def test_provider_errors_do_not_fallback(monkeypatch, status):
    count = 0

    async def post(*args, **kw):
        nonlocal count
        count += 1
        return httpx.Response(status, json={"error": "RAW_SECRET_MUST_NOT_APPEAR"})

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    g = Gateway(Detector())
    g.api_key = "test"
    with pytest.raises(PrivacyError) as e:
        await g.plan({"context": "public"}, "read", [], [], "gemini")
    assert "RAW_SECRET" not in str(e.value) and count == 1
    assert g.last_receipt["transport"] == "response received"
    assert g.last_receipt["http_status"] == status
    assert g.provider_status["http_status"] == status
    assert "RAW_SECRET" not in json.dumps(g.provider_status)
    if status == 402:
        assert g.provider_status["state"] == "billing_required"
        assert "billing" in str(e.value)


async def test_transport_failure_is_safe_and_not_retried(monkeypatch):
    calls = []

    async def post(*args, **kwargs):
        calls.append(1)
        raise httpx.ReadTimeout("PRIVATE_CANARY")

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    gateway = Gateway(Detector())
    gateway.api_key = "PRIVATE_KEY"
    with pytest.raises(PrivacyError) as exc:
        await gateway.plan({}, "read", [], [], "gemini")
    assert len(calls) == 1
    assert "PRIVATE" not in str(exc.value)
    assert gateway.provider_status["state"] == "connection_error"
    assert gateway.last_receipt["transport"] == "attempted"


@pytest.mark.parametrize("malformed_json", [False, True])
async def test_invalid_model_response(monkeypatch, malformed_json):
    async def post(*a, **kw):
        if malformed_json:
            return httpx.Response(200, text="PRIVATE_CANARY")
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {"content": {"parts": [{"text": "execute arbitrary javascript"}]}}
                ]
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    g = Gateway(Detector())
    g.api_key = "test"
    with pytest.raises(PrivacyError, match="action contract"):
        await g.plan({}, "read", [], [], "gemini")
    assert g.provider_status["state"] == "invalid_response"
    assert "PRIVATE_CANARY" not in json.dumps(g.provider_status)


async def test_key_required_before_network(monkeypatch):
    async def post(*a, **kw):
        pytest.fail("No key should mean no request")

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    with pytest.raises(PrivacyError, match="API key"):
        await Gateway(Detector()).plan({}, "read", [], [], "gemini")


def test_validation_errors_never_echo_secrets():
    from fastapi.testclient import TestClient
    from backend.app import app, token

    response = TestClient(app).post(
        "/api/settings",
        headers={"x-privacy-session": token},
        json={"api_key": "PRIVATE_CANARY", "gemini_model": "invalid/path"},
    )
    assert response.status_code == 422 and "PRIVATE_CANARY" not in response.text
