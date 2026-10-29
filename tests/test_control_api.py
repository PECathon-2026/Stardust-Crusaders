from fastapi.testclient import TestClient
from backend.app import app, token


def test_session_is_required():
    c = TestClient(app)
    assert c.get("/api/status").status_code == 401
    assert c.get("/api/status", headers={"x-privacy-session": token}).status_code == 200


def test_cross_origin_and_rebinding_rejected():
    c = TestClient(app)
    for headers in [
        {"origin": "https://attacker.invalid"},
        {"host": "attacker.invalid"},
        {"sec-fetch-site": "cross-site"},
    ]:
        assert c.get("/api/bootstrap", headers=headers).status_code == 403


def test_forged_approval():
    assert (
        TestClient(app)
        .post(
            "/api/approve",
            headers={"x-privacy-session": token},
            json={"approval_id": "forged", "approved": True},
        )
        .status_code
        == 409
    )
