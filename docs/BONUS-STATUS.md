# Bonus capabilities

| Capability | Implemented mechanism |
|---|---|
| Fully local AI | Ollama text planner using an on-device model, without cloud fallback. Team reported a successful local AI test on 30 October 2026. |
| Contextual PII detection | Local NER, OCR, face detection and DOM private-region hints alongside identifier rules. |
| Adaptive context preservation | Span-level masks, task-minimal observations, Public/Private profiles and approved sanitized-region disclosure. |
| Adversarial safeguards | Strict actions, snapshot checks, local secret scopes, payload leakage gate and synthetic misuse probes. |
| User privacy controls and explanations | Public/Private profiles, Draft only, explicit secret values and per-finding reasons. |
| Local secret injection | Task/origin/field/use-bound memory-only values, resolved during authorized execution. |
| Synthetic leakage testing | Known canaries and encoded-secret checks at the outgoing boundary. |
| Human approval | Approval for recognized consequential controls and extra sanitized image regions. |

## Scope
The local-model test is team-reported rather than a saved automated performance benchmark. Privacy profiles are explicit choices, not automatic public/private classification. Custom regex editing, a broad adversarial-webpage benchmark and general desktop control are outside this implementation. The demonstrated browser is Chrome for Testing; additional browser compatibility needs separate testing.

See [architecture](ARCHITECTURE.md), [evaluation](EVALUATION.md) and [demo](DEMO.md) for implementation details and reproducible evidence.
