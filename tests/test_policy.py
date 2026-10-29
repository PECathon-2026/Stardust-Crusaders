import base64, json
import pytest
from PIL import Image
import io
from backend.privacy import Detector, PrivacyError, leak_check, redact_image
from backend.agent import PermitVault, consequential, Gateway
from backend.contracts import Action
from backend.fixtures import values
from backend.evaluation import attack_lab


@pytest.fixture
def detector():
    return Detector()


@pytest.mark.parametrize(
    "text",
    [
        "person@example.test",
        "ABCDE1234F",
        "4111 1111 1111 1111",
        "98765 10001",
        "192.168.1.4",
        "ghp_" + "a" * 36,
        "password: secretvalue",
        "person\u200b@example.test",
    ],
)
def test_sensitive_patterns(detector, text):
    assert detector.detect(text)
    assert text not in detector.sanitize(text)[0]


@pytest.mark.parametrize(
    "text",
    [
        "Order ORD-2026-114 costs 1299 rupees.",
        "Build version 1.4.2",
        "Quantity: 3. Discount: 15%.",
    ],
)
def test_public_context_survives(detector, text):
    assert detector.sanitize(text)[0] == text


@pytest.mark.parametrize(
    "key", ["text", "data", "image_base64", "history", "title", "url"]
)
def test_no_unchecked_payload_fields(detector, key):
    with pytest.raises(PrivacyError):
        leak_check(
            json.dumps({key: "DemoOnly!1Private"}).encode(),
            ["DemoOnly!1Private"],
            detector,
        )


@pytest.mark.parametrize(
    "secret",
    [
        "DemoOnly!1Private",
        "DemoOnly%211Private",
        base64.b64encode(b"DemoOnly!1Private").decode(),
    ],
)
def test_encoded_known_secret(detector, secret):
    with pytest.raises(PrivacyError):
        leak_check(
            json.dumps({"text": secret}).encode(), ["DemoOnly!1Private"], detector
        )


def test_image_bypass_exact_bytes_and_path(detector):
    b = b"sanitized image"
    body = {
        "contents": [
            {
                "parts": [
                    {"text": "Public"},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64.b64encode(b).decode(),
                        }
                    },
                ]
            }
        ]
    }
    assert leak_check(json.dumps(body).encode(), [], detector, approved_image=b)
    with pytest.raises(PrivacyError):
        leak_check(json.dumps(body).encode(), [], detector, approved_image=b"other")


def test_opaque_mask_is_irreversible():
    img = Image.new("RGB", (50, 50), "red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    out = Image.open(
        io.BytesIO(
            redact_image(buf.getvalue(), [{"x": 5, "y": 5, "width": 20, "height": 20}])
        )
    )
    assert out.getpixel((10, 10)) == (24, 62, 55)
    assert out.getpixel((40, 40)) == (255, 0, 0)


def test_scoped_secret_uses():
    v = PermitVault("authentication", "http://allowed", values())
    for _ in range(2):
        assert v.resolve("password", "password", "http://allowed")
        v.consume("password")
    with pytest.raises(PrivacyError):
        v.resolve("password", "password", "http://allowed")


@pytest.mark.parametrize(
    "action",
    [
        {"type": "javascript", "text": "alert(1)"},
        {"type": "click", "target_id": "x", "url": "https://bad.invalid"},
        {"type": "fill_secret", "target_id": "x"},
        {"type": "done", "text": "secret"},
    ],
)
def test_action_schema_rejects_unsupported(action):
    with pytest.raises(ValueError):
        Action.model_validate({"snapshot_id": "s", **action})


def test_attack_suite(detector):
    r = attack_lab(detector)
    assert r["blocked"] == r["total"] == 8


def test_consequential():
    assert consequential({"label": "Place demo order"})
    assert consequential({"label": "Revoke demo key"})
    assert not consequential({"label": "Open key details"})


def test_planner_schema_excludes_completed_secret_fields():
    from backend.contracts import planner_schema

    obs = {
        "snapshot_id": "s_abc",
        "controls": [
            {
                "id": "e_a",
                "role": "input",
                "purpose": "password",
                "filled": True,
                "disabled": False,
            }
        ],
        "regions": [],
    }
    schema = planner_schema(obs, ["password"])
    assert "fill_secret" not in json.dumps(schema)
    obs["controls"][0]["filled"] = False
    schema = planner_schema(obs, ["password"])
    branch = next(
        b
        for b in schema["properties"]["action"]["anyOf"]
        if b["properties"]["type"]["enum"] == ["fill_secret"]
    )
    assert branch["required"] == ["type", "snapshot_id", "target_id", "secret_ref"]
    assert branch["additionalProperties"] is False


def test_public_dictionary_never_overrides_known_secret(detector):
    safe, _ = detector.sanitize(
        "Sauce Labs Backpack", ["Sauce Labs Backpack"], ["Sauce Labs Backpack"]
    )
    assert "Sauce Labs Backpack" not in safe


@pytest.mark.asyncio
async def test_gateway_exact_transport(monkeypatch, detector):
    import httpx

    captured = []

    async def fake_post(self, url, content, headers):
        captured.append(content)
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": json.dumps(
                                        {"type": "done", "snapshot_id": "snapshot"}
                                    )
                                }
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    g = Gateway(detector)
    g.api_key = "synthetic-test-key"
    action, receipt = await g.plan(
        {"snapshot_id": "snapshot", "context": "Public"},
        "Read public context",
        [],
        ["DemoOnly!1Private"],
        "gemini",
    )
    assert action.type == "done" and len(captured) == 1
    import hashlib

    assert receipt["digest"] == hashlib.sha256(captured[0]).hexdigest()
    assert b"DemoOnly!1Private" not in captured[0]


@pytest.mark.asyncio
async def test_gateway_rejects_before_transport(monkeypatch, detector):
    import httpx

    async def unexpected(*args, **kw):
        pytest.fail("Unapproved request reached transport")

    monkeypatch.setattr(httpx.AsyncClient, "post", unexpected)
    g = Gateway(detector)
    g.api_key = "synthetic"
    with pytest.raises(PrivacyError):
        await g.plan({"context": "person@example.test"}, "Read", [], [], "gemini")
