"""Small, explicit trust-boundary types. Unknown fields are always rejected."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Action(Strict):
    type: Literal[
        "click",
        "fill_public",
        "fill_secret",
        "select",
        "scroll",
        "wait",
        "request_context",
        "done",
    ]
    snapshot_id: str
    target_id: str | None = None
    text: str | None = Field(default=None, max_length=500)
    secret_ref: str | None = None
    region_id: str | None = None
    direction: Literal["up", "down"] | None = None

    @model_validator(mode="after")
    def complete(self):
        permitted = {
            "click": {"target_id"},
            "fill_public": {"target_id", "text"},
            "fill_secret": {"target_id", "secret_ref"},
            "select": {"target_id", "text"},
            "scroll": {"direction"},
            "wait": set(),
            "request_context": {"region_id"},
            "done": set(),
        }[self.type]
        for key in ["target_id", "text", "secret_ref", "region_id", "direction"]:
            value = getattr(self, key)
            if key in permitted and value is None:
                raise ValueError("Action is missing a required field")
            if key not in permitted and value is not None:
                raise ValueError("Action has an unrelated field")
        return self


class StartRequest(Strict):
    scenario: Literal[
        "checkout",
        "authentication",
        "support",
        "conference",
        "developer",
        "wikipedia",
        "saucedemo",
    ]
    task: str = Field(default="", max_length=2000)
    provider: Literal["demo", "gemini", "groq", "ollama"] = "demo"
    mode: Literal["contract", "baseline"] = "contract"
    privacy_profile: Literal["private", "public"] = "private"
    seed: int = Field(default=1, ge=1, le=10000)
    layout: int = Field(default=0, ge=0, le=1)


class ApprovalRequest(Strict):
    approval_id: str
    approved: bool


class PromptRequest(Strict):
    url: str = Field(min_length=1, max_length=500)
    task: str = Field(min_length=3, max_length=2000)
    provider: Literal["groq", "gemini", "ollama"] = "groq"


class SettingsRequest(Strict):
    api_key: str = Field(default="", max_length=300)
    gemini_model: str = Field(
        default="gemini-3.5-flash-lite", pattern=r"^[a-zA-Z0-9.\-]+$", max_length=80
    )
    groq_api_key: str = Field(default="", max_length=300)
    groq_model: Literal["openai/gpt-oss-120b", "openai/gpt-oss-20b"] = "openai/gpt-oss-120b"
    headless: bool = True


class SecretEntry(Strict):
    reference: str = Field(pattern=r"^[a-z_]{1,40}$")
    value: str = Field(min_length=1, max_length=500)


DEFAULT_TASKS = {
    "checkout": "Fill the checkout form using the permitted secret references, then review the order and request approval before placing it.",
    "authentication": "Fill the email, password and one-time code using local secret references, then sign in.",
    "support": 'Set the issue category to "Billing". Enter the public reply "I can help with your billing question.", and request approval to send it.',
    "conference": "Mute the microphone without disclosing participant identities or private chat.",
    "developer": "Open the key details and request approval before revoking the demo key.",
    "wikipedia": "Search Wikipedia for Privacy and open the article.",
    "saucedemo": "Log in using the permitted demonstration credentials, add the Sauce Labs Backpack to the cart, open the cart, and stop before checkout.",
}

PURPOSES = {
    "checkout": ["name", "address", "card", "cvv"],
    "authentication": ["email", "password", "otp"],
    "support": [],
    "conference": [],
    "developer": [],
    "wikipedia": [],
    "saucedemo": ["username", "password"],
}


def planner_schema(observation, refs, allow_context=True):
    """Expose only action shapes and handles valid for the current observation."""
    controls = [c for c in observation.get("controls", []) if not c.get("disabled")]
    targets = [c["id"] for c in controls]
    public = [
        c["id"]
        for c in controls
        if c["role"] in ("input", "textarea") and not c.get("purpose")
    ]
    protected = [
        c["id"]
        for c in controls
        if c["role"] in ("input", "textarea")
        and c.get("purpose") in refs
        and not c.get("filled")
    ]
    selections = [c["id"] for c in controls if c["role"] == "select"]
    regions = [r["id"] for r in observation.get("regions", [])]
    branches = []

    def branch(kind, fields):
        properties = {
            "type": {"type": "string", "enum": [kind]},
            "snapshot_id": {
                "type": "string",
                "enum": [observation.get("snapshot_id", "snapshot")],
            },
            **fields,
        }
        branches.append(
            {
                "type": "object",
                "properties": properties,
                "required": list(properties),
                "additionalProperties": False,
            }
        )

    if targets:
        branch("click", {"target_id": {"type": "string", "enum": targets}})
    if public:
        branch(
            "fill_public",
            {
                "target_id": {"type": "string", "enum": public},
                "text": {"type": "string", "maxLength": 500},
            },
        )
    if protected:
        branch(
            "fill_secret",
            {
                "target_id": {"type": "string", "enum": protected},
                "secret_ref": {"type": "string", "enum": refs},
            },
        )
    if selections:
        branch(
            "select",
            {
                "target_id": {"type": "string", "enum": selections},
                "text": {"type": "string", "maxLength": 500},
            },
        )
    if regions and allow_context:
        branch("request_context", {"region_id": {"type": "string", "enum": regions}})
    branch("scroll", {"direction": {"type": "string", "enum": ["up", "down"]}})
    branch("wait", {})
    branch("done", {})
    return {
        "type": "object",
        "properties": {"action": {"anyOf": branches}},
        "required": ["action"],
        "additionalProperties": False,
    }


def groq_schema(observation, refs):
    """Use one fixed object for the provider; enforce dependent fields locally."""
    properties = {
        "type": {"type": "string", "enum": ["click", "fill_public", "fill_secret", "select", "scroll", "wait", "done"]},
        "snapshot_id": {"type": "string"},
    }
    for field in ("target_id", "text", "secret_ref", "direction"):
        properties[field] = {"type": ["string", "null"]}
    return {
        "type": "object",
        "properties": {"action": {
            "type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False,
        }},
        "required": ["action"], "additionalProperties": False,
    }


def validate_text_proposal(action, observation, refs):
    """Keep the dynamic action contract authoritative regardless of cloud schema."""
    branches = planner_schema(observation, refs, allow_context=False)["properties"]["action"]["anyOf"]
    for branch in branches:
        properties = branch["properties"]
        if action.type != properties["type"]["enum"][0]:
            continue
        if all("enum" not in rule or getattr(action, field) in rule["enum"] for field, rule in properties.items()):
            return
    raise ValueError("Proposal is outside the current text action contract")
